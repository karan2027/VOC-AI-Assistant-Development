import re
import math
import datetime
import asyncio
from typing import Dict, Any, Union, Optional
import logging

logger = logging.getLogger("assistant.helpers")

def calculate_bmi(weight_kg: float, height_m: float) -> Dict[str, Any]:
    """Calculates BMI and returns BMI value and category."""
    try:
        bmi = weight_kg / (height_m ** 2)
        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi < 24.9:
            category = "Normal weight"
        elif 25.0 <= bmi < 29.9:
            category = "Overweight"
        else:
            category = "Obese"
        return {"bmi": round(bmi, 2), "category": category, "success": True}
    except ZeroDivisionError:
        return {"error": "Height cannot be zero", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}

def calculate_age(birth_date_str: str) -> Dict[str, Any]:
    """Calculates age based on birth date (YYYY-MM-DD)."""
    try:
        birth_date = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return {"age": age, "success": True}
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD.", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}

def convert_units(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    """Converts common units (Celsius, Fahrenheit, km, miles, kg, lbs)."""
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()
    
    try:
        # Temperature
        if from_unit in ["celsius", "c"] and to_unit in ["fahrenheit", "f"]:
            result = (value * 9/5) + 32
        elif from_unit in ["fahrenheit", "f"] and to_unit in ["celsius", "c"]:
            result = (value - 32) * 5/9
        # Distance
        elif from_unit in ["km", "kilometers", "kilometer"] and to_unit in ["miles", "mile", "mi"]:
            result = value * 0.621371
        elif from_unit in ["miles", "mile", "mi"] and to_unit in ["km", "kilometers", "kilometer"]:
            result = value / 0.621371
        # Weight
        elif from_unit in ["kg", "kilograms", "kilogram"] and to_unit in ["lbs", "pounds", "pound", "lb"]:
            result = value * 2.20462
        elif from_unit in ["lbs", "pounds", "pound", "lb"] and to_unit in ["kg", "kilograms", "kilogram"]:
            result = value / 2.20462
        else:
            return {"error": f"Unsupported conversion from {from_unit} to {to_unit}", "success": False}
            
        return {"result": round(result, 2), "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}

def convert_currency(amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
    """Offline currency converter with standard base exchange rates (approximate/base rates)."""
    # Base rates relative to USD
    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.78,
        "INR": 83.5,
        "PKR": 278.0,
        "CAD": 1.37,
        "AUD": 1.50,
        "JPY": 157.0,
        "CNY": 7.25
    }
    
    from_curr = from_currency.upper().strip()
    to_curr = to_currency.upper().strip()
    
    if from_curr not in rates or to_curr not in rates:
        return {
            "error": f"Unsupported currency. Supported currencies: {', '.join(rates.keys())}",
            "success": False
        }
    
    try:
        # Convert to USD first, then to target currency
        amount_in_usd = amount / rates[from_curr]
        result = amount_in_usd * rates[to_curr]
        return {"result": round(result, 2), "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}

def evaluate_math_expression(expression: str) -> Dict[str, Any]:
    """Safely evaluates basic/scientific math expressions."""
    # Clean expression
    expr = expression.replace("x", "*").replace("divided by", "/").replace("times", "*")
    
    # Extract all alphabetical names
    words = re.findall(r'[a-zA-Z_]+', expr)
    allowed_names = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "sqrt": math.sqrt,
        "pi": math.pi, "e": math.e, "pow": math.pow
    }
    
    for word in words:
        if word not in allowed_names:
            return {"error": f"Forbidden token or function: '{word}'", "success": False}
            
    # Keep only safe mathematical and name characters
    if not re.match(r'^[0-9a-zA-Z\+\-\*\/\.\(\)\s\%\*\*\_]*$', expr):
        return {"error": "Invalid mathematical expression characters.", "success": False}
        
    try:
        # Evaluate in a restricted environment
        result = eval(expr, {"__builtins__": None}, allowed_names)
        return {"result": round(result, 4), "success": True}
    except Exception as e:
        return {"error": f"Math error: {str(e)}", "success": False}

class ActiveTimers:
    """Manages active timers and alarms in background threads/async loops."""
    def __init__(self, callback_func):
        self.callback_func = callback_func
        self.timers = {}
        self.alarms = {}
        self._counter = 0

    async def start_timer(self, seconds: int, label: str = "Timer"):
        timer_id = self._counter
        self._counter += 1
        self.timers[timer_id] = {
            "seconds": seconds,
            "label": label,
            "start_time": datetime.datetime.now(),
            "task": asyncio.create_task(self._timer_run(timer_id, seconds, label))
        }
        logger.info("Timer %d started for %d seconds (%s)", timer_id, seconds, label)
        return timer_id

    async def _timer_run(self, timer_id: int, seconds: int, label: str):
        try:
            await asyncio.sleep(seconds)
            logger.info("Timer %d elapsed: %s", timer_id, label)
            if asyncio.iscoroutinefunction(self.callback_func):
                await self.callback_func(f"Timer update: Your {seconds} second timer for {label} is done!")
            else:
                self.callback_func(f"Timer update: Your {seconds} second timer for {label} is done!")
        except asyncio.CancelledError:
            logger.info("Timer %d cancelled", timer_id)
        finally:
            self.timers.pop(timer_id, None)

    async def set_alarm(self, alarm_time_str: str, label: str = "Alarm"):
        """Sets alarm for time format HH:MM (24-hour)."""
        try:
            target_time = datetime.datetime.strptime(alarm_time_str, "%H:%M").time()
            alarm_id = self._counter
            self._counter += 1
            self.alarms[alarm_id] = {
                "time": alarm_time_str,
                "label": label,
                "task": asyncio.create_task(self._alarm_run(alarm_id, target_time, label))
            }
            logger.info("Alarm %d set for %s (%s)", alarm_id, alarm_time_str, label)
            return alarm_id, None
        except Exception as e:
            return None, str(e)

    async def _alarm_run(self, alarm_id: int, target_time, label: str):
        try:
            while True:
                now = datetime.datetime.now().time()
                # Check if current time matches target hour and minute
                if now.hour == target_time.hour and now.minute == target_time.minute:
                    logger.info("Alarm %d triggered: %s", alarm_id, label)
                    msg = f"Alarm trigger: Your alarm set for {target_time.strftime('%H:%M')} ({label}) is ringing!"
                    if asyncio.iscoroutinefunction(self.callback_func):
                        await self.callback_func(msg)
                    else:
                        self.callback_func(msg)
                    break
                await asyncio.sleep(15) # Check every 15 seconds
        except asyncio.CancelledError:
            logger.info("Alarm %d cancelled", alarm_id)
        finally:
            self.alarms.pop(alarm_id, None)

    def cancel_timer(self, timer_id: int) -> bool:
        if timer_id in self.timers:
            self.timers[timer_id]["task"].cancel()
            return True
        return False

    def cancel_alarm(self, alarm_id: int) -> bool:
        if alarm_id in self.alarms:
            self.alarms[alarm_id]["task"].cancel()
            return True
        return False
