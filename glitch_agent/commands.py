"""
GLTCH Commands Module
All slash command handlers: notes, missions, kb, modes, etc.
"""
import os
from typing import Dict, Any, List

from rich.console import Console

from memory import save_memory, now_iso, KB_DIR, DEFAULT_STATE
from llm import test_connection, get_last_stats
from gamification import add_xp, get_rank_title, get_progress_bar, xp_menu

console = Console()
AGENT_NAME = "GLTCH"



def set_mode(mem: Dict[str, Any], mode: str) -> None:
    mode = mode.strip().lower()
    allowed = {"operator", "cyberpunk", "loyal", "unhinged"}
    if mode not in allowed:
        console.print("[red]Invalid mode.[/red]")
        return
    
    # UNLOCK CHECK
    if mode == "unhinged" and mem.get("level", 1) < 3:
        console.print("[red]🔒 LOCKED: 'unhinged' mode requires Level 3[/red]")
        return

    mem["mode"] = mode
    save_memory(mem)
    console.print(f"[green]Mode set:[/green] {mode}")


def set_mood(mem: Dict[str, Any], mood: str) -> None:
    mood = mood.strip().lower()
    allowed = {"calm", "focused", "feral", "affectionate"}
    if mood not in allowed:
        console.print("[red]Invalid mood.[/red]")
        return

    # UNLOCK CHECK
    if mood == "feral" and mem.get("level", 1) < 7:
        console.print("[red]🔒 LOCKED: 'feral' mood requires Level 7[/red]")
        return
    if mood == "affectionate" and mem.get("level", 1) < 10:
        console.print("[red]🔒 LOCKED: 'affectionate' mood requires Level 10[/red]")
        return

    mem["mood"] = mood
    save_memory(mem)
    console.print(f"[green]Mood set:[/green] {mood}")


def toggle_network(mem: Dict[str, Any], state: str) -> None:
    state = state.strip().lower()
    if state not in ("on", "off"):
        console.print("[red]Usage: /net <on|off>[/red]")
        return
    
    is_on = (state == "on")
    mem["network_active"] = is_on
    if is_on:
        add_xp(mem, 2)
    save_memory(mem)
    status_str = "[bold green]ONLINE[/bold green]" if is_on else "[dim]OFFLINE[/dim]"
    console.print(f"Network interfaces: {status_str}")


def add_note(mem: Dict[str, Any], text: str) -> None:
    text = text.strip()
    if not text:
        console.print("[red]No note text.[/red]")
        return
    mem["notes"].append({"time": now_iso(), "text": text})
    add_xp(mem, 5) # +5 XP for note taking
    save_memory(mem)
    console.print("[green]Saved.[/green] (+5 XP)")


def recall_notes(mem: Dict[str, Any]) -> None:
    notes: List[Dict[str, str]] = mem["notes"]
    if not notes:
        console.print("[yellow]No notes yet.[/yellow]")
        return
    for i, n in enumerate(notes[-50:], 1):
        console.print(f"[cyan]{i}[/cyan]. {n['text']} [dim]{n['time']}[/dim]")


def clear_notes(mem: Dict[str, Any]) -> None:
    mem["notes"] = []
    save_memory(mem)
    console.print("[green]Notes cleared.[/green]")


def note_delete(mem: Dict[str, Any], note_id: str) -> None:
    note_id = note_id.strip()
    if not note_id.isdigit():
        console.print("[red]Note id must be a number.[/red]")
        return
    idx = int(note_id) - 1
    notes = mem["notes"]
    if idx < 0 or idx >= len(notes):
        console.print("[red]Note not found.[/red]")
        return
    removed = notes.pop(idx)
    save_memory(mem)
    console.print(f"[green]Deleted:[/green] {removed['text'][:40]}...")


def mission_add(mem: Dict[str, Any], text: str) -> None:
    text = text.strip()
    if not text:
        console.print("[red]No mission text.[/red]")
        return
    next_id = 1 if not mem["missions"] else max(m["id"] for m in mem["missions"]) + 1
    mem["missions"].append({"id": next_id, "ts": now_iso(), "text": text})
    save_memory(mem)
    console.print(f"[green]Mission added.[/green] id={next_id}")


