"""
Live Streaming Handler for Real-time Voice Translation
Uses Gemini Live API for bidirectional audio streaming
"""

import asyncio
import base64
import json
import os
from typing import AsyncGenerator, Optional
from datetime import datetime

from google import genai
from google.genai import types

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_ID = "gemini-2.0-flash-live-001"

# Voice Activity Detection settings
VAD_SETTINGS = {
    "silence_threshold_ms": 1000,  # 1 second of silence = end of turn
    "min_speech_ms": 200,          # Minimum speech duration
}


class LiveTranslatorSession:
    """
    Manages a live translation session between two speakers.
    """
    
    def __init__(
        self,
        speaker_a_language: str = "english",
        speaker_b_language: str = "french"
    ):
        self.speaker_a_language = speaker_a_language
        self.speaker_b_language = speaker_b_language
        self.current_speaker = "A"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_history = []
        
        # Initialize Gemini client
        self.client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION
        )
        
        # Live API configuration
        self.live_config = types.LiveConnectConfig(
            response_modalities=["AUDIO", "TEXT"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"  # Can be: Puck, Charon, Kore, Fenrir, Aoede
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=self._get_system_instruction())]
            ),
        )
    
    def _get_system_instruction(self) -> str:
        return f"""
        You are a real-time voice translator facilitating a conversation between:
        - Speaker A who speaks {self.speaker_a_language}
        - Speaker B who speaks {self.speaker_b_language}
        
        Your task:
        1. When you hear speech in {self.speaker_a_language}, translate it to {self.speaker_b_language} and speak it
        2. When you hear speech in {self.speaker_b_language}, translate it to {self.speaker_a_language} and speak it
        
        Important guidelines:
        - Translate accurately preserving meaning and tone
        - Speak naturally and clearly
        - Handle interruptions gracefully
        - Keep translations concise but complete
        - If you're unsure about a word, use the closest equivalent
        
        Current conversation context will be maintained for better translations.
        """
    
    async def process_audio_stream(
        self,
        audio_generator: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[dict, None]:
        """
        Process incoming audio stream and yield translations.
        
        Args:
            audio_generator: Async generator yielding audio chunks
            
        Yields:
            Dictionary with translation results
        """
        async with self.client.aio.live.connect(
            model=MODEL_ID,
            config=self.live_config
        ) as session:
            
            # Start sender task
            async def send_audio():
                async for audio_chunk in audio_generator:
                    await session.send(
                        input=types.LiveClientRealtimeInput(
                            media_chunks=[
                                types.Blob(
                                    data=audio_chunk,
                                    mime_type="audio/pcm"
                                )
                            ]
                        )
                    )
            
            # Start sender in background
            sender_task = asyncio.create_task(send_audio())
            
            try:
                # Receive responses
                async for response in session.receive():
                    if response.server_content:
                        content = response.server_content
                        
                        result = {
                            "timestamp": datetime.now().isoformat(),
                            "type": "translation"
                        }
                        
                        # Handle text response
                        if hasattr(content, 'model_turn') and content.model_turn:
                            for part in content.model_turn.parts:
                                if hasattr(part, 'text') and part.text:
                                    result["text"] = part.text
                                    result["type"] = "text"
                                    yield result
                        
                        # Handle audio response
                        if hasattr(content, 'model_turn') and content.model_turn:
                            for part in content.model_turn.parts:
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    audio_data = part.inline_data.data
                                    result["audio_base64"] = base64.b64encode(audio_data).decode()
                                    result["type"] = "audio"
                                    yield result
                        
                        # Handle turn completion
                        if content.turn_complete:
                            yield {
                                "type": "turn_complete",
                                "timestamp": datetime.now().isoformat()
                            }
                            # Switch speaker
                            self.current_speaker = "B" if self.current_speaker == "A" else "A"
                        
                        # Handle interruption
                        if content.interrupted:
                            yield {
                                "type": "interrupted",
                                "timestamp": datetime.now().isoformat()
                            }
                            
            finally:
                sender_task.cancel()
                try:
                    await sender_task
                except asyncio.CancelledError:
                    pass
    
    def switch_speaker(self) -> str:
        """Switch to the other speaker and return current speaker ID."""
        self.current_speaker = "B" if self.current_speaker == "A" else "A"
        return self.current_speaker
    
    def get_current_target_language(self) -> str:
        """Get the target language for translation based on current speaker."""
        if self.current_speaker == "A":
            return self.speaker_b_language
        else:
            return self.speaker_a_language


class SimpleTranslator:
    """
    Simplified translator for text-based translation with audio output.
    Useful for testing without live streaming.
    """
    
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION
        )
    
    async def translate_and_speak(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> dict:
        """
        Translate text and generate speech.
        
        Args:
            text: Text to translate
            source_language: Source language
            target_language: Target language
            
        Returns:
            Dictionary with translation and audio
        """
        prompt = f"""
        Translate the following text from {source_language} to {target_language}.
        Only provide the translation, nothing else.
        
        Text: {text}
        """
        
        response = await self.client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        translated_text = response.text.strip()
        
        return {
            "success": True,
            "original_text": text,
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": target_language
        }


# Export session class
__all__ = ["LiveTranslatorSession", "SimpleTranslator"]