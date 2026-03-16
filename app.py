"""
Live AI Voice Translator - Web Application
Pipeline: Mic -> STT -> Gemini Translation -> TTS -> Speaker
FIXED: Audio encoding, empty audio handling, STT config
"""

import base64
import os
import logging
from datetime import datetime
from aiohttp import web
from google import genai
from google.cloud import speech_v1 as speech
from google.cloud import texttospeech_v1 as texttospeech
from google.cloud import translate_v2 as gtranslate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("translator")

PROJECT_ID = "future-bucksaw-489512-m4"
LOCATION = "us-central1"
GEMINI_MODEL = "gemini-2.5-flash"

LANGUAGES = {
    "english":    {"code":"en","bcp47":"en-US","voice":"en-US-Neural2-D"},
    "french":     {"code":"fr","bcp47":"fr-FR","voice":"fr-FR-Neural2-B"},
    "spanish":    {"code":"es","bcp47":"es-ES","voice":"es-ES-Neural2-B"},
    "german":     {"code":"de","bcp47":"de-DE","voice":"de-DE-Neural2-B"},
    "italian":    {"code":"it","bcp47":"it-IT","voice":"it-IT-Neural2-B"},
    "portuguese": {"code":"pt","bcp47":"pt-BR","voice":"pt-BR-Neural2-B"},
    "japanese":   {"code":"ja","bcp47":"ja-JP","voice":"ja-JP-Neural2-B"},
    "chinese":    {"code":"zh","bcp47":"zh-CN","voice":"cmn-CN-Neural2-B"},
    "korean":     {"code":"ko","bcp47":"ko-KR","voice":"ko-KR-Neural2-B"},
    "hindi":      {"code":"hi","bcp47":"hi-IN","voice":"hi-IN-Neural2-B"},
}

gemini_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)


# ============================================================================
# STT - FIXED: handles empty audio, proper encoding config
# ============================================================================

def do_stt(audio_bytes, language):
    """Speech-to-Text with proper error handling."""
    logger.info(f"STT: received {len(audio_bytes)} bytes for language={language}")

    if not audio_bytes or len(audio_bytes) < 100:
        logger.warning(f"STT: audio too small ({len(audio_bytes)} bytes)")
        return ""

    client = speech.SpeechClient()
    lc = LANGUAGES.get(language, LANGUAGES["english"])

    # Use auto-detect encoding for WebM files from browser
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code=lc["bcp47"],
        enable_automatic_punctuation=True,
        audio_channel_count=1,
    )

    audio = speech.RecognitionAudio(content=audio_bytes)

    try:
        resp = client.recognize(config=config, audio=audio)
    except Exception as e:
        logger.warning(f"STT first attempt failed: {e}")
        # Retry with different config - let Google auto-detect
        try:
            config2 = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=48000,
                language_code=lc["bcp47"],
                enable_automatic_punctuation=True,
                audio_channel_count=1,
            )
            resp = client.recognize(config=config2, audio=audio)
        except Exception as e2:
            logger.error(f"STT retry also failed: {e2}")
            return ""

    if not resp.results:
        logger.warning("STT: no results returned")
        return ""

    text = resp.results[0].alternatives[0].transcript
    conf = resp.results[0].alternatives[0].confidence
    logger.info(f"STT result: '{text}' (confidence: {conf:.2f})")
    return text


def do_translate_gemini(text, src_lang, tgt_lang):
    """Translate using Gemini LLM."""
    logger.info(f"Gemini: {src_lang}->{tgt_lang}: {text}")
    prompt = (
        f"You are a professional interpreter. Translate from {src_lang} to {tgt_lang}.\n"
        f"Reply ONLY with the translation. No quotes, no notes.\n\n{text}"
    )
    resp = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    result = resp.text.strip()
    for q in ['"', "'", "\u201c", "\u201d"]:
        if result.startswith(q) and result.endswith(q):
            result = result[1:-1]
            break
    logger.info(f"Gemini result: {result}")
    return result


def do_translate_cloud(text, src_lang, tgt_lang):
    """Translate using Cloud API."""
    client = gtranslate.Client()
    src_code = LANGUAGES.get(src_lang, {}).get("code", "en")
    tgt_code = LANGUAGES.get(tgt_lang, {}).get("code", "fr")
    result = client.translate(text, source_language=src_code, target_language=tgt_code)
    return result["translatedText"]


