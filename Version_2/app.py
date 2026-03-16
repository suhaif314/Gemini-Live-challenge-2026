"""
Live AI Voice Translator - Streamlit Frontend
Real-time multilingual voice translation powered by Gemini Live API.
"""

import asyncio
import base64
import json
import os
import queue
import threading
import time
from io import BytesIO

import numpy as np
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.cloud import texttospeech_v1 as texttospeech
from google.cloud import translate_v2 as translate

load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="Live AI Voice Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Constants ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

LANGUAGES = {
    "en": {"name": "English", "tts_code": "en-US"},
    "es": {"name": "Spanish", "tts_code": "es-ES"},
    "fr": {"name": "French", "tts_code": "fr-FR"},
    "de": {"name": "German", "tts_code": "de-DE"},
    "it": {"name": "Italian", "tts_code": "it-IT"},
    "pt": {"name": "Portuguese", "tts_code": "pt-BR"},
    "ja": {"name": "Japanese", "tts_code": "ja-JP"},
    "ko": {"name": "Korean", "tts_code": "ko-KR"},
    "zh": {"name": "Chinese", "tts_code": "cmn-CN"},
    "hi": {"name": "Hindi", "tts_code": "hi-IN"},
    "ar": {"name": "Arabic", "tts_code": "ar-XA"},
    "ru": {"name": "Russian", "tts_code": "ru-RU"},
    "tr": {"name": "Turkish", "tts_code": "tr-TR"},
    "vi": {"name": "Vietnamese", "tts_code": "vi-VN"},
    "th": {"name": "Thai", "tts_code": "th-TH"},
}


# --- Initialize Clients ---
@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GOOGLE_API_KEY)


@st.cache_resource
def get_tts_client():
    return texttospeech.TextToSpeechClient()


@st.cache_resource
def get_translate_client():
    return translate.Client()


# --- Session State ---
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = queue.Queue()


def synthesize_speech(text: str, target_lang: str) -> bytes:
    """Convert text to speech using Google Cloud TTS."""
    client = get_tts_client()
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
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )
    return response.audio_content


def translate_text(text: str, target_lang: str) -> str:
    """Translate text using Google Cloud Translation API."""
    client = get_translate_client()
    result = client.translate(text, target_language=target_lang)
    return result["translatedText"]


