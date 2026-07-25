import time
from typing import List, Callable, Optional
from core.speech import SpeechToTextController
import logging

logger = logging.getLogger("assistant.core.wakeword")

class WakeWordDetector:
    def __init__(self, stt_controller: SpeechToTextController, wake_words: Optional[List[str]] = None):
        self.stt = stt_controller
        self.wake_words = wake_words or ["hello ai", "jarvis", "assistant", "hey ai", "wake up"]
        self.wake_words = [w.lower().strip() for w in self.wake_words]
        self.is_listening = False
        
        logger.info("WakeWordDetector initialized with words: %s", self.wake_words)

    def wait_for_wake_word(self, on_wake_detected: Optional[Callable] = None) -> bool:
        """Blocks and continuously listens until a wake word is detected.
        Returns True when wake word is detected.
        """
        self.is_listening = True
        logger.info("Starting background wake-word listening...")
        
        # Calibrate once before loop
        self.stt.calibrate(duration=1.0)
        
        while self.is_listening:
            # Listen with short timeouts for responsiveness
            text, success = self.stt.listen_and_transcribe(timeout=2.0, phrase_time_limit=3.0)
            if not success or not text:
                continue
                
            clean_text = text.lower().strip()
            logger.debug("WakeWord monitor transcribed: '%s'", clean_text)
            
            # Check matches
            matched = False
            for wake_word in self.wake_words:
                if wake_word in clean_text:
                    logger.info("Wake word '%s' detected!", wake_word)
                    matched = True
                    break
                    
            if matched:
                self.is_listening = False
                if on_wake_detected:
                    on_wake_detected()
                return True
                
            # Yield control slightly
            time.sleep(0.1)
            
        return False

    def stop(self):
        """Stops the active wake word monitor loop."""
        self.is_listening = False
        logger.info("Wake-word listening stopped.")