def mission_list(mem: Dict[str, Any]) -> None:
    missions = mem["missions"]
    if not missions:
        console.print("[yellow]No missions.[/yellow]")
        return
    console.print(f"[bold]{AGENT_NAME} MISSIONS[/bold]")
    for m in missions:
        done = "✅" if m.get("done_ts") else "🟦"
        tail = f" [dim](done {m['done_ts']})[/dim]" if m.get("done_ts") else ""
        console.print(f"{done} [cyan]{m['id']}[/cyan] {m['text']}{tail}")


def mission_done(mem: Dict[str, Any], mid: str) -> None:
    mid = mid.strip()
    if not mid.isdigit():
        console.print("[red]Mission id must be a number.[/red]")
        return
    mid_i = int(mid)
    for m in mem["missions"]:
        if m["id"] == mid_i:
            if m.get("done_ts"):
                console.print("[yellow]Already done.[/yellow]")
                return
            m["done_ts"] = now_iso()
            add_xp(mem, 50) # +50 XP for completing a mission
            save_memory(mem)
            console.print(f"[green]Mission {mid_i} marked done.[/green] (+50 XP)")
            return
    console.print("[red]Mission not found.[/red]")


def mission_clear(mem: Dict[str, Any]) -> None:
    mem["missions"] = []
    save_memory(mem)
    console.print("[green]Missions cleared.[/green]")


def kb_add(mem, title: str, text: str):
    title = title.strip().replace("/", "-")
    text = text.strip()
    if not title or not text:
        console.print("[red]Usage: /kb add <title> <text>[/red]")
        return
    os.makedirs(KB_DIR, exist_ok=True)
    path = os.path.join(KB_DIR, f"{title}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{now_iso()}] {text}\n")
    console.print(f"[green]KB saved:[/green] {path}")


def kb_list():
    if not os.path.exists(KB_DIR):
        console.print("[yellow]No KB yet.[/yellow]")
        return
    files = sorted([f for f in os.listdir(KB_DIR) if f.endswith(".txt")])
    if not files:
        console.print("[yellow]No KB entries.[/yellow]")
        return
    console.print("[bold]KB entries[/bold]")
    for f in files:
        console.print(f"- {f[:-4]}")


def kb_read(title: str):
    title = title.strip().replace("/", "-")
    if not title:
        console.print("[red]Usage: /kb read <title>[/red]")
        return
    path = os.path.join(KB_DIR, f"{title}.txt")
    if not os.path.exists(path):
        console.print(f"[red]KB entry not found:[/red] {title}")
        return
    console.print(f"[bold]KB: {title}[/bold]")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            console.print(line.rstrip())


def kb_delete(title: str):
    title = title.strip().replace("/", "-")
    if not title:
        console.print("[red]Usage: /kb delete <title>[/red]")
        return
    path = os.path.join(KB_DIR, f"{title}.txt")
    if not os.path.exists(path):
        console.print(f"[red]KB entry not found:[/red] {title}")
        return
    os.remove(path)
    console.print(f"[green]KB deleted:[/green] {title}")


