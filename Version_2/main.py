"""
Live AI Voice Translator - Gemini Live API Backend
Real-time multilingual voice translation using Gemini Live API with
Google Cloud Text-to-Speech and Translation.
"""

import base64
import asyncio
import json
import os
import logging
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.cloud import texttospeech_v1 as texttospeech
from google.cloud import translate_v2 as translate

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("LOCATION", "us-central1")
USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"

# Model for live audio streaming
LIVE_MODEL = os.getenv("LIVE_MODEL", "gemini-2.5-flash")
# Model for text-based translation
TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-2.5-flash")

SESSION_TIME_LIMIT = int(os.getenv("SESSION_TIME_LIMIT", "300"))

# --- Initialize Clients ---
if USE_VERTEX:
    gemini_client = genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=LOCATION,
    )
else:
    gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

tts_client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

# --- Supported Languages ---
LANGUAGES = {
    "en": {"name": "English", "tts_code": "en-US"},
    "es": {"name": "Spanish", "tts_code": "es-ES"},
    "fr": {"name": "French", "tts_code": "fr-FR"},
    "de": {"name": "German", "tts_code": "de-DE"},
    "it": {"name": "Italian", "tts_code": "it-IT"},
    "pt": {"name": "Portuguese", "tts_code": "pt-BR"},
    "ja": {"name": "Japanese", "tts_code": "ja-JP"},
    "ko": {"name": "Korean", "tts_code": "ko-KR"},
    "zh": {"name": "Chinese (Mandarin)", "tts_code": "cmn-CN"},
    "hi": {"name": "Hindi", "tts_code": "hi-IN"},
    "ar": {"name": "Arabic", "tts_code": "ar-XA"},
    "ru": {"name": "Russian", "tts_code": "ru-RU"},
    "tr": {"name": "Turkish", "tts_code": "tr-TR"},
    "vi": {"name": "Vietnamese", "tts_code": "vi-VN"},
    "th": {"name": "Thai", "tts_code": "th-TH"},
    "nl": {"name": "Dutch", "tts_code": "nl-NL"},
    "pl": {"name": "Polish", "tts_code": "pl-PL"},
    "sv": {"name": "Swedish", "tts_code": "sv-SE"},
    "da": {"name": "Danish", "tts_code": "da-DK"},
    "fi": {"name": "Finnish", "tts_code": "fi-FI"},
}

# --- FastAPI App ---
app = FastAPI(
    title="Live AI Voice Translator",
    description="Real-time voice translation powered by Gemini Live API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_index():
    """Serve the main frontend page."""
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "live-ai-voice-translator"}


@app.get("/api/languages")
async def get_languages():
    """Return supported languages."""
    return {code: info["name"] for code, info in LANGUAGES.items()}


def synthesize_speech_sync(text: str, target_lang: str) -> bytes:
    """Convert text to speech using Google Cloud TTS."""
    lang_info = LANGUAGES.get(target_lang, LANGUAGES["en"])
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_info["tts_code"],
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )
    return response.audio_content


def translate_text_sync(text: str, target_lang: str) -> str:
    """Translate text using Google Cloud Translation API."""
    if not text.strip():
        return ""
    result = translate_client.translate(text, target_language=target_lang)
    return result["translatedText"]


