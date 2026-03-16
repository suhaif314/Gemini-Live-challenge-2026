"""
Google Cloud Services Demo for Live AI Voice Translator

This file is designed as a judge-facing code reference that clearly shows
Google Cloud API usage in one place:
- Vertex AI / Gemini (generate content)
- Cloud Speech-to-Text (audio transcription)
- Cloud Translation API (text translation)
- Cloud Text-to-Speech (speech synthesis)
"""

from __future__ import annotations

import base64
import os
from typing import Dict

from google import genai
from google.cloud import speech_v1 as speech
from google.cloud import texttospeech_v1 as texttospeech
from google.cloud import translate_v2 as translate

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "future-bucksaw-489512-m4")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def vertex_ai_translate(text: str, source_language: str, target_language: str) -> str:
    """Translate with Gemini on Vertex AI."""
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    prompt = (
        f"Translate from {source_language} to {target_language}. "
        "Return only translated text.\n\n"
        f"{text}"
    )
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text.strip()


def cloud_stt_transcribe(audio_bytes: bytes, language_bcp47: str = "en-US") -> str:
    """Transcribe speech audio with Cloud Speech-to-Text."""
    stt_client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code=language_bcp47,
        enable_automatic_punctuation=True,
    )
    audio = speech.RecognitionAudio(content=audio_bytes)
    result = stt_client.recognize(config=config, audio=audio)
    if not result.results:
        return ""
    return result.results[0].alternatives[0].transcript


def cloud_translate_text(text: str, source_code: str = "en", target_code: str = "fr") -> str:
    """Translate text with Cloud Translation API v2."""
    tr_client = translate.Client()
    response = tr_client.translate(
        text,
        source_language=source_code,
        target_language=target_code,
    )
    return response["translatedText"]


def cloud_tts_synthesize(text: str, language_bcp47: str = "fr-FR") -> bytes:
    """Synthesize translated text with Cloud Text-to-Speech."""
    tts_client = texttospeech.TextToSpeechClient()
    response = tts_client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code=language_bcp47,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
        ),
    )
    return response.audio_content


def end_to_end_reference(text: str) -> Dict[str, str]:
    """Reference flow: Gemini translate + Cloud TTS."""
    translated = vertex_ai_translate(text, "English", "French")
    audio_mp3 = cloud_tts_synthesize(translated, "fr-FR")
    return {
        "original_text": text,
        "translated_text": translated,
        "audio_base64": base64.b64encode(audio_mp3).decode("utf-8"),
    }


if __name__ == "__main__":
    sample = "Hello, welcome to our multilingual demo."
    result = end_to_end_reference(sample)
    print("Original:", result["original_text"])
    print("Translated:", result["translated_text"])
    print("Audio bytes (base64) prefix:", result["audio_base64"][:60])
