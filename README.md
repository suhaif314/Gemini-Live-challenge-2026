# 🌐 Live AI Voice Translator

**Real-time multilingual conversation translator powered by Gemini AI + Google Cloud**

> Built for the [Gemini Live Agent Challenge 2026](https://geminiliveagentchallenge.devpost.com/)

---

## 🎯 What It Does

Live-AI-Voice-Translator enables real-time multilingual conversations by:
1. **Capturing speech** from Speaker A (e.g., English)
2. **Converting to text** using Google Cloud Speech-to-Text
3. **Translating with AI** using Gemini 2.5 Flash LLM (or Cloud Translate API)
4. **Generating speech** using Google Cloud Text-to-Speech
5. **Playing translated audio** for Speaker B (e.g., French)

The flow works **bidirectionally** — Speaker B can respond and Speaker A hears the translation instantly.

---

## 🔗 Judge-Ready Links

- Google Cloud API usage reference code: [google_cloud_services_demo.py](google_cloud_services_demo.py)
- Visual architecture diagram: [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)

---

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

---

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

---

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

---

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

---

## 🚀 Quick Start

### Prerequisites

- Google Cloud project with billing enabled
- The following APIs enabled in your GCP project:
  - Vertex AI API
  - Cloud Speech-to-Text API
  - Cloud Text-to-Speech API
  - Cloud Translate API

### Run Locally

```bash
# Clone the repository
git clone https://github.com/suhaif314/live-voice-translator.git
cd live-voice-translator

# Install dependencies
pip install -r requirements.txt

# Authenticate with Google Cloud
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Run the voice web app
python3 app.py

# Open http://localhost:8080
```

### Deploy to Cloud Run

```bash
gcloud run deploy live-voice-translator \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --timeout 300 \
    --port 8080
```

---

## 🧪 Reproducible Testing Instructions (For Judges)

> **Judges can fully verify this project in under 5 minutes using the steps below.**
> No microphone is required — Text Mode allows complete pipeline validation from any browser.

### Option A: Test the Live Deployed Version (Fastest)

1. Open the deployed app URL:
   **https://voice-translator-XXXXX-uc.a.run.app**
   *(Replace with your actual Cloud Run URL)*

2. The app loads instantly in any modern browser — no login or setup needed.

3. Follow the test cases below.

### Option B: Run Locally and Test

1. **Clone and install:**

   ```bash
   git clone https://github.com/suhaif314/live-voice-translator.git
   cd live-voice-translator
   pip install -r requirements.txt
   ```

2. **Set up Google Cloud authentication:**

   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable required APIs:**

   ```bash
   gcloud services enable \
     aiplatform.googleapis.com \
     speech.googleapis.com \
     texttospeech.googleapis.com \
     translate.googleapis.com
   ```

4. **Start the server:**

   ```bash
   python3 app.py
   ```

5. **Open in browser:**

   ```
   http://localhost:8080
   ```

---

### ✅ Test Case 1: Text Translation (No Microphone Needed)

> This is the **fastest way** to validate the full pipeline without microphone permissions.

| Step | Action |
|------|--------|
| 1 | Open the app in your browser |
| 2 | Set **Speaker A** language to `English` |
| 3 | Set **Speaker B** language to `French` |
| 4 | Keep engine set to `🤖 Gemini LLM` |
| 5 | Scroll to the **📝 Text Translation** section at the bottom |
| 6 | Type: `Hello, thank you for joining the meeting today.` |
| 7 | Click **Translate & Speak** |

**✅ Expected Result:**
- ✔️ The original English text appears in the conversation log
- ✔️ A French translation is returned (e.g., *"Bonjour, merci de vous joindre à la réunion aujourd'hui."*)
- ✔️ Audio playback is generated and plays automatically
- ✔️ The entry appears in the **💬 Conversation** history section

---

### ✅ Test Case 2: Voice Translation (Microphone Required)

| Step | Action |
|------|--------|
| 1 | Allow microphone access when prompted by the browser |
| 2 | Set **Speaker A** to `English`, **Speaker B** to `French` |
| 3 | **Hold** the blue 🎤 button under Speaker A |
| 4 | Speak clearly: *"Can we review the project timeline tomorrow morning?"* |
| 5 | **Release** the button and wait 2-3 seconds |

**✅ Expected Result:**
- ✔️ The pipeline visualization lights up: **Capture → STT → Translate → TTS → Play**
- ✔️ The recognized English transcript appears under Speaker A
- ✔️ The French translation appears under Speaker B
- ✔️ French audio plays automatically
- ✔️ Timing metrics appear in the status bar (typically 1-3 seconds total)

---

### ✅ Test Case 3: Bidirectional Conversation

| Step | Action |
|------|--------|
| 1 | Complete Test Case 2 first |
| 2 | Now **hold** the purple 🎤 button under **Speaker B** |
| 3 | Speak a short reply in French (or any language set for Speaker B) |
| 4 | **Release** the button |

**✅ Expected Result:**
- ✔️ Speaker B's speech is transcribed
- ✔️ Translation back to English is displayed for Speaker A
- ✔️ English audio plays automatically for Speaker A
- ✔️ Both conversation turns appear in the **💬 Conversation** history with timestamps

---

### ✅ Test Case 4: Fallback Engine (Cloud Translate API)

| Step | Action |
|------|--------|
| 1 | Click the **☁️ Cloud API** button at the top (switches from Gemini to Cloud Translate) |
| 2 | Repeat **Test Case 1** (text) or **Test Case 2** (voice) |

**✅ Expected Result:**
- ✔️ Translation still succeeds using Google Cloud Translate API
- ✔️ Audio is still generated and plays correctly
- ✔️ The app works seamlessly with both translation engines

---

### ✅ Test Case 5: Health Check Endpoint

```bash
curl https://YOUR_CLOUD_RUN_URL/health
```

**✅ Expected Result:**
```json
{"status": "ok", "version": "3.0"}
```

---

### 📝 Notes for Judges

| Topic | Detail |
|-------|--------|
| **No mic?** | Use **Text Mode** (Test Case 1) to fully verify STT → Translate → TTS pipeline |
| **STT returns empty?** | Speak for 2+ seconds, clearly, in a quiet environment |
| **Best browsers** | Chrome or Edge (best microphone + audio support) |
| **Typical latency** | 1–3 seconds end-to-end depending on network |
| **Languages** | All 10 languages (EN, FR, ES, DE, IT, PT, JA, ZH, KO, HI) work for text and voice |
| **Mobile** | Fully responsive — works on phone browsers too |

---

## 🎮 How to Use

1. **Select languages** for Speaker A and Speaker B
2. **Choose engine**: Gemini LLM (richer) or Cloud API (faster)
3. **Speaker A**: Hold the blue button → Speak → Release
4. AI translates and plays audio on Speaker B's side
5. **Speaker B**: Hold the purple button → Respond → Release
6. AI translates back for Speaker A
7. Conversation continues naturally!

---

## 📊 Performance

| Step | Typical Latency |
|------|----------------|
| STT | 500–1500ms |
| Gemini Translation | 300–800ms |
| Cloud Translation | 100–300ms |
| TTS | 200–500ms |
| **Total Pipeline** | **1–3 seconds** |

---

## 🏆 Challenge Category

**Live Agents 🗣️** — Real-time Interaction (Audio)

This agent enables natural voice conversations between speakers of different languages, with:
- Real-time audio input/output (multimodal, beyond text-in/text-out)
- Automatic turn-taking via silence detection
- Gemini LLM for context-aware translation
- Google ADK agent orchestration
- Hosted on Google Cloud

---

## 📄 License

MIT License

---

## 👤 Author

Built by [suhaif314](https://github.com/suhaif314) for the Gemini Live Agent Challenge 2026
