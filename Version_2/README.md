# Live AI Voice Translator

Real-time multilingual voice translation powered by **Gemini Live API**, **Google Cloud Text-to-Speech**, and **Google Cloud Translation**.

> Built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) | Category: **Live Agents** | #GeminiLiveAgentChallenge

---

## What It Does

**Live AI Voice Translator** is a **real-time Live Agent** that enables seamless multilingual conversations by:

1. **Streaming live microphone audio** to Gemini Live API via WebSocket
2. **Transcribing and translating in real-time** using Gemini's native audio understanding
3. **Generating natural translated speech** using Google Cloud Text-to-Speech
4. **Playing back translated audio instantly** — enabling live cross-language conversations

Supports **20 languages** including English, Spanish, French, German, Japanese, Korean, Chinese, Hindi, Arabic, and more.

The agent supports **barge-in** (interruption while speaking), **live transcription**, and handles the full speech-to-speech pipeline in real-time.

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Browser (User)                                   │
│  ┌─────────────┐  ┌──────────────────────────┐   │
│  │ Microphone   │  │  Audio Playback (TTS)    │   │
│  │ Web Audio API│  │  Conversation Display     │   │
│  └──────┬──────┘  └──────────▲───────────────┘   │
│         │ PCM 16kHz           │ JSON + MP3 audio  │
│         │ (binary)            │                    │
└─────────┼─────────────────────┼────────────────────┘
          │    WebSocket (wss://)│
┌─────────▼─────────────────────┼────────────────────┐
│  FastAPI Backend (Cloud Run)                        │
│                                                     │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Gemini Live │  │ Cloud    │  │ Cloud         │  │
│  │ API         │  │ TTS      │  │ Translation   │  │
│  │ (streaming  │  │ (speech  │  │ (fallback     │  │
│  │  audio I/O) │  │  output) │  │  translation) │  │
│  └─────────────┘  └──────────┘  └──────────────┘  │
│                                                     │
│          Google Cloud Platform                      │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|---|---|
| **AI Model** | Gemini 2.5 Flash (native audio) via Google GenAI SDK |
| **Live Streaming** | Gemini Live API (bidirectional WebSocket) |
| **Speech Synthesis** | Google Cloud Text-to-Speech API |
| **Text Translation** | Google Cloud Translation API (fallback) |
| **Backend** | FastAPI + uvicorn (Python, async) |
| **Frontend** | Vanilla HTML/JS + Web Audio API |
| **Audio Capture** | ScriptProcessorNode (PCM 16-bit 16kHz) |
| **Deployment** | Docker + Google Cloud Run |
| **SDK** | Google GenAI SDK (`google-genai`) |

---

## How It Works — Live Agent Flow

1. User clicks the **microphone button** in the browser
2. Browser captures **raw PCM audio** (16kHz, 16-bit, mono) via Web Audio API
3. Audio chunks are **streamed in real-time** over a WebSocket to the FastAPI backend
4. Backend forwards audio to **Gemini Live API** session using `send_realtime_input()`
5. Gemini processes the speech and returns a **transcription + translation** as text
6. Backend sends the translation to **Google Cloud TTS** to generate spoken audio
7. Both the text translation and audio (MP3) are sent back to the browser via WebSocket
8. Browser **auto-plays** the translated audio and displays conversation history

---

## Prerequisites

- **Python 3.11+**
- **Google AI API Key** — Get from [Google AI Studio](https://aistudio.google.com/apikey)
- **Google Cloud account** with billing enabled
- **Google Cloud CLI** (`gcloud`) installed and authenticated
- Enabled GCP APIs: Text-to-Speech, Translation, Cloud Run, Cloud Build

---

## Local Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/live-ai-voice-translator.git
cd live-ai-voice-translator
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY and GOOGLE_CLOUD_PROJECT
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 4. Run locally

```bash
python main.py
```

Open `http://localhost:8080` in your browser.

---

## Google Cloud Deployment

### Automated (recommended)

```bash
export GOOGLE_API_KEY="your-key"
export GOOGLE_CLOUD_PROJECT="your-project-id"
chmod +x deploy.sh
./deploy.sh
```

### Manual

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
    texttospeech.googleapis.com translate.googleapis.com artifactregistry.googleapis.com

gcloud run deploy live-ai-voice-translator \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --set-env-vars "GOOGLE_API_KEY=your-key,GOOGLE_CLOUD_PROJECT=your-project-id"
```

---

## Project Structure

```
live-ai-voice-translator/
├── main.py                # FastAPI backend + Gemini Live API WebSocket handler
├── static/
│   └── index.html         # Frontend with Web Audio API + WebSocket client
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container config for Cloud Run
├── deploy.sh              # Automated GCP deployment script
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore rules
├── .dockerignore          # Docker ignore rules
└── README.md              # This file
```

---

## Supported Languages

| Language | Code | Language | Code |
|---|---|---|---|
| English | en | Korean | ko |
| Spanish | es | Chinese | zh |
| French | fr | Hindi | hi |
| German | de | Arabic | ar |
| Italian | it | Russian | ru |
| Portuguese | pt | Turkish | tr |
| Japanese | ja | Vietnamese | vi |
| Thai | th | Dutch | nl |
| Polish | pl | Swedish | sv |
| Danish | da | Finnish | fi |

---

## Google Cloud Services Used

1. **Cloud Run** — Hosts the containerized application
2. **Cloud Build** — Builds the Docker container image
3. **Cloud Text-to-Speech API** — Generates natural-sounding translated speech
4. **Cloud Translation API** — Provides text translation as fallback
5. **Gemini Live API (via GenAI SDK)** — Real-time speech transcription and AI translation

---

## Key Features

- **Real-time live audio streaming** to Gemini via WebSocket
- **Barge-in support** — interrupt the agent while it's speaking
- **Live transcription** — see what you're saying in real-time
- **AI-powered context-aware translation** using Gemini 2.5 Flash
- **Natural text-to-speech output** in 20 target languages
- **Dual input modes:** live voice streaming and text input
- **Conversation history** with playable audio for each translation
- **Auto-play** translated audio for hands-free operation
- **Fully containerized** and deployed on Google Cloud Run

---

## License

MIT License

---

## Acknowledgments

- [Google Gemini Live API](https://ai.google.dev/gemini-api/docs/live) — Real-time audio AI
- [Google Cloud](https://cloud.google.com/) — TTS, Translation, and Cloud Run
- [FastAPI](https://fastapi.tiangolo.com/) — Async Python backend
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API) — Browser audio capture

Built with Gemini Live API for the **Gemini Live Agent Challenge**.
