import pywhatkit
import webbrowser
import urllib.parse
from typing import Dict, Any, List
import logging

logger = logging.getLogger("assistant.search.youtube")

class YouTubeSearch:
    def __init__(self):
        pass

    def play_video(self, topic: str) -> Dict[str, Any]:
        """Uses pywhatkit to search and play a video on YouTube directly."""
        try:
            logger.info("Playing YouTube video for: %s", topic)
            # pywhatkit.playonyt automatically searches and opens the first video in a browser tab
            pywhatkit.playonyt(topic)
            return {"success": True, "message": f"Playing {topic} on YouTube."}
        except Exception as e:
            logger.error("Failed to play on YouTube using pywhatkit: %s", e)
            # Fallback to direct search URL
            return self.open_search_results(topic)

    def open_search_results(self, query: str) -> Dict[str, Any]:
        """Opens YouTube search results page directly in the default browser."""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            webbrowser.open(url)
            logger.info("Opened YouTube search results in browser for: %s", query)
            return {"success": True, "message": f"Opened YouTube search results for: {query}."}
        except Exception as e:
            logger.error("Failed to open YouTube search in browser: %s", e)
            return {"success": False, "message": f"Error opening YouTube: {str(e)}"}
