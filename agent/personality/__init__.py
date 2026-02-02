"""
GLTCH Personality Module
Modes, moods, and emotional dynamics.
"""

from agent.personality.modes import MODES, get_mode_description
from agent.personality.moods import MOODS, MOOD_UI, get_mood_description
from agent.personality.emotions import (
    get_day_cycle, get_system_stress, get_environmental_context,
    get_emotion_metrics, resolve_mood
)

__all__ = [
    "MODES", "get_mode_description",
    "MOODS", "MOOD_UI", "get_mood_description",
    "get_day_cycle", "get_system_stress", "get_environmental_context",
    "get_emotion_metrics", "resolve_mood"
]
