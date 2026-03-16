"""
Web Server for Live Voice Translator
Provides WebSocket interface for real-time audio streaming
"""

import asyncio
import base64
import json
import os
from aiohttp import web
import aiohttp

# Import our modules
from agent import (
    speech_to_text,
    translate_text, 
    text_to_speech,
    full_translation_pipeline,
    SUPPORTED_LANGUAGES
)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live AI Voice Translator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            color: #888;
            font-size: 1.1em;
        }
        
        .translator-container {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 30px;
            margin-top: 30px;
        }
        
        .speaker-panel {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .panel-title {
            font-size: 1.3em;
            font-weight: 600;
        }
        
        select {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: #fff;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
        }
        
        .record-btn {
            width: 100%;
            padding: 20px;
            font-size: 1.2em;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .record-btn.idle {
            background: linear-gradient(135deg, #00d4ff, #0099cc);
            color: #fff;
        }
        
        .record-btn.recording {
            background: linear-gradient(135deg, #ff4757, #ff6b81);
            color: #fff;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }
        
        .transcript-box {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            min-height: 150px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .transcript-label {
            font-size: 0.9em;
            color: #888;
            margin-bottom: 10px;
        }
        
        .transcript-text {
            font-size: 1.1em;
            line-height: 1.6;
        }
        
        .middle-section {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .arrow {
            font-size: 2em;
            color: #00d4ff;
            margin: 10px 0;
        }
        
        .status {
            text-align: center;
            padding: 15px;
            background: rgba(0,212,255,0.1);
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-indicator.connected {
            background: #00ff88;
        }
        
        .status-indicator.disconnected {
            background: #ff4757;
        }
        
        .conversation-log {
            margin-top: 40px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 25px;
        }
        
        .log-entry {
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            background: rgba(0,0,0,0.2);
        }
        
        .log-entry.speaker-a {
            border-left: 4px solid #00d4ff;
        }
        
        .log-entry.speaker-b {
            border-left: 4px solid #7c3aed;
        }
        
        .log-speaker {
            font-size: 0.9em;
            color: #888;
            margin-bottom: 5px;
        }
        
        .log-original {
            margin-bottom: 8px;
        }
        
        .log-translated {
            color: #00d4ff;
            font-style: italic;
        }
        
        .audio-player {
            margin-top: 15px;
        }
        
        audio {
            width: 100%;
            height: 40px;
        }

        .test-section {
            margin-top: 40px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 25px;
        }

        .test-input {
            width: 100%;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 1em;
            margin-bottom: 15px;
        }

        .test-btn {
            background: linear-gradient(135deg, #7c3aed, #a855f7);
            color: #fff;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .test-btn:hover {
            transform: scale(1.02);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌐 Live AI Voice Translator</h1>
            <p class="subtitle">Real-time multilingual conversation powered by Gemini</p>
        </header>
        
        <div class="translator-container">
            <!-- Speaker A Panel -->
            <div class="speaker-panel">
                <div class="panel-header">
                    <span class="panel-title">👤 Speaker A</span>
                    <select id="langA">
                        <option value="english" selected>English</option>
                        <option value="french">French</option>
                        <option value="spanish">Spanish</option>
                        <option value="german">German</option>
                        <option value="italian">Italian</option>
                        <option value="japanese">Japanese</option>
                        <option value="chinese">Chinese</option>
                    </select>
                </div>
                
                <button id="recordA" class="record-btn idle">
                    <span id="recordAIcon">🎤</span>
                    <span id="recordAText">Press to Speak</span>
                </button>
                
                <div class="transcript-box">
                    <div class="transcript-label">Transcript</div>
                    <div id="transcriptA" class="transcript-text">
                        Your speech will appear here...
                    </div>
                </div>
                
                <div class="audio-player">
                    <audio id="audioA" controls></audio>
                </div>
            </div>
            
            <!-- Middle Section -->
            <div class="middle-section">
                <div class="arrow">⟷</div>
                <div class="status">
                    <span id="statusIndicator" class="status-indicator connected"></span>
                    <span id="statusText">Ready</span>
                </div>
            </div>
            
            <!-- Speaker B Panel -->
            <div class="speaker-panel">
                <div class="panel-header">
                    <span class="panel-title">👤 Speaker B</span>
                    <select id="langB">
                        <option value="english">English</option>
                        <option value="french" selected>French</option>
                        <option value="spanish">Spanish</option>
                        <option value="german">German</option>
                        <option value="italian">Italian</option>
                        <option value="japanese">Japanese</option>
                        <option value="chinese">Chinese</option>
                    </select>
                </div>
                
                <button id="recordB" class="record-btn idle">
                    <span id="recordBIcon">🎤</span>
                    <span id="recordBText">Press to Speak</span>
                </button>
                
                <div class="transcript-box">
                    <div class="transcript-label">Transcript</div>
                    <div id="transcriptB" class="transcript-text">
                        Your speech will appear here...
                    </div>
                </div>
                
                <div class="audio-player">
                    <audio id="audioB" controls></audio>
                </div>
            </div>
        </div>
        
        <!-- Test Section for Text Input -->
        <div class="test-section">
            <h3 style="margin-bottom: 20px;">📝 Test Translation (Text Input)</h3>
            <input type="text" id="testInput" class="test-input" 
                   placeholder="Type something to translate...">
            <button id="testBtn" class="test-btn">Translate & Speak</button>
            <div id="testResult" class="transcript-box" style="margin-top: 20px;">
                <div class="transcript-label">Translation Result</div>
                <div id="testOutput" class="transcript-text"></div>
            </div>
        </div>
        
        <!-- Conversation Log -->
        <div class="conversation-log">
            <h3 style="margin-bottom: 20px;">💬 Conversation History</h3>
            <div id="conversationLog"></div>
        </div>
    </div>
    
    <script>
        // Audio Recording Setup
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        let currentSpeaker = null;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            setupRecordButtons();
            setupTestButton();
        });
        
        function setupRecordButtons() {
            ['A', 'B'].forEach(speaker => {
                const btn = document.getElementById(`record${speaker}`);
                btn.addEventListener('mousedown', () => startRecording(speaker));
                btn.addEventListener('mouseup', () => stopRecording(speaker));
                btn.addEventListener('mouseleave', () => {
                    if (isRecording && currentSpeaker === speaker) {
                        stopRecording(speaker);
                    }
                });
                
                // Touch events for mobile
                btn.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    startRecording(speaker);
                });
                btn.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    stopRecording(speaker);
                });
            });
        }
        
        async function startRecording(speaker) {
            if (isRecording) return;
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        sampleRate: 16000,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true
                    } 
                });
                
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                
                audioChunks = [];
                currentSpeaker = speaker;
                isRecording = true;
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    await processRecording(audioBlob, speaker);
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start(100); // Collect data every 100ms
                
                // Update UI
                const btn = document.getElementById(`record${speaker}`);
                btn.classList.remove('idle');
                btn.classList.add('recording');
                document.getElementById(`record${speaker}Text`).textContent = 'Recording...';
                document.getElementById(`record${speaker}Icon`).textContent = '🔴';
                
                updateStatus('Recording...', true);
                
            } catch (error) {
                console.error('Error starting recording:', error);
                updateStatus('Microphone access denied', false);
            }
        }
        
        function stopRecording(speaker) {
            if (!isRecording || currentSpeaker !== speaker) return;
            
            isRecording = false;
            
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            
            // Update UI
            const btn = document.getElementById(`record${speaker}`);
            btn.classList.remove('recording');
            btn.classList.add('idle');
            document.getElementById(`record${speaker}Text`).textContent = 'Press to Speak';
            document.getElementById(`record${speaker}Icon`).textContent = '🎤';
            
            updateStatus('Processing...', true);
        }
        
        async function processRecording(audioBlob, speaker) {
            try {
                // Convert to base64
                const arrayBuffer = await audioBlob.arrayBuffer();
                const base64Audio = btoa(
                    new Uint8Array(arrayBuffer)
                        .reduce((data, byte) => data + String.fromCharCode(byte), '')
                );
                
                // Get language settings
                const sourceLang = document.getElementById(`lang${speaker}`).value;
                const targetLang = document.getElementById(`lang${speaker === 'A' ? 'B' : 'A'}`).value;
                
                // Send to server
                const response = await fetch('/api/translate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        audio_base64: base64Audio,
                        source_language: sourceLang,
                        target_language: targetLang,
                        speaker: speaker
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Update transcripts
                    document.getElementById(`transcript${speaker}`).textContent = 
                        result.original_text;
                    
                    // Play translated audio on the other speaker's side
                    const otherSpeaker = speaker === 'A' ? 'B' : 'A';
                    if (result.audio_base64) {
                        const audio = document.getElementById(`audio${otherSpeaker}`);
                        audio.src = `data:audio/mp3;base64,${result.audio_base64}`;
                        audio.play();
                    }
                    
                    // Update other speaker's transcript with translation
                    document.getElementById(`transcript${otherSpeaker}`).textContent = 
                        result.translated_text;
                    
                    // Add to conversation log
                    addToLog(speaker, sourceLang, targetLang, 
                             result.original_text, result.translated_text);
                    
                    updateStatus('Ready', true);
                } else {
                    updateStatus(`Error: ${result.error}`, false);
                }
                
            } catch (error) {
                console.error('Error processing recording:', error);
                updateStatus('Processing error', false);
            }
        }
        
        function setupTestButton() {
            document.getElementById('testBtn').addEventListener('click', async () => {
                const text = document.getElementById('testInput').value;
                if (!text) return;
                
                const sourceLang = document.getElementById('langA').value;
                const targetLang = document.getElementById('langB').value;
                
                updateStatus('Translating...', true);
                
                try {
                    const response = await fetch('/api/translate-text', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            text: text,
                            source_language: sourceLang,
                            target_language: targetLang
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('testOutput').innerHTML = `
                            <strong>Original (${sourceLang}):</strong> ${result.original_text}<br><br>
                            <strong>Translation (${targetLang}):</strong> ${result.translated_text}
                        `;
                        
                        // Play audio if available
                        if (result.audio_base64) {
                            const audio = document.getElementById('audioB');
                            audio.src = `data:audio/mp3;base64,${result.audio_base64}`;
                            audio.play();
                        }
                        
                        updateStatus('Ready', true);
                    } else {
                        updateStatus(`Error: ${result.error}`, false);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    updateStatus('Translation error', false);
                }
            });
        }
        
        function addToLog(speaker, sourceLang, targetLang, original, translated) {
            const log = document.getElementById('conversationLog');
            const entry = document.createElement('div');
            entry.className = `log-entry speaker-${speaker.toLowerCase()}`;
            entry.innerHTML = `
                <div class="log-speaker">Speaker ${speaker} (${sourceLang} → ${targetLang})</div>
                <div class="log-original">${original}</div>
                <div class="log-translated">${translated}</div>
            `;
            log.insertBefore(entry, log.firstChild);
        }
        
        function updateStatus(text, isOk) {
            document.getElementById('statusText').textContent = text;
            const indicator = document.getElementById('statusIndicator');
            indicator.className = 'status-indicator ' + (isOk ? 'connected' : 'disconnected');
        }
    </script>
</body>
</html>
"""


# API Routes
routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
    """Serve the main web interface."""
    return web.Response(text=HTML_TEMPLATE, content_type='text/html')


@routes.post('/api/translate')
async def translate_audio(request):
    """
    Handle audio translation requests.
    Receives base64 audio, returns translation with TTS audio.
    """
    try:
        data = await request.json()
        
        audio_base64 = data.get('audio_base64', '')
        source_language = data.get('source_language', 'english')
        target_language = data.get('target_language', 'french')
        
        # Use the full pipeline
        result = full_translation_pipeline(
            audio_content=audio_base64,
            source_language=source_language,
            target_language=target_language
        )
        
        return web.json_response(result)
        
    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


@routes.post('/api/translate-text')
async def translate_text_endpoint(request):
    """
    Handle text translation requests.
    Receives text, returns translation with TTS audio.
    """
    try:
        data = await request.json()
        
        text = data.get('text', '')
        source_language = data.get('source_language', 'english')
        target_language = data.get('target_language', 'french')
        
        # Translate
        translation_result = translate_text(text, source_language, target_language)
        
        if not translation_result['success']:
            return web.json_response(translation_result)
        
        # Generate speech
        tts_result = text_to_speech(
            translation_result['translated_text'],
            target_language
        )
        
        return web.json_response({
            'success': True,
            'original_text': text,
            'translated_text': translation_result['translated_text'],
            'audio_base64': tts_result.get('audio_base64', ''),
            'source_language': source_language,
            'target_language': target_language
        })
        
    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


@routes.get('/api/languages')
async def get_languages(request):
    """Return list of supported languages."""
    return web.json_response({
        'success': True,
        'languages': SUPPORTED_LANGUAGES
    })


@routes.get('/health')
async def health_check(request):
    """Health check endpoint."""
    return web.json_response({'status': 'healthy'})


def create_app():
    """Create and configure the web application."""
    app = web.Application()
    app.add_routes(routes)
    return app


if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)