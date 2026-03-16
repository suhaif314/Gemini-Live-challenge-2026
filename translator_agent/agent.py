"""
Live AI Voice Translator Agent
Pipeline: Audio -> STT -> Translation -> TTS -> Audio
Model: gemini-2.5-flash @ us-central1
"""

import os
import base64

from google.adk.agents import Agent
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech_v1 as texttospeech


# ============================================================================
# CONFIG
# ============================================================================

PROJECT_ID = "future-bucksaw-489512-m4"
LOCATION = "us-central1"
GEMINI_MODEL = "gemini-2.5-flash"

SUPPORTED_LANGUAGES = {
    "english":    {"code": "en", "bcp47": "en-US", "voice": "en-US-Neural2-D", "flag": "🇺🇸"},
    "french":     {"code": "fr", "bcp47": "fr-FR", "voice": "fr-FR-Neural2-B", "flag": "🇫🇷"},
    "spanish":    {"code": "es", "bcp47": "es-ES", "voice": "es-ES-Neural2-B", "flag": "🇪🇸"},
    "german":     {"code": "de", "bcp47": "de-DE", "voice": "de-DE-Neural2-B", "flag": "🇩🇪"},
    "italian":    {"code": "it", "bcp47": "it-IT", "voice": "it-IT-Neural2-B", "flag": "🇮🇹"},
    "portuguese": {"code": "pt", "bcp47": "pt-BR", "voice": "pt-BR-Neural2-B", "flag": "🇧🇷"},
    "japanese":   {"code": "ja", "bcp47": "ja-JP", "voice": "ja-JP-Neural2-B", "flag": "🇯🇵"},
    "chinese":    {"code": "zh", "bcp47": "zh-CN", "voice": "cmn-CN-Neural2-B", "flag": "🇨🇳"},
    "korean":     {"code": "ko", "bcp47": "ko-KR", "voice": "ko-KR-Neural2-B", "flag": "🇰🇷"},
    "hindi":      {"code": "hi", "bcp47": "hi-IN", "voice": "hi-IN-Neural2-B", "flag": "🇮🇳"},
}

CODE_TO_NAME = {v["code"]: k for k, v in SUPPORTED_LANGUAGES.items()}


# ============================================================================
# TOOL: Detect Language (Google Cloud Translate API - fast & reliable)
# ============================================================================

def detect_language(text: str) -> dict:
    """
    Detect the language of given text using Google Cloud Translate API.

    Args:
        text: The text to detect the language of.

    Returns:
        Dictionary with detected_language name and confidence score.
    """
    try:
        client = translate.Client()
        result = client.detect_language(text)
        detected_code = result["language"]
        detected_name = CODE_TO_NAME.get(detected_code, detected_code)
        return {
            "success": True,
            "detected_language": detected_name,
            "confidence": float(result.get("confidence", 0.0)),
            "language_code": detected_code,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "detected_language": "unknown"}


# ============================================================================
# TOOL: Translate Text (Google Cloud Translate API)
# ============================================================================

def translate_text(
    text: str,
    source_language: str,
    target_language: str
) -> dict:
    """
    Translate text from source language to target language.

    Args:
        text: The text to translate.
        source_language: Source language name like english, french, spanish.
        target_language: Target language name like french, english, german.

    Returns:
        Dictionary with original_text, translated_text, and language info.
    """
    try:
        client = translate.Client()
        src = SUPPORTED_LANGUAGES.get(source_language.lower(), {})
        tgt = SUPPORTED_LANGUAGES.get(target_language.lower(), {})
        src_code = src.get("code", source_language[:2])
        tgt_code = tgt.get("code", target_language[:2])

        result = client.translate(
            text,
            source_language=src_code,
            target_language=tgt_code,
        )
        return {
            "success": True,
            "original_text": text,
            "translated_text": result["translatedText"],
            "source_language": source_language,
            "target_language": target_language,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "original_text": text, "translated_text": ""}


# ============================================================================
# TOOL: Text to Speech (Google Cloud TTS)
# ============================================================================

def text_to_speech(
    text: str,
    target_language: str = "french"
) -> dict:
    """
    Convert text to natural speech audio.

    Args:
        text: The text to speak aloud.
        target_language: Language for audio like french, english, spanish.

    Returns:
        Dictionary with audio_base64 MP3 data, text, and language.
    """
    try:
        client = texttospeech.TextToSpeechClient()
        lang_config = SUPPORTED_LANGUAGES.get(
            target_language.lower(), SUPPORTED_LANGUAGES["french"]
        )
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code=lang_config["bcp47"],
                name=lang_config["voice"],
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0,
            ),
        )
        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        return {
            "success": True,
            "audio_base64": audio_b64,
            "text": text,
            "language": target_language,
            "format": "mp3",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "audio_base64": ""}


# ============================================================================
# TOOL: Full Pipeline
# ============================================================================

def full_translate_pipeline(
    text: str,
    source_language: str,
    target_language: str
) -> dict:
    """
    Complete translation pipeline: detect, translate, and generate speech.

    Args:
        text: The text spoken by the user.
        source_language: Language the user speaks like english or french.
        target_language: Language to translate into like french or english.

    Returns:
        Dictionary with original_text, translated_text, and audio_base64.
    """
    try:
        tr = translate_text(text, source_language, target_language)
        if not tr["success"]:
            return tr
        tts = text_to_speech(tr["translated_text"], target_language)
        if not tts["success"]:
            return {"success": False, "error": tts["error"],
                    "original_text": text, "translated_text": tr["translated_text"]}
        return {
            "success": True,
            "original_text": text,
            "translated_text": tr["translated_text"],
            "audio_base64": tts["audio_base64"],
            "source_language": source_language,
            "target_language": target_language,
            "audio_format": "mp3",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL: Supported Languages
# ============================================================================

def get_supported_languages() -> dict:
    """
    Get all supported languages for translation.

    Returns:
        Dictionary with language names and their flag emojis.
    """
    return {"success": True, "languages": {k: v["flag"] for k, v in SUPPORTED_LANGUAGES.items()}}


# ============================================================================
# AGENT DEFINITION - Using gemini-2.5-flash
# ============================================================================

root_agent = Agent(
    model=GEMINI_MODEL,
    name="live_voice_translator",
    description="Live AI Voice Translator for real-time multilingual conversations.",
    instruction="""You are a real-time voice translation agent. You help two people
who speak different languages communicate naturally.

DEFAULT: Speaker A = English, Speaker B = French.

WHEN A USER SENDS A MESSAGE:
1. Use detect_language to identify the language
2. Use translate_text to translate:
   - If english -> translate to french
   - If french -> translate to english
   - Other languages -> translate to english
3. Use text_to_speech to generate audio of the translation
4. Show results clearly

RESPONSE FORMAT:
🗣️ Original ([language]): [original text]
🔄 Translation ([target]): [translated text]
🔊 Audio generated in [target language]

RULES:
- ALWAYS use the tools, never translate yourself
- ALWAYS call all 3 tools: detect_language -> translate_text -> text_to_speech
- Be fast and direct
""",
    tools=[
        detect_language,
        translate_text,
        text_to_speech,
        full_translate_pipeline,
        get_supported_languages,
    ],
)