def search_all(mem, keyword: str):
    keyword = keyword.strip().lower()
    if not keyword:
        console.print("[red]Usage: /search <keyword>[/red]")
        return

    hits = []

    for n in mem.get("notes", []):
        if keyword in n.get("text", "").lower():
            hits.append(("note", n.get("time","?"), n.get("text","")))

    if os.path.exists(KB_DIR):
        for fname in os.listdir(KB_DIR):
            if not fname.endswith(".txt"):
                continue
            path = os.path.join(KB_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if keyword in line.lower():
                            hits.append((f"kb:{fname[:-4]}", "", line.strip()))
            except Exception:
                pass

    if not hits:
        console.print("[yellow]No hits.[/yellow]")
        return

    console.print(f"[bold]Search hits[/bold] for: [cyan]{keyword}[/cyan]")
    for src, ts, text in hits[:50]:
        stamp = f" [dim]{ts}[/dim]" if ts else ""
        console.print(f"[magenta]{src}[/magenta]{stamp} → {text}")


def status(mem: Dict[str, Any]) -> None:
    console.print(f"[bold]{AGENT_NAME} STATUS[/bold]")
    op = mem.get("operator", "unknown")
    console.print(f"operator: [cyan]{op}[/cyan]")
    console.print(f"mode: {mem['mode']}")
    console.print(f"mood: {mem['mood']}")
    boost_on = mem.get("boost", False)
    boost_status = "[red]ON (4090)[/red]" if boost_on else "[dim]OFF (local)[/dim]"
    console.print(f"boost: {boost_status}")
    openai_on = mem.get("openai_mode", False)
    openai_status = "[green]ON (cloud)[/green]" if openai_on else "[dim]OFF[/dim]"
    console.print(f"openai: {openai_status}")
    llm_ok = test_connection(boost=boost_on)
    llm_status = "[green]connected[/green]" if llm_ok else "[red]offline[/red]"
    console.print(f"llm: {llm_status}")
    console.print(f"notes: {len(mem['notes'])}")
    console.print(f"missions: {len(mem['missions'])} total | {sum(1 for m in mem['missions'] if m.get('done_ts'))} done")
    console.print(f"chat history: {len(mem.get('chat_history', []))} turns")


def help_menu() -> None:
    console.print(f"\n[bold]{AGENT_NAME} COMMANDS[/bold]")
    console.print("[dim]─────────────────────────────────────────────────[/dim]")
    console.print("[cyan]CORE[/cyan]")
    console.print("  /help                       show commands")
    console.print("  /status                     show agent status")
    console.print("  /ping                       alive check")
    console.print("  /sys                        system/LLM stats")
    console.print("  /exit                       quit")
    console.print("\n[cyan]LLM[/cyan]")
    console.print("  /models                     list available models")
    console.print("  /load <model>               switch to model")
    console.print("  /boost                      toggle remote LM Studio")
    console.print("  /lms                        start LM Studio server")
    console.print("  /openai                     toggle OpenAI cloud API")
    console.print("\n[cyan]PERSONALITY[/cyan]")
    console.print("  /mode <operator|cyberpunk|loyal|unhinged>")
    console.print("  /mood <calm|focused|feral|affectionate>")
    console.print("  /xp                         show rank & unlocks")
    console.print("\n[cyan]NOTES & MISSIONS[/cyan]")
    console.print("  /note <text>                save a note")
    console.print("  /note delete <id>           delete a note")
    console.print("  /recall                     list notes")
    console.print("  /clear_notes                clear notes")
    console.print("  /mission add <text>         add mission")
    console.print("  /mission list               list missions")
    console.print("  /mission done <id>          mark mission done")
    console.print("  /mission clear              clear all missions")
    console.print("\n[cyan]KNOWLEDGE BASE[/cyan]")
    console.print("  /kb add <title> <text>      add to knowledge base")
    console.print("  /kb read <title>            read KB entry")
    console.print("  /kb list                    list KB entries")
    console.print("  /kb delete <title>          delete KB entry")
    console.print("  /search <keyword>           search notes and KB")
    console.print("\n[cyan]FILES[/cyan]")
    console.print("  /write <file> <content>     create/overwrite file")
    console.print("  /append <file> <content>    append to file")
    console.print("  /cat <file>                 read file contents")
    console.print("  /ls [path]                  list directory")
    console.print("\n[cyan]DATA[/cyan]")
    console.print("  /backup                     backup memory")
    console.print("  /restore <file>             restore from backup")
    console.print("  /clear_chat                 clear chat history")
    console.print("  /net <on|off>               toggle network")
    console.print("[dim]─────────────────────────────────────────────────[/dim]\n")


def ping(mem: Dict[str, Any]) -> None:
    mode = mem["mode"]
    mood = mem["mood"]
    if mode == "operator":
        responses = {"calm": "Online.", "focused": "Operational.", "feral": "Hot and ready."}
    elif mode == "cyberpunk":
        responses = {"calm": "Signal clean.", "focused": "Jacked in.", "feral": "Lit up."}
    elif mode == "loyal":
        responses = {"calm": "Here.", "focused": "Standing by.", "feral": "Locked on."}
    else:  # unhinged
        responses = {"calm": "...yeah?", "focused": "Present. Unfortunately.", "feral": "WHAT."}
    console.print(f"[bold]{AGENT_NAME}[/bold]: {responses.get(mood, 'Pong.')}")


def system_stats(mem: Dict[str, Any]) -> None:
    """Display system and LLM stats."""
    import psutil
    
    stats = get_last_stats()
    boost_on = mem.get("boost", False)
    
    console.print(f"[bold red]═══════════════════════════════════════════════════════[/bold red]")
    console.print(f"[bold red]                    {AGENT_NAME} SYSTEM STATUS[/bold red]")
    console.print(f"[bold red]═══════════════════════════════════════════════════════[/bold red]")
    
    cpu_pct = psutil.cpu_percent(interval=0.1)
    mem_info = psutil.virtual_memory()
    mem_pct = mem_info.percent
    mem_used = mem_info.used // (1024**3)
    mem_total = mem_info.total // (1024**3)
    
    cpu_bar = "█" * int(cpu_pct // 10) + "░" * (10 - int(cpu_pct // 10))
    mem_bar = "█" * int(mem_pct // 10) + "░" * (10 - int(mem_pct // 10))
    
    console.print(f"[cyan]SYSTEM[/cyan]")
    console.print(f"  CPU  [{cpu_bar}] {cpu_pct:5.1f}%")
    console.print(f"  RAM  [{mem_bar}] {mem_pct:5.1f}% ({mem_used}G/{mem_total}G)")
    
    console.print(f"\n[cyan]LLM ENGINE[/cyan]")
    model = stats.get("model", "none")
    target = "[red]⚡ REMOTE (4090)[/red]" if boost_on else "[dim]LOCAL[/dim]"
    llm_ok = test_connection(boost=boost_on)
    status_txt = "[green]● ONLINE[/green]" if llm_ok else "[red]● OFFLINE[/red]"
    console.print(f"  Target: {target} {status_txt}")
    console.print(f"  Model:  {model}")
    
    if stats.get("context_max"):
        ctx_pct = int((stats["context_used"] / stats["context_max"]) * 100)
        ctx_bar = "█" * (ctx_pct // 10) + "░" * (10 - ctx_pct // 10)
        console.print(f"  CTX    [{ctx_bar}] {ctx_pct}% ({stats['context_used']}/{stats['context_max']})")
    
    if stats.get("time_ms"):
        console.print(f"\n[cyan]LAST REQUEST[/cyan]")
        console.print(f"  Prompt:     {stats['prompt_tokens']} tokens")
        console.print(f"  Completion: {stats['completion_tokens']} tokens")
        console.print(f"  Speed:      {stats['tokens_per_sec']} tok/s")
        console.print(f"  Latency:    {stats['time_ms']}ms")
    
    console.print(f"\n[cyan]SESSION[/cyan]")
    console.print(f"  Operator: [bold]{mem.get('operator', 'unknown')}[/bold]")
    console.print(f"  Mode:     {mem['mode']}")
    console.print(f"  Mood:     {mem['mood']}")
    console.print(f"  History:  {len(mem.get('chat_history', []))} messages")
    
    console.print(f"\n[cyan]PROGRESS[/cyan]")
    console.print(f"  Rank:     [magenta]{get_rank_title(mem.get('level', 1))}[/magenta]")
    console.print(f"  XP:       {get_progress_bar(mem, width=20)}")

    console.print(f"[bold red]═══════════════════════════════════════════════════════[/bold red]")
