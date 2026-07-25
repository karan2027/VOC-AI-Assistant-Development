import os
import datetime
import pyautogui
import psutil
from typing import Dict, Any
import logging

logger = logging.getLogger("assistant.automation.system")

class SystemAutomation:
    def __init__(self, screenshot_dir: str = "output/screenshots"):
        self.screenshot_dir = screenshot_dir
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def change_volume(self, direction: str, amount: int = 5) -> Dict[str, Any]:
        """Controls system volume (up, down, mute)."""
        cmd = direction.lower().strip()
        try:
            if cmd == "up":
                # PyAutoGUI sends a single volumeup keystroke, which is typically 2% change
                # Run it in a loop for multiple adjustments
                steps = max(1, amount // 2)
                for _ in range(steps):
                    pyautogui.press("volumeup")
                logger.info("Volume increased by %d steps", steps)
                return {"success": True, "message": "Volume increased."}
            elif cmd == "down":
                steps = max(1, amount // 2)
                for _ in range(steps):
                    pyautogui.press("volumedown")
                logger.info("Volume decreased by %d steps", steps)
                return {"success": True, "message": "Volume decreased."}
            elif cmd == "mute" or cmd == "unmute":
                pyautogui.press("volumemute")
                logger.info("Volume mute toggled")
                return {"success": True, "message": "Volume muted/unmuted."}
            else:
                return {"success": False, "message": f"Unsupported volume action: {direction}"}
        except Exception as e:
            logger.error("Volume adjustment failed: %s", e)
            return {"success": False, "message": f"Could not adjust volume: {str(e)}"}

    def media_control(self, action: str) -> Dict[str, Any]:
        """Controls system media playback."""
        cmd = action.lower().strip()
        try:
            if cmd in ["play", "pause", "playpause", "play/pause"]:
                pyautogui.press("playpause")
                logger.info("Media play/pause toggled")
                return {"success": True, "message": "Media play/pause toggled."}
            elif cmd in ["next", "next track", "next song"]:
                pyautogui.press("nexttrack")
                logger.info("Skipped to next track")
                return {"success": True, "message": "Skipped to next track."}
            elif cmd in ["prev", "previous", "previous track", "previous song"]:
                pyautogui.press("prevtrack")
                logger.info("Went back to previous track")
                return {"success": True, "message": "Went back to previous track."}
            else:
                return {"success": False, "message": f"Unsupported media action: {action}"}
        except Exception as e:
            logger.error("Media control failed: %s", e)
            return {"success": False, "message": f"Could not control media: {str(e)}"}

    def take_screenshot(self) -> Dict[str, Any]:
        """Takes a screenshot and saves it to the output folder."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            path = os.path.join(self.screenshot_dir, filename)
            
            # Take screenshot using pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(path)
            
            logger.info("Screenshot saved to %s", path)
            return {
                "success": True, 
                "message": f"Screenshot saved successfully as {filename} in your screenshots folder.",
                "path": path
            }
        except Exception as e:
            logger.error("Screenshot capture failed: %s", e)
            return {"success": False, "message": f"Failed to take screenshot: {str(e)}"}

    def get_system_stats(self) -> Dict[str, Any]:
        """Retrieves CPU usage, RAM usage, and battery status."""
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory().percent
            
            battery_info = {}
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = {
                        "percent": battery.percent,
                        "plugged": battery.power_plugged,
                        "time_left": battery.secsleft
                    }
            
            stats = {
                "cpu_percent": cpu,
                "memory_percent": memory,
                "battery": battery_info,
                "success": True
            }
            logger.info("System stats retrieved: CPU=%s%%, Memory=%s%%", cpu, memory)
            return stats
        except Exception as e:
            logger.error("Failed to retrieve system stats: %s", e)
            return {"success": False, "message": f"Failed to read system status: {str(e)}"}
            
    def get_time_date(self) -> Dict[str, str]:
        """Gets current local time and date."""
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p") # 12-hour format with AM/PM
        date_str = now.strftime("%A, %B %d, %Y") # e.g. Tuesday, July 21, 2026
        return {
            "time": time_str,
            "date": date_str
        }
