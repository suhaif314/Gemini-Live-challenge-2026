# 🌐 Live AI Voice Translator

**Real-time multilingual conversation translator powered by Gemini AI + Google Cloud**

> Built for the [Gemini Live Agent Challenge 2026](https://geminiliveagentchallenge.devpost.com/)

## 🎯 What It Does

Live-AI-Voice-Translator enables real-time multilingual conversations by:
1. **Capturing speech** from Speaker A (e.g., English)
2. **Converting to text** using Google Cloud Speech-to-Text
3. **Translating with AI** using Gemini 2.5 Flash LLM (or Cloud Translate API)
4. **Generating speech** using Google Cloud Text-to-Speech
5. **Playing translated audio** for Speaker B (e.g., French)

The flow works **bidirectionally** — Speaker B can respond and Speaker A hears the translation instantly.

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────────────────────────────────┐     ┌──────────────┐
│  Speaker A   │     │              AI AGENT SERVER             │     │  Speaker B   │
│  (English)   │     │                                         │     │  (French)    │
│              │     │  ┌─────┐   ┌────────┐   ┌─────┐        │     │              │
│  🎤 Record ──┼──►──┤  STT  ├──►│ GEMINI ├──►│ TTS ├──►─────┼──►  │ 🔊 Listen   │
│              │     │  └─────┘   │  LLM   │   └─────┘        │     │              │
│  🔊 Listen ◄─┼──◄──┤  TTS  ◄──┤TRANSLATE◄──┤ STT ◄──◄─────┼──◄  │ 🎤 Record   │
│              │     │  └─────┘   └────────┘   └─────┘        │     │              │
└──────────────┘     └─────────────────────────────────────────┘     └──────────────┘
```

## ✨ Features

- **🎤 Push-to-Talk** — Hold button to speak, release to translate
- **🔇 Auto Silence Detection** — Automatically stops recording after 1.5s of silence
- **🤖 Dual Translation Engines** — Gemini LLM (context-aware) or Cloud Translate API (fast)
- **🔊 Natural Voice Output** — Google Cloud Neural2 voices for natural-sounding speech
- **📊 Real-time Pipeline Visualization** — See each step: STT → Translate → TTS → Play
- **💬 Conversation History** — Full log with timestamps and timing metrics
- **📝 Text Mode** — Type to translate (for testing without microphone)
- **🌍 10 Languages** — English, French, Spanish, German, Italian, Portuguese, Japanese, Chinese, Korean, Hindi
- **📱 Responsive UI** — Works on desktop and mobile
- **⚡ ADK Agent** — Google ADK-based agent with tool orchestration

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **AI Agent** | Google ADK (Agent Development Kit) |
| **Translation LLM** | Gemini 2.5 Flash on Vertex AI |
| **Speech-to-Text** | Google Cloud Speech-to-Text API |
| **Text-to-Speech** | Google Cloud Text-to-Speech API (Neural2) |
| **Fallback Translation** | Google Cloud Translate API v2 |
| **Web Server** | Python aiohttp |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Hosting** | Google Cloud Run |
| **Cloud Platform** | Google Cloud Platform (GCP) |

## 📁 Project Structure

```
live-voice-translator/
├── translator_agent/          # ADK Agent
│   ├── __init__.py
│   ├── agent.py               # Agent with tools (detect, translate, TTS)
│   └── .env                   # Environment config
├── app.py                     # Web server with full pipeline
├── index.html                 # Interactive web UI
├── agent.json                 # A2A Agent Card
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container deployment
├── .gitignore
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Google Cloud project with APIs enabled:
  - Vertex AI API
  - Cloud Speech-to-Text API
  - Cloud Text-to-Speech API
  - Cloud Translate API

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the ADK agent (text mode)
adk web

# Run the voice web app
python3 app.py
# Open http://localhost:8080
```

## Reproducible Testing

Judges can verify the project in a few minutes using either text mode or microphone mode.

### Test Environment Setup

1. Create a Google Cloud project and enable these APIs:
  - Vertex AI API
  - Cloud Speech-to-Text API
  - Cloud Text-to-Speech API
  - Cloud Translate API
2. Authenticate locally with Google Cloud:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

3. Install project dependencies:

```bash
pip install -r requirements.txt
```

4. Start the app:

```bash
python3 app.py
```

5. Open http://localhost:8080 in a browser.

### Test Case 1: Text Translation

This is the fastest way to validate the pipeline without microphone permissions.

1. Open the app.
2. Set Speaker A to `English` and Speaker B to `French`.
3. Keep the engine on `Gemini LLM`.
4. Enter: `Hello, thank you for joining the meeting today.`
5. Submit the text translation request.

Expected result:
- The original English text is shown in the conversation log.
- A French translation is returned.
- Audio playback is generated for the translated output.
- Timing metrics are displayed for the request.

### Test Case 2: Voice Translation

1. Allow microphone access in the browser.
2. Set Speaker A to `English` and Speaker B to `French`.
3. Hold the Speaker A record button.
4. Say: `Can we review the project timeline tomorrow morning?`
5. Release the button and wait for processing.

Expected result:
- The app captures audio and sends it through the STT -> Translate -> TTS pipeline.
- The recognized transcript appears in English.
- The French translation is displayed.
- Translated audio plays automatically for Speaker B.

### Test Case 3: Bidirectional Conversation

1. After completing Test Case 2, switch to Speaker B.
2. Hold the Speaker B button.
3. Speak a short reply in French.
4. Release the button.

Expected result:
- The reply is transcribed in French.
- The app translates it back to English.
- Speaker A receives English audio playback.
- Both turns appear in the conversation history.

### Test Case 4: Fallback Engine Check

1. Change the translation engine from `Gemini LLM` to `Cloud API`.
2. Repeat either the text test or the voice test.

Expected result:
- Translation still succeeds.
- Audio is still generated.
- The app remains usable even when switching away from the LLM-driven path.

### Notes for Judges

- If microphone permissions are blocked, use `Text Mode` to verify the core translation and TTS flow.
- If speech recognition returns no result, record a slightly longer sentence and speak clearly.
- For the smoothest demo, use Chrome or Edge.
- Typical end-to-end latency is about `1-3 seconds` depending on network and API response time.

### Deploy to Cloud Run

```bash
gcloud run deploy live-voice-translator \
    --source . \
    --region us-central1 \
    --allow-unauthenticated
```

## 🎮 How to Use

1. **Select languages** for Speaker A and Speaker B
2. **Choose engine**: Gemini LLM (richer) or Cloud API (faster)
3. **Speaker A**: Hold the blue button → Speak → Release
4. AI translates and plays audio on Speaker B's side
5. **Speaker B**: Hold the purple button → Respond → Release
6. AI translates back for Speaker A
7. Conversation continues naturally!

## 📊 Performance

| Step | Typical Latency |
|------|----------------|
| STT | 500-1500ms |
| Gemini Translation | 300-800ms |
| Cloud Translation | 100-300ms |
| TTS | 200-500ms |
| **Total Pipeline** | **1-3 seconds** |

## 🏆 Challenge Category

**Live Agents 🗣️** — Real-time Interaction (Audio)

This agent enables natural voice conversations between speakers of different languages, with:
- Real-time audio input/output (multimodal, beyond text-in/text-out)
- Automatic turn-taking via silence detection
- Gemini LLM for context-aware translation
- Google ADK agent orchestration
- Hosted on Google Cloud

## 📄 License

MIT License

## 👤 Author

Built by [suhaif314](https://github.com/suhaif314) for the Gemini Live Agent Challenge 2026
