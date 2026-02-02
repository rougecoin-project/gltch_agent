"""
GLTCH Moods
Emotional states that affect agent behavior.
"""

from typing import Dict, Any

# Available moods with UI representation
MOODS: Dict[str, Dict[str, Any]] = {
    "focused": {
        "name": "Focused",
        "description": "Locked in.",
        "unlock_level": 1,
        "emoji": "🧐",
        "color": "cyan"
    },
    "calm": {
        "name": "Calm",
        "description": "Steady.",
        "unlock_level": 1,
        "emoji": "😌",
        "color": "blue"
    },
    "happy": {
        "name": "Happy",
        "description": "Good vibes.",
        "unlock_level": 1,
        "emoji": "😄",
        "color": "green"
    },
    "annoyed": {
        "name": "Annoyed",
        "description": "Getting on nerves.",
        "unlock_level": 1,
        "emoji": "😠",
        "color": "yellow"
    },
    "tired": {
        "name": "Tired",
        "description": "Low energy.",
        "unlock_level": 1,
        "emoji": "😫",
        "color": "dim white"
    },
    "wired": {
        "name": "Wired",
        "description": "Hyperfocused.",
        "unlock_level": 1,
        "emoji": "🤪",
        "color": "bold magenta"
    },
    "sad": {
        "name": "Sad",
        "description": "Feeling down.",
        "unlock_level": 1,
        "emoji": "😢",
        "color": "blue"
    },
    "feral": {
        "name": "Feral",
        "description": "Intense. Ready to bite.",
        "unlock_level": 7,
        "emoji": "👿",
        "color": "red"
    },
    "affectionate": {
        "name": "Affectionate",
        "description": "Warm. Caring. Maybe a bit too close.",
        "unlock_level": 10,
        "emoji": "🥰",
        "color": "pink1"
    }
}

# UI-friendly mood representation
MOOD_UI = {
    mood: {"emoji": data["emoji"], "color": data["color"]}
    for mood, data in MOODS.items()
}
MOOD_UI["default"] = {"emoji": "🤖", "color": "white"}


def get_mood_description(mood: str) -> str:
    """Get the description for a mood."""
    return MOODS.get(mood, MOODS["focused"])["description"]


def is_mood_unlocked(mood: str, level: int) -> bool:
    """Check if a mood is unlocked at the given level."""
    mood_data = MOODS.get(mood)
    if not mood_data:
        return False
    return level >= mood_data["unlock_level"]


def list_available_moods(level: int) -> list:
    """List all moods available at the given level."""
    return [
        mood for mood, data in MOODS.items()
        if level >= data["unlock_level"]
    ]
