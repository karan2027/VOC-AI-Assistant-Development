import os
import sys
import asyncio
import logging
from flask import Flask, render_template, request, jsonify

# Add project root to sys.path if not present
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import Config
from assistant import VoiceAssistantApp

logger = logging.getLogger("assistant.gui")

def run_async_safe(coro):
    """Safely executes an async coroutine across Flask WSGI threads and existing event loops."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

def create_app(assistant_app: VoiceAssistantApp = None):
    """Factory function to create Flask GUI application."""
    if assistant_app is None:
        assistant_app = VoiceAssistantApp()

    template_dir = os.path.join(project_root, "gui", "templates")
    static_dir = os.path.join(project_root, "gui", "static")

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/chat", methods=["POST"])
    def chat_endpoint():
        try:
            data = request.get_json() or {}
            user_text = data.get("text", "").strip()
            if not user_text:
                return jsonify({"status": "error", "message": "Empty text"}), 400

            logger.info("GUI Chat Request: '%s'", user_text)

            # Check for exit commands
            exit_cmds = ["goodbye", "good bye", "bye", "exit", "terminate", "shutdown", "turn off", "stop assistant"]
            if any(cmd in user_text.lower() for cmd in exit_cmds):
                response_text = "Goodbye! Have a great day."
                assistant_app.tts.speak(response_text, block=False)
                return jsonify({"status": "success", "user_text": user_text, "response": response_text})

            # Process query via brain using thread-safe async executor
            response_text = run_async_safe(assistant_app.brain.process_query(user_text))

            # Mandatory speech synthesis output
            assistant_app.tts.speak(response_text, block=False)

            return jsonify({
                "status": "success",
                "user_text": user_text,
                "response": response_text
            })
        except Exception as e:
            logger.error("Error in /api/chat: %s", e)
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/listen", methods=["POST"])
    def listen_endpoint():
        try:
            logger.info("GUI Listen Request: listening to microphone...")
            
            # Listen to microphone input with fast 1.0s pause threshold
            user_text, success = assistant_app.stt.listen_and_transcribe(timeout=5.0, phrase_time_limit=15.0)

            if success and user_text:
                logger.info("Microphone Transcribed: '%s'", user_text)
                
                # Process query via brain
                response_text = run_async_safe(assistant_app.brain.process_query(user_text))

                # Mandatory speech synthesis output
                assistant_app.tts.speak(response_text, block=False)

                return jsonify({
                    "status": "success",
                    "user_text": user_text,
                    "response": response_text
                })
            else:
                return jsonify({
                    "status": "no_audio",
                    "user_text": None,
                    "response": None
                })
        except Exception as e:
            logger.error("Error in /api/listen: %s", e)
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/clear", methods=["POST"])
    def clear_endpoint():
        try:
            assistant_app.memory.clear_all()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/stop_speech", methods=["POST"])
    def stop_speech_endpoint():
        try:
            logger.info("GUI Request: stopping voice speech output...")
            assistant_app.tts.stop_speech()
            return jsonify({"status": "success", "message": "Voice output stopped."})
        except Exception as e:
            logger.error("Error in /api/stop_speech: %s", e)
            return jsonify({"status": "error", "message": str(e)}), 500

    return app

def start_gui_server(assistant_app: VoiceAssistantApp = None, host: str = "127.0.0.1", port: int = 5000):
    """Starts the Flask GUI web server."""
    app = create_app(assistant_app)
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    start_gui_server()
