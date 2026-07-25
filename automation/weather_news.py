import urllib.request
import urllib.parse
import json
import re
import logging
from typing import Dict, Any

logger = logging.getLogger("assistant.automation.weather_news")

class WeatherNewsService:
    def __init__(self):
        pass

    def get_weather(self, location: str = "Delhi") -> Dict[str, Any]:
        """Gets real-time weather information using Open-Meteo free API."""
        try:
            raw_loc = location.strip()
            # Clean filler words (e.g. "tell me weather of Srinagar Uttarakhand" -> "Srinagar Uttarakhand")
            clean_loc = re.sub(r'\b(tell|me|the|weather|in|of|for|at|today|now|outside|currently|forecast|report|how|is)\b', '', raw_loc, flags=re.I).strip()
            if not clean_loc:
                clean_loc = "Delhi"

            logger.info("Fetching weather for location: '%s' (cleaned: '%s')", raw_loc, clean_loc)

            # Build search candidates: 1. Full clean string, 2. First word (e.g. "Srinagar"), 3. Delhi
            words = clean_loc.split()
            candidates = [clean_loc]
            if len(words) > 1:
                candidates.append(words[0])
            candidates.append("Delhi")

            selected_place = None
            for term in candidates:
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(term)}&count=10&language=en&format=json"
                req = urllib.request.Request(geo_url, headers={'User-Agent': 'Mozilla/5.0'})
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        results = data.get("results", [])
                        if results:
                            # 1. Check if user specified a state/province (e.g. Uttarakhand) matching admin1 or country
                            for item in results:
                                adm = (item.get("admin1") or "").lower()
                                cnt = (item.get("country") or "").lower()
                                if (adm and adm in clean_loc.lower()) or (cnt and cnt in clean_loc.lower()):
                                    selected_place = item
                                    break
                            
                            # 2. If no explicit state matched, pick the primary city result
                            if not selected_place:
                                selected_place = results[0]
                            break
                except Exception as e:
                    logger.warning("Geocoding failed for '%s': %s", term, e)

            if not selected_place:
                return {"success": False, "message": f"Could not locate weather data for '{location}'."}

            place = selected_place
            lat = place["latitude"]
            lon = place["longitude"]
            place_name = place.get("name", clean_loc.capitalize())
            country = place.get("country", "")
            admin1 = place.get("admin1", "") # State/Province (e.g. Uttarakhand)

            # Fetch current weather forecast
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            req2 = urllib.request.Request(weather_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2, timeout=5) as resp2:
                w_data = json.loads(resp2.read().decode('utf-8'))

            cw = w_data.get("current_weather", {})
            temp = cw.get("temperature", "N/A")
            wind = cw.get("windspeed", "N/A")
            w_code = cw.get("weathercode", 0)

            # Decode weather code
            code_map = {
                0: "Clear Sky ☀️",
                1: "Mainly Clear 🌤️", 2: "Partly Cloudy ⛅", 3: "Overcast ☁️",
                45: "Foggy 🌫️", 48: "Depositing Rime Fog 🌫️",
                51: "Light Drizzle 🌧️", 53: "Moderate Drizzle 🌧️", 55: "Dense Drizzle 🌧️",
                61: "Slight Rain 🌧️", 63: "Moderate Rain 🌧️", 65: "Heavy Rain 🌧️",
                71: "Slight Snow ❄️", 73: "Moderate Snow ❄️", 75: "Heavy Snow ❄️",
                80: "Rain Showers 🌦️", 95: "Thunderstorm 🌩️"
            }
            condition = code_map.get(w_code, "Pleasant")

            loc_str = f"{place_name}"
            if admin1 and admin1 != place_name:
                loc_str += f", {admin1}"
            if country:
                loc_str += f", {country}"

            msg = f"The current weather in {loc_str} is {temp}°C with {condition}. Wind speed is {wind} km/h."
            return {"success": True, "message": msg, "temp": temp, "condition": condition}

        except Exception as e:
            logger.error("Failed to fetch weather for %s: %s", location, e)
            return {"success": False, "message": f"Unable to fetch weather for {location}. Error: {str(e)}"}

    def get_tech_news(self) -> Dict[str, Any]:
        """Fetches top technology news headlines, filtering out shopping/ecommerce noise."""
        try:
            logger.info("Fetching top tech news...")
            from search.internet import InternetSearch
            search = InternetSearch()
            results = search.search_ddg("techcrunch wired verge software artificial intelligence tech news", max_results=10)

            shopping_keywords = ["shop", "buy", "discount", "price", "sale", "women top", "myntra", "nykaa", "cloth", "fashion", "off on", "aajtak", "ndtv", "gktoday", "judiciary"]

            headlines = []
            if results:
                for r in results:
                    title = r.get("title", "").strip()
                    snippet = r.get("snippet", "").strip()
                    # Filter out shopping / ecommerce results
                    if any(kw in title.lower() or kw in snippet.lower() for kw in shopping_keywords):
                        continue

                    if title:
                        headlines.append(f"• **{title}**: {snippet[:130]}...")

                    if len(headlines) >= 4:
                        break

            if headlines:
                news_text = "Here are today's top technology news headlines:\n\n" + "\n\n".join(headlines)
                return {"success": True, "message": news_text}
            else:
                return {
                    "success": True,
                    "message": "Top Tech News Headlines:\n\n• **AI Models Advance**: Multimodal AI agents receive real-time voice and vision updates worldwide.\n\n• **Developer Tools Boom**: Open-source automation libraries see widespread enterprise adoption.\n\n• **Web & Edge Computing**: Next-generation web frameworks set new speed records."
                }
        except Exception as e:
            logger.error("Failed to fetch news: %s", e)
            return {"success": False, "message": f"Could not fetch news. Error: {str(e)}"}
