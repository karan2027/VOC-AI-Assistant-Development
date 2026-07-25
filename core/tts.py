import os
import re
import time
import ctypes
import threading
import pyttsx3
from gtts import gTTS
from typing import Optional
from ai_agent.openai_client import OpenAIClient
import logging

logger = logging.getLogger("assistant.core.tts")

def play_audio_windows(file_path: str):
    """Uses Windows Multimedia API (MCI) to play MP3/WAV files without external processes."""
    try:
        # Resolve to absolute path and normalize slashes
        abs_path = os.path.abspath(file_path)
        logger.info("Playing audio file natively: %s", abs_path)
        
        # Open the media file
        ctypes.windll.winmm.mciSendStringW(f'open "{abs_path}" type mpegvideo alias tts_audio', None, 0, 0)
        # Play the media file (wait block tells MCI to return only after audio finishes playing)
        ctypes.windll.winmm.mciSendStringW('play tts_audio wait', None, 0, 0)
        # Close media file to free resources
        ctypes.windll.winmm.mciSendStringW('close tts_audio', None, 0, 0)
    except Exception as e:
        logger.error("Failed to play audio natively on Windows: %s", e)
        # Fallback to os.system start (last resort)
        try:
            os.system(f'start /min "" "{abs_path}"')
        except Exception:
            pass

class TextToSpeechController:
    def __init__(self, openai_client: OpenAIClient, engine_type: str = "pyttsx3", voice_index: int = 0):
        self.openai_client = openai_client
        self.engine_type = engine_type.lower().strip()
        self.voice_index = voice_index
        
        # Cache directory for audio outputs
        self.cache_dir = "output/audio"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        logger.info("TextToSpeechController initialized with engine: %s", self.engine_type)

    def speak(self, text: str, block: bool = True):
        """Synthesizes text and reads it out loud."""
        if not text.strip():
            return

        # Clean text specifically for spoken output (removes code blocks/markdown characters from voice)
        speech_text = re.sub(r'```[\s\S]*?```', ' [code snippet rendered on screen] ', text)
        speech_text = re.sub(r'[\*\#\_`~]', '', speech_text).strip()
        if not speech_text:
            speech_text = "Here is the result."

        logger.info("Speaking: '%s' using %s engine", speech_text[:60], self.engine_type)

        if self.engine_type == "openai" and self.openai_client.is_available():
            self._speak_openai(speech_text, block)
        elif self.engine_type == "gtts":
            self._speak_gtts(speech_text, block)
        else:
            self._speak_local(speech_text, block)

    def stop_speech(self):
        """Stops any ongoing speech playback immediately."""
        logger.info("Stopping ongoing speech playback...")
        try:
            if hasattr(self, "_active_engine") and self._active_engine:
                self._active_engine.stop()
                self._active_engine = None
        except Exception as e:
            logger.warning("Error stopping speech: %s", e)

    def _speak_local(self, text: str, block: bool):
        """Offline speech using pyttsx3."""
        def run():
            try:
                # Initialize pyttsx3 locally on this thread to avoid SAPI COM threading issues
                engine = pyttsx3.init()
                self._active_engine = engine
                voices = engine.getProperty('voices')
                if voices and len(voices) > self.voice_index:
                    engine.setProperty('voice', voices[self.voice_index].id)
                engine.setProperty('rate', 175)
                
                engine.say(text)
                engine.runAndWait()
                self._active_engine = None
            except Exception as e:
                logger.error("pyttsx3 speech failed: %s", e)
                self._active_engine = None

        if block:
            run()
        else:
            threading.Thread(target=run, daemon=True).start()

    def _speak_gtts(self, text: str, block: bool):
        """Online speech using gTTS."""
        output_file = os.path.join(self.cache_dir, "gtts_temp.mp3")
        
        def run():
            try:
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(output_file)
                play_audio_windows(output_file)
            except Exception as e:
                logger.error("gTTS speech failed: %s. Falling back to local offline speech.", e)
                self._speak_local(text, block=True)

        if block:
            run()
        else:
            threading.Thread(target=run, daemon=True).start()

    def _speak_openai(self, text: str, block: bool):
        """Premium online speech using OpenAI TTS API."""
        output_file = os.path.join(self.cache_dir, "openai_temp.mp3")
        
        def run():
            # Call openai_client to generate TTS mp3 file
            success = self.openai_client.generate_speech_file(
                text=text,
                output_path=output_file,
                voice="alloy"
            )
            if success:
                play_audio_windows(output_file)
            else:
                logger.warning("OpenAI TTS failed. Falling back to local speech.")
                self._speak_local(text, block=True)

        if block:
            run()
        else:
            threading.Thread(target=run, daemon=True).start()
