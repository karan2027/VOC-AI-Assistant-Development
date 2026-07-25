import os
import subprocess
import psutil
from typing import Dict, Any, List
import logging

logger = logging.getLogger("assistant.automation.apps")

# Map common app names to executable commands / paths
APP_COMMANDS = {
    "chrome": "start chrome",
    "vs code": "code",
    "vscode": "code",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "spotify": "spotify",
    "whatsapp": "start whatsapp:",
    "word": "winword",
    "ms word": "winword",
    "powerpoint": "powerpnt",
    "power point": "powerpnt",
    "excel": "excel",
    "terminal": "start wt",
    "cmd": "start cmd",
    "command prompt": "start cmd",
    "powershell": "start powershell",
    "camera": "start microsoft.windows.camera:"
}

# Processes list mapping for closing apps
APP_PROCESSES = {
    "chrome": "chrome.exe",
    "vs code": "Code.exe",
    "vscode": "Code.exe",
    "notepad": "notepad.exe",
    "calculator": "CalculatorApp.exe",
    "spotify": "Spotify.exe",
    "whatsapp": "WhatsApp.exe",
    "word": "WINWORD.EXE",
    "powerpoint": "POWERPNT.EXE",
    "excel": "EXCEL.EXE",
    "terminal": "WindowsTerminal.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
}

class AppAutomation:
    def __init__(self):
        pass

    def open_app(self, app_name: str) -> Dict[str, Any]:
        """Launches a desktop application."""
        name = app_name.lower().strip()
        
        # Check direct mapping
        command = None
        for key, cmd in APP_COMMANDS.items():
            if key in name:
                command = cmd
                break

        if not command:
            # Try to launch directly by name if it's not in the map
            command = name

        try:
            logger.info("Opening app: %s using command: %s", app_name, command)
            # Use shell=True for 'start' commands
            if command.startswith("start "):
                subprocess.Popen(command, shell=True)
            else:
                subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "message": f"Successfully opened {app_name}."}
        except Exception as e:
            logger.error("Failed to open app %s: %s", app_name, e)
            return {"success": False, "message": f"Could not open {app_name}. Error: {str(e)}"}

    def close_app(self, app_name: str) -> Dict[str, Any]:
        """Closes a running desktop application by terminating its process."""
        name = app_name.lower().strip()
        process_name = None
        
        for key, proc in APP_PROCESSES.items():
            if key in name:
                process_name = proc
                break
                
        if not process_name:
            # Fallback to appending .exe to name
            process_name = f"{name}.exe"

        terminated_count = 0
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                    proc.terminate()
                    terminated_count += 1
            
            if terminated_count > 0:
                logger.info("Closed %d instances of app %s", terminated_count, app_name)
                return {"success": True, "message": f"Closed {app_name}."}
            else:
                logger.info("No running instances of %s found", app_name)
                return {"success": False, "message": f"No running instances of {app_name} found."}
        except Exception as e:
            logger.error("Failed to close app %s: %s", app_name, e)
            return {"success": False, "message": f"Could not close {app_name}. Error: {str(e)}"}

    def list_running_apps(self) -> List[str]:
        """Lists currently running mapped applications."""
        running = []
        for key, proc_name in APP_PROCESSES.items():
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == proc_name.lower():
                    if key not in running:
                        running.append(key)
        return running
