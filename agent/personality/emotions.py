"""
GLTCH Emotions Module
Environmental factors and dynamic mood influences.
"""

import psutil
from datetime import datetime
from typing import Dict, Any


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


def get_battery_status() -> str:
    """Get battery status if available."""
    if not hasattr(psutil, "sensors_battery"):
        return "unknown"
    
    bat = psutil.sensors_battery()
    if not bat:
        return "unknown"
    
    if bat.percent < 20 and not bat.power_plugged:
        return "critical"
    elif bat.percent < 50 and not bat.power_plugged:
        return "low"
    elif bat.power_plugged:
        return "charging"
    return "ok"


def get_environmental_context() -> str:
    """
    Generate a context string about the 'world' state.
    Used to inject feeling into the prompt.
    """
    cycle = get_day_cycle()
    stress = get_system_stress()
    battery_status = get_battery_status()
    
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


def get_emotion_metrics() -> Dict[str, Any]:
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
        "cycle": get_day_cycle(),
        "cpu": cpu,
        "ram": ram
    }


def resolve_mood(current_mood: str, user_input: str, metrics: Dict[str, Any] = None) -> str:
    """
    Heuristic mood adjustments based on system state.
    Can be used before LLM for automatic mood shifts.
    """
    if metrics is None:
        metrics = get_emotion_metrics()
    
    # High stress might shift mood
    if metrics["stress"] > 80 and current_mood in ("calm", "happy"):
        return "annoyed"
    
    # Low energy might make tired
    if metrics["energy"] < 20 and current_mood != "tired":
        return "tired"
    
    return current_mood
