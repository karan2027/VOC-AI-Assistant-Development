import os
import re
import speech_recognition as sr
from typing import Optional, Tuple
from ai_agent.openai_client import OpenAIClient
import logging

logger = logging.getLogger("assistant.core.speech")

class SpeechToTextController:
    def __init__(self, openai_client: OpenAIClient, engine_type: str = "google"):
        self.openai_client = openai_client
        self.engine_type = engine_type.lower().strip()
        self.recognizer = sr.Recognizer()
        
        # Configure thresholds
        from config import Config
        self.recognizer.energy_threshold = Config.MICROPHONE_THRESHOLD
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = Config.PAUSE_THRESHOLD
        
        self.cache_dir = "output/audio"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def calibrate(self, duration: float = 1.0):
        """Calibrates microphone for ambient noise levels with safety bounds."""
        try:
            with sr.Microphone() as source:
                logger.info("Calibrating microphone for ambient noise (%d sec)...", duration)
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                self.recognizer.dynamic_energy_threshold = False
                
                # Keep threshold within safe bounds for human speech
                if self.recognizer.energy_threshold < 300:
                    self.recognizer.energy_threshold = 300
                elif self.recognizer.energy_threshold > 1200:
                    logger.info("Calibration threshold %s was too high, capping at 1200.", self.recognizer.energy_threshold)
                    self.recognizer.energy_threshold = 1200
                    
                logger.info("Calibration complete. Energy threshold set to: %s", self.recognizer.energy_threshold)
        except Exception as e:
            logger.warning("Microphone calibration failed (no mic?): %s", e)

    def listen_and_transcribe(self, timeout: float = 5.0, phrase_time_limit: float = 15.0) -> Tuple[Optional[str], bool]:
        """Listens from the microphone and transcribes it to text.
        Returns:
            Tuple[transcription_text, success_status]
        """
        try:
            with sr.Microphone() as source:
                logger.info("Listening (waiting for up to %s seconds pause before processing)...", self.recognizer.pause_threshold)
                # Capture audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                logger.info("Audio captured successfully, processing transcription...")
                
                if self.engine_type == "openai" and self.openai_client.is_available():
                    return self._transcribe_openai(audio)
                else:
                    return self._transcribe_google(audio)
        except sr.WaitTimeoutError:
            # Idle listening timeout
            return None, False
        except Exception as e:
            logger.error("Error capturing speech: %s", e)
            return None, False

    def _transcribe_google(self, audio: sr.AudioData) -> Tuple[Optional[str], bool]:
        """Recognizes speech using Google Speech Recognition API (built into library)."""
        try:
            text = self.recognizer.recognize_google(audio)
            logger.info("Google Speech transcription: %s", text)
            return text, True
        except sr.UnknownValueError:
            logger.info("Google Speech could not understand audio.")
            return None, False
        except sr.RequestError as e:
            logger.error("Google Speech API request failed: %s", e)
            return None, False

    def _transcribe_openai(self, audio: sr.AudioData) -> Tuple[Optional[str], bool]:
        """Recognizes speech using OpenAI Whisper API."""
        wav_path = os.path.join(self.cache_dir, "stt_temp.wav")
        try:
            # Write audio object as WAV file
            with open(wav_path, "wb") as f:
                f.write(audio.get_wav_data())
            
            # Send file to Whisper STT
            text = self.openai_client.transcribe_audio_file(wav_path)
            
            # Remove temp file
            if os.path.exists(wav_path):
                os.remove(wav_path)
                
            if text:
                return text, True
            else:
                return None, False
        except Exception as e:
            logger.error("OpenAI Whisper transcription failed: %s. Falling back to Google.", e)
            return self._transcribe_google(audio)
