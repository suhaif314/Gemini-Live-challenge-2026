# Live AI Voice Translator - Architecture Diagram

This diagram shows how Gemini and Google Cloud services connect to the web frontend and backend.

```mermaid
flowchart LR
    %% User and browser experience
    U1[Speaker A\nMic Input] --> FE
    U2[Speaker B\nSpeaker Output] <-- FE

    subgraph FE[Frontend - Browser UI]
      UI[Language Selector\nPush-to-Talk\nConversation Timeline]
      CAP[Web Audio Capture\nWebM/Opus Chunks]
      PLAY[Audio Player\nMP3 Playback]
      UI --> CAP
      PLAY --> UI
    end

    CAP --> WS

    subgraph BE[Python Backend - aiohttp]
      WS[REST + Pipeline API\n/api/pipeline\n/api/translate-text]
      STT[Speech-to-Text Adapter]
      ORCH[Translation Orchestrator\nGemini or Cloud Translate]
      TTS[Text-to-Speech Adapter]
      METRICS[Timing + Conversation Logs]
      WS --> STT --> ORCH --> TTS --> WS
      ORCH --> METRICS
      STT --> METRICS
      TTS --> METRICS
    end

    WS --> GC_STT
    ORCH --> VERTEX
    ORCH --> GC_TRANSLATE
    TTS --> GC_TTS

    subgraph GCP[Google Cloud Services]
      VERTEX[Vertex AI\nGemini 2.5 Flash]
      GC_STT[Cloud Speech-to-Text API]
      GC_TRANSLATE[Cloud Translate API v2]
      GC_TTS[Cloud Text-to-Speech API\nNeural2 Voices]
      IAM[Application Default Credentials]
    end

    IAM -.auth.-> VERTEX
    IAM -.auth.-> GC_STT
    IAM -.auth.-> GC_TRANSLATE
    IAM -.auth.-> GC_TTS

    WS --> PLAY

    classDef frontend fill:#E8F4FF,stroke:#2E6CF6,stroke-width:1.5px,color:#0B1F44;
    classDef backend fill:#EFFFF3,stroke:#1B8E3E,stroke-width:1.5px,color:#12341F;
    classDef cloud fill:#FFF4E8,stroke:#C96A15,stroke-width:1.5px,color:#4A2A0A;
    classDef user fill:#F8ECFF,stroke:#7E3BB6,stroke-width:1.5px,color:#30124A;

    class UI,CAP,PLAY frontend;
    class WS,STT,ORCH,TTS,METRICS backend;
    class VERTEX,GC_STT,GC_TRANSLATE,GC_TTS,IAM cloud;
    class U1,U2 user;
```

## End-to-End Flow

1. Browser captures voice input and sends audio to the backend.
2. Backend sends audio to Cloud Speech-to-Text for transcription.
3. Backend chooses translation engine: Gemini on Vertex AI or Cloud Translate API.
4. Translated text is synthesized through Cloud Text-to-Speech.
5. MP3 audio returns to the browser and is played for the other speaker.
6. Conversation text and timings are logged and shown in the UI.
