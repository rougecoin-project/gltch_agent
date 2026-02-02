"""
GLTCH Gamification Module
XP, Leveling, and Rank logic.
"""
import math
from typing import Dict, Any, Tuple

from rich.console import Console

console = Console()

# RANKS based on Level
RANKS = {
    1: "Script Kiddie",
    5: "Console Cowboy",
    10: "Cyberdeck Operator",
    20: "Netrunner",
    35: "System Admin",
    50: "Construct",
    100: "Glitch God"
}

# Feature Unlocks
UNLOCKS = {
    3: "Mode: UNHINGED",
    7: "Mood: FERAL",
    10: "Mood: AFFECTIONATE",
    15: "Secret: ???",
    20: "Rank: NETRUNNER"
}

def get_rank_title(level: int) -> str:
    # Find the highest rank less than or equal to current level
    current_rank = "Unknown"
    for lvl, title in sorted(RANKS.items()):
        if level >= lvl:
            current_rank = title
        else:
            break
    return current_rank

def xp_for_next_level(level: int) -> int:
    """Quadratic XP curve: 100 * level^1.5"""
    return int(100 * math.pow(level, 1.2))

def add_xp(mem: Dict[str, Any], amount: int) -> None:
    """Add XP and handle level ups."""
    current_xp = mem.get("xp", 0)
    current_level = mem.get("level", 1)
    
    mem["xp"] = current_xp + amount
    
    # Check level up
    required = xp_for_next_level(current_level)
    
    if mem["xp"] >= required:
        mem["xp"] -= required
        mem["level"] = current_level + 1
        new_rank = get_rank_title(mem["level"])
        
        console.print(f"\n[bold yellow]⚡ LEVEL UP! ⚡[/bold yellow]")
        console.print(f"[cyan]Promoted to Level {mem['level']}: {new_rank}[/cyan]")
        
        # Check for unlocks
        if mem["level"] in UNLOCKS:
            console.print(f"[bold green]🔓 UNLOCKED: {UNLOCKS[mem['level']]}[/bold green]")
            
        console.print(f"[dim]Next level requires {xp_for_next_level(mem['level'])} XP[/dim]\n")

def get_progress_bar(mem: Dict[str, Any], width: int = 10) -> str:
    """Return a string progress bar for current level."""
    xp = mem.get("xp", 0)
    level = mem.get("level", 1)
    required = xp_for_next_level(level)
    
    pct = min(1.0, xp / required)
    filled = int(width * pct)
    empty = width - filled
    
    # Gradient colors could be cool, but sticking to simple for now
    bar = "█" * filled + "░" * empty
    return f"LVL {level} [{bar}] {int(pct*100)}%"

def xp_menu(mem: Dict[str, Any]) -> None:
    """Display detailed XP stats and future unlocks."""
    level = mem.get("level", 1)
    xp = mem.get("xp", 0)
    needed = xp_for_next_level(level)
    rank = get_rank_title(level)
    
    console.print(f"\n[bold]{rank.upper()}[/bold] (Level {level})")
    console.print(f"XP: [cyan]{xp}/{needed}[/cyan]")
    console.print(get_progress_bar(mem, width=30))
    console.print("")
    console.print("[bold]Unlocks:[/bold]")
    
    # Show past unlocks and next 2 future ones
    shown = 0
    for lvl in sorted(UNLOCKS.keys()):
        if lvl <= level:
            console.print(f" [green]✓ LVL {lvl}: {UNLOCKS[lvl]}[/green]")
        elif shown < 2:
            console.print(f" [dim]🔒 LVL {lvl}: {UNLOCKS[lvl]}[/dim]")
            shown += 1
        else:
            console.print(f" [dim]🔒 LVL {lvl}: ???[/dim]")

