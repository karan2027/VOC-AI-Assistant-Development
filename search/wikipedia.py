import wikipediaapi
from typing import Dict, Any
import logging

logger = logging.getLogger("assistant.search.wikipedia")

class WikipediaSearch:
    def __init__(self, language: str = "en", user_agent: str = "AIPersonalVoiceAssistant/1.0 (evaluator@university.edu)"):
        # wikipedia-api requires a specific User-Agent as per Wikipedia Policy
        self.wiki = wikipediaapi.Wikipedia(
            user_agent=user_agent,
            language=language
        )

    def get_summary(self, query: str, sentences_limit: int = 3) -> Dict[str, Any]:
        """Searches Wikipedia for a query and returns a summary."""
        try:
            page = self.wiki.page(query)
            if not page.exists():
                logger.info("Wikipedia page not found for query: %s", query)
                return {"success": False, "message": "Wikipedia page does not exist."}

            summary = page.summary
            # Split sentences and limit
            sentences = summary.split(". ")
            short_summary = ". ".join(sentences[:sentences_limit])
            if len(sentences) > sentences_limit:
                short_summary += "."

            logger.info("Wikipedia match found for query: %s", query)
            return {
                "success": True,
                "title": page.title,
                "summary": short_summary,
                "url": page.fullurl
            }
        except Exception as e:
            logger.error("Wikipedia search failed: %s", e)
            return {"success": False, "message": f"Error searching Wikipedia: {str(e)}"}
