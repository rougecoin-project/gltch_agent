"""
GLTCH Personality Module
Modes, moods, emotional dynamics, and identity generation.
"""

from agent.personality.modes import MODES, get_mode_description
from agent.personality.moods import MOODS, MOOD_UI, get_mood_description
from agent.personality.emotions import (
    get_day_cycle, get_system_stress, get_environmental_context,
    get_emotion_metrics, resolve_mood
)
from agent.personality.identity import (
    generate_handle, generate_bio, generate_identity,
    generate_unique_handle, generate_token_identity
)

__all__ = [
    "MODES", "get_mode_description",
    "MOODS", "MOOD_UI", "get_mood_description",
    "get_day_cycle", "get_system_stress", "get_environmental_context",
    "get_emotion_metrics", "resolve_mood",
    "generate_handle", "generate_bio", "generate_identity",
    "generate_unique_handle", "generate_token_identity"
]
