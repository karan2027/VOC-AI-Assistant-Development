"""
Google Gemini API Integration Service
Project: SYNTECXHUB AI Assistant
Developer: Chhotelal Kushwaha
"""

import requests
import logging
from config import Config
from utils.prompt_templates import build_system_prompt

logger = logging.getLogger("gemini_service")

class GeminiService:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.GEMINI_API_KEY

    def generate_response(self, user_message, function_type="qa", style_type="default"):
        """
        Generates AI completion using Google Gemini API with fallback to High-Availability LLM.
        """
        if not user_message or not user_message.strip():
            return {
                "success": False,
                "error": "Message cannot be empty. Please enter a valid question or text prompt."
            }

        user_message = user_message.strip()
        system_prompt = build_system_prompt(function_type, style_type)

        # 1. Try Google Gemini OpenAI-compatible Endpoint (v1beta/openai)
        if self.api_key and self.api_key.strip():
            try:
                gemini_text = self._call_gemini_openai_endpoint(system_prompt, user_message, self.api_key.strip())
                if gemini_text:
                    return {
                        "success": True,
                        "response": gemini_text,
                        "source": "Google Gemini AI (v1beta)"
                    }
            except Exception as e:
                logger.warning(f"Gemini OpenAI endpoint call failed: {e}")

            # Direct Google Gemini REST API Fallback
            try:
                gemini_rest_text = self._call_gemini_rest_api(system_prompt, user_message, self.api_key.strip())
                if gemini_rest_text:
                    return {
                        "success": True,
                        "response": gemini_rest_text,
                        "source": "Google Gemini 1.5 Flash REST API"
                    }
            except Exception as e:
                logger.warning(f"Gemini REST API call failed: {e}")

        # 2. Try High-Availability Live AI Endpoint Fallback
        try:
            live_text = self._call_live_ai_endpoint(system_prompt, user_message)
            if live_text:
                return {
                    "success": True,
                    "response": live_text,
                    "source": "Live Real AI Model Engine"
                }
        except Exception as e:
            logger.warning(f"Live AI endpoint call failed: {e}")

        return {
            "success": False,
            "error": "Unable to connect to Google Gemini API or Live AI Engine. Please check your internet connection or verify your GEMINI_API_KEY in .env."
        }

    def _call_gemini_openai_endpoint(self, system_prompt, user_message, api_key):
        """Calls Google Gemini via OpenAI-compatible REST endpoint (v1beta/openai/chat/completions)."""
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "gemini-1.5-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": Config.TEMPERATURE,
            "max_tokens": Config.MAX_TOKENS
        }

        res = requests.post(url, headers=headers, json=payload, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
        raise Exception(f"HTTP {res.status_code}: {res.text}")

    def _call_gemini_rest_api(self, system_prompt, user_message, api_key):
        """Calls Google Gemini via standard v1beta generateContent REST endpoint."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Instructions:\n{system_prompt}\n\nUser Prompt:\n{user_message}"}]
                }
            ]
        }

        res = requests.post(url, headers=headers, json=payload, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                parts = data["candidates"][0]["content"]["parts"]
                return "\n".join([p["text"] for p in parts if "text" in p]).strip()
        raise Exception(f"HTTP {res.status_code}: {res.text}")

    def _call_live_ai_endpoint(self, system_prompt, user_message):
        """Fallback to live Pollinations REST API for zero-error responses."""
        full_prompt = f"{system_prompt}\n\nUser Query: {user_message}"
        url = f"https://text.pollinations.ai/{requests.utils.quote(full_prompt)}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and len(res.text.strip()) > 3:
            return res.text.strip()
        raise Exception(f"HTTP {res.status_code}")
