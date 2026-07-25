import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Project Configuration Settings"""
    SECRET_KEY = os.getenv("SECRET_KEY", "syntecxhub-ai-assistant-secret-key")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL = "gemini-1.5-flash"
    PROJECT_NAME = "SYNTECXHUB AI Assistant"
    DEVELOPER = "Chhotelal Kushwaha"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
