"""
Live AI Voice Translator - FastAPI Backend Server
Handles WebSocket connections for real-time audio streaming with Gemini Live API
and Google Cloud Text-to-Speech for translated audio output.
"""

import asyncio
import base64
import json
import os
import struct
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from google.cloud import texttospeech_v1 as texttospeech
from google.cloud import translate_v2 as translate

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# Gemini Live API model
GEMINI_MODEL = "gemini-2.0-flash-live-001"

# Supported languages mapping
LANGUAGES = {
    "en": {"name": "English", "bcp47": "en-US", "tts_code": "en-US"},
    "es": {"name": "Spanish", "bcp47": "es-ES", "tts_code": "es-ES"},
    "fr": {"name": "French", "bcp47": "fr-FR", "tts_code": "fr-FR"},
    "de": {"name": "German", "bcp47": "de-DE", "tts_code": "de-DE"},
    "it": {"name": "Italian", "bcp47": "it-IT", "tts_code": "it-IT"},
    "pt": {"name": "Portuguese", "bcp47": "pt-BR", "tts_code": "pt-BR"},
    "ja": {"name": "Japanese", "bcp47": "ja-JP", "tts_code": "ja-JP"},
    "ko": {"name": "Korean", "bcp47": "ko-KR", "tts_code": "ko-KR"},
    "zh": {"name": "Chinese", "bcp47": "zh-CN", "tts_code": "cmn-CN"},
    "hi": {"name": "Hindi", "bcp47": "hi-IN", "tts_code": "hi-IN"},
    "ar": {"name": "Arabic", "bcp47": "ar-XA", "tts_code": "ar-XA"},
    "ru": {"name": "Russian", "bcp47": "ru-RU", "tts_code": "ru-RU"},
    "tr": {"name": "Turkish", "bcp47": "tr-TR", "tts_code": "tr-TR"},
    "vi": {"name": "Vietnamese", "bcp47": "vi-VN", "tts_code": "vi-VN"},
    "th": {"name": "Thai", "bcp47": "th-TH", "tts_code": "th-TH"},
}


# Initialize clients
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
tts_client = texttospeech.TextToSpeechAsyncClient()
translate_client = translate.Client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 Live AI Voice Translator backend starting...")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Live AI Voice Translator",
    description="Real-time multilingual voice translation powered by Gemini Live API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/languages")
async def get_languages():
    """Return supported languages."""
    return {code: info["name"] for code, info in LANGUAGES.items()}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "live-ai-voice-translator"}


async def synthesize_speech(text: str, target_lang: str) -> bytes:
    """Convert translated text to speech using Google Cloud TTS."""
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

    response = await tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )
    return response.audio_content


async def translate_text(text: str, target_lang: str) -> str:
    """Translate text using Google Cloud Translation API."""
    if not text.strip():
        return ""
    result = translate_client.translate(text, target_language=target_lang)
    return result["translatedText"]


@app.websocket("/ws/translate")
async def websocket_translate(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice translation.

    Protocol:
    1. Client sends JSON config: {"source_lang": "en", "target_lang": "es"}
    2. Client sends audio chunks as base64: {"audio": "<base64_pcm_data>"}
    3. Server responds with transcription, translation, and translated audio.
    """
    await websocket.accept()
    session = None

    try:
        # Step 1: Receive configuration
        config_data = await websocket.receive_json()
        source_lang = config_data.get("source_lang", "en")
        target_lang = config_data.get("target_lang", "es")
        source_name = LANGUAGES.get(source_lang, {}).get("name", "English")
        target_name = LANGUAGES.get(target_lang, {}).get("name", "Spanish")

        await websocket.send_json({
            "type": "status",
            "message": f"Connected. Translating {source_name} → {target_name}",
        })

        # Step 2: Configure Gemini Live session for transcription
        system_instruction = (
            f"You are a real-time voice translator. "
            f"Listen to the user speaking in {source_name}. "
            f"First, transcribe exactly what they said in {source_name}. "
            f"Then, translate it to {target_name}. "
            f"Respond ONLY with a JSON object in this exact format: "
            f'{{"transcription": "<what the user said in {source_name}>", '
            f'"translation": "<the translation in {target_name}>"}}'
            f"\nDo NOT add any extra text, explanation, or formatting outside the JSON."
        )

        live_config = {
            "response_modalities": ["TEXT"],
            "system_instruction": system_instruction,
        }

        session = await gemini_client.aio.live.connect(
            model=GEMINI_MODEL,
            config=live_config,
        )

        await websocket.send_json({
            "type": "status",
            "message": "Gemini Live session connected. Start speaking!",
        })

        # Step 3: Handle bidirectional streaming
        async def receive_from_client():
            """Receive audio from the client and forward to Gemini."""
            try:
                while True:
                    data = await websocket.receive_json()
                    if data.get("type") == "audio":
                        audio_bytes = base64.b64decode(data["audio"])
                        await session.send_realtime_input(
                            audio=types.Blob(
                                data=audio_bytes,
                                mime_type="audio/pcm;rate=16000",
                            )
                        )
                    elif data.get("type") == "end":
                        break
            except WebSocketDisconnect:
                pass

        async def receive_from_gemini():
            """Receive responses from Gemini session and send to client."""
            text_buffer = ""
            try:
                async for response in session.receive():
                    content = response.server_content
                    if content is None:
                        continue

                    # Handle text responses
                    if content.model_turn:
                        for part in content.model_turn.parts:
                            if part.text:
                                text_buffer += part.text

                    # When turn is complete, process the accumulated text
                    if content.turn_complete:
                        if text_buffer.strip():
                            await process_translation(
                                websocket, text_buffer, target_lang
                            )
                        text_buffer = ""

                    # Handle input transcription from Gemini
                    if content.input_transcription:
                        await websocket.send_json({
                            "type": "input_transcription",
                            "text": content.input_transcription.text,
                        })

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Gemini session error: {str(e)}",
                })

        # Run both tasks concurrently
        await asyncio.gather(
            receive_from_client(),
            receive_from_gemini(),
            return_exceptions=True,
        )

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        if session:
            try:
                await session.close()
            except Exception:
                pass


async def process_translation(websocket: WebSocket, text: str, target_lang: str):
    """Process raw Gemini response, extract translation, and generate TTS audio."""
    transcription = ""
    translation = ""

    # Try to parse JSON response from Gemini
    try:
        text_clean = text.strip()
        # Handle markdown code blocks
        if text_clean.startswith("```"):
            lines = text_clean.split("\n")
            text_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else text_clean
        parsed = json.loads(text_clean)
        transcription = parsed.get("transcription", "")
        translation = parsed.get("translation", "")
    except json.JSONDecodeError:
        # If Gemini didn't return JSON, use Cloud Translation as fallback
        transcription = text.strip()
        try:
            translation = await translate_text(transcription, target_lang)
        except Exception as e:
            translation = f"[Translation error: {e}]"

    if not translation:
        return

    # Send transcription and translation text
    await websocket.send_json({
        "type": "translation",
        "transcription": transcription,
        "translation": translation,
    })

    # Generate translated speech with Google Cloud TTS
    try:
        audio_bytes = await synthesize_speech(translation, target_lang)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        await websocket.send_json({
            "type": "audio",
            "audio": audio_b64,
            "format": "mp3",
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"TTS error: {str(e)}",
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
