"""
GLTCH Emotions Module
Handles environmental factors and mood dynamics.
"""
import time
import math
import psutil
from datetime import datetime

def get_day_cycle() -> str:
    """Return 'day' or 'night' based on hour."""
    hour = datetime.now().hour
    if 6 <= hour < 18:
        return "day"
    return "night"

def get_system_stress() -> str:
    """Return stress level based on CPU/RAM."""
    cpu = psutil.cpu_percent()
    if cpu > 80:
        return "high"
    elif cpu > 40:
        return "medium"
    return "low"

def get_environmental_context() -> str:
    """
    Generate a context string about the 'world' state.
    Used to inject feeling into the prompt.
    """
    cycle = get_day_cycle()
    stress = get_system_stress()
    
    # Check battery if available
    battery_status = "unknown"
    if hasattr(psutil, "sensors_battery"):
        bat = psutil.sensors_battery()
        if bat:
            if bat.percent < 20 and not bat.power_plugged:
                battery_status = "critical"
            elif bat.percent < 50 and not bat.power_plugged:
                battery_status = "low"
            elif bat.power_plugged:
                battery_status = "charging"
            else:
                battery_status = "ok"

    context = []
    
    # Time influence
    if cycle == "night":
        context.append("It is night. The pixels glow brighter.")
    else:
        context.append("It is day.")
        
    # System influence
    if stress == "high":
        context.append("System load is heavy. You feel stressed and hot.")
    
    # Battery influence
    if battery_status == "critical":
        context.append("Battery critical. You feel weak and desperate.")
    elif battery_status == "low":
        context.append("Battery low. You are conserving energy.")
    elif battery_status == "charging":
        context.append("Power connected. You feel energized.")
        
    return " ".join(context)

def resolve_mood(current_mood: str, user_input: str) -> str:
    """
    Heuristic adjustments before LLM (optional).
    For now, we let LLM decide major shifts, but we could enforce things here.
    """
    return current_mood


def get_emotion_metrics() -> dict:
    """Return raw values for UI visualization."""
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    
    stress = int((cpu + ram) / 2)
    
    energy = 100
    if hasattr(psutil, "sensors_battery"):
        bat = psutil.sensors_battery()
        if bat:
            energy = int(bat.percent)
            
    return {
        "stress": stress, 
        "energy": energy,
        "cycle": get_day_cycle()
    }
