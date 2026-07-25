import sys
import os
import re
import asyncio
import logging
import time
import threading
from config import Config
from utils.logger import setup_logger

from ai_agent.openai_client import OpenAIClient
from core.memory import ConversationMemory
from core.speech import SpeechToTextController
from core.tts import TextToSpeechController
from core.brain import AssistantBrain
from core.wake_word import WakeWordDetector

# Initialize logging
logger = setup_logger("assistant", Config.LOG_FILE, level=getattr(logging, Config.LOG_LEVEL))

class VoiceAssistantApp:
    def __init__(self):
        logger.info("Initializing AI Voice Assistant Application...")
        
        # 1. Initialize DB Memory
        self.memory = ConversationMemory(Config.DB_PATH)
        
        # Save configured names in preferences
        self.memory.set_preference("assistant_name", Config.ASSISTANT_NAME)
        self.memory.set_preference("user_name", Config.USER_NAME)

        # 2. Initialize OpenAI Client
        self.openai_client = OpenAIClient(Config.OPENAI_API_KEY)
        
        # 3. Initialize Speech STT & TTS controllers
        self.stt = SpeechToTextController(self.openai_client, Config.STT_ENGINE)
        self.tts = TextToSpeechController(self.openai_client, Config.TTS_ENGINE, Config.LOCAL_VOICE_INDEX)
        
        # 4. Initialize Brain orchestrator
        # We pass a callback for background timer triggers
        self.brain = AssistantBrain(
            self.openai_client, 
            self.memory, 
            timer_callback=self.on_timer_triggered
        )
        
        # 5. Initialize Wake Word detector
        self.wake_detector = WakeWordDetector(self.stt, Config.WAKE_WORDS)

    def on_timer_triggered(self, message: str):
        """Asynchronous callback executed when a timer or alarm fires."""
        logger.info("Timer event received: %s", message)
        self.tts.speak(message, block=False)

    def speak(self, text: str, block: bool = True):
        self.tts.speak(text, block)

    async def active_chat_session(self):
        """Runs continuous listening session. Jarvis never goes to sleep unless explicitly told to close/exit."""
        logger.info("Entering continuous active chat session...")
        print(f"\n{Config.ASSISTANT_NAME}: How can I help you?")
        self.tts.speak("How can I help you?", block=True)
        time.sleep(0.5)
        
        exit_cmds = ["goodbye", "good bye", "bye", "exit", "terminate", "shutdown", "turn off", "stop assistant", "close assistant", "quit", "close"]
        
        while True:
            text, success = self.stt.listen_and_transcribe(timeout=5.0, phrase_time_limit=15.0)
            
            if success and text:
                cleaned_text = text.lower().strip()
                logger.info("User input: '%s'", text)
                print(f"\n{Config.USER_NAME}: {text}")
                
                # Check for exit/close commands
                if any(cmd in cleaned_text for cmd in exit_cmds):
                    print(f"\n{Config.ASSISTANT_NAME}: Goodbye! Shutting down.")
                    self.tts.speak("Goodbye! Shutting down.", block=True)
                    sys.exit(0)
                
                # Check if user said wake word alone
                if cleaned_text in [w.lower() for w in Config.WAKE_WORDS]:
                    reply = f"Yes {Config.USER_NAME}? I'm listening."
                    print(f"\n{Config.ASSISTANT_NAME}: {reply}")
                    self.tts.speak(reply, block=True)
                    continue
                
                # Process the query through the brain
                response = await self.brain.process_query(text)
                logger.info("Brain Response: '%s'", response)
                print(f"\n{Config.ASSISTANT_NAME}: {response}")
                
                # Speak response out loud
                self.tts.speak(response, block=True)
                time.sleep(0.5) # Wait for room to settle
            else:
                # Silence or unrecognized speech: continue listening silently without going to sleep
                pass

    def run_wake_word_mode(self):
        """Main entry loop for voice assistant. Continuously listens for commands or wake word without sleeping."""
        logger.info("Voice Assistant started in continuous mode.")
        print(f"\n{Config.ASSISTANT_NAME}: System online. Ready for your command.")
        self.tts.speak(f"System online. Ready for your command.", block=True)
        
        try:
            asyncio.run(self.active_chat_session())
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt detected. Shutting down assistant.")
            print(f"\n{Config.ASSISTANT_NAME}: Goodbye!")
            self.tts.speak("Shutting down. Goodbye.", block=True)
            self.wake_detector.stop()
            sys.exit(0)

    def run_direct_mode(self):
        """Runs the assistant in direct listening mode, continuously waiting for commands without sleeping."""
        logger.info("Voice Assistant started in Direct Command listening mode.")
        print(f"\n{Config.ASSISTANT_NAME}: System online. Ready for your command.")
        self.tts.speak("System online. Ready for your command.", block=True)
        
        # Calibrate once on startup
        self.stt.calibrate(duration=1.0)
        
        exit_cmds = ["goodbye", "good bye", "bye", "exit", "terminate", "shutdown", "turn off", "stop assistant", "close assistant", "quit", "close"]
        
        try:
            while True:
                # Listen to voice input
                text, success = self.stt.listen_and_transcribe(timeout=5.0, phrase_time_limit=15.0)
                
                if success and text:
                    cleaned_text = text.lower().strip()
                    logger.info("User input: '%s'", text)
                    print(f"\n{Config.USER_NAME}: {text}")
                    
                    # Check for exit commands
                    if any(cmd in cleaned_text for cmd in exit_cmds):
                        print(f"\n{Config.ASSISTANT_NAME}: Goodbye!")
                        self.tts.speak("Goodbye! Shutting down.", block=True)
                        sys.exit(0)
                    
                    # Process the query through the brain
                    response = asyncio.run(self.brain.process_query(text))
                    logger.info("Brain Response: '%s'", response)
                    print(f"\n{Config.ASSISTANT_NAME}: {response}")
                    
                    # Speak response out loud
                    self.tts.speak(response, block=True)
                    time.sleep(0.5) # Wait for room to settle
                else:
                    # In direct mode, we don't say anything on silence, just continue waiting
                    pass
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt detected. Shutting down assistant.")
            print(f"\n{Config.ASSISTANT_NAME}: Goodbye!")
            self.tts.speak("Shutting down. Goodbye.", block=True)
            sys.exit(0)

    async def run_cli_mode(self):
        """CLI text-only mode for grading/testing purposes without voice hardware."""
        print("="*60)
        print(f" {Config.ASSISTANT_NAME} AI VOICE ASSISTANT - COMMAND LINE INTERFACE")
        print("="*60)
        print("Type your request below. Type 'exit' or 'quit' to close.")
        
        self.tts.speak("System online in command-line interface mode.", block=False)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    print(f"\n{Config.ASSISTANT_NAME}: Goodbye!")
                    self.tts.speak("Goodbye!", block=True)
                    break
                    
                # Process the query using brain
                response = await self.brain.process_query(user_input)
                print(f"\n{Config.ASSISTANT_NAME}: {response}")
                
                # Speak response in background
                self.tts.speak(response, block=False)
            except KeyboardInterrupt:
                print(f"\n{Config.ASSISTANT_NAME}: Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                logger.error("Error in CLI mode: %s", e)

    def run_gui_mode(self, host: str = None, port: int = None):
        """Launches the ChatGPT/Gemini style Visual Web GUI Assistant."""
        import webbrowser
        host = host or Config.GUI_HOST
        port = port or Config.GUI_PORT

        logger.info("Starting Jarvis Visual Web GUI server on http://%s:%d", host, port)
        print("="*60)
        print(f" {Config.ASSISTANT_NAME} VISUAL VOICE ASSISTANT (ChatGPT/Gemini Style)")
        print("="*60)
        print(f" Web GUI running at: http://{host}:{port}")
        print(" Opening application in your default browser...")
        print(" Press Ctrl+C in terminal to stop.")
        print("="*60)

        # Open web browser after server starts
        def open_browser():
            time.sleep(1.2)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=open_browser, daemon=True).start()

        from gui.app import start_gui_server
        start_gui_server(assistant_app=self, host=host, port=port)
