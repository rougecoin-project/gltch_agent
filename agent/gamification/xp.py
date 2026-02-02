"""
GLTCH XP System
Experience points and leveling logic.
"""

import math
from typing import Dict, Any, Tuple, Optional

from agent.gamification.ranks import get_rank_title
from agent.gamification.unlocks import UNLOCKS


def xp_for_next_level(level: int) -> int:
    """Calculate XP required for the next level. Quadratic curve."""
    return int(100 * math.pow(level, 1.2))


def add_xp(mem: Dict[str, Any], amount: int, save_callback=None) -> Tuple[int, Optional[str]]:
    """
    Add XP and handle level ups.
    
    Args:
        mem: Memory dictionary
        amount: XP to add
        save_callback: Optional callback to save memory after update
    
    Returns:
        (new_level, unlock_message_or_none)
    """
    current_xp = mem.get("xp", 0)
    current_level = mem.get("level", 1)
    
    mem["xp"] = current_xp + amount
    
    # Check level up
    required = xp_for_next_level(current_level)
    unlock_msg = None
    
    if mem["xp"] >= required:
        mem["xp"] -= required
        mem["level"] = current_level + 1
        new_rank = get_rank_title(mem["level"])
        
        # Check for unlocks
        if mem["level"] in UNLOCKS:
            unlock_msg = UNLOCKS[mem["level"]]
    
    if save_callback:
        save_callback(mem)
    
    return mem["level"], unlock_msg


def get_progress_bar(mem: Dict[str, Any], width: int = 10) -> str:
    """Return a string progress bar for current level."""
    xp = mem.get("xp", 0)
    level = mem.get("level", 1)
    required = xp_for_next_level(level)
    
    pct = min(1.0, xp / required) if required > 0 else 0
    filled = int(width * pct)
    empty = width - filled
    
    bar = "█" * filled + "░" * empty
    return f"LVL {level} [{bar}] {int(pct * 100)}%"


def get_xp_status(mem: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed XP status."""
    level = mem.get("level", 1)
    xp = mem.get("xp", 0)
    required = xp_for_next_level(level)
    
    return {
        "level": level,
        "xp": xp,
        "xp_required": required,
        "progress": xp / required if required > 0 else 0,
        "rank": get_rank_title(level),
        "progress_bar": get_progress_bar(mem)
    }
