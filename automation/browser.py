import webbrowser
import urllib.parse
from typing import Dict, Any
import logging

logger = logging.getLogger("assistant.automation.browser")

WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "linkedin": "https://www.linkedin.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://x.com",
    "chatgpt": "https://chatgpt.com",
    "chat gpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
    "gemini": "https://gemini.google.com",
    "wikipedia": "https://www.wikipedia.org",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "gmail": "https://mail.google.com",
    "google drive": "https://drive.google.com"
}

class BrowserAutomation:
    def __init__(self):
        pass

    def open_website(self, site_name: str) -> Dict[str, Any]:
        """Opens a mapped website in the default web browser."""
        name = site_name.lower().strip()
        url = None
        
        # Check mapping
        for key, web_url in WEBSITES.items():
            if key in name:
                url = web_url
                break
                
        if not url:
            # If not in mapping, assume it's a domain name (like "example.com")
            if "." in name:
                url = f"https://{name}" if not name.startswith(("http://", "https://")) else name
            else:
                # If no dot, search Google instead
                return self.search_google(site_name)

        try:
            logger.info("Opening URL: %s", url)
            webbrowser.open(url)
            return {"success": True, "message": f"Opening {site_name} in your browser."}
        except Exception as e:
            logger.error("Failed to open website %s: %s", site_name, e)
            return {"success": False, "message": f"Could not open {site_name}. Error: {str(e)}"}

    def search_google(self, query: str) -> Dict[str, Any]:
        """Performs a Google search in the default web browser."""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            logger.info("Searching Google for: %s", query)
            webbrowser.open(url)
            return {"success": True, "message": f"Searching Google for: {query}."}
        except Exception as e:
            logger.error("Google search failed: %s", e)
            return {"success": False, "message": f"Failed to search Google. Error: {str(e)}"}

    def search_github(self, query: str) -> Dict[str, Any]:
        """Performs a GitHub search in the default web browser."""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://github.com/search?q={encoded_query}"
            logger.info("Searching GitHub for: %s", query)
            webbrowser.open(url)
            return {"success": True, "message": f"Searching GitHub for: {query}."}
        except Exception as e:
            logger.error("GitHub search failed: %s", e)
            return {"success": False, "message": f"Failed to search GitHub. Error: {str(e)}"}

    def search_stackoverflow(self, query: str) -> Dict[str, Any]:
        """Performs a StackOverflow search in the default web browser."""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://stackoverflow.com/search?q={encoded_query}"
            logger.info("Searching StackOverflow for: %s", query)
            webbrowser.open(url)
            return {"success": True, "message": f"Searching StackOverflow for: {query}."}
        except Exception as e:
            logger.error("StackOverflow search failed: %s", e)
            return {"success": False, "message": f"Failed to search StackOverflow. Error: {str(e)}"}
