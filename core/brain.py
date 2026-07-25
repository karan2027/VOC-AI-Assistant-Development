import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

from ai_agent.openai_client import OpenAIClient
from ai_agent.prompt_manager import PromptManager
from ai_agent.conversation import ConversationContext
from core.memory import ConversationMemory

from automation.apps import AppAutomation
from automation.browser import BrowserAutomation
from automation.system import SystemAutomation
from automation.files import FileAutomation
from automation.weather_news import WeatherNewsService

from search.wikipedia import WikipediaSearch
from search.internet import InternetSearch
from search.youtube import YouTubeSearch

from utils.helpers import (
    calculate_bmi,
    calculate_age,
    convert_units,
    convert_currency,
    evaluate_math_expression,
    ActiveTimers
)

logger = logging.getLogger("assistant.core.brain")

class AssistantBrain:
    def __init__(self, openai_client: OpenAIClient, memory: ConversationMemory, timer_callback=None):
        self.openai = openai_client
        self.memory = memory
        
        # Instantiate subsystems
        self.apps = AppAutomation()
        self.browser = BrowserAutomation()
        self.system = SystemAutomation()
        self.files = FileAutomation()
        self.weather_news = WeatherNewsService()
        
        self.wiki = WikipediaSearch()
        self.internet = InternetSearch()
        self.youtube = YouTubeSearch()
        
        self.timers = ActiveTimers(timer_callback or self._default_timer_callback)
        
        # Setup conversation context
        # We retrieve user name and assistant name from preferences
        self.assistant_name = self.memory.get_preference("assistant_name", "Assistant")
        self.user_name = self.memory.get_preference("user_name", "User")
        
        self.prompt_manager = PromptManager(self.assistant_name, self.user_name)
        self.chat_context = ConversationContext(max_history=10)
        
        # Load previous history from DB to seed conversation context
        self._load_history_from_db()
        
        # Setup OpenAI tools list
        self.tools_schema = self._build_tools_schema()

    def _default_timer_callback(self, message: str):
        logger.info("Timer Callback triggered: %s", message)

    def _load_history_from_db(self):
        history = self.memory.get_recent_history(limit=8)
        for msg in history:
            if msg["role"] == "user":
                self.chat_context.add_user_message(msg["message"])
            elif msg["role"] == "assistant":
                self.chat_context.add_assistant_message(msg["message"])

    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Returns JSON schema for OpenAI tool-calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "open_app",
                    "description": "Opens a Windows application by name (e.g. chrome, notepad, calculator, vs code).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {"type": "string", "description": "The name of the application to open."}
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "close_app",
                    "description": "Closes a Windows application by name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {"type": "string", "description": "The name of the application to close."}
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_website",
                    "description": "Opens a website in the default browser (e.g. YouTube, GitHub, LinkedIn, Amazon).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "site_name": {"type": "string", "description": "The name of the website or URL to open."}
                        },
                        "required": ["site_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_google",
                    "description": "Performs a Google search in the user's default browser.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_github",
                    "description": "Searches GitHub in the web browser.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The repository or code query."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_stackoverflow",
                    "description": "Searches StackOverflow in the browser.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The programming question to search."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "play_youtube",
                    "description": "Searches and plays a video on YouTube.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "The video topic or query."}
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "change_volume",
                    "description": "Increases, decreases, or mutes the system volume.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {"type": "string", "enum": ["up", "down", "mute", "unmute"]},
                            "amount": {"type": "integer", "description": "The percentage steps to adjust by. Default is 10."}
                        },
                        "required": ["direction"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "media_control",
                    "description": "Controls music/video playback (play, pause, next, previous).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["play", "pause", "next", "prev"]}
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description": "Takes a screenshot of the user's screen and saves it.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_status",
                    "description": "Gets CPU and memory usage, along with battery percentage.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_folder",
                    "description": "Creates a new folder or nested subfolders on the local file system (supports absolute paths like C:\\Users\\... or D:\\... or relative folder names).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Folder name or nested folder name."},
                            "parent_folder": {"type": "string", "description": "Parent directory (desktop, documents, downloads)."},
                            "path": {"type": "string", "description": "Full absolute path or target directory (e.g. C:\\Projects\\App or D:\\Work\\Folder)."}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Creates a new file of ANY type (.py, .java, .c, .cpp, .html, .css, .js, .json, .sql, .txt, .xlsx, .pptx, .csv, .docx) with optional code content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "File name with extension (e.g. script.py, Main.java, code.cpp, test.c, notes.txt, sheet.xlsx, demo.pptx)."},
                            "content": {"type": "string", "description": "Source code or text content to write inside the file."},
                            "parent_folder": {"type": "string", "description": "Parent directory (desktop, documents, downloads)."},
                            "path": {"type": "string", "description": "Target folder directory or full file path."}
                        },
                        "required": ["filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_multiple_folders",
                    "description": "Creates multiple folders at once on the system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "folder_names": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of folder names to create (e.g. ['Project1', 'Project2', 'Project3'])."
                            },
                            "parent_folder": {"type": "string", "description": "Parent directory (desktop, documents, downloads)."},
                            "path": {"type": "string", "description": "Target directory path."}
                        },
                        "required": ["folder_names"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_multiple_files",
                    "description": "Creates multiple files at once on the system with optional code content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_list": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "filename": {"type": "string", "description": "File name with extension."},
                                        "content": {"type": "string", "description": "Optional code or text content."}
                                    },
                                    "required": ["filename"]
                                },
                                "description": "List of file objects containing filename and optional content."
                            },
                            "parent_folder": {"type": "string", "description": "Parent directory."},
                            "path": {"type": "string", "description": "Target directory path."}
                        },
                        "required": ["file_list"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "Deletes a file or directory. Safety: requires confirmation first.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Name of the file/folder to delete."},
                            "parent_folder": {"type": "string", "description": "Parent directory."},
                            "confirmed": {"type": "boolean", "description": "Set to true only if the user explicitly confirmed they want to delete."}
                        },
                        "required": ["filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_note",
                    "description": "Saves a quick text note in the assistant's logs directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Note title."},
                            "content": {"type": "string", "description": "Note body."}
                        },
                        "required": ["title", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_note",
                    "description": "Reads a previously saved note.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Note title."}
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Gets real-time weather information for any city or location in the world.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City or place name (e.g. Srinagar, London, Delhi, Tokyo, New York)."}
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_tech_news",
                    "description": "Gets top technology news headlines.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_internet",
                    "description": "Searches the web for recent info, news, sports, weather, stock details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_wikipedia",
                    "description": "Looks up historical figures, scientific definitions, or concepts on Wikipedia.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The Wikipedia search term."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_bmi",
                    "description": "Calculates BMI using weight in kg and height in meters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "weight_kg": {"type": "number"},
                            "height_m": {"type": "number"}
                        },
                        "required": ["weight_kg", "height_m"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "convert_units",
                    "description": "Converts measurements between Celsius/Fahrenheit, km/miles, kg/lbs.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "number"},
                            "from_unit": {"type": "string"},
                            "to_unit": {"type": "string"}
                        },
                        "required": ["value", "from_unit", "to_unit"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "convert_currency",
                    "description": "Converts currency values offline (USD, EUR, GBP, INR, PKR, etc.).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number"},
                            "from_currency": {"type": "string"},
                            "to_currency": {"type": "string"}
                        },
                        "required": ["amount", "from_currency", "to_currency"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "remember_user_fact",
                    "description": "Saves a personal fact about the user (name, preferences, birthdays, likes) in database memory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fact": {"type": "string", "description": "The personal fact (e.g. 'User likes Python coding' or 'User name is Sarah')."}
                        },
                        "required": ["fact"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_alarm",
                    "description": "Sets an alarm for a specific time in 24h format HH:MM (e.g., '07:30', '18:45').",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_str": {"type": "string", "description": "Time in 24h HH:MM format."},
                            "label": {"type": "string", "description": "Optional label/purpose of alarm."}
                        },
                        "required": ["time_str"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "start_timer",
                    "description": "Starts a countdown timer in seconds.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seconds": {"type": "integer", "description": "Duration in seconds."},
                            "label": {"type": "string", "description": "Label for the timer."}
                        },
                        "required": ["seconds"]
                    }
                }
            }
        ]

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Executes the tool by name and returns a string confirmation message."""
        logger.info("Executing tool: %s with args: %s", name, args)
        try:
            if name == "open_app":
                res = self.apps.open_app(args["app_name"])
                return res["message"]
            elif name == "close_app":
                res = self.apps.close_app(args["app_name"])
                return res["message"]
            elif name == "open_website":
                res = self.browser.open_website(args["site_name"])
                return res["message"]
            elif name == "search_google":
                res = self.browser.search_google(args["query"])
                return res["message"]
            elif name == "search_github":
                res = self.browser.search_github(args["query"])
                return res["message"]
            elif name == "search_stackoverflow":
                res = self.browser.search_stackoverflow(args["query"])
                return res["message"]
            elif name == "play_youtube":
                res = self.youtube.play_video(args["topic"])
                return res["message"]
            elif name == "change_volume":
                res = self.system.change_volume(args["direction"], args.get("amount", 10))
                return res["message"]
            elif name == "media_control":
                res = self.system.media_control(args["action"])
                return res["message"]
            elif name == "take_screenshot":
                res = self.system.take_screenshot()
                return res["message"]
            elif name == "get_system_status":
                res = self.system.get_system_stats()
                if res.get("success"):
                    bat = res["battery"]
                    bat_str = f"Battery: {bat.get('percent')}% {'(charging)' if bat.get('plugged') else ''}" if bat else "Battery: unknown"
                    return f"System CPU usage is at {res['cpu_percent']}%, and Memory usage is at {res['memory_percent']}%. {bat_str}"
                return "Failed to read system status."
            elif name == "create_folder":
                res = self.files.create_folder(
                    name=args.get("name", ""),
                    parent_folder=args.get("parent_folder", "desktop"),
                    path=args.get("path", "")
                )
                return res["message"]
            elif name == "create_file":
                res = self.files.create_file(
                    filename=args.get("filename", ""),
                    content=args.get("content", ""),
                    parent_folder=args.get("parent_folder", "desktop"),
                    path=args.get("path", "")
                )
                return res["message"]
            elif name == "create_multiple_folders":
                res = self.files.create_multiple_folders(
                    folder_names=args.get("folder_names", []),
                    parent_folder=args.get("parent_folder", "desktop"),
                    path=args.get("path", "")
                )
                return res["message"]
            elif name == "create_multiple_files":
                res = self.files.create_multiple_files(
                    file_list=args.get("file_list", []),
                    parent_folder=args.get("parent_folder", "desktop"),
                    path=args.get("path", "")
                )
                return res["message"]
            elif name == "delete_file":
                res = self.files.delete_file(args["filename"], args.get("parent_folder", "desktop"), args.get("confirmed", False))
                return res["message"]
            elif name == "write_note":
                res = self.files.write_note(args["title"], args["content"])
                return res["message"]
            elif name == "read_note":
                res = self.files.read_note(args["title"])
                if res.get("success"):
                    return f"Note content: {res['content']}"
                return res["message"]
            elif name == "get_weather":
                loc = args.get("location", "Delhi")
                res = self.weather_news.get_weather(loc)
                return res["message"]
            elif name == "get_tech_news":
                res = self.weather_news.get_tech_news()
                return res["message"]
            elif name == "search_internet":
                res = self.internet.search_ddg(args["query"], max_results=3)
                if res:
                    summary = "; ".join([f"{r['title']}: {r['snippet']}" for r in res])
                    return f"Internet search results for '{args['query']}': {summary[:600]}..."
                return "No internet search results found."
            elif name == "search_wikipedia":
                res = self.wiki.get_summary(args["query"])
                if res.get("success"):
                    return f"Wikipedia details for '{res['title']}': {res['summary']}"
                return res.get("message", "No Wikipedia article found.")
            elif name == "calculate_bmi":
                res = calculate_bmi(args["weight_kg"], args["height_m"])
                if res.get("success"):
                    return f"BMI is {res['bmi']}. Category: {res['category']}."
                return res.get("error", "Error calculating BMI.")
            elif name == "convert_units":
                res = convert_units(args["value"], args["from_unit"], args["to_unit"])
                if res.get("success"):
                    return f"Conversion result: {args['value']} {args['from_unit']} is equals to {res['result']} {args['to_unit']}."
                return res.get("error", "Error converting units.")
            elif name == "convert_currency":
                res = convert_currency(args["amount"], args["from_currency"], args["to_currency"])
                if res.get("success"):
                    return f"Conversion result: {args['amount']} {args['from_currency']} is approximately {res['result']} {args['to_currency']}."
                return res.get("error", "Error converting currency.")
            elif name == "remember_user_fact":
                self.memory.add_fact(args["fact"])
                return f"I have saved that fact in memory: {args['fact']}"
            elif name == "set_alarm":
                alarm_id, err = await self.timers.set_alarm(args["time_str"], args.get("label", "Alarm"))
                if err:
                    return f"Failed to set alarm: {err}"
                return f"Alarm set for {args['time_str']}."
            elif name == "start_timer":
                await self.timers.start_timer(args["seconds"], args.get("label", "Timer"))
                return f"Timer started for {args['seconds']} seconds."
            else:
                return "Unknown tool name."
        except Exception as e:
            logger.error("Tool execution failed: %s", e)
            return f"Error executing tool: {str(e)}"

    def _check_offline_heuristics(self, query: str) -> Optional[str]:
        """Handles basic system commands offline when OpenAI is unavailable or for instant response."""
        q = query.lower().strip()
        
        # PDF & Document Reader Heuristic (e.g. "read pdf file report.pdf", "read document notes.txt", "read file resume.pdf")
        match = re.search(r"(?:read|parse|summarize)\s+(?:pdf|document|file)\s+(?:named\s+)?([a-zA-Z0-9\._\-\\\/]+)", q)
        if match and not q.startswith("read note"):
            doc_name = match.group(1).strip()
            res = self.files.read_document_file(doc_name)
            return res["message"]
        match = re.search(r"(?:create|make)\s+(?:multiple\s+)?folders\s+(.+?)(?:\s+(?:in|inside|on|at)\s+(.+))?$", q)
        if match:
            names_raw = match.group(1).strip()
            loc = match.group(2).strip() if match.group(2) else "desktop"
            names = [n.strip() for n in re.split(r'[,&]|\band\b', names_raw) if n.strip()]
            if names:
                res = self.files.create_multiple_folders(folder_names=names, path=loc)
                return res["message"]

        # Create Folder Heuristic (e.g. "create folder Projects on Desktop", "create a folder on this path D:\... with folder name Karan")
        folder_cmd = self._parse_folder_command(query)
        if folder_cmd:
            res = self.files.create_folder(name=folder_cmd["name"], path=folder_cmd["path"])
            return res["message"]

        # Create File Heuristic (e.g. "create file main.py on Desktop", "create a file on this path D:\... with file name main.py")
        file_cmd = self._parse_file_command(query)
        if file_cmd:
            res = self.files.create_file(filename=file_cmd["filename"], path=file_cmd["path"], content=file_cmd.get("content", ""))
            return res["message"]

        # Open website (e.g. "open website youtube", "open chat gpt", "open chatgpt", "open gemini", "open google")
        match = re.search(r"(?:open\s+website|open|launch)\s+(youtube|google|github|linkedin|instagram|facebook|twitter|chatgpt|chat\s+gpt|claude|gemini|wikipedia|amazon|netflix|gmail|google\s+drive)", q)
        if match:
            site = match.group(1).strip()
            res = self.browser.open_website(site)
            return res["message"]

        # Open Application
        match = re.match(r"(?:open|launch)\s+([a-zA-Z0-9\s]+)", q)
        if match:
            app_name = match.group(1).strip()
            # If it's a website keyword, skip apps
            web_keywords = ["youtube", "google", "github", "linkedin", "instagram", "facebook", "twitter", "chatgpt", "chat gpt", "claude", "gemini", "wikipedia", "amazon", "netflix", "gmail", "google drive"]
            if app_name not in web_keywords:
                res = self.apps.open_app(app_name)
                return res["message"]

        # Close Application
        match = re.match(r"(?:close|exit|terminate)\s+([a-zA-Z0-9\s]+)", q)
        if match:
            app_name = match.group(1).strip()
            res = self.apps.close_app(app_name)
            return res["message"]

        # Open website
        match = re.match(r"(?:open website|open)\s+(youtube|google|github|linkedin|instagram|facebook|twitter|chatgpt|claude|gemini|wikipedia|amazon|netflix|gmail|google drive)", q)
        if match:
            site = match.group(1).strip()
            res = self.browser.open_website(site)
            return res["message"]

        # Search Google
        match = re.match(r"(?:search google for|google search for|search google|google)\s+(.+)", q)
        if match:
            search_query = match.group(1).strip()
            res = self.browser.search_google(search_query)
            return res["message"]

        # Volume control
        if "volume up" in q or "increase volume" in q:
            res = self.system.change_volume("up", 10)
            return res["message"]
        elif "volume down" in q or "decrease volume" in q:
            res = self.system.change_volume("down", 10)
            return res["message"]
        elif "mute volume" in q or "unmute volume" in q or "toggle mute" in q:
            res = self.system.change_volume("mute")
            return res["message"]

        # Take screenshot
        if "screenshot" in q or "take a screenshot" in q or "capture screen" in q:
            res = self.system.take_screenshot()
            return res["message"]

        # Basic Time & Date
        if q in ["what time is it", "tell me the time", "current time", "what is the time"]:
            td = self.system.get_time_date()
            return f"The current time is {td['time']}."
        elif q in ["what day is today", "what is today's date", "tell me the date", "date today"]:
            td = self.system.get_time_date()
            return f"Today is {td['date']}."

        # Simple math evaluation
        if q.startswith("calculate ") or q.startswith("what is "):
            expr_candidate = q.replace("calculate", "").replace("what is", "").strip()
            res = evaluate_math_expression(expr_candidate)
            if res.get("success"):
                return f"The result is {res['result']}."

        return None

    def _parse_folder_command(self, query: str) -> Optional[Dict[str, str]]:
        """Smartly parses folder creation queries including explicit paths with spaces, drive letters, and folder names."""
        q_strip = query.strip()
        q_lower = q_strip.lower()

        if not ("create" in q_lower or "make" in q_lower) or "folder" not in q_lower:
            return None

        if "folders" in q_lower or "multiple folders" in q_lower:
            return None

        name = None
        path = ""

        # 1. Look for explicit name phrases: "with folder name X", "with name X", "folder name X", "named X"
        match_name = re.search(r"(?:with\s+)?(?:folder\s+)?name\s+[\"']?([a-zA-Z0-9\._\-]+)[\"']?", q_strip, re.I)
        if not match_name:
            match_name = re.search(r"\bnamed\s+[\"']?([a-zA-Z0-9\._\-]+)[\"']?", q_strip, re.I)

        if match_name:
            cand = match_name.group(1).strip()
            if cand.lower() not in ["on", "in", "at", "with", "this", "path", "folder", "file"]:
                name = cand

        # 2. Look for drive letter path like "D:\SEMESTER\..." or "C:/..." anywhere in the query
        match_drive = re.search(r"([a-zA-Z]:\\[^\n\r]+?|[a-zA-Z]:/[^\n\r]+?)(?=\s+(?:with|and|folder|name)|$)", q_strip, re.I)
        if match_drive:
            path = match_drive.group(1).strip()

        # 3. If no drive letter, look for explicit path phrase
        if not path:
            match_path_phrase = re.search(r"(?:on\s+this\s+path|on\s+path|in\s+path|at\s+path)\s+(.+?)(?=\s+(?:with|and|folder|name)|$)", q_strip, re.I)
            if match_path_phrase:
                path = match_path_phrase.group(1).strip()

        if name:
            if not path:
                match_loc = re.search(r"(?:in|inside|on|at)\s+(?!this\s+path|path)(.+?)(?:\s+with|\s+and|$)", q_strip, re.I)
                if match_loc:
                    path = match_loc.group(1).strip()
                else:
                    path = "desktop"
            return {"name": name, "path": path}

        # 4. Fallback for positional commands: "create folder Projects on Desktop", "make folder Karan on D:\output"
        match_simple = re.search(r"(?:create|make)\s+(?:a\s+)?folder\s+(?:named\s+)?([a-zA-Z0-9\._\-]+)(?:\s+(?:in|inside|on|at)\s+(.+))?", q_strip, re.I)
        if match_simple:
            cand_name = match_simple.group(1).strip()
            cand_path = match_simple.group(2).strip() if match_simple.group(2) else "desktop"

            stop_words = ["on", "in", "at", "with", "this", "path", "a", "the", "for", "to", "folder", "file"]
            if cand_name.lower() in stop_words:
                return None
            return {"name": cand_name, "path": cand_path}

        return None

    def _parse_file_command(self, query: str) -> Optional[Dict[str, str]]:
        """Smartly parses file creation queries including explicit paths with spaces, drive letters, and filenames."""
        q_strip = query.strip()
        q_lower = q_strip.lower()

        if not ("create" in q_lower or "make" in q_lower) or "file" not in q_lower:
            return None

        if "files" in q_lower or "multiple files" in q_lower:
            return None

        name = None
        path = ""
        content = ""

        # Check extension / language hint
        ext = ".py"
        if "python" in q_lower or ".py" in q_lower:
            ext = ".py"
        elif "java" in q_lower or ".java" in q_lower:
            ext = ".java"
        elif "c++" in q_lower or "cpp" in q_lower or ".cpp" in q_lower:
            ext = ".cpp"
        elif "c file" in q_lower or ".c" in q_lower:
            ext = ".c"
        elif "html" in q_lower or ".html" in q_lower:
            ext = ".html"
        elif "css" in q_lower or ".css" in q_lower:
            ext = ".css"
        elif "js" in q_lower or "javascript" in q_lower or ".js" in q_lower:
            ext = ".js"
        elif "text" in q_lower or "txt" in q_lower or ".txt" in q_lower:
            ext = ".txt"

        # 1. Look for explicit filename extension (e.g. main.py, script.py, App.java)
        match_ext_filename = re.search(r"([a-zA-Z0-9_\-]+\.(?:py|java|cpp|c|html|css|js|txt|json|sql|csv|docx|pptx|xlsx))", q_strip, re.I)
        if match_ext_filename:
            name = match_ext_filename.group(1).strip()

        # 2. Look for "for <topic>" phrase (e.g. "for snack game", "for snake game", "for calculator")
        if not name:
            match_for = re.search(r"(?:file\s+)?for\s+([a-zA-Z0-9\s_\-]+?)(?=\s+(?:on|in|at|with|path)|$)", q_strip, re.I)
            if match_for:
                topic = match_for.group(1).strip().replace(" ", "_")
                if topic.lower() not in ["on", "in", "at", "this", "path"]:
                    name = f"{topic}{ext}"

        # 3. Look for explicit name phrases: "with file name X", "with name X", "file name X", "named X"
        if not name:
            match_name = re.search(r"(?:with\s+)?(?:file\s+)?name\s+[\"']?([a-zA-Z0-9\._\-]+)[\"']?", q_strip, re.I)
            if not match_name:
                match_name = re.search(r"\bnamed\s+[\"']?([a-zA-Z0-9\._\-]+)[\"']?", q_strip, re.I)

            if match_name:
                cand = match_name.group(1).strip()
                if cand.lower() not in ["on", "in", "at", "with", "this", "path", "folder", "file"]:
                    name = cand if "." in cand else f"{cand}{ext}"

        # 4. Look for drive letter path
        match_drive = re.search(r"([a-zA-Z]:\\[^\n\r]+?|[a-zA-Z]:/[^\n\r]+?)(?=\s+(?:with|and|file|name)|$)", q_strip, re.I)
        if match_drive:
            path = match_drive.group(1).strip()

        # 5. If no drive letter, look for explicit path phrase
        if not path:
            match_path_phrase = re.search(r"(?:on\s+this\s+path|on\s+path|in\s+path|at\s+path)\s+(.+?)(?=\s+(?:with|and|file|name)|$)", q_strip, re.I)
            if match_path_phrase:
                path = match_path_phrase.group(1).strip()

        if name:
            if not path:
                match_loc = re.search(r"(?:in|inside|on|at)\s+(?!this\s+path|path)(.+?)(?:\s+with|\s+and|$)", q_strip, re.I)
                if match_loc:
                    path = match_loc.group(1).strip()
                else:
                    path = "desktop"

            # Generate Snake/Snack game code if topic is snake/snack game
            if "snack" in name.lower() or "snake" in name.lower():
                content = (
                    "# Python Snake / Snack Game\n"
                    "import turtle\n"
                    "import time\n"
                    "import random\n\n"
                    "delay = 0.1\n"
                    "score = 0\n"
                    "high_score = 0\n\n"
                    "# Set up screen\n"
                    "wn = turtle.Screen()\n"
                    "wn.title('Snack Game by Assistant of Karan')\n"
                    "wn.bgcolor('black')\n"
                    "wn.setup(width=600, height=600)\n"
                    "wn.tracer(0)\n\n"
                    "# Snake head\n"
                    "head = turtle.Turtle()\n"
                    "head.speed(0)\n"
                    "head.shape('square')\n"
                    "head.color('green')\n"
                    "head.penup()\n"
                    "head.goto(0, 0)\n"
                    "head.direction = 'stop'\n\n"
                    "print('Snake/Snack Game initialized! Run python " + name + " to play.')\n"
                )
            return {"filename": name, "path": path, "content": content}

        # 6. Fallback for positional commands: "create file main.py on Desktop"
        match_simple = re.search(r"(?:create|make)\s+(?:a\s+)?(?:[a-zA-Z0-9]+\s+)?file\s+(?:named\s+)?([a-zA-Z0-9\._\-]+)(?:\s+(?:in|inside|on|at)\s+(.+))?", q_strip, re.I)
        if match_simple:
            cand_name = match_simple.group(1).strip()
            cand_path = match_simple.group(2).strip() if match_simple.group(2) else "desktop"

            stop_words = ["on", "in", "at", "with", "this", "path", "a", "the", "for", "to", "folder", "file"]
            if cand_name.lower() in stop_words:
                return None
            return {"filename": cand_name, "path": cand_path, "content": content}

        return None

    async def process_query(self, user_query: str) -> str:
        """Processes the user voice query and returns the assistant spoken response."""
        logger.info("Processing user query: '%s'", user_query)
        self.memory.save_message("user", user_query)
        self.chat_context.add_user_message(user_query)
        
        # 1. First check offline commands (super fast, works without API keys)
        offline_response = self._check_offline_heuristics(user_query)
        if offline_response:
            logger.info("Offline heuristics matched.")
            self.memory.save_message("assistant", offline_response)
            self.chat_context.add_assistant_message(offline_response)
            return offline_response

        # 2. Query GPT with tools enabled
        if not self.openai.is_available():
            err_msg = "I am sorry, my artificial intelligence core is offline since the API key is not configured. I can only perform local system controls right now."
            self.memory.save_message("assistant", err_msg)
            self.chat_context.add_assistant_message(err_msg)
            return err_msg

        # Retrieve user facts for dynamic prompt inclusion
        facts = self.memory.get_all_facts()
        system_prompt = self.prompt_manager.build_system_prompt(facts)
        
        messages = self.chat_context.get_messages(system_prompt)
        
        # Execute chat completion
        response_msg = self.openai.get_chat_response(
            messages=messages,
            model="gpt-4o",
            tools=self.tools_schema
        )
        
        # If tool-enabled completion failed or returned None, retry standard completion without tools
        if not response_msg:
            logger.info("Tool-enabled chat request failed. Retrying without tools...")
            response_msg = self.openai.get_chat_response(
                messages=messages,
                model="gpt-4o"
            )
            
        if not response_msg:
            err_msg = "I'm having trouble connecting to my brain server. Please check your internet connection."
            return err_msg

        # Handle tool calls
        if hasattr(response_msg, "tool_calls") and response_msg.tool_calls:
            tool_calls = response_msg.tool_calls
            logger.info("GPT generated %d tool calls.", len(tool_calls))
            
            # Create an ephemeral turn message sequence for tool resolution without corrupting persistent chat context
            ephemeral_messages = list(messages)
            
            # Format assistant message object as dict for OpenAI compatibility
            assistant_tool_msg = {
                "role": "assistant",
                "content": response_msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            }
            ephemeral_messages.append(assistant_tool_msg)
            
            last_tool_res = ""
            for tool_call in tool_calls:
                t_name = tool_call.function.name
                try:
                    t_args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                except Exception:
                    t_args = {}
                
                # Execute the tool
                tool_res = await self.execute_tool(t_name, t_args)
                last_tool_res = str(tool_res)
                
                # Append tool result to ephemeral messages
                ephemeral_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": t_name or "tool_call",
                    "content": str(tool_res)
                })
                
            # Request final summary/answer from model after adding tool outputs
            try:
                final_response = self.openai.get_chat_response(messages=ephemeral_messages, model="gpt-4o")
                if final_response and hasattr(final_response, "content") and final_response.content:
                    ans_text = str(final_response.content).strip()
                else:
                    ans_text = last_tool_res or "I have completed the requested system action."
            except Exception:
                ans_text = last_tool_res or "I have completed the requested system action."
        else:
            ans_text = response_msg.content if hasattr(response_msg, "content") else str(response_msg)

        # Save clean text to DB and conversation memory cache
        if not ans_text or not str(ans_text).strip():
            ans_text = "I have completed your request."

        ans_text = str(ans_text).strip()
        
        self.memory.save_message("assistant", ans_text)
        self.chat_context.add_assistant_message(ans_text)
        
        return ans_text
