import sys
import argparse
import asyncio
import logging
from config import Config
from assistant import VoiceAssistantApp

# LiveKit Imports (wrapped in try/except to prevent failure if user only wants offline/local mode without livekit installed)
try:
    from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
    from livekit.agents.voice_assistant import VoiceAssistant
    from livekit.plugins import openai, silero
    HAS_LIVEKIT = True
except ImportError:
    HAS_LIVEKIT = False

# LiveKit Function Context integration (if LiveKit mode is selected)
if HAS_LIVEKIT:
    class LiveKitAssistantFunctions(llm.FunctionContext):
        def __init__(self, assistant_app: VoiceAssistantApp):
            super().__init__()
            self.app = assistant_app

        @llm.ai_callable(description="Opens a Windows application by name (e.g. Chrome, Notepad, Calculator, VS Code)")
        def open_application(self, app_name: str) -> str:
            res = self.app.brain.apps.open_app(app_name)
            return res["message"]

        @llm.ai_callable(description="Closes a Windows application by name")
        def close_application(self, app_name: str) -> str:
            res = self.app.brain.apps.close_app(app_name)
            return res["message"]

        @llm.ai_callable(description="Opens a website in the default browser")
        def open_website(self, site_name: str) -> str:
            res = self.app.brain.browser.open_website(site_name)
            return res["message"]

        @llm.ai_callable(description="Performs a Google search in the browser")
        def search_google(self, query: str) -> str:
            res = self.app.brain.browser.search_google(query)
            return res["message"]

        @llm.ai_callable(description="Performs a GitHub search in the browser")
        def search_github(self, query: str) -> str:
            res = self.app.brain.browser.search_github(query)
            return res["message"]

        @llm.ai_callable(description="Performs a StackOverflow search in the browser")
        def search_stackoverflow(self, query: str) -> str:
            res = self.app.brain.browser.search_stackoverflow(query)
            return res["message"]

        @llm.ai_callable(description="Plays a video on YouTube")
        def play_youtube_video(self, topic: str) -> str:
            res = self.app.brain.youtube.play_video(topic)
            return res["message"]

        @llm.ai_callable(description="Changes the operating system volume (direction: up, down, mute, unmute)")
        def change_volume(self, direction: str, amount: int = 10) -> str:
            res = self.app.brain.system.change_volume(direction, amount)
            return res["message"]

        @llm.ai_callable(description="Takes a screenshot of the user's screen")
        def take_screenshot(self) -> str:
            res = self.app.brain.system.take_screenshot()
            return res["message"]

        @llm.ai_callable(description="Saves a personal fact about the user in the database")
        def remember_user_fact(self, fact: str) -> str:
            self.app.brain.memory.add_fact(fact)
            return f"I have saved that fact in memory: {fact}"

        @llm.ai_callable(description="Creates a new folder on the local file system")
        def create_folder(self, name: str, parent_folder: str = "desktop") -> str:
            res = self.app.brain.files.create_folder(name, parent_folder)
            return res["message"]

        @llm.ai_callable(description="Creates a file on the local file system with content")
        def create_file(self, filename: str, content: str = "", parent_folder: str = "desktop") -> str:
            res = self.app.brain.files.create_file(filename, content, parent_folder)
            return res["message"]

        @llm.ai_callable(description="Deletes a file or folder from the system (safety: requires confirmation)")
        def delete_file(self, filename: str, parent_folder: str = "desktop", confirmed: bool = False) -> str:
            res = self.app.brain.files.delete_file(filename, parent_folder, confirmed)
            return res["message"]

        @llm.ai_callable(description="Saves a quick text note in the notes folder")
        def write_note(self, title: str, content: str) -> str:
            res = self.app.brain.files.write_note(title, content)
            return res["message"]

        @llm.ai_callable(description="Reads a saved note")
        def read_note(self, title: str) -> str:
            res = self.app.brain.files.read_note(title)
            if res.get("success"):
                return f"Note content: {res['content']}"
            return res["message"]

        @llm.ai_callable(description="Searches the web for recent info")
        def search_internet(self, query: str) -> str:
            res = self.app.brain.internet.search_ddg(query, max_results=2)
            if res:
                return "; ".join([f"{r['title']}: {r['snippet']}" for r in res])
            return "No web results found."

        @llm.ai_callable(description="Searches Wikipedia for concepts or entities")
        def search_wikipedia(self, query: str) -> str:
            res = self.app.brain.wiki.get_summary(query)
            if res.get("success"):
                return res["summary"]
            return res.get("message", "No article found.")

        @llm.ai_callable(description="Gets CPU, memory, and battery statistics")
        def get_system_status(self) -> str:
            res = self.app.brain.system.get_system_stats()
            if res.get("success"):
                bat = res["battery"]
                bat_str = f"Battery: {bat.get('percent')}% {'(charging)' if bat.get('plugged') else ''}" if bat else "Battery: unknown"
                return f"CPU: {res['cpu_percent']}%, Memory: {res['memory_percent']}%. {bat_str}"
            return "Failed to fetch stats."

    async def livekit_entrypoint(ctx: JobContext):
        """Entry point for LiveKit agents connecting to room events."""
        logger = logging.getLogger("livekit-worker")
        logger.info("Initializing LiveKit voice agent session...")
        
        # Instantiate assistant resources
        app = VoiceAssistantApp()
        
        # Create LiveKit chat context
        initial_ctx = llm.ChatContext().append(
            role="system",
            text=(
                f"You are {app.assistant_name}, a friendly AI personal voice assistant.\n"
                f"Your interface with {app.user_name} is voice.\n"
                "Keep responses concise, natural, and friendly. Avoid code blocks, markdown asterisks, or complex symbols."
            ),
        )
        
        # Connect to room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info("Connected to room: %s", ctx.room.name)
        
        # Map LiveKit calling to our automation brain
        fnc_ctx = LiveKitAssistantFunctions(app)
        
        # Initialize assistant
        assistant = VoiceAssistant(
            vad=silero.VAD.load(),
            stt=openai.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            chat_ctx=initial_ctx,
            fnc_ctx=fnc_ctx,
        )
        
        assistant.start(ctx.room)
        logger.info("LiveKit VoiceAssistant started in room.")
        
        await asyncio.sleep(1)
        await assistant.say(f"Hello, I am {app.assistant_name}. How can I assist you today?", allow_interruptions=True)

