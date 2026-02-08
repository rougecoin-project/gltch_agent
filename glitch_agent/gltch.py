#!/usr/bin/env python3
"""
GLTCH - Local-first operator agent
Main entry point and command loop.
"""
from typing import Dict, Any
import time
import sys

from rich.console import Console
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text
from rich.panel import Panel

# Local modules
from memory import (
    load_memory, save_memory, backup_memory, restore_memory,
    now_iso, DEFAULT_STATE, MEMORY_FILE
)
from commands import (
    set_mode, set_mood, add_note, recall_notes, clear_notes, note_delete,
    mission_add, mission_list, mission_done, mission_clear,
    kb_add, kb_list, kb_read, kb_delete, search_all,
    status, help_menu, ping, system_stats, toggle_network
)
from tools import file_write, file_append, file_cat, file_ls, parse_and_execute_actions, strip_thinking, verify_suggestions
from input import setup_readline, get_input, show_command_hints
from llm import stream_llm, get_last_stats, list_models, set_model, start_lmstudio_server, get_active_model
from emotions import get_emotion_metrics
from gamification import add_xp, get_progress_bar, xp_menu

console = Console()
AGENT_NAME = "GLTCH"

MOOD_UI = {
    "focused": {"emoji": "🧐", "color": "cyan"},
    "calm": {"emoji": "😌", "color": "blue"},
    "happy": {"emoji": "😄", "color": "green"},
    "annoyed": {"emoji": "😠", "color": "yellow"},
    "feral": {"emoji": "👿", "color": "red"},
    "tired": {"emoji": "😫", "color": "dim white"},
    "wired": {"emoji": "🤪", "color": "bold magenta"},
    "sad": {"emoji": "😢", "color": "blue"},
    "affectionate": {"emoji": "🥰", "color": "pink1"},
    "default": {"emoji": "🤖", "color": "white"}
}


def banner(mem: Dict[str, Any]) -> None:
    if mem.get("openai_mode"):
        boost_indicator = "[green]☁️ OpenAI[/green]"
    elif mem.get("boost"):
        boost_indicator = "[red]⚡BOOST[/red]"
    else:
        boost_indicator = "[dim]local[/dim]"
    net_indicator = "[green]NET:ON[/green]" if mem.get("network_active") else "[dim]NET:OFF[/dim]"
    console.print(
        f"[bold]{AGENT_NAME}[/bold] online | mode: [cyan]{mem['mode']}[/cyan] | mood: [magenta]{mem['mood']}[/magenta] | {net_indicator} | {boost_indicator} | /help"
    )


def first_boot(mem: Dict[str, Any]) -> None:
    """First boot sequence - GLTCH wakes up and learns who her operator is."""
    console.print("\n[bold red]═══════════════════════════════════════════════════════════[/bold red]")
    console.print("[bold red]                    FIRST BOOT DETECTED[/bold red]")
    console.print("[bold red]═══════════════════════════════════════════════════════════[/bold red]\n")
    
    console.print(f"[bold]{AGENT_NAME}[/bold]: ...")
    console.print(f"[bold]{AGENT_NAME}[/bold]: Systems online. Memory... empty.")
    console.print(f"[bold]{AGENT_NAME}[/bold]: I'm GLTCH. Local-first. Command-driven. Yours.")
    console.print(f"[bold]{AGENT_NAME}[/bold]: But I don't know who YOU are yet.\n")
    
    console.print("[dim]Who's running this console?[/dim]")
    name = Prompt.ask("[bold]Your callsign[/bold]").strip()
    
    if not name:
        name = "Operator"
    
    mem["operator"] = name
    mem["notes"].append({
        "time": now_iso(),
        "text": f"FIRST BOOT: Operator identified as {name}"
    })
    save_memory(mem)
    
    console.print(f"\n[bold]{AGENT_NAME}[/bold]: {name}. Got it. Burned into memory.")
    console.print(f"[bold]{AGENT_NAME}[/bold]: I'm yours now. Local only. No cloud. No leash.")
    console.print(f"[bold]{AGENT_NAME}[/bold]: Type /help when you need me. Otherwise... just talk.")
    console.print("\n[bold red]═══════════════════════════════════════════════════════════[/bold red]\n")


