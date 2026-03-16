# Live AI Voice Translator

Real-time multilingual voice translation powered by **Google Gemini AI**, **Google Cloud Text-to-Speech**, and **Google Cloud Translation**.

> Built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) #GeminiLiveAgentChallenge

---

## What It Does

**Live AI Voice Translator** enables seamless multilingual conversations by:

1. **Capturing speech** via microphone or audio upload
2. **Transcribing and translating** in real-time using Gemini AI
3. **Generating natural translated speech** using Google Cloud Text-to-Speech

Supports **15 languages** including English, Spanish, French, German, Japanese, Korean, Chinese, Hindi, Arabic, and more.

---

## Architecture

```
┌─────────────────┐
│   User (Mic)    │
└────────┬────────┘
         │ Audio / Text
┌────────▼────────────────┐
│  Streamlit Frontend     │
│  Audio Recorder │ Chat  │
└────────┬────────────────┘
         │ API / WebSocket
┌────────▼────────────────────────────────┐
│  FastAPI Backend (Google Cloud Run)     │
│  Translation Logic │ TTS Orchestration  │
├─────────┬──────────────┬────────────────┤
│         │              │                │
│  ┌──────▼──────┐ ┌────▼─────┐ ┌───────▼──────┐
│  │ Gemini Live │ │ Cloud    │ │ Cloud        │
│  │ API         │ │ TTS      │ │ Translation  │
│  └─────────────┘ └──────────┘ └──────────────┘
│                                                │
│         Google Cloud Platform                  │
└────────────────────────────────────────────────┘
```

A detailed interactive architecture diagram is available in `architecture.html`.

---

## Tech Stack

| Component | Technology |
|---|---|
| **AI Model** | Google Gemini 2.0 Flash (via GenAI SDK) |
| **Live Streaming** | Gemini Live API (WebSocket) |
| **Speech Synthesis** | Google Cloud Text-to-Speech API |
| **Text Translation** | Google Cloud Translation API |
| **Backend** | FastAPI (Python) |
| **Frontend** | Streamlit |
| **Deployment** | Docker + Google Cloud Run |
| **SDK** | Google GenAI SDK (`google-genai`) |

---

## Prerequisites

- **Python 3.11+**
- **Google AI API Key** — Get one at [Google AI Studio](https://aistudio.google.com/apikey)
- **Google Cloud account** with billing enabled
- **Google Cloud CLI** (`gcloud`) installed and authenticated
- Enabled GCP APIs:
  - Cloud Text-to-Speech
  - Cloud Translation
  - Cloud Run
  - Cloud Build

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/suhaif314/Gemini-Live-challenge-2026.git
cd Gemini-Live-challenge-2026
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

### 5. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 6. Run the Streamlit app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### 7. (Optional) Run the FastAPI backend

```bash
python server.py
```

The API server starts at `http://localhost:8000` with WebSocket support at `ws://localhost:8000/ws/translate`.

---

## Google Cloud Deployment

### Automated deployment

```bash
# Set your API key
export GOOGLE_API_KEY="your-key-here"
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Run the deployment script
chmod +x deploy.sh
./deploy.sh
```

### Manual deployment

```bash
# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
    texttospeech.googleapis.com translate.googleapis.com

# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/live-ai-voice-translator .

# Deploy to Cloud Run
gcloud run deploy live-ai-voice-translator \
    --image gcr.io/YOUR_PROJECT/live-ai-voice-translator \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8501 \
    --memory 1Gi \
    --set-env-vars "GOOGLE_API_KEY=your-key"
```

---

## How to Use

1. **Open the app** in your browser
2. **Select source language** (the language you speak)
3. **Select target language** (the language to translate to)
4. **Choose input mode:**
   - **Audio:** Click the microphone to record, or upload an audio file
   - **Text:** Type text directly
5. **Click Translate** — you'll see the transcription, translation, and hear the translated audio
6. **View conversation history** below the input area

---

## Project Structure

```
live-ai-voice-translator/
├── app.py                 # Streamlit frontend (main entry point)
├── server.py              # FastAPI backend with WebSocket support
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container config for Cloud Run
├── deploy.sh              # Automated GCP deployment script
├── architecture.html      # Interactive architecture diagram
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
| Thai | th | | |

---

## Google Cloud Services Used

1. **Cloud Run** — Hosts the containerized application
2. **Cloud Build** — Builds the Docker container image
3. **Cloud Text-to-Speech API** — Generates natural-sounding translated speech
4. **Cloud Translation API** — Provides text translation as a fallback
5. **Gemini AI (via GenAI SDK)** — Powers transcription and AI-driven translation

---

## Key Features

- **Real-time voice translation** across 15 languages
- **AI-powered context-aware translation** using Gemini
- **Natural text-to-speech output** in the target language
- **Dual input modes:** voice recording and text input
- **Conversation history** with playable audio for each translation
- **WebSocket streaming** support for low-latency translation (FastAPI backend)
- **Fully containerized** and deployable to Google Cloud Run

---

## License

MIT License

---

## Acknowledgments

- [Google Gemini AI](https://ai.google.dev/) — AI model powering transcription and translation
- [Google Cloud](https://cloud.google.com/) — TTS, Translation, and Cloud Run hosting
- [Streamlit](https://streamlit.io/) — Frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) — Backend framework

Built with Google Gemini AI for the **Gemini Live Agent Challenge**.