def do_tts(text, language):
    """Text-to-Speech."""
    client = texttospeech.TextToSpeechClient()
    lc = LANGUAGES.get(language, LANGUAGES["french"])
    resp = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(language_code=lc["bcp47"], name=lc["voice"]),
        audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=1.0),
    )
    return resp.audio_content


# ============================================================================
# ROUTES
# ============================================================================

routes = web.RouteTableDef()


@routes.post("/api/pipeline")
async def pipeline(request):
    """Full pipeline: audio -> STT -> translate -> TTS -> audio."""
    try:
        data = await request.json()
        audio_b64 = data.get("audio", "")
        src_lang = data.get("source_language", "english")
        tgt_lang = data.get("target_language", "french")
        use_gemini = data.get("use_gemini", True)

        # Validate audio
        if not audio_b64:
            return web.json_response({
                "success": False,
                "error": "No audio data received. Please try again."
            })

        # Clean base64 - remove data URL prefix if present
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",", 1)[1]

        # Remove whitespace/newlines
        audio_b64 = audio_b64.strip().replace("\n", "").replace("\r", "").replace(" ", "")

        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return web.json_response({
                "success": False,
                "error": "Invalid audio data. Please try again."
            })

        logger.info(f"Pipeline: received {len(audio_bytes)} audio bytes")

        if len(audio_bytes) < 100:
            return web.json_response({
                "success": False,
                "error": "Recording too short. Please hold the button and speak for at least 1 second."
            })

        t0 = datetime.now()

        # 1) STT
        transcript = do_stt(audio_bytes, src_lang)
        t1 = datetime.now()

        if not transcript:
            return web.json_response({
                "success": False,
                "error": "No speech detected. Please speak louder and longer (at least 2 seconds)."
            })

        # 2) Translate
        if use_gemini:
            translation = do_translate_gemini(transcript, src_lang, tgt_lang)
        else:
            translation = do_translate_cloud(transcript, src_lang, tgt_lang)
        t2 = datetime.now()

        # 3) TTS
        tts_bytes = do_tts(translation, tgt_lang)
        tts_b64 = base64.b64encode(tts_bytes).decode()
        t3 = datetime.now()

        return web.json_response({
            "success": True,
            "original_text": transcript,
            "translated_text": translation,
            "audio": tts_b64,
            "timings": {
                "stt_ms": int((t1 - t0).total_seconds() * 1000),
                "translate_ms": int((t2 - t1).total_seconds() * 1000),
                "tts_ms": int((t3 - t2).total_seconds() * 1000),
                "total_ms": int((t3 - t0).total_seconds() * 1000),
            },
        })

    except Exception as e:
        logger.exception("Pipeline error")
        return web.json_response({"success": False, "error": str(e)}, status=500)


@routes.post("/api/translate-text")
async def translate_text_ep(request):
    """Text-only translation + TTS."""
    try:
        data = await request.json()
        text = data.get("text", "")
        if not text:
            return web.json_response({"success": False, "error": "No text provided"})

        src = data.get("source_language", "english")
        tgt = data.get("target_language", "french")
        use_gemini = data.get("use_gemini", True)

        translation = do_translate_gemini(text, src, tgt) if use_gemini else do_translate_cloud(text, src, tgt)
        tts_bytes = do_tts(translation, tgt)
        tts_b64 = base64.b64encode(tts_bytes).decode()

        return web.json_response({
            "success": True,
            "original_text": text,
            "translated_text": translation,
            "audio": tts_b64,
        })

    except Exception as e:
        logger.exception("Text translate error")
        return web.json_response({"success": False, "error": str(e)}, status=500)


@routes.get("/health")
async def health(request):
    return web.json_response({"status": "ok"})


@routes.get("/")
async def index(request):
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(html_path) as f:
        return web.Response(text=f.read(), content_type="text/html")


def main():
    app = web.Application(client_max_size=50 * 1024 * 1024)  # 50MB max upload
    app.add_routes(routes)
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Live Voice Translator on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
