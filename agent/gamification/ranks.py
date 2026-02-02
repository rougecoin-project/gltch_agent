"""
GLTCH Rank System
Rank titles based on level progression.
"""

from typing import Dict

# Ranks based on level thresholds
RANKS: Dict[int, str] = {
    1: "Script Kiddie",
    5: "Console Cowboy",
    10: "Cyberdeck Operator",
    20: "Netrunner",
    35: "System Admin",
    50: "Construct",
    100: "Glitch God"
}


def get_rank_title(level: int) -> str:
    """Get the rank title for a given level."""
    current_rank = "Unknown"
    for lvl, title in sorted(RANKS.items()):
        if level >= lvl:
            current_rank = title
        else:
            break
    return current_rank


def get_next_rank(level: int) -> tuple:
    """
    Get the next rank and level required.
    
    Returns:
        (next_rank_title, level_required) or (None, None) if max rank
    """
    for lvl, title in sorted(RANKS.items()):
        if level < lvl:
            return title, lvl
    return None, None


def list_all_ranks() -> list:
    """List all ranks with their level requirements."""
    return [
        {"level": lvl, "title": title}
        for lvl, title in sorted(RANKS.items())
    ]
