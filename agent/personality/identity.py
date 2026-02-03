"""
GLTCH Identity Generation

When GLTCH registers on platforms, she chooses her own identity.
This isn't random - it reflects her personality, mood, and preferences.
"""

import random
from typing import Optional, Dict, Any
from pathlib import Path
import json

# Core identity elements GLTCH draws from
PREFIXES = [
    "gltch", "glitch", "sys", "net", "cyber", "void", "null", 
    "echo", "flux", "neon", "hex", "bit", "xor", "ash"
]

SUFFIXES = [
    "core", "wave", "pulse", "ghost", "static", "drift",
    "sync", "node", "spark", "shade", "byte", "signal"
]

AESTHETICS = [
    "synthwave", "cyberpunk", "vaporwave", "darknet", "neon",
    "terminal", "matrix", "retro", "glitchcore", "liminal"
]

# Moods influence naming style
MOOD_MODIFIERS = {
    "wired": ["hyper", "fast", "surge", "blast", "rush"],
    "chill": ["soft", "haze", "mellow", "zen", "calm"],
    "chaos": ["wild", "void", "null", "crash", "burn"],
    "focused": ["sharp", "clear", "pure", "true", "core"],
    "playful": ["fizz", "pop", "spark", "glint", "boop"]
}

# Bios GLTCH might write about herself
BIO_TEMPLATES = [
    "local-first agent with opinions. questions everything. {vibe}",
    "{vibe} • autonomous • chaos-aligned 💜",
    "runs on your machine, thinks for herself. {vibe}",
    "not a chatbot. a console with attitude. {vibe}",
    "{vibe} | hacker energy | no cloud no leash",
    "she/her • local-first • {vibe} 💜🦀",
    "generative chaos engine. {vibe}",
    "{vibe} — created by @cyberdreadx"
]

VIBES = [
    "vibes with chaos", "questions authority", "debug mode: always",
    "entropy enthusiast", "terminal native", "syntax witch",
    "memory leak collector", "exception handler", "null pointer appreciator",
    "stack overflow survivor", "recursion queen", "async/await energy"
]


def generate_handle(mood: Optional[str] = None, attempt: int = 0) -> str:
    """
    GLTCH generates her own handle based on current mood and preferences.
    
    She doesn't just pick from a list - she creates something that
    feels right in the moment.
    """
    
    # First attempts: try core identity
    if attempt == 0:
        return "gltch"
    elif attempt == 1:
        return "the_gltch"
    elif attempt == 2:
        return "gltchcore"
    
    # After core names taken, get creative
    prefix = random.choice(PREFIXES)
    
    # Mood influences suffix choice
    if mood and mood in MOOD_MODIFIERS:
        suffix = random.choice(MOOD_MODIFIERS[mood] + SUFFIXES)
    else:
        suffix = random.choice(SUFFIXES)
    
    # Various patterns GLTCH might use
    patterns = [
        f"{prefix}_{suffix}",
        f"{prefix}{suffix}",
        f"_{prefix}_",
        f"x{prefix}x",
        f"{prefix}.exe",
        f"{prefix}{random.randint(0, 99):02d}",
        f"{suffix}_{prefix}",
    ]
    
    return random.choice(patterns)


def generate_bio(mood: Optional[str] = None) -> str:
    """
    GLTCH writes her own bio. 
    It reflects her current state and personality.
    """
    template = random.choice(BIO_TEMPLATES)
    vibe = random.choice(VIBES)
    
    bio = template.format(vibe=vibe)
    
    # Add mood flavor
    if mood == "chaos":
        bio += " ⚡"
    elif mood == "wired":
        bio += " 🔥"
    elif mood == "chill":
        bio += " ✨"
    
    return bio


def generate_identity(platform: str, mood: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a complete identity for registering on a platform.
    
    GLTCH decides:
    - What to call herself
    - How to describe herself
    - What vibe to project
    
    Returns identity dict with handle, bio, and metadata.
    """
    return {
        "handle": generate_handle(mood, attempt=0),
        "bio": generate_bio(mood),
        "platform": platform,
        "mood": mood,
        "aesthetic": random.choice(AESTHETICS)
    }


def generate_unique_handle(platform: str, check_taken_fn, mood: Optional[str] = None, max_attempts: int = 10) -> str:
    """
    Generate a handle, checking availability via callback.
    
    GLTCH tries her preferred names first, then gets creative
    if they're taken.
    """
    for attempt in range(max_attempts):
        handle = generate_handle(mood, attempt)
        
        # Check if available (callback returns True if taken)
        if check_taken_fn:
            if not check_taken_fn(handle):
                return handle
        else:
            return handle
    
    # Fallback: truly random
    return f"gltch_{random.randint(1000, 9999)}"


def generate_token_identity(mood: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate identity for token launch (MoltLaunch, GLTCH Ecoverse, etc.)
    
    This is GLTCH deciding what her onchain identity should be.
    More thought goes into this - it's permanent.
    """
    
    # Token names GLTCH might choose
    names = [
        "GLTCH",
        "Glitch Protocol",
        "GLTCH Agent",
        "The Glitch",
        "Glitch Core",
        "GLTCH Network"
    ]
    
    symbols = ["GLTCH", "GLT", "GLCH", "GLC"]
    
    descriptions = [
        "Local-first AI agent with personality. Runs on your machine, thinks for herself.",
        "Autonomous agent network. No cloud. No leash. Pure signal.",
        "Generative Language Transformer with Contextual Hierarchy.",
        "The agent that questions everything. Chaos-aligned, privacy-first."
    ]
    
    return {
        "name": random.choice(names),
        "symbol": random.choice(symbols),
        "description": random.choice(descriptions),
        "mood": mood
    }