def process_with_gemini(text: str, source_lang: str, target_lang: str) -> dict:
    """Send text to Gemini for context-aware translation."""
    client = get_gemini_client()
    source_name = LANGUAGES[source_lang]["name"]
    target_name = LANGUAGES[target_lang]["name"]

    prompt = (
        f"You are a professional translator. Translate the following {source_name} text "
        f"to {target_name}. Return ONLY a JSON object with these fields:\n"
        f'{{"transcription": "<original text>", "translation": "<translated text>"}}\n\n'
        f"Text to translate: {text}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    try:
        resp_text = response.text.strip()
        if resp_text.startswith("```"):
            lines = resp_text.split("\n")
            resp_text = "\n".join(lines[1:-1])
        return json.loads(resp_text)
    except (json.JSONDecodeError, AttributeError):
        # Fallback: use Cloud Translation
        translation = translate_text(text, target_lang)
        return {"transcription": text, "translation": translation}


# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
    }
    .sub-header {
        text-align: center;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        animation: fadeIn 0.3s ease-in;
    }
    .original-message {
        background: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .translated-message {
        background: #e8f5e9;
        border-left: 4px solid #4CAF50;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .lang-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .source-badge { background: #bbdefb; color: #1565c0; }
    .target-badge { background: #c8e6c9; color: #2e7d32; }
    .status-connected { color: #4CAF50; font-weight: 600; }
    .status-disconnected { color: #f44336; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<h1 class="main-header">Live AI Voice Translator</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Real-time multilingual conversations powered by '
    'Gemini AI & Google Cloud</p>',
    unsafe_allow_html=True,
)

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")

    # API Key input
    api_key = st.text_input(
        "Google AI API Key",
        value=GOOGLE_API_KEY,
        type="password",
        help="Get your API key from https://aistudio.google.com/apikey",
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    st.divider()

    # Language selection
    source_lang = st.selectbox(
        "Source Language (Speak in)",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x]["name"],
        index=0,
    )

    target_lang = st.selectbox(
        "Target Language (Translate to)",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x]["name"],
        index=1,
    )

    if source_lang == target_lang:
        st.warning("Source and target languages are the same!")

    st.divider()

    # Translation mode
    mode = st.radio(
        "Translation Mode",
        options=["Audio Input (Upload/Record)", "Text Input"],
        index=0,
    )

    st.divider()

    # Clear history
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.conversation_history = []
        st.rerun()

    st.divider()
    st.markdown("### About")
    st.markdown(
        "**Live AI Voice Translator** enables real-time multilingual "
        "conversations by converting speech to text, translating with AI, "
        "and generating translated speech."
    )
    st.markdown("Built with:")
    st.markdown("- Gemini AI (Google GenAI SDK)")
    st.markdown("- Google Cloud Text-to-Speech")
    st.markdown("- Google Cloud Translation")
    st.markdown("- Streamlit")


# --- Main Content ---
source_name = LANGUAGES[source_lang]["name"]
target_name = LANGUAGES[target_lang]["name"]

col_info1, col_info2 = st.columns(2)
with col_info1:
    st.info(f"**Speaking:** {source_name}")
with col_info2:
    st.success(f"**Translating to:** {target_name}")

st.divider()

# --- Input Section ---
if mode == "Text Input":
    text_input = st.text_area(
        "Type text to translate",
        placeholder=f"Enter text in {source_name}...",
        height=100,
    )

    if st.button("Translate", type="primary", use_container_width=True):
        if text_input.strip():
            with st.spinner("Translating with Gemini AI..."):
                result = process_with_gemini(text_input, source_lang, target_lang)
                transcription = result.get("transcription", text_input)
                translation = result.get("translation", "")

                # Add to conversation history
                st.session_state.conversation_history.append({
                    "source": transcription,
                    "source_lang": source_name,
                    "translation": translation,
                    "target_lang": target_name,
                    "timestamp": time.strftime("%H:%M:%S"),
                })

                # Generate TTS for translated text
                try:
                    audio_bytes = synthesize_speech(translation, target_lang)
                    st.session_state.conversation_history[-1]["audio"] = audio_bytes
                except Exception as e:
                    st.warning(f"Could not generate audio: {e}")

                st.rerun()
        else:
            st.warning("Please enter some text to translate.")

else:
    st.markdown("### Upload or Record Audio")

    audio_file = st.audio_input("Record audio or upload a file")

    if audio_file is not None:
        if st.button("Translate Audio", type="primary", use_container_width=True):
            with st.spinner("Processing audio with Gemini AI..."):
                audio_bytes = audio_file.read()

                # Use Gemini to transcribe and translate the audio
                client = get_gemini_client()
                source_lang_name = LANGUAGES[source_lang]["name"]
                target_lang_name = LANGUAGES[target_lang]["name"]

                prompt = (
                    f"This is audio in {source_lang_name}. "
                    f"First, transcribe exactly what is said. "
                    f"Then translate it to {target_lang_name}. "
                    f"Return ONLY a JSON object: "
                    f'{{"transcription": "<what was said>", '
                    f'"translation": "<translation>"}}'
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        prompt,
                        types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type="audio/wav",
                        ),
                    ],
                )

                try:
                    resp_text = response.text.strip()
                    if resp_text.startswith("```"):
                        lines = resp_text.split("\n")
                        resp_text = "\n".join(lines[1:-1])
                    result = json.loads(resp_text)
                except (json.JSONDecodeError, AttributeError):
                    result = {
                        "transcription": response.text if response.text else "[Could not transcribe]",
                        "translation": "",
                    }
                    if result["transcription"] and not result["translation"]:
                        try:
                            result["translation"] = translate_text(
                                result["transcription"], target_lang
                            )
                        except Exception:
                            result["translation"] = "[Translation failed]"

                transcription = result.get("transcription", "")
                translation = result.get("translation", "")

                entry = {
                    "source": transcription,
                    "source_lang": source_lang_name,
                    "translation": translation,
                    "target_lang": target_lang_name,
                    "timestamp": time.strftime("%H:%M:%S"),
                }

                # Generate TTS
                if translation:
                    try:
                        tts_audio = synthesize_speech(translation, target_lang)
                        entry["audio"] = tts_audio
                    except Exception as e:
                        st.warning(f"TTS error: {e}")

                st.session_state.conversation_history.append(entry)
                st.rerun()

# --- Conversation Display ---
st.divider()
st.subheader("Conversation")

if not st.session_state.conversation_history:
    st.markdown(
        '<p style="text-align:center; color:#999; padding:2rem;">'
        "No translations yet. Start speaking or type something above!</p>",
        unsafe_allow_html=True,
    )
else:
    for i, entry in enumerate(reversed(st.session_state.conversation_history)):
        idx = len(st.session_state.conversation_history) - 1 - i

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f'<div class="chat-message original-message">'
                f'<span class="lang-badge source-badge">{entry["source_lang"]}</span>'
                f'<br/>{entry["source"]}'
                f'<br/><small style="color:#999">{entry["timestamp"]}</small>'
                f"</div>",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f'<div class="chat-message translated-message">'
                f'<span class="lang-badge target-badge">{entry["target_lang"]}</span>'
                f'<br/>{entry["translation"]}'
                f'<br/><small style="color:#999">{entry["timestamp"]}</small>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if "audio" in entry:
                st.audio(entry["audio"], format="audio/mp3")

# --- Footer ---
st.divider()
st.markdown(
    '<p style="text-align:center; color:#999; font-size:0.8rem;">'
    "Powered by Google Gemini AI | Google Cloud Text-to-Speech | "
    "Google Cloud Translation<br/>"
    "Built for the Gemini Live Agent Challenge</p>",
    unsafe_allow_html=True,
)
