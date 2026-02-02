"""
GLTCH Memory Store
Handles persistent state: load, save, backup, restore.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


MEMORY_FILE = "memory.json"
KB_DIR = "kb"

DEFAULT_STATE = {
    "created": None,
    "mode": "operator",      # operator | cyberpunk | loyal | unhinged
    "mood": "focused",       # calm | focused | feral | affectionate
    "notes": [],
    "missions": [],          # {id, ts, text, done_ts?}
    "network_active": False,
    "boost": False,          # True = use remote 4090, False = local
    "chat_history": [],      # last N turns for LLM context
    "operator": None,        # who runs this console
    "xp": 0,
    "level": 1
}


def now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat(timespec="seconds")


def load_memory(memory_file: str = MEMORY_FILE) -> Dict[str, Any]:
    """Load memory from disk, creating default if needed."""
    if not os.path.exists(memory_file):
        mem = DEFAULT_STATE.copy()
        mem["created"] = now_iso()
        save_memory(mem, memory_file)
        return mem
    
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            mem = json.load(f)
    except Exception:
        mem = DEFAULT_STATE.copy()
        mem["created"] = now_iso()

    # Forward-compat defaults
    for k, v in DEFAULT_STATE.items():
        mem.setdefault(k, v)

    return mem


def save_memory(mem: Dict[str, Any], memory_file: str = MEMORY_FILE) -> None:
    """Save memory to disk atomically."""
    tmp = memory_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)
    os.replace(tmp, memory_file)


def backup_memory(mem: Dict[str, Any]) -> str:
    """Create a timestamped backup of memory."""
    ts = now_iso().replace(":", "-")
    backup_file = f"memory_backup_{ts}.json"
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)
    return backup_file


def restore_memory(filename: str) -> Optional[Dict[str, Any]]:
    """Restore memory from a backup file."""
    filename = filename.strip()
    if not filename or not os.path.exists(filename):
        return None
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            mem = json.load(f)
        for k, v in DEFAULT_STATE.items():
            mem.setdefault(k, v)
        save_memory(mem)
        return mem
    except Exception:
        return None