def main():
    parser = argparse.ArgumentParser(description="AI Personal Voice Assistant")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--gui", action="store_true", help="Run the Visual ChatGPT/Gemini style Web GUI Assistant (Default)")
    group.add_argument("--terminal", action="store_true", help="Run continuous background voice mode in terminal")
    group.add_argument("--cli", action="store_true", help="Run the assistant in text CLI mode")
    group.add_argument("--livekit", action="store_true", help="Run the assistant as a LiveKit agent worker connection")
    group.add_argument("--direct", action="store_true", help="Run the assistant locally in direct listening mode")
    
    args = parser.parse_args()
    
    # Initialize Application
    app = VoiceAssistantApp()
    
    if args.cli:
        # Run text CLI mode
        asyncio.run(app.run_cli_mode())
    elif args.direct or args.terminal:
        # Run local direct listening mode in console
        app.run_direct_mode()
    elif args.livekit:
        # Run LiveKit agent worker
        if not HAS_LIVEKIT:
            print("Error: LiveKit SDK dependencies are missing. Run: pip install livekit-agents livekit-plugins-openai livekit-plugins-silero")
            sys.exit(1)
            
        print("Starting LiveKit agent worker...")
        cli.run_app(WorkerOptions(entrypoint_fnc=livekit_entrypoint))
    else:
        # Default: Visual ChatGPT/Gemini Style Web GUI Mode
        app.run_gui_mode()

if __name__ == "__main__":
    main()
