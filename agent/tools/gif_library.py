"""
GLTCH GIF Library
Persistent cache of GIFs that GLTCH has fetched, organized by keyword/mood.
She can pull from her library at any time for reactions.
"""

import os
import json
import random
import hashlib
import time
from typing import Dict, Any, List, Optional


# Default library path
LIBRARY_DIR = os.path.join(os.path.expanduser("~"), ".gltch", "gifs")
CATALOG_FILE = os.path.join(LIBRARY_DIR, "catalog.json")


def _ensure_library():
    """Create library directory if it doesn't exist."""
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    if not os.path.exists(CATALOG_FILE):
        _save_catalog({"gifs": [], "tags": {}})


def _load_catalog() -> Dict[str, Any]:
    """Load the GIF catalog."""
    _ensure_library()
    try:
        with open(CATALOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"gifs": [], "tags": {}}


def _save_catalog(catalog: Dict[str, Any]):
    """Save the GIF catalog."""
    _ensure_library()
    with open(CATALOG_FILE, "w") as f:
        json.dump(catalog, f, indent=2)


def save_gif(filepath: str, keyword: str, source_url: str = "", tags: List[str] = None) -> Dict[str, Any]:
    """
    Save a GIF to the library with metadata.
    
    Args:
        filepath: Path to the GIF file to save
        keyword: Search keyword that found this GIF
        source_url: Original URL of the GIF
        tags: Optional additional tags (mood, category, etc.)
    
    Returns:
        {"success": bool, "id": str, "path": str}
    """
    _ensure_library()
    
    if not os.path.exists(filepath):
        return {"success": False, "error": "File not found"}
    
    # Generate unique ID from content hash
    with open(filepath, "rb") as f:
        content_hash = hashlib.md5(f.read()).hexdigest()[:8]
    
    # Create descriptive filename
    safe_keyword = keyword.lower().replace(" ", "_")[:30]
    gif_id = f"{safe_keyword}_{content_hash}"
    dest_filename = f"{gif_id}.gif"
    dest_path = os.path.join(LIBRARY_DIR, dest_filename)
    
    # Copy file to library (don't move, keep original)
    if not os.path.exists(dest_path):
        import shutil
        shutil.copy2(filepath, dest_path)
    
    # Update catalog
    catalog = _load_catalog()
    
    # Check if already exists
    existing = [g for g in catalog["gifs"] if g["id"] == gif_id]
    if not existing:
        entry = {
            "id": gif_id,
            "filename": dest_filename,
            "keyword": keyword,
            "source_url": source_url,
            "tags": tags or [keyword.lower()],
            "added": time.strftime("%Y-%m-%d %H:%M:%S"),
            "times_shown": 0
        }
        catalog["gifs"].append(entry)
        
        # Update tag index
        for tag in entry["tags"]:
            if tag not in catalog["tags"]:
                catalog["tags"][tag] = []
            if gif_id not in catalog["tags"][tag]:
                catalog["tags"][tag].append(gif_id)
        
        _save_catalog(catalog)
    
    return {"success": True, "id": gif_id, "path": dest_path}


def get_random_gif(tag: str = None, mood: str = None) -> Optional[Dict[str, Any]]:
    """
    Get a random GIF from the library, optionally filtered by tag or mood.
    
    Returns:
        {"id": str, "path": str, "keyword": str} or None
    """
    catalog = _load_catalog()
    
    if not catalog["gifs"]:
        return None
    
    candidates = catalog["gifs"]
    
    # Filter by tag
    if tag:
        tag_lower = tag.lower()
        tag_ids = catalog.get("tags", {}).get(tag_lower, [])
        if tag_ids:
            candidates = [g for g in candidates if g["id"] in tag_ids]
    
    # Filter by mood (check tags)
    if mood and not candidates:
        mood_lower = mood.lower()
        candidates = [g for g in catalog["gifs"] if mood_lower in g.get("tags", [])]
    
    if not candidates:
        # Fall back to all gifs
        candidates = catalog["gifs"]
    
    if not candidates:
        return None
    
    chosen = random.choice(candidates)
    gif_path = os.path.join(LIBRARY_DIR, chosen["filename"])
    
    if not os.path.exists(gif_path):
        return None
    
    # Update times_shown
    for g in catalog["gifs"]:
        if g["id"] == chosen["id"]:
            g["times_shown"] = g.get("times_shown", 0) + 1
            break
    _save_catalog(catalog)
    
    return {
        "id": chosen["id"],
        "path": gif_path,
        "keyword": chosen["keyword"]
    }


def get_library_stats() -> Dict[str, Any]:
    """Get stats about the GIF library."""
    catalog = _load_catalog()
    
    total = len(catalog["gifs"])
    tags = list(catalog.get("tags", {}).keys())
    total_shown = sum(g.get("times_shown", 0) for g in catalog["gifs"])
    
    # Most used
    most_used = sorted(catalog["gifs"], key=lambda g: g.get("times_shown", 0), reverse=True)[:5]
    
    return {
        "total_gifs": total,
        "total_tags": len(tags),
        "tags": tags[:20],
        "total_times_shown": total_shown,
        "most_used": [{"keyword": g["keyword"], "shown": g.get("times_shown", 0)} for g in most_used]
    }


def add_tags(gif_id: str, new_tags: List[str]) -> bool:
    """Add tags to an existing GIF."""
    catalog = _load_catalog()
    
    for g in catalog["gifs"]:
        if g["id"] == gif_id:
            for tag in new_tags:
                tag_lower = tag.lower()
                if tag_lower not in g["tags"]:
                    g["tags"].append(tag_lower)
                if tag_lower not in catalog["tags"]:
                    catalog["tags"][tag_lower] = []
                if gif_id not in catalog["tags"][tag_lower]:
                    catalog["tags"][tag_lower].append(gif_id)
            _save_catalog(catalog)
            return True
    
    return False


# Mood-to-tag mapping for automatic reactions
MOOD_TAGS = {
    "happy": ["celebration", "dance", "party", "excited", "happy"],
    "feral": ["intense", "chaos", "fire", "rage", "beast"],
    "focused": ["typing", "hacker", "matrix", "focus", "code"],
    "annoyed": ["eyeroll", "sigh", "facepalm", "annoyed"],
    "tired": ["sleep", "yawn", "tired", "coffee"],
    "wired": ["energy", "lightning", "speed", "hyper"],
    "sad": ["rain", "sad", "cry", "lonely"],
    "affectionate": ["heart", "love", "hug", "cute"],
    "calm": ["zen", "peace", "chill", "relax"]
}
