import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("assistant.search.internet")

class InternetSearch:
    def __init__(self):
        pass

    def search_ddg(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Performs a search on DuckDuckGo and returns a list of results."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                logger.info("DuckDuckGo search successful for: %s", query)
                return [{"title": r.get("title"), "snippet": r.get("body"), "link": r.get("href")} for r in results]
        except Exception as e:
            logger.error("DuckDuckGo search failed: %s, attempting backup", e)
            return self._backup_search_ddg(query, max_results)

    def _backup_search_ddg(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Backup simple HTML scraping for DuckDuckGo if the API library fails."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for link in soup.find_all("a", class_="result__url")[:max_results]:
                parent = link.find_parent("div", class_="result")
                if parent:
                    title_elem = parent.find("a", class_="result__snippet")
                    snippet_elem = parent.find("a", class_="result__snippet")
                    title = title_elem.text.strip() if title_elem else "No Title"
                    snippet = snippet_elem.text.strip() if snippet_elem else "No Snippet"
                    href = link.get("href", "")
                    # Extract URL from DDG redirect format
                    if "duckduckgo.com/l/?kh=-1&uddg=" in href:
                        href = href.split("uddg=")[1].split("&")[0]
                        href = requests.utils.unquote(href)
                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "link": href
                    })
            return results
        except Exception as e:
            logger.error("Backup search failed: %s", e)
            return []

    def get_weather(self, location: str) -> Dict[str, Any]:
        """Gets weather information using DuckDuckGo search query."""
        query = f"weather in {location}"
        results = self.search_ddg(query, max_results=3)
        if not results:
            return {"success": False, "message": "Could not retrieve weather information."}
            
        summary = "\n".join([f"{r['title']}: {r['snippet']}" for r in results])
        return {
            "success": True,
            "location": location,
            "weather_summary": summary
        }

    def get_news(self, category: str = "general") -> List[Dict[str, Any]]:
        """Gets latest news headlines using DuckDuckGo search."""
        query = f"latest {category} news"
        results = self.search_ddg(query, max_results=5)
        return results
        
    def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """Gets approximate stock price using search."""
        query = f"{ticker} stock price history"
        results = self.search_ddg(query, max_results=2)
        if not results:
            return {"success": False, "message": "Could not retrieve stock info."}
        summary = "\n".join([f"{r['title']} - {r['snippet']}" for r in results])
        return {"success": True, "ticker": ticker, "summary": summary}