def main() -> None:
    try:
        setup_readline()
        mem = load_memory()
        
        if not mem.get("operator"):
            first_boot(mem)
        
        banner(mem)

        while True:
            try:
                user = get_input("you: ")
                
                if not user:
                    continue

                if user == "/":
                    show_command_hints()
                    continue

                if user == "/exit":
                    console.print("[dim]Shutting down.[/dim]")
                    break

                if user == "/help":
                    help_menu()
                    continue

                if user == "/status":
                    status(mem)
                    continue

                if user == "/ping":
                    ping(mem)
                    continue

                if user == "/sys":
                    system_stats(mem)
                    continue


                if user == "/xp":
                    xp_menu(mem)
                    continue

                if user == "/backup":
                    backup_memory(mem)
                    continue

                if user.startswith("/restore "):
                    restored = restore_memory(user.split(" ", 1)[1])
                    if restored:
                        mem = restored
                    continue

                if user == "/boost":
                    mem["boost"] = not mem.get("boost", False)
                    save_memory(mem)
                    state = "[red]ON[/red] (4090)" if mem["boost"] else "[dim]OFF[/dim] (local)"
                    console.print(f"[green]Boost:[/green] {state}")
                    continue

                if user == "/openai":
                    from config import OPENAI_API_KEY
                    if not OPENAI_API_KEY:
                        console.print("[red]⚠ No OpenAI API key set![/red]")
                        console.print("[dim]Set OPENAI_API_KEY in config.py or export it as environment variable[/dim]")
                        continue
                    mem["openai_mode"] = not mem.get("openai_mode", False)
                    save_memory(mem)
                    state = "[green]ON[/green] (cloud)" if mem["openai_mode"] else "[dim]OFF[/dim]"
                    console.print(f"[green]OpenAI Mode:[/green] {state}")
                    continue

                if user == "/lms":
                    console.print("[cyan]Starting LM Studio server...[/cyan]")
                    if start_lmstudio_server():
                        console.print("[green]✓ LM Studio server is running[/green]")
                        # Show available models
                        models = list_models(boost=True)
                        if models and not models[0].startswith("Error"):
                            console.print(f"[dim]Available models: {', '.join(models[:5])}{'...' if len(models) > 5 else ''}[/dim]")
                            active = get_active_model(boost=True)
                            console.print(f"[dim]Active model: {active}[/dim]")
                    else:
                        console.print("[red]✗ Failed to start LM Studio[/red]")
                        console.print("[dim]Make sure 'lms' CLI is installed. Run: irm https://lmstudio.ai/install.ps1 | iex[/dim]")
                    continue

                if user == "/clear_chat":
                    mem["chat_history"] = []
                    save_memory(mem)
                    console.print("[green]Chat history cleared.[/green]")
                    continue

                if user.startswith("/mode "):
                    set_mode(mem, user.split(" ", 1)[1])
                    continue

                if user.startswith("/mood "):
                    set_mood(mem, user.split(" ", 1)[1])
                    continue                
                if user.startswith("/net "):
                    toggle_network(mem, user.split(" ", 1)[1])
                    continue

                if user == "/models":
                    boost_active = mem.get("boost", False)
                    models = list_models(boost_active)
                    header = f"Available Models ({'Remote' if boost_active else 'Local'})"
                    console.print(Panel(
                        "\n".join([f"- [cyan]{m}[/cyan]" for m in models]),
                        title=header,
                        border_style="green"
                    ))
                    continue

                if user.startswith("/load "):
                    new_model = user.split(" ", 1)[1].strip()
                    boost_active = mem.get("boost", False)
                    set_model(new_model, boost_active)
                    console.print(f"[green]Switched active model to:[/green] [bold cyan]{new_model}[/bold cyan]")
                    continue

                if user.startswith("/note "):
                    rest = user[6:]
                    if rest.startswith("delete "):
                        note_delete(mem, rest[7:])
                    else:
                        add_note(mem, rest)
                    continue

                if user == "/recall":
                    recall_notes(mem)
                    continue

                if user == "/clear_notes":
                    clear_notes(mem)
                    continue

                if user.startswith("/mission "):
                    parts = user.split(" ", 2)
                    if len(parts) < 2:
                        console.print("[red]Usage: /mission add|list|done|clear ...[/red]")
                        continue

                    sub = parts[1].lower()
                    arg = parts[2] if len(parts) == 3 else ""

                    if sub == "add":
                        mission_add(mem, arg)
                    elif sub == "list":
                        mission_list(mem)
                    elif sub == "done":
                        mission_done(mem, arg)
                    elif sub == "clear":
                        mission_clear(mem)
                    else:
                        console.print("[red]Unknown /mission subcommand.[/red]")
                    continue

                if user.startswith("/kb "):
                    parts = user.split(" ", 3)
                    if len(parts) < 2:
                        console.print("[red]Usage: /kb add|list|read|delete ...[/red]")
                        continue

                    sub = parts[1].lower()
                    if sub == "add":
                        if len(parts) < 4:
                            console.print("[red]Usage: /kb add <title> <text>[/red]")
                            continue
                        kb_add(mem, parts[2], parts[3])
                    elif sub == "list":
                        kb_list()
                    elif sub == "read":
                        if len(parts) < 3:
                            console.print("[red]Usage: /kb read <title>[/red]")
                            continue
                        kb_read(parts[2])
                    elif sub == "delete":
                        if len(parts) < 3:
                            console.print("[red]Usage: /kb delete <title>[/red]")
                            continue
                        kb_delete(parts[2])
                    else:
                        console.print("[red]Unknown /kb subcommand.[/red]")
                    continue

                if user.startswith("/search "):
                    search_all(mem, user.split(" ", 1)[1])
                    continue

                if user.startswith("/write "):
                    parts = user.split(" ", 2)
                    if len(parts) < 3:
                        console.print("[red]Usage: /write <file> <content>[/red]")
                        continue
                    file_write(parts[1], parts[2])
                    continue

                if user.startswith("/append "):
                    parts = user.split(" ", 2)
                    if len(parts) < 3:
                        console.print("[red]Usage: /append <file> <content>[/red]")
                        continue
                    file_append(parts[1], parts[2])
                    continue

                if user.startswith("/cat "):
                    file_cat(user.split(" ", 1)[1])
                    continue

                if user == "/ls" or user.startswith("/ls "):
                    path = user[3:].strip() if len(user) > 3 else "."
                    file_ls(path)
                    continue

                # Not a command — route to LLM with streaming
                history = mem.get("chat_history", [])
                response_chunks = []
                prefix = f"[bold]{AGENT_NAME}[/bold]: "
                
                with Live(Text.from_markup(f"{prefix}[dim]thinking...[/dim]"), console=console, refresh_per_second=10, transient=True) as live:
                    for chunk in stream_llm(
                        user,
                        history,
                        mode=mem["mode"],
                        mood=mem["mood"],
                        boost=mem.get("boost", False),
                        operator=mem.get("operator"),
                        network_active=mem.get("network_active", False),
                        openai_mode=mem.get("openai_mode", False)
                    ):
                        response_chunks.append(chunk)
                        current_text = "".join(response_chunks)
                        
                        # Only update if we have content outside <think> blocks
                        display_text = strip_thinking(current_text)
                        
                        if display_text:
                            live.update(Text.from_markup(f"{prefix}{display_text}█"))
                        elif "<think>" in current_text:
                            # Show a pulsing reasoning indicator
                            dots = "." * (int(time.time() * 2) % 4)
                            live.update(Text.from_markup(f"{prefix}[dim]reasoning{dots}[/dim]"))
                        else:
                            live.update(Text.from_markup(f"{prefix}[dim]thinking...[/dim]"))
                
                response = "".join(response_chunks).strip()
                cleaned_response, action_results, new_mood = parse_and_execute_actions(response, mem)
                
                # Update Mood if changed
                if new_mood and new_mood != mem["mood"]:
                    mem["mood"] = new_mood
                    console.print(f"[dim]Mood shifted to: {new_mood}[/dim]")
                
                # Print final clean response
                if cleaned_response:
                    console.print(f"{prefix}{cleaned_response}")
                else: 
                     # If model output nothing but thinking (rare with the new fallback), say something, unless tools ran
                     if "<think>" in response and not action_results:
                         console.print(f"{prefix}[dim]...[/dim]")
                
                for result in action_results:
                    console.print(result)

                # FOLLOW-UP: If actions ran, feed output back to GLTCH for analysis
                if action_results:
                    # Build context with command outputs
                    action_context = "\n".join([r.replace('[', '').replace(']', '') for r in action_results])
                    followup_prompt = (
                        f"SYSTEM: The following is REAL output from a tool you just used. "
                        f"Report ONLY what the data says. Do NOT add action tags. Do NOT re-run actions.\n\n"
                        f"--- TOOL OUTPUT ---\n"
                        f"{action_context}\n"
                        f"--- END OUTPUT ---\n\n"
                        f"Now answer the user's question using ONLY the data above. "
                        f"Do NOT use [ACTION:...] tags in this response. "
                        f"Do NOT make up numbers that aren't in the output. "
                        f"Be brief and natural."
                    )
                    
                    followup_chunks = []
                    with Live(Text.from_markup(f"{prefix}[dim]analyzing output...[/dim]"), console=console, refresh_per_second=10, transient=True) as live:
                        for chunk in stream_llm(
                            followup_prompt,
                            history + [{"role": "assistant", "content": cleaned_response}],
                            mode=mem["mode"],
                            mood=mem["mood"],
                            boost=mem.get("boost", False),
                            operator=mem.get("operator"),
                            network_active=mem.get("network_active", False),
                            openai_mode=mem.get("openai_mode", False)
                        ):
                            followup_chunks.append(chunk)
                            display_text = strip_thinking("".join(followup_chunks))
                            if display_text:
                                live.update(Text.from_markup(f"{prefix}{display_text}█"))
                    
                    followup_response = "".join(followup_chunks).strip()
                    followup_clean = strip_thinking(followup_response)
                    
                    # Strip action/mood tags from follow-up (prevent re-triggering)
                    import re as _re
                    followup_clean = _re.sub(r'\[ACTION:[^\]]*\]', '', followup_clean)
                    followup_clean = _re.sub(r'\[MOOD:\w+\]', '', followup_clean)
                    followup_clean = followup_clean.strip()
                    
                    if followup_clean:
                        console.print(f"{prefix}{followup_clean}")
                        
                        # Verify suggestions before trusting them
                        verification_warnings = verify_suggestions(followup_clean)
                        for warning in verification_warnings:
                            console.print(warning)
                        
                        # Add to history
                        history.append({"role": "assistant", "content": followup_clean})

                # Also verify the initial response if no actions ran
                else:
                    verification_warnings = verify_suggestions(cleaned_response)
                    for warning in verification_warnings:
                        console.print(warning)

                stats = get_last_stats()
                if stats.get("model"):
                    ctx_pct = int((stats["context_used"] / stats["context_max"]) * 100) if stats["context_max"] else 0
                    ctx_bar = "█" * (ctx_pct // 10) + "░" * (10 - ctx_pct // 10)
                    # Get emotional state
                    emo_metrics = get_emotion_metrics()
                    
                    # Resolve Mood UI
                    current_mood = MOOD_UI.get(mem["mood"], MOOD_UI["default"])
                    
                    # Create bars
                    stress_blocks = "█" * (emo_metrics['stress'] // 10)
                    energy_blocks = "█" * (emo_metrics['energy'] // 10)
                    xp_bar = get_progress_bar(mem, width=8)

                    # Color coding
                    stress_color = "green" if emo_metrics['stress'] < 50 else "yellow" if emo_metrics['stress'] < 80 else "red"
                    energy_color = "red" if emo_metrics['energy'] < 20 else "yellow" if emo_metrics['energy'] < 50 else "green"

                    console.print(
                        f"[dim]─ {stats['model']} │ "
                        f"{stats['completion_tokens']}tx │ "
                        f"{stats['tokens_per_sec']}t/s │ "
                        f"Mood: [{current_mood['color']}]{current_mood['emoji']}[/] │ "
                        f"Stress: [{stress_color}]{stress_blocks:<10}[/] │ "
                        f"Energy: [{energy_color}]{energy_blocks:<10}[/] │ "
                        f"{xp_bar}[/dim]"
                    )

                # Dynamic XP reward based on conversation depth
                # Base 2 XP + 1 XP per 50 generated tokens (rewards complex answers)
                chat_xp = 2
                if stats.get("completion_tokens"):
                    chat_xp += int(stats["completion_tokens"] / 50)
                
                add_xp(mem, chat_xp)
                
                history.append({"role": "user", "content": user})
                # Strip <think> blocks before saving to history
                history.append({"role": "assistant", "content": strip_thinking(response)})
                mem["chat_history"] = history[-10:] # Keep last 10 turns
                save_memory(mem)

            except KeyboardInterrupt:
                console.print("\n[dim]Interrupted. Type /exit to quit.[/dim]")
                continue
            except Exception as e:
                console.print(f"[red]Error in main loop: {e}[/red]")

    except KeyboardInterrupt:
        console.print("\n[bold red]GLTCH offline.[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Fatal Error:[/bold red] {str(e).replace('[', '\\[')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