@app.websocket("/ws/translate")
async def websocket_translate(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice translation using Gemini Live API.

    Protocol:
    1. Client sends config JSON: {"source_lang": "en", "target_lang": "es"}
    2. Client sends audio as binary (raw PCM 16-bit 16kHz) or base64 JSON
    3. Server streams back transcription, translation, and TTS audio
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    try:
        # Step 1: Receive language configuration
        config_data = await websocket.receive_text()
        config = json.loads(config_data)
        source_lang = config.get("source_lang", "en")
        target_lang = config.get("target_lang", "es")
        source_name = LANGUAGES.get(source_lang, {}).get("name", "English")
        target_name = LANGUAGES.get(target_lang, {}).get("name", "Spanish")

        await websocket.send_json({
            "type": "status",
            "message": f"Connected. Translating {source_name} to {target_name}",
        })

        logger.info(f"Translation session: {source_name} -> {target_name}")

        # Step 2: Set up Gemini Live API session
        system_instruction = (
            f"You are a real-time voice translator. "
            f"The user will speak in {source_name}. "
            f"Your job is to:\n"
            f"1. Listen carefully to what the user says in {source_name}\n"
            f"2. Transcribe it accurately\n"
            f"3. Translate it to {target_name}\n"
            f"Respond ONLY with a JSON object in this exact format:\n"
            f'{{"transcription": "<what the user said in {source_name}>", '
            f'"translation": "<the translation in {target_name}>"}}\n'
            f"Do NOT add any extra text outside the JSON. "
            f"Do NOT add markdown formatting."
        )

        live_config = types.LiveConnectConfig(
            response_modalities=[types.Modality.TEXT],
            system_instruction=types.Content(
                parts=[types.Part(text=system_instruction)]
            ),
            input_audio_transcription=types.AudioTranscriptionConfig(),
        )

        async with gemini_client.aio.live.connect(
            model=LIVE_MODEL, config=live_config
        ) as session:
            await websocket.send_json({
                "type": "status",
                "message": "Live session ready. Start speaking!",
            })

            audio_input_queue = asyncio.Queue()

            # Task: receive audio from browser and queue it
            async def receive_from_client():
                try:
                    while True:
                        message = await websocket.receive()

                        if "bytes" in message and message["bytes"]:
                            # Binary audio data
                            await audio_input_queue.put(message["bytes"])
                        elif "text" in message and message["text"]:
                            try:
                                data = json.loads(message["text"])
                                if data.get("type") == "audio":
                                    # Base64 encoded audio
                                    audio_bytes = base64.b64decode(data["audio"])
                                    await audio_input_queue.put(audio_bytes)
                                elif data.get("type") == "text":
                                    # Direct text input for translation
                                    text = data.get("text", "")
                                    if text.strip():
                                        await process_text_translation(
                                            websocket, text, source_lang,
                                            target_lang, source_name, target_name
                                        )
                                elif data.get("type") == "end":
                                    break
                            except json.JSONDecodeError:
                                pass
                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                except Exception as e:
                    logger.error(f"Error receiving from client: {e}")

            # Task: stream audio from queue to Gemini
            async def send_audio_to_gemini():
                try:
                    while True:
                        chunk = await audio_input_queue.get()
                        await session.send_realtime_input(
                            audio=types.Blob(
                                data=chunk,
                                mime_type="audio/pcm;rate=16000",
                            )
                        )
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Error sending audio to Gemini: {e}")

            # Task: receive responses from Gemini and send to client
            async def receive_from_gemini():
                text_buffer = ""
                try:
                    async for response in session.receive():
                        server_content = response.server_content
                        if server_content is None:
                            continue

                        # Accumulate text from model turn
                        if server_content.model_turn:
                            for part in server_content.model_turn.parts:
                                if part.text:
                                    text_buffer += part.text

                        # Input transcription (what the user said)
                        if server_content.input_transcription:
                            transcript = server_content.input_transcription.text
                            if transcript:
                                await websocket.send_json({
                                    "type": "input_transcription",
                                    "text": transcript,
                                    "lang": source_name,
                                })

                        # When model finishes its turn, process the translation
                        if server_content.turn_complete:
                            if text_buffer.strip():
                                await process_gemini_response(
                                    websocket, text_buffer, target_lang, target_name
                                )
                            text_buffer = ""

                            await websocket.send_json({
                                "type": "turn_complete",
                            })

                        # Handle interruption (barge-in)
                        if server_content.interrupted:
                            text_buffer = ""
                            await websocket.send_json({
                                "type": "interrupted",
                            })

                except Exception as e:
                    logger.error(f"Error in Gemini receive loop: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Gemini error: {str(e)}",
                    })

            # Run all tasks concurrently with timeout
            client_task = asyncio.create_task(receive_from_client())
            audio_task = asyncio.create_task(send_audio_to_gemini())
            gemini_task = asyncio.create_task(receive_from_gemini())

            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        client_task, audio_task, gemini_task,
                        return_exceptions=True,
                    ),
                    timeout=SESSION_TIME_LIMIT,
                )
            except asyncio.TimeoutError:
                logger.info("Session time limit reached")
                await websocket.send_json({
                    "type": "status",
                    "message": "Session time limit reached.",
                })
            finally:
                client_task.cancel()
                audio_task.cancel()
                gemini_task.cancel()

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


async def process_gemini_response(
    websocket: WebSocket, text: str, target_lang: str, target_name: str
):
    """Parse Gemini's JSON response, extract translation, generate TTS."""
    transcription = ""
    translation = ""

    try:
        text_clean = text.strip()
        if text_clean.startswith("```"):
            lines = text_clean.split("\n")
            text_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else text_clean
        parsed = json.loads(text_clean)
        transcription = parsed.get("transcription", "")
        translation = parsed.get("translation", "")
    except json.JSONDecodeError:
        # Fallback: use Cloud Translation
        transcription = text.strip()
        try:
            loop = asyncio.get_event_loop()
            translation = await loop.run_in_executor(
                None, translate_text_sync, transcription, target_lang
            )
        except Exception as e:
            translation = f"[Translation error: {e}]"

    if not translation:
        return

    # Send text translation to client
    await websocket.send_json({
        "type": "translation",
        "transcription": transcription,
        "translation": translation,
        "target_lang": target_name,
    })

    # Generate TTS audio for the translation
    try:
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(
            None, synthesize_speech_sync, translation, target_lang
        )
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        await websocket.send_json({
            "type": "tts_audio",
            "audio": audio_b64,
            "format": "mp3",
        })
    except Exception as e:
        logger.error(f"TTS error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"TTS error: {str(e)}",
        })


async def process_text_translation(
    websocket: WebSocket, text: str, source_lang: str,
    target_lang: str, source_name: str, target_name: str
):
    """Handle direct text translation (non-audio path)."""
    try:
        prompt = (
            f"Translate the following {source_name} text to {target_name}. "
            f'Return ONLY JSON: {{"transcription": "<original>", "translation": "<translated>"}}\n\n'
            f"Text: {text}"
        )
        response = gemini_client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt,
        )
        resp_text = response.text.strip()
        if resp_text.startswith("```"):
            lines = resp_text.split("\n")
            resp_text = "\n".join(lines[1:-1])
        result = json.loads(resp_text)
        transcription = result.get("transcription", text)
        translation = result.get("translation", "")
    except Exception:
        transcription = text
        try:
            loop = asyncio.get_event_loop()
            translation = await loop.run_in_executor(
                None, translate_text_sync, text, target_lang
            )
        except Exception as e:
            translation = f"[Error: {e}]"

    await websocket.send_json({
        "type": "translation",
        "transcription": transcription,
        "translation": translation,
        "target_lang": target_name,
    })

    # TTS
    if translation and not translation.startswith("["):
        try:
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(
                None, synthesize_speech_sync, translation, target_lang
            )
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            await websocket.send_json({
                "type": "tts_audio",
                "audio": audio_b64,
                "format": "mp3",
            })
        except Exception as e:
            logger.error(f"TTS error: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
