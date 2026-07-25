import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("assistant.ai.openai")

class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.model_override = None
        if self.api_key:
            try:
                # Detect Google Gemini key prefix (handles both classic 'AIzaSy' and new 'AQ.' keys)
                if self.api_key.strip().startswith(("AIzaSy", "AQ.")):
                    self.client = OpenAI(
                        api_key=self.api_key.strip(),
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                    )
                    self.model_override = "gemini-3.5-flash-lite"
                    logger.info("Configured to use free Google Gemini API compatibility layer (gemini-3.5-flash-lite).")
                else:
                    self.client = OpenAI(api_key=self.api_key)
                    logger.info("OpenAI Client successfully initialized.")
            except Exception as e:
                logger.error("Failed to initialize Client: %s", e)
        else:
            logger.warning("No API key found. AI features will be unavailable.")

    def is_available(self) -> bool:
        return self.client is not None

    def get_chat_response(self, messages: List[Dict[str, str]], model: str = "gpt-4o", tools: Optional[List[Dict[str, Any]]] = None) -> Optional[Any]:
        """Gets chat completion from GPT/Gemini, supporting tool calls."""
        if not self.is_available():
            logger.error("Client is not initialized.")
            return None
        try:
            target_model = self.model_override or model
            logger.info("Requesting chat completion (model: %s)...", target_model)
            kwargs = {
                "model": target_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
                
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            logger.info("Chat completion received successfully.")
            return message
        except Exception as e:
            logger.error("Chat completion failed: %s", e)
            return None

    def transcribe_audio_file(self, audio_file_path: str) -> Optional[str]:
        """Transcribes an audio file using Whisper API."""
        if not self.is_available():
            logger.error("OpenAI Client is not initialized for STT.")
            return None
        try:
            logger.info("Transcribing audio file: %s using Whisper API", audio_file_path)
            with open(audio_file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            text = transcription.text
            logger.info("Whisper transcription success: %s", text)
            return text
        except Exception as e:
            logger.error("Whisper transcription failed: %s", e)
            return None

    def generate_speech_file(self, text: str, output_path: str, voice: str = "alloy", model: str = "tts-1") -> bool:
        """Synthesizes text to speech file using OpenAI TTS API."""
        if not self.is_available():
            logger.error("OpenAI Client is not initialized for TTS.")
            return False
        try:
            logger.info("Generating TTS speech for text (length: %d) -> %s", len(text), output_path)
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            response.stream_to_file(output_path)
            logger.info("OpenAI TTS file saved successfully.")
            return True
        except Exception as e:
            logger.error("OpenAI TTS generation failed: %s", e)
            return False
