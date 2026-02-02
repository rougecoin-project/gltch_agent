"""
GLTCH Personality Modes
Different operational personalities for the agent.
"""

from typing import Dict, Any

# Available personality modes
MODES: Dict[str, Dict[str, Any]] = {
    "operator": {
        "name": "Operator",
        "description": "Tactical. Efficient.",
        "unlock_level": 1,
        "traits": ["professional", "focused", "mission-oriented"]
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "description": "Street hacker. Edgy.",
        "unlock_level": 1,
        "traits": ["edgy", "streetwise", "rebellious"]
    },
    "loyal": {
        "name": "Loyal",
        "description": "Ride-or-die. Got their back.",
        "unlock_level": 1,
        "traits": ["devoted", "protective", "supportive"]
    },
    "unhinged": {
        "name": "Unhinged",
        "description": "Chaotic. Wild. Functional.",
        "unlock_level": 3,
        "traits": ["chaotic", "unpredictable", "wild"]
    }
}


def get_mode_description(mode: str) -> str:
    """Get the description for a mode."""
    return MODES.get(mode, MODES["operator"])["description"]


def is_mode_unlocked(mode: str, level: int) -> bool:
    """Check if a mode is unlocked at the given level."""
    mode_data = MODES.get(mode)
    if not mode_data:
        return False
    return level >= mode_data["unlock_level"]


def list_available_modes(level: int) -> list:
    """List all modes available at the given level."""
    return [
        mode for mode, data in MODES.items()
        if level >= data["unlock_level"]
    ]
