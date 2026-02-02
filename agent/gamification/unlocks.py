"""
GLTCH Unlock System
Feature unlocks based on level progression.
"""

from typing import Dict, List, Optional

# Feature unlocks by level
UNLOCKS: Dict[int, str] = {
    3: "Mode: UNHINGED",
    7: "Mood: FERAL",
    10: "Mood: AFFECTIONATE",
    15: "Secret: ???",
    20: "Rank: NETRUNNER"
}


def get_unlocks_for_level(level: int) -> List[str]:
    """Get all unlocks earned at or before the given level."""
    return [
        unlock for lvl, unlock in sorted(UNLOCKS.items())
        if level >= lvl
    ]


def get_pending_unlocks(level: int, limit: int = 2) -> List[dict]:
    """Get upcoming unlocks the user hasn't reached yet."""
    pending = []
    for lvl, unlock in sorted(UNLOCKS.items()):
        if level < lvl:
            pending.append({"level": lvl, "unlock": unlock})
            if len(pending) >= limit:
                break
    return pending


def is_feature_unlocked(feature: str, level: int) -> bool:
    """
    Check if a specific feature is unlocked.
    
    Args:
        feature: Feature identifier (e.g., "unhinged", "feral", "affectionate")
        level: Current user level
    """
    feature_lower = feature.lower()
    
    # Map features to their unlock levels
    feature_levels = {
        "unhinged": 3,
        "feral": 7,
        "affectionate": 10
    }
    
    required = feature_levels.get(feature_lower)
    if required is None:
        return True  # Unknown features are unlocked by default
    
    return level >= required


def get_unlock_status(level: int) -> dict:
    """Get comprehensive unlock status."""
    earned = []
    pending = []
    
    for lvl, unlock in sorted(UNLOCKS.items()):
        if level >= lvl:
            earned.append({"level": lvl, "unlock": unlock})
        else:
            pending.append({"level": lvl, "unlock": unlock})
    
    return {
        "level": level,
        "earned": earned,
        "pending": pending,
        "next": pending[0] if pending else None
    }
