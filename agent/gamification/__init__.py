"""
GLTCH Gamification Module
XP, leveling, ranks, and unlocks.
"""

from agent.gamification.xp import add_xp, get_progress_bar, xp_for_next_level
from agent.gamification.ranks import RANKS, get_rank_title
from agent.gamification.unlocks import UNLOCKS, get_unlocks_for_level, is_feature_unlocked

__all__ = [
    "add_xp", "get_progress_bar", "xp_for_next_level",
    "RANKS", "get_rank_title",
    "UNLOCKS", "get_unlocks_for_level", "is_feature_unlocked"
]
