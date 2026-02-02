"""
GLTCH Memory Module
Handles persistent state: load, save, backup, restore.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any

from rich.console import Console

console = Console()

MEMORY_FILE = "memory.json"
KB_DIR = "kb"

DEFAULT_STATE = {
    "created": None,
    "mode": "operator",   # operator | cyberpunk | loyal | unhinged
    "mood": "focused",    # calm | focused | feral
    "notes": [],
    "missions": [],       # {id, ts, text, done_ts?}
    "network_active": False,
    "boost": False,       # True = use remote 4090, False = local
    "chat_history": [],   # last N turns for LLM context
    "operator": None,     # who runs this console
    "xp": 0,
    "level": 1
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_memory() -> Dict[str, Any]:
    if not os.path.exists(MEMORY_FILE):
        mem = DEFAULT_STATE.copy()
        mem["created"] = now_iso()
        save_memory(mem)
        return mem
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            mem = json.load(f)
    except Exception:
        console.print("[red]Memory corrupted. Starting fresh.[/red]")
        mem = DEFAULT_STATE.copy()
        mem["created"] = now_iso()

    # forward-compat defaults
    for k, v in DEFAULT_STATE.items():
        mem.setdefault(k, v)

    return mem


def save_memory(mem: Dict[str, Any]) -> None:
    tmp = MEMORY_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)
    os.replace(tmp, MEMORY_FILE)


def backup_memory(mem: Dict[str, Any]) -> None:
    ts = now_iso().replace(":", "-")
    backup_file = f"memory_backup_{ts}.json"
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)
    console.print(f"[green]Backup saved:[/green] {backup_file}")


def restore_memory(filename: str) -> Dict[str, Any] | None:
    filename = filename.strip()
    if not filename:
        console.print("[red]Usage: /restore <file>[/red]")
        return None
    if not os.path.exists(filename):
        console.print(f"[red]File not found:[/red] {filename}")
        return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            mem = json.load(f)
        for k, v in DEFAULT_STATE.items():
            mem.setdefault(k, v)
        save_memory(mem)
        console.print(f"[green]Memory restored from:[/green] {filename}")
        return mem
    except Exception as e:
        console.print(f"[red]Restore failed:[/red] {e}")
        return None
