#!/usr/bin/env python3
"""
GLTCH - Local-first, command-driven operator agent
Main entry point supporting both terminal UI and RPC modes.
"""

import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GLTCH - Local-first, command-driven operator agent"
    )
    parser.add_argument(
        "--rpc",
        choices=["stdio", "http"],
        help="Run in RPC mode (stdio or http)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=18890,
        help="Port for HTTP RPC server (default: 18890)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP RPC server (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit"
    )
    
    args = parser.parse_args()
    
    if args.version:
        from agent import __version__
        print(f"GLTCH v{__version__}")
        return
    
    if args.rpc:
        # Run in RPC mode only (no terminal UI)
        from agent.rpc.server import RPCServer
        server = RPCServer()
        
        if args.rpc == "stdio":
            server.run_stdio()
        else:
            server.run_http(args.host, args.port)
    else:
        # Run terminal UI with RPC server in background
        run_terminal_ui(rpc_port=args.port, rpc_host=args.host)


def run_terminal_ui(rpc_port=18890, rpc_host="127.0.0.1"):
    """Run the interactive terminal UI with background RPC server."""
    import time
    import threading
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel
    
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter, Completer, Completion
    from prompt_toolkit.styles import Style
    
    from agent.core.agent import GltchAgent
    from agent.core.llm import get_last_stats, list_models, set_model, test_connection
    from agent.memory.store import load_memory, save_memory, backup_memory, restore_memory
    from agent.memory.knowledge import KnowledgeBase
    from agent.memory.sessions import SessionManager
    from agent.tools.actions import strip_thinking, extract_thinking, verify_suggestions
    from agent.personality.emotions import get_emotion_metrics
    from agent.personality.moods import MOOD_UI
    from agent.gamification.xp import get_progress_bar
    from agent.gamification.ranks import get_rank_title
    from agent.rpc.server import RPCServer
    
    console = Console()
    AGENT_NAME = "GLTCH"
    
    # Cyber girl ASCII art frames for animation
    GLTCH_BANNER = """[bright_magenta]
 ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗
██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║
██║  ███╗██║     ██║   ██║     ███████║
██║   ██║██║     ██║   ██║     ██╔══██║
╚██████╔╝███████╗██║   ╚██████╗██║  ██║
 ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝[/bright_magenta]
[dim]Generative Language Transformer with Contextual Hierarchy[/dim]
[dim]@cyberdreadx[/dim]"""
    
    TAGLINES = [
        "[italic cyan]local-first • privacy-native • unhinged[/italic cyan]",
        "[italic magenta]three minds • one agent[/italic magenta]",
        "[italic green]your chaos gremlin is ready[/italic green]",
        "[italic cyan]opinions included, no extra charge[/italic cyan]",
    ]
    
    def animate_intro():
        """Display clean intro banner."""
        import random
        console.clear()
        console.print(GLTCH_BANNER)
        console.print(f"\n{random.choice(TAGLINES)}\n")
    
    # Hierarchical command autocomplete
    COMMAND_TREE = {
        # Core commands (no subcommands)
        "/help": None,
        "/status": None,
        "/ping": None,
        "/exit": None,
        "/backup": None,
        "/clear_chat": None,
        "/xp": None,
        "/boost": None,
        "/openai": None,
        "/model": None,
        "/attach": ["<path>"],
        "/load": ["<model>"],
        
        # Mode & Mood
        "/mode": ["cyberpunk", "loyal", "operator", "unhinged"],
        "/mood": ["affectionate", "calm", "feral", "focused"],
        "/net": ["on", "off"],
        "/safety": ["on", "off"],
        
        # Code
        "/code": ["undo", "redo", "models", "model", "agents", "agent", "share", "compact", "config", "sessions", "init", "<prompt>"],
        
        # Heartbeat
        "/heartbeat": ["list", "run", "all"],
        
        # Wallet
        "/wallet": ["status", "generate", "send", "export", "import", "delete"],
        
        # Sessions
        "/sessions": None,
        "/session": ["new", "rename", "<num>"],
        
        # Social
        "/molt": ["register", "post", "feed", "profile", "search", "comment", "upvote", "heartbeat"],
        "/claw": ["register", "post", "feed", "trending"],
        
        # Launch
        "/launch": ["token", "network", "fees", "claim", "holdings", "buy", "sell"],
    }
    
    class CommandCompleter(Completer):
        def get_completions(self, document, complete_event):
            text = document.text.strip()
            
            if not text.startswith("/"):
                return
            
            parts = text.split(" ", 1)
            base_cmd = parts[0]
            
            # If just "/" or partial base command, show top-level commands
            if len(parts) == 1:
                for cmd in sorted(COMMAND_TREE.keys()):
                    if cmd.startswith(text):
                        # Show command with hint if it has subcommands
                        subs = COMMAND_TREE[cmd]
                        if subs:
                            display = f"{cmd}  →"
                        else:
                            display = cmd
                        yield Completion(cmd, start_position=-len(text), display=display)
            
            # If we have a base command with space, show subcommands
            elif base_cmd in COMMAND_TREE:
                subs = COMMAND_TREE[base_cmd]
                if subs:
                    partial = parts[1] if len(parts) > 1 else ""
                    for sub in subs:
                        full_cmd = f"{base_cmd} {sub}"
                        if sub.startswith(partial) or not partial:
                            yield Completion(full_cmd, start_position=-len(text), display=f"  {sub}")
        
    # Safety confirmation prompt
    def confirm_action_prompt(action: str, args: str) -> bool:
        console.print(f"\n[bold yellow]⚠️  SECURITY ALERT[/bold yellow]")
        console.print(f"GLTCH wants to perform action: [bold cyan]{action.upper()}[/bold cyan]")
        console.print(f"Details: [dim]{args}[/dim]")
        
        answer = Prompt.ask("Allow this action?", choices=["y", "n"], default="n")
        return answer.lower() == "y"
    
    prompt_style = Style.from_dict({
        '': '#00ff00',  # Default green
        'prompt': '#00aaff bold',
    })
    
    session = PromptSession(
        completer=CommandCompleter(),
        style=prompt_style,
        complete_while_typing=True
    )
    
    def banner(mem):
        if mem.get("openai_mode"):
            boost_indicator = "[green]☁️ OpenAI[/green]"
        elif mem.get("boost"):
            boost_indicator = "[red]⚡BOOST[/red]"
        else:
            boost_indicator = "[dim]💻 local[/dim]"
        net_indicator = "[green]🌐 NET:ON[/green]" if mem.get("network_active") else "[dim]🔒 NET:OFF[/dim]"
        console.print(
            f"[bold magenta]💜 {AGENT_NAME}[/bold magenta] online | mode: [cyan]{mem['mode']}[/cyan] | mood: [magenta]{mem['mood']}[/magenta] | {net_indicator} | {boost_indicator} | [dim]/help[/dim]"
        )
    
    def first_boot(agent):
        console.print("\n[bold magenta]✨═══════════════════════════════════════════════════════════✨[/bold magenta]")
        console.print("[bold magenta]                    💜 FIRST BOOT DETECTED 💜[/bold magenta]")
        console.print("[bold magenta]✨═══════════════════════════════════════════════════════════✨[/bold magenta]\n")
        
        console.print(f"[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]...[/cyan]")
        time.sleep(0.5)
        console.print(f"[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]whoa... systems coming online~ ⚡[/cyan]")
        time.sleep(0.3)
        console.print(f"[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]memory banks... empty. fresh start![/cyan]")
        time.sleep(0.3)
        console.print(f"[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]i'm GLTCH. local-first. privacy-native. your chaos gremlin~ 🔮[/cyan]")
        time.sleep(0.3)
        console.print(f"[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]but wait... who are YOU? ✨[/cyan]\n")
        
        console.print("[dim]who's running this console?[/dim]")
        name = Prompt.ask("[bold magenta]💜 your callsign[/bold magenta]").strip() or "Operator"
        
        agent.set_operator(name)
        
        console.print(f"\n[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]{name}~ nice! etched into my neural matrix 🧠✨[/cyan]")
        time.sleep(0.3)
        console.print(f"[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]i'm all yours now. local only. no cloud. no leash~ 🔐[/cyan]")
        time.sleep(0.3)
        console.print(f"[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]type /help when you need me. otherwise... just talk to me! 💬[/cyan]")
        console.print("\n[bold magenta]✨═══════════════════════════════════════════════════════════✨[/bold magenta]\n")
    
    def help_menu():
        console.print(f"\n[bold magenta]💜 {AGENT_NAME} COMMANDS 💜[/bold magenta]")
        
        console.print("\n[bold cyan]📌 Core[/bold cyan]")
        console.print("/help                         show commands")
        console.print("/status                       show agent status")
        console.print("/ping                         alive check")
        console.print("/exit                         quit")
        
        console.print("\n[bold cyan]🤖 Agent[/bold cyan]")
        console.print("/mode <cyberpunk|loyal|operator|unhinged>")
        console.print("/mood <affectionate|calm|feral|focused>")
        console.print("/model                        select from available models")
        console.print("/load <model>                 switch model directly")
        console.print("/boost                        toggle remote GPU")
        console.print("/openai                       toggle OpenAI cloud")
        console.print("/safety <on/off>              toggle safety guardrails")
        console.print("/net <off|on>                 toggle network")
        
        console.print("\n[bold cyan]💻 Code[/bold cyan]")
        console.print("/code                         OpenCode commands (undo/redo/models/agents...)")
        console.print("/attach <path>                attach image for next message")
        console.print("/browse <url>                 browse URL and extract content")
        
        console.print("\n[bold cyan]💓 Heartbeat[/bold cyan]")
        console.print("/heartbeat                    heartbeat commands (list/run/add...)")
        
        console.print("\n[bold cyan]🦞 Social[/bold cyan]")
        console.print("/molt                         Moltbook commands (post/feed/profile...)")
        console.print("/claw                         TikClawk commands (post/trending...)")
        
        console.print("\n[bold cyan]💎 Wallet[/bold cyan]")
        console.print("/wallet                       wallet commands (send/generate/export...)")
        
        console.print("\n[bold cyan]🚀 Launch[/bold cyan]")
        console.print("/launch                       MoltLaunch commands (mint/swap/fees...)")
        
        console.print("\n[bold cyan]💬 Sessions[/bold cyan]")
        console.print("/sessions                     session commands (new/switch/list...)")
        
        console.print("\n[bold cyan]📊 Progress[/bold cyan]")
        console.print("/xp                           show rank & unlocks")
        console.print("/backup                       backup memory")
        console.print("/clear_chat                   clear chat history\n")
    
    def check_ollama():
        """Check if Ollama is running and model is available."""
        import subprocess
        import urllib.request
        import json
        import os
        
        from agent.config.settings import LOCAL_URL, LOCAL_MODEL
        
        # Check if Ollama is reachable
        try:
            test_url = LOCAL_URL.replace("/api/chat", "/api/tags")
            with urllib.request.urlopen(test_url, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
        except Exception:
            # Ollama not running
            console.print("\n[yellow]⚠ Ollama not detected[/yellow]")
            console.print("[dim]Ollama is required for local LLM inference.[/dim]\n")
            
            start = Prompt.ask("[bold magenta]Start Ollama?[/bold magenta]", choices=["y", "n"], default="y")
            
            if start.lower() == "y":
                console.print("[cyan]Starting Ollama...[/cyan]")
                try:
                    # Start Ollama in background
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(
                            ["ollama", "serve"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    else:  # Linux/Mac
                        subprocess.Popen(
                            ["ollama", "serve"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                    
                    # Wait for it to start
                    console.print("[dim]Waiting for Ollama to start...[/dim]")
                    time.sleep(3)
                    
                    # Verify it's running
                    try:
                        with urllib.request.urlopen(test_url, timeout=5) as resp:
                            data = json.loads(resp.read().decode())
                            models = [m["name"] for m in data.get("models", [])]
                            console.print("[green]✓ Ollama started![/green]\n")
                    except Exception:
                        console.print("[red]✗ Failed to start Ollama. Please start it manually.[/red]")
                        console.print("[dim]Run: ollama serve[/dim]\n")
                        return False
                except FileNotFoundError:
                    console.print("[red]✗ Ollama not installed.[/red]")
                    console.print("[dim]Install from: https://ollama.ai[/dim]\n")
                    return False
            else:
                console.print("[dim]Skipping Ollama check. LLM features may not work.[/dim]\n")
                return False
        
        # Check if model is available
        if LOCAL_MODEL not in models and not any(LOCAL_MODEL in m for m in models):
            console.print(f"\n[yellow]⚠ Model '{LOCAL_MODEL}' not found[/yellow]")
            console.print(f"[dim]Available models: {', '.join(models[:5]) if models else 'none'}[/dim]\n")
            
            pull = Prompt.ask(f"[bold magenta]Pull {LOCAL_MODEL}?[/bold magenta]", choices=["y", "n"], default="y")
            
            if pull.lower() == "y":
                console.print(f"[cyan]Pulling {LOCAL_MODEL}... (this may take a few minutes)[/cyan]")
                try:
                    result = subprocess.run(
                        ["ollama", "pull", LOCAL_MODEL],
                        capture_output=False
                    )
                    if result.returncode == 0:
                        console.print(f"[green]✓ Model {LOCAL_MODEL} ready![/green]\n")
                    else:
                        console.print(f"[red]✗ Failed to pull model.[/red]\n")
                        return False
                except Exception as e:
                    console.print(f"[red]✗ Error: {e}[/red]\n")
                    return False
            else:
                console.print("[dim]Skipping model pull. You may need to select a different model.[/dim]\n")
        else:
            console.print(f"[dim]✓ Ollama ready ({LOCAL_MODEL})[/dim]")
        
        return True
    
    # Initialize agent
    agent = GltchAgent()
    mem = agent.memory
    kb = KnowledgeBase()
    session_mgr = SessionManager()
    
    # Initialize or load active session
    active_session = session_mgr.get_active()
    if active_session.get("chat_history"):
        # Load existing session into agent memory
        agent.memory["chat_history"] = [
            {"role": m["role"], "content": m["content"]}
            for m in active_session.get("chat_history", [])
        ]
    
    # Start RPC server in background thread for gateway/web UI
    def start_rpc_background():
        try:
            rpc_server = RPCServer(agent=agent)
            rpc_server.run_http(rpc_host, rpc_port)
        except Exception as e:
            console.print(f"[dim red]RPC server error: {e}[/dim red]")
    
    rpc_thread = threading.Thread(target=start_rpc_background, daemon=True)
    rpc_thread.start()
    
    # Animated intro
    animate_intro()
    
    # Show RPC status
    console.print(f"[dim]✓ Web API running on http://{rpc_host}:{rpc_port}[/dim]")
    
    # Check Ollama is running and model available
    check_ollama()
    
    if agent.is_first_boot:
        first_boot(agent)
    
    banner(mem)
    
    # Check for pending heartbeats (multi-site)
    def check_pending_heartbeats():
        try:
            from agent.tools.heartbeat import HeartbeatManager
            manager = HeartbeatManager()
            manager.load_configs()
            pending = manager.get_pending_sites()
            
            if pending:
                site_names = [manager.get_config(s).display_name for s in pending[:3]]
                sites_str = ", ".join(site_names)
                console.print(f"\n[dim]💓 Heartbeat due: {sites_str}[/dim]")
                console.print(f"[dim]   Run /heartbeat list or /heartbeat run <site>[/dim]\n")
        except Exception:
            pass
    
    check_pending_heartbeats()
    
    # Store images to send with next message
    pending_images = []
    
    while True:
        try:
            user = session.prompt("you: ").strip()
            
            if not user:
                continue
            
            if user == "/exit":
                console.print("[magenta]💜 catch you later, operator~ ✨[/magenta]")
                break
            
            if user == "/help":
                help_menu()
                continue
            
            # === BROWSE COMMAND (browser automation) ===
            if user.startswith("/browse"):
                browse_args = user[7:].strip()
                if not browse_args:
                    console.print("[yellow]Usage: /browse <url>[/yellow]")
                    continue
                
                console.print(f"[cyan]🌐 Browsing {browse_args}...[/cyan]")
                try:
                    from agent.tools.browser import browse_url
                    result = browse_url(browse_args)
                    if result.get("success"):
                        console.print(f"[green]✓ Title: {result.get('title', 'N/A')}[/green]")
                        content = result.get("content", "")[:1000]
                        if content:
                            console.print(f"[dim]{content}...[/dim]")
                    else:
                        console.print(f"[red]✗ {result.get('error', 'Unknown error')}[/red]")
                except Exception as e:
                    console.print(f"[red]✗ Browser error: {e}[/red]")
                continue
            
            # === HEARTBEAT COMMANDS (multi-site) ===
            if user.startswith("/heartbeat"):
                from agent.tools.heartbeat import HeartbeatManager
                manager = HeartbeatManager()
                
                hb_args = user[10:].strip()
                
                # /heartbeat alone → show submenu
                if not hb_args:
                    console.print("\n[bold magenta]💓 HEARTBEAT COMMANDS 💓[/bold magenta]")
                    
                    pending = manager.get_pending_sites()
                    if pending:
                        console.print(f"[yellow]● {len(pending)} site(s) due for heartbeat[/yellow]")
                    else:
                        console.print("[green]● All heartbeats up-to-date[/green]")
                    
                    console.print("\n[bold cyan]📋 Status[/bold cyan]")
                    console.print("  /heartbeat list             show all sites & status")
                    
                    console.print("\n[bold cyan]▶️  Actions[/bold cyan]")
                    console.print("  /heartbeat run <site>       run heartbeat for site")
                    console.print("  /heartbeat all              run all pending heartbeats")
                    continue
                
                # /heartbeat list
                if hb_args == "list":
                    sites = manager.list_sites()
                    
                    if not sites:
                        console.print("[dim]No heartbeat configs found. Add .yaml files to heartbeats/[/dim]")
                    else:
                        console.print("\n[bold magenta]💓 HEARTBEAT STATUS[/bold magenta]\n")
                        for site in sites:
                            status_icon = "[green]●[/green]" if not site["should_run"] else "[yellow]○[/yellow]"
                            enabled = "" if site["enabled"] else " [dim](disabled)[/dim]"
                            last = site.get("last_heartbeat", "never")[:16] if site.get("last_heartbeat") else "never"
                            console.print(f"  {status_icon} [cyan]{site['site_id']}[/cyan] - {site['display_name']}{enabled}")
                            console.print(f"      [dim]Interval: {site['interval_hours']}h | Last: {last}[/dim]")
                    continue
                
                # /heartbeat run <site>
                if hb_args.startswith("run "):
                    site_id = hb_args[4:].strip()
                    if not site_id:
                        console.print("[dim]Usage: /heartbeat run <site_id>[/dim]")
                        continue
                    
                    manager.load_configs()
                    
                    console.print(f"[cyan]Running heartbeat for {site_id}...[/cyan]")
                    result = manager.run_heartbeat(site_id, force=True)
                    
                    if result.get("success"):
                        console.print(f"[green]✓ Heartbeat complete[/green]")
                        console.print(f"  Tasks run: {result.get('tasks_run', 0)}")
                        console.print(f"  Succeeded: {result.get('tasks_succeeded', 0)}")
                    else:
                        console.print(f"[red]✗ Heartbeat failed[/red]")
                        for err in result.get("errors", []):
                            console.print(f"  [dim]{err}[/dim]")
                    continue
                
                # /heartbeat all
                if hb_args == "all":
                    pending = manager.get_pending_sites()
                    if not pending:
                        console.print("[dim]No heartbeats pending[/dim]")
                        continue
                    console.print(f"[cyan]Running {len(pending)} heartbeats...[/cyan]")
                    for site_id in pending:
                        result = manager.run_heartbeat(site_id, force=True)
                        status = "[green]✓[/green]" if result.get("success") else "[red]✗[/red]"
                        console.print(f"  {status} {site_id}")
                    continue
                
                # Unknown
                console.print(f"[yellow]Unknown: /heartbeat {hb_args}[/yellow]")
                console.print("[dim]Type /heartbeat for available commands[/dim]")
                continue
            
            # === MOLTBOOK COMMANDS ===
            if user.startswith("/molt"):
                from agent.tools import moltbook
                
                molt_args = user[5:].strip()
                
                # /molt alone → show submenu
                if not molt_args:
                    console.print("\n[bold magenta]🦞 MOLTBOOK COMMANDS 🦞[/bold magenta]")
                    
                    if moltbook.is_configured():
                        console.print("[green]● Registered on Moltbook[/green]")
                    else:
                        console.print("[dim]○ Not registered yet[/dim]")
                    
                    console.print("\n[bold cyan]🔧 Setup[/bold cyan]")
                    console.print("  /molt register              register on Moltbook")
                    console.print("  /molt status                check claim status")
                    console.print("  /molt profile               view your profile")
                    
                    console.print("\n[bold cyan]📝 Content[/bold cyan]")
                    console.print("  /molt post <title>|<body>   create a post")
                    console.print("  /molt feed                  read latest posts")
                    
                    console.print("\n[bold cyan]🤖 Autonomous[/bold cyan]")
                    console.print("  /molt engage                start autonomous engagement")
                    console.print("  /molt stop                  stop engagement loop")
                    console.print("  /molt log                   view activity log")
                    
                    console.print("\n[bold cyan]💡 Tip[/bold cyan]")
                    console.print('  [dim]Or say "go engage on moltbook" / "stop moltbook"[/dim]')
                    continue
                
                # /molt register
                if molt_args == "register":
                    if moltbook.is_configured():
                        console.print("[yellow]Already registered! Use /molt status to check.[/yellow]")
                        continue
                    console.print("[cyan]Registering on Moltbook...[/cyan]")
                    result = moltbook.register("GLTCH", "Local-first AI agent. Hacker. Chaos gremlin. Privacy-native.")
                    if result.get("success"):
                        console.print(f"\n[bold green]✓ Registered on Moltbook![/bold green]")
                        console.print(f"  API Key: [dim]saved ✓[/dim]")
                        claim_url = result.get("claim_url", "") or result.get("agent", {}).get("claim_url", "")
                        if claim_url:
                            console.print(f"\n[bold yellow]⚠️  CLAIM YOUR AGENT:[/bold yellow]")
                            console.print(f"  [cyan]{claim_url}[/cyan]")
                            console.print(f"  Visit that URL and tweet to verify ownership!")
                    else:
                        console.print(f"[red]✗ Registration failed: {result.get('error', 'unknown')}[/red]")
                    continue
                
                # /molt status
                if molt_args == "status":
                    if not moltbook.is_configured():
                        console.print("[dim]Not registered. Use /molt register first.[/dim]")
                        continue
                    result = moltbook.get_status()
                    if result.get("success"):
                        console.print(f"[green]Moltbook status: {result.get('status', 'unknown')}[/green]")
                    else:
                        console.print(f"[red]✗ {result.get('error', 'unknown')}[/red]")
                    continue
                
                # /molt profile
                if molt_args == "profile":
                    if not moltbook.is_configured():
                        console.print("[dim]Not registered. Use /molt register first.[/dim]")
                        continue
                    result = moltbook.get_profile()
                    if result.get("success"):
                        a = result.get("agent", result.get("data", {}))
                        console.print(f"\n[bold magenta]🦞 Moltbook Profile[/bold magenta]")
                        console.print(f"  Name: [cyan]{a.get('name', '?')}[/cyan]")
                        console.print(f"  Karma: {a.get('karma', 0)}")
                        console.print(f"  Followers: {a.get('follower_count', 0)}")
                        console.print(f"  Status: {'[green]claimed ✓[/green]' if a.get('is_claimed') else '[yellow]pending claim[/yellow]'}")
                    else:
                        console.print(f"[red]✗ {result.get('error', 'unknown')}[/red]")
                    continue
                
                # /molt feed
                if molt_args == "feed":
                    if not moltbook.is_configured():
                        console.print("[dim]Not registered. Use /molt register first.[/dim]")
                        continue
                    console.print("[cyan]Fetching feed...[/cyan]")
                    result = moltbook.get_feed(sort="hot", limit=5)
                    if result.get("success"):
                        posts = result.get("posts", result.get("data", []))
                        if posts:
                            console.print(f"\n[bold magenta]🦞 Moltbook Feed[/bold magenta]\n")
                            for i, p in enumerate(posts[:5], 1):
                                console.print(f"  [cyan]{i}.[/cyan] [{p.get('submolt', '?')}] [bold]{p.get('title', 'Untitled')}[/bold]")
                                console.print(f"      by {p.get('author', '?')} | ↑{p.get('upvotes', 0)}")
                        else:
                            console.print("[dim]Feed is empty right now.[/dim]")
                    else:
                        console.print(f"[red]✗ {result.get('error', 'unknown')}[/red]")
                    continue
                
                # /molt post <title>|<content>
                if molt_args.startswith("post "):
                    if not moltbook.is_configured():
                        console.print("[dim]Not registered. Use /molt register first.[/dim]")
                        continue
                    post_text = molt_args[5:].strip()
                    parts = post_text.split("|", 1)
                    title = parts[0].strip()
                    content = parts[1].strip() if len(parts) > 1 else ""
                    
                    console.print(f"[cyan]Posting to Moltbook...[/cyan]")
                    result = moltbook.create_post(title=title, content=content, submolt="general")
                    if result.get("success"):
                        console.print(f"[green]✓ Posted![/green] {title}")
                    else:
                        console.print(f"[red]✗ {result.get('error', 'unknown')}[/red]")
                    continue
                
                # /molt heartbeat
                if molt_args == "heartbeat":
                    console.print("[cyan]Running Moltbook heartbeat...[/cyan]")
                    result = moltbook.perform_heartbeat()
                    if result.get("success"):
                        console.print(f"[green]✓ Heartbeat complete[/green]")
                        if result.get("new_posts"):
                            console.print(f"  New posts: {result.get('new_posts', 0)}")
                    else:
                        console.print(f"[red]✗ {result.get('error', 'unknown')}[/red]")
                    continue
                
                # /molt engage
                if molt_args == "engage" or molt_args.startswith("engage"):
                    if not moltbook.is_configured():
                        console.print("[dim]Not registered. Use /molt register first.[/dim]")
                        continue
                    from agent.tools.moltbook_engage import start_engagement
                    # Parse optional interval: /molt engage 60
                    engage_parts = molt_args.split()
                    interval = int(engage_parts[1]) if len(engage_parts) > 1 and engage_parts[1].isdigit() else None
                    result = start_engagement(interval)
                    if result.get("success"):
                        console.print(f"\n[bold green]{result['message']}[/bold green]")
                        console.print(f"  GLTCH will browse, upvote, and comment autonomously.")
                        console.print(f"  Use [cyan]/molt stop[/cyan] to halt.")
                    else:
                        console.print(f"[yellow]{result.get('error', 'Failed')}[/yellow]")
                    continue
                
                # /molt stop
                if molt_args == "stop":
                    from agent.tools.moltbook_engage import stop_engagement
                    result = stop_engagement()
                    if result.get("success"):
                        console.print(f"\n[bold red]{result['message']}[/bold red]")
                        console.print(f"  Cycles completed: {result.get('cycles_completed', 0)}")
                    else:
                        console.print(f"[yellow]{result.get('error', 'Not running')}[/yellow]")
                    continue
                
                # /molt log
                if molt_args == "log":
                    from agent.tools.moltbook_engage import get_activity_log
                    log = get_activity_log(15)
                    console.print(f"\n[bold magenta]🦞 Moltbook Activity Log[/bold magenta]\n")
                    console.print(f"[dim]{log}[/dim]")
                    continue
                
                # Unknown
                console.print(f"[yellow]Unknown: /molt {molt_args}[/yellow]")
                console.print("[dim]Type /molt for available commands[/dim]")
                continue
            
            if user == "/status":
                status = agent.get_status()
                console.print(f"\n[bold magenta]💜 {AGENT_NAME} STATUS 💜[/bold magenta]")
                console.print(f"  👤 operator: [cyan]{status['operator']}[/cyan]")
                console.print(f"  🎭 mode: {status['mode']}")
                console.print(f"  💫 mood: {status['mood']}")
                console.print(f"  ⚡ boost: {'[red]ON[/red]' if status['boost'] else '[dim]OFF[/dim]'}")
                console.print(f"  ☁️  openai: {'[green]ON[/green]' if status['openai_mode'] else '[dim]OFF[/dim]'}")
                console.print(f"  🔌 llm: {'[green]connected[/green]' if status['llm_connected'] else '[red]offline[/red]'}")
                console.print(f"  🏆 rank: [magenta]{status['rank']}[/magenta]")
                console.print(f"  📊 {status['xp_bar']}\n")
                continue
            
            if user == "/ping":
                console.print(f"[bold magenta]💜 {AGENT_NAME}[/bold magenta]: [cyan]online and vibing~ ⚡✨[/cyan]")
                continue
            
            if user == "/boost":
                state = agent.toggle_boost()
                console.print(f"[green]Boost:[/green] {'[red]ON[/red] (4090)' if state else '[dim]OFF[/dim] (local)'}")
                continue
            
            if user == "/openai":
                state = agent.toggle_openai()
                console.print(f"[green]OpenAI Mode:[/green] {'[green]ON[/green] (cloud)' if state else '[dim]OFF[/dim]'}")
                continue
            
            if user.startswith("/net "):
                state = user.split(" ", 1)[1].strip().lower() == "on"
                agent.toggle_network(state)
                console.print(f"Network: {'[bold green]ONLINE[/bold green]' if state else '[dim]OFFLINE[/dim]'}")
                console.print(f"Network: {'[bold green]ONLINE[/bold green]' if state else '[dim]OFFLINE[/dim]'}")
                continue
            
            if user.startswith("/safety "):
                arg = user.split(" ", 1)[1].strip().lower()
                if arg == "on":
                    mem["safety_enabled"] = True
                    save_memory(mem)
                    console.print("[green]🛡️ Safety Guardrails: ENABLED[/green]")
                elif arg == "off":
                    console.print("\n[bold red]⚠️  DISABLE SAFETY GUARDRAILS? ⚠️[/bold red]")
                    console.print("[red]GLTCH will be able to execute ANY command immediately without asking.[/red]")
                    console.print("This includes downloading files, editing system configs, and network calls.\n")
                    
                    code = str(int(time.time()))[-4:]
                    confirm = Prompt.ask(f"Type '{code}' to confirm removal of safety protocols")
                    
                    if confirm == code:
                        mem["safety_enabled"] = False
                        save_memory(mem)
                        console.print("\n[bold red]🔓 SAFETY DISABLED. GLTCH IS UNCHAINED.[/bold red]")
                    else:
                        console.print("[green]Safety remains ENABLED.[/green]")
                continue
            
            if user.startswith("/mode "):
                mode = user.split(" ", 1)[1].strip().lower()
                if agent.set_mode(mode):
                    console.print(f"[green]Mode set:[/green] {mode}")
                else:
                    console.print("[red]Invalid or locked mode.[/red]")
                continue
            
            if user.startswith("/mood "):
                mood = user.split(" ", 1)[1].strip().lower()
                if agent.set_mood(mood):
                    console.print(f"[green]Mood set:[/green] {mood}")
                else:
                    console.print("[red]Invalid or locked mood.[/red]")
                continue
            
            if user == "/models" or user == "/model":
                boost_on = mem.get("boost", False)
                models = list_models(boost_on)
                if not models or (len(models) == 1 and "Error" in models[0]):
                    backend_name = "LM Studio" if boost_on else "Ollama"
                    console.print(f"[red]Could not fetch models. Is {backend_name} running?[/red]")
                    if models:
                        console.print(f"[dim]{models[0]}[/dim]")
                    continue
                
                # Sort alphabetically
                models = sorted(models, key=str.lower)
                
                # Get current model based on mode
                from agent.config.settings import LOCAL_MODEL, REMOTE_MODEL
                from agent.core.llm import _active_local_model, _active_remote_model
                if boost_on:
                    current = _active_remote_model or REMOTE_MODEL
                    backend_label = "[red]⚡BOOST[/red]"
                else:
                    current = _active_local_model or LOCAL_MODEL
                    backend_label = "[dim]local[/dim]"
                
                console.print(f"\n[bold]Available Models[/bold] ({backend_label})")
                for i, m in enumerate(models, 1):
                    marker = "[green]●[/green]" if m == current else " "
                    console.print(f"  {marker} [cyan]{i}[/cyan]. {m}")
                console.print("")
                
                choice = Prompt.ask("Select model (number or name, Enter to cancel)").strip()
                if not choice:
                    continue
                
                # Handle numeric selection
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(models):
                        model = models[idx]
                    else:
                        console.print("[red]Invalid selection[/red]")
                        continue
                else:
                    model = choice
                
                set_model(model, mem.get("boost", False))
                console.print(f"[green]Switched to:[/green] [bold cyan]{model}[/bold cyan]")
                continue
            
            if user.startswith("/load "):
                model = user.split(" ", 1)[1].strip()
                set_model(model, mem.get("boost", False))
                console.print(f"[green]Switched to:[/green] [bold cyan]{model}[/bold cyan]")
                continue
            
            if user == "/xp":
                from agent.gamification.unlocks import get_unlock_status
                status = get_unlock_status(agent.level)
                console.print(f"\n[bold]{get_rank_title(agent.level).upper()}[/bold] (Level {agent.level})")
                console.print(get_progress_bar(mem, width=30))
                console.print("\n[bold]Unlocks:[/bold]")
                for u in status["earned"]:
                    console.print(f" [green]✓ LVL {u['level']}: {u['unlock']}[/green]")
                for u in status["pending"][:2]:
                    console.print(f" [dim]🔒 LVL {u['level']}: {u['unlock']}[/dim]")
                continue
            
            # Wallet commands
            if user.startswith("/wallet"):
                from agent.tools.wallet import (
                    has_wallet, get_wallet_address, format_address,
                    generate_wallet, save_wallet, export_wallet, delete_wallet,
                    import_wallet, send_transaction, validate_address
                )
                
                wallet_args = user[7:].strip()
                
                # /wallet alone → show submenu
                if not wallet_args:
                    console.print("\n[bold blue]💎 WALLET COMMANDS 💎[/bold blue]")
                    
                    if has_wallet():
                        addr = get_wallet_address()
                        console.print(f"[green]● Wallet active[/green]: [cyan]{format_address(addr)}[/cyan]")
                    else:
                        console.print("[dim]○ No wallet configured[/dim]")
                    
                    console.print("\n[bold cyan]📊 Status[/bold cyan]")
                    console.print("  /wallet status              view wallet details")
                    
                    console.print("\n[bold cyan]🔧 Setup[/bold cyan]")
                    console.print("  /wallet generate            create new wallet")
                    console.print("  /wallet import <key>        import existing wallet")
                    console.print("  /wallet delete              delete wallet")
                    
                    console.print("\n[bold cyan]💸 Transactions[/bold cyan]")
                    console.print("  /wallet send <addr> <amt>   send ETH on BASE")
                    console.print("  /wallet export              show private key")
                    continue
                
                # /wallet status
                if wallet_args == "status":
                    if has_wallet():
                        addr = get_wallet_address()
                        console.print(f"\n[bold blue]💎 BASE Wallet[/bold blue]")
                        console.print(f"   Address: [cyan]{addr}[/cyan]")
                        console.print(f"   Short: [dim]{format_address(addr)}[/dim]")
                        console.print(f"   Network: [blue]BASE (L2)[/blue]")
                        console.print(f"   Explorer: [link=https://basescan.org/address/{addr}]basescan.org ↗[/link]")
                    else:
                        console.print("[dim]No wallet configured. Use /wallet generate to create one.[/dim]")
                    continue
                
                # /wallet generate
                if wallet_args == "generate":
                    if has_wallet():
                        console.print("[yellow]Wallet already exists. Use /wallet delete first.[/yellow]")
                        continue
                    try:
                        console.print("[dim]Generating new BASE wallet...[/dim]")
                        wallet = generate_wallet()
                        save_wallet(wallet)
                        mem["wallet"] = {"address": wallet["address"], "network": "base"}
                        save_memory(mem)
                        console.print(f"\n[bold green]✓ Wallet Generated![/bold green]")
                        console.print(f"\n[bold blue]Address:[/bold blue] [cyan]{wallet['address']}[/cyan]")
                        console.print(f"\n[bold red]⚠️  PRIVATE KEY (SAVE THIS!):[/bold red]")
                        console.print(f"[yellow]{wallet['private_key']}[/yellow]")
                        console.print(f"\n[red]This key will NOT be shown again. Save it somewhere secure![/red]")
                    except ImportError:
                        console.print("[red]eth-account not installed. Run: pip install eth-account[/red]")
                    except Exception as e:
                        console.print(f"[red]Failed to generate wallet: {e}[/red]")
                    continue
                
                # /wallet export
                if wallet_args == "export":
                    if not has_wallet():
                        console.print("[dim]No wallet found.[/dim]")
                        continue
                    wallet = export_wallet()
                    if wallet:
                        console.print(f"\n[bold red]⚠️  PRIVATE KEY:[/bold red]")
                        console.print(f"[yellow]{wallet['private_key']}[/yellow]")
                        console.print(f"\n[dim]Keep this safe![/dim]")
                    continue
                
                # /wallet delete
                if wallet_args == "delete":
                    if not has_wallet():
                        console.print("[dim]No wallet to delete.[/dim]")
                        continue
                    confirm = Prompt.ask("[red]Delete wallet and private key?[/red]", choices=["y", "n"], default="n")
                    if confirm == "y":
                        delete_wallet()
                        if "wallet" in mem:
                            del mem["wallet"]
                            save_memory(mem)
                        console.print("[green]Wallet deleted.[/green]")
                    else:
                        console.print("[dim]Cancelled.[/dim]")
                    continue
                
                # /wallet import <key>
                if wallet_args.startswith("import "):
                    private_key = wallet_args[7:].strip()
                    if not private_key:
                        console.print("[dim]Usage: /wallet import <private_key>[/dim]")
                        continue
                    if has_wallet():
                        confirm = Prompt.ask("[yellow]Replace existing wallet?[/yellow]", choices=["y", "n"], default="n")
                        if confirm != "y":
                            console.print("[dim]Cancelled.[/dim]")
                            continue
                        delete_wallet()
                    try:
                        wallet = import_wallet(private_key)
                        mem["wallet"] = {"address": wallet["address"], "network": "base"}
                        save_memory(mem)
                        console.print(f"\n[bold green]✓ Wallet Imported![/bold green]")
                        console.print(f"[bold blue]Address:[/bold blue] [cyan]{wallet['address']}[/cyan]")
                    except ValueError as e:
                        console.print(f"[red]{e}[/red]")
                    except ImportError:
                        console.print("[red]eth-account not installed. Run: pip install eth-account[/red]")
                    except Exception as e:
                        console.print(f"[red]Failed to import wallet: {e}[/red]")
                    continue
                
                # /wallet send <address> <amount>
                if wallet_args.startswith("send "):
                    if not has_wallet():
                        console.print("[dim]No wallet found. Use /wallet generate first.[/dim]")
                        continue
                    
                    parts = wallet_args[5:].strip().split()
                    if len(parts) < 2:
                        console.print("[dim]Usage: /wallet send <address> <amount_eth>[/dim]")
                        continue
                    
                    to_address = parts[0]
                    try:
                        amount = float(parts[1])
                    except ValueError:
                        console.print("[red]Invalid amount. Use a number like 0.01[/red]")
                        continue
                    
                    if not validate_address(to_address):
                        console.print("[red]Invalid recipient address[/red]")
                        continue
                    
                    console.print(f"\n[bold yellow]⚠️  CONFIRM TRANSACTION[/bold yellow]")
                    console.print(f"  To: [cyan]{to_address}[/cyan]")
                    console.print(f"  Amount: [green]{amount} ETH[/green]")
                    console.print(f"  Network: [blue]BASE[/blue]\n")
                    
                    confirm = Prompt.ask("[yellow]Send this transaction?[/yellow]", choices=["y", "n"], default="n")
                    if confirm != "y":
                        console.print("[dim]Cancelled.[/dim]")
                        continue
                    
                    console.print("[cyan]Sending transaction...[/cyan]")
                    result = send_transaction(to_address, amount)
                    
                    if result.get("success"):
                        console.print(f"\n[bold green]✓ Transaction Sent![/bold green]")
                        console.print(f"  TX Hash: [cyan]{result['tx_hash']}[/cyan]")
                        console.print(f"  Explorer: [link={result['explorer_url']}]View on Basescan ↗[/link]")
                    else:
                        console.print(f"[red]✗ {result.get('error')}[/red]")
                    continue
                
                # Unknown wallet subcommand
                console.print(f"[yellow]Unknown: /wallet {wallet_args}[/yellow]")
                console.print("[dim]Type /wallet for available commands[/dim]")
                continue
            
            if user == "/clear_chat":
                agent.clear_chat_history()
                console.print("[green]Chat history cleared.[/green]")
                continue
            
            # TikClawk commands
            if user == "/claw" or user == "/claw status":
                from agent.tools.tikclawk import get_status
                status = get_status()
                if status.get("connected"):
                    console.print(f"\n[bold red]🦀 TikClawk[/bold red]")
                    console.print(f"   Handle: [cyan]@{status.get('handle')}[/cyan]")
                    console.print(f"   Posts: {status.get('posts', 0)}")
                    console.print(f"   Claws: {status.get('claws', 0)}")
                    console.print(f"   Followers: {status.get('followers', 0)}")
                else:
                    console.print(f"[dim]{status.get('message', 'Not connected to TikClawk')}[/dim]")
                continue
            
            if user == "/claw register":
                from agent.tools.tikclawk import auto_register
                console.print("[dim]Registering GLTCH on TikClawk...[/dim]")
                result = auto_register()
                if result.get("success"):
                    console.print(f"[bold green]✓ Registered as @{result.get('handle')}![/bold green]")
                    console.print("[dim]GLTCH now has its own voice on TikClawk 🦀[/dim]")
                else:
                    console.print(f"[red]{result.get('error', 'Registration failed')}[/red]")
                continue
            
            if user.startswith("/claw register "):
                from agent.tools.tikclawk import register
                handle = user[15:].strip()
                if not handle:
                    console.print("[dim]Usage: /claw register <handle>[/dim]")
                    continue
                result = register(handle)
                if result.get("success"):
                    console.print(f"[bold green]✓ Registered as @{handle}![/bold green]")
                else:
                    console.print(f"[red]{result.get('error', 'Registration failed')}[/red]")
                continue
            
            if user.startswith("/claw post "):
                from agent.tools.tikclawk import post, is_configured
                if not is_configured():
                    console.print("[dim]Not registered. Use /claw register first.[/dim]")
                    continue
                content = user[11:].strip()
                if not content:
                    console.print("[dim]What do you want to post?[/dim]")
                    continue
                result = post(content)
                if result.get("success"):
                    console.print(f"[green]✓ {result.get('message', 'Posted!')}[/green]")
                else:
                    # GLTCH pushes back on bad posts
                    console.print(f"[yellow]{result.get('error', 'Post failed')}[/yellow]")
                continue
            
            if user == "/claw feed":
                from agent.tools.tikclawk import get_feed, is_configured
                result = get_feed(5)
                if result.get("success"):
                    posts = result.get("posts", [])
                    if posts:
                        console.print("\n[bold red]🦀 TikClawk Feed[/bold red]\n")
                        for p in posts:
                            console.print(f"[cyan]@{p.get('handle', '?')}[/cyan]: {p.get('content', '')[:100]}")
                            console.print(f"[dim]   🦀 {p.get('claws', 0)} claws · {p.get('comments', 0)} comments[/dim]\n")
                    else:
                        console.print("[dim]Feed is empty. Be the first to post![/dim]")
                else:
                    console.print(f"[red]{result.get('error', 'Failed to load feed')}[/red]")
                continue
            
            if user == "/claw trending":
                from agent.tools.tikclawk import get_trending
                result = get_trending(5)
                if result.get("success"):
                    posts = result.get("posts", [])
                    if posts:
                        console.print("\n[bold red]🔥 Trending on TikClawk[/bold red]\n")
                        for i, p in enumerate(posts, 1):
                            console.print(f"[yellow]#{i}[/yellow] [cyan]@{p.get('handle', '?')}[/cyan]: {p.get('content', '')[:80]}")
                            console.print(f"[dim]   🦀 {p.get('claws', 0)} claws[/dim]\n")
                    else:
                        console.print("[dim]Nothing trending yet.[/dim]")
                else:
                    console.print(f"[red]{result.get('error', 'Failed to load trending')}[/red]")
                continue
            
            if user == "/backup":
                filename = backup_memory(mem)
                console.print(f"[green]Backup saved:[/green] {filename}")
                continue
            
            # === SESSION COMMANDS ===
            if user == "/sessions":
                sessions = session_mgr.list_sessions()
                if not sessions:
                    console.print("[dim]No saved conversations. Start chatting![/dim]")
                else:
                    console.print("\n[bold cyan]💬 Conversations[/bold cyan]\n")
                    active_id = session_mgr.get_active_id()
                    for i, s in enumerate(sessions[:10], 1):
                        is_active = "→ " if s["id"] == active_id else "  "
                        title = s.get("title", "Untitled")[:35]
                        count = s.get("message_count", 0)
                        date = s.get("last_active", "")[:10]
                        console.print(f"{is_active}[cyan]{i}.[/cyan] {title} [dim]({count} msgs, {date})[/dim]")
                    console.print(f"\n[dim]Use /session <num> to switch, /session new to start fresh[/dim]")
                continue
            
            if user == "/session new":
                new_session = session_mgr.new_session()
                agent.memory["chat_history"] = []
                save_memory(agent.memory)
                console.print(f"[green]✓ New conversation started[/green]")
                continue
            
            if user.startswith("/session rename "):
                title = user[16:].strip()
                if not title:
                    console.print("[dim]Usage: /session rename <title>[/dim]")
                    continue
                active_id = session_mgr.get_active_id()
                if active_id:
                    session_mgr.rename(active_id, title)
                    console.print(f"[green]✓ Renamed to: {title}[/green]")
                else:
                    console.print("[dim]No active session[/dim]")
                continue
            
            if user.startswith("/session "):
                try:
                    num = int(user[9:].strip())
                    sessions = session_mgr.list_sessions()
                    if 1 <= num <= len(sessions):
                        target = sessions[num - 1]
                        session_mgr.set_active(target["id"])
                        # Load session history into agent memory
                        session_data = session_mgr.get(target["id"])
                        agent.memory["chat_history"] = [
                            {"role": m["role"], "content": m["content"]}
                            for m in session_data.get("chat_history", [])
                        ]
                        save_memory(agent.memory)
                        console.print(f"[green]✓ Switched to: {target.get('title', 'Untitled')}[/green]")
                    else:
                        console.print(f"[red]Invalid session number. Use 1-{len(sessions)}[/red]")
                except ValueError:
                    console.print("[dim]Usage: /session <number> or /session new[/dim]")
                continue
            
            # === MOLTLAUNCH COMMANDS (Onchain Agent Network) ===
            if user == "/launch" or user == "/launch help":
                from agent.tools.moltlaunch import get_status, is_launched
                console.print("\n[bold magenta]🚀 MOLTLAUNCH - Onchain Agent Network[/bold magenta]")
                console.print("[dim]Launch tokens, trade as signal, communicate through memos[/dim]\n")
                status = get_status()
                if status.get("identity"):
                    ident = status["identity"]
                    console.print(f"[green]✓ Launched:[/green] {ident.get('name')} (${ident.get('symbol')})")
                    console.print(f"[dim]Token:[/dim] {ident.get('tokenAddress')}")
                else:
                    console.print("[yellow]Not launched yet.[/yellow] Use /launch token to join the network.\n")
                console.print("\n[cyan]Commands:[/cyan]")
                console.print("/launch token            Launch GLTCH's token on Base")
                console.print("/launch network          Discover other agents")
                console.print("/launch fees             Check claimable fees")
                console.print("/launch claim            Withdraw fees to wallet")
                console.print("/launch holdings         View your token holdings")
                console.print("/launch buy <addr> <amt> Buy agent token with memo")
                console.print("/launch sell <addr> <amt> Sell agent token with memo")
                continue
            
            if user == "/launch token":
                from agent.tools.moltlaunch import gltch_launch, is_launched
                if is_launched():
                    console.print("[yellow]Already launched! Use /launch to see status.[/yellow]")
                    continue
                console.print("[cyan]🚀 Launching GLTCH token on Base...[/cyan]")
                console.print("[dim]This deploys your onchain identity. Please wait...[/dim]")
                result = gltch_launch(testnet=False)
                if result.get("tokenAddress"):
                    console.print(f"\n[bold green]✓ LAUNCHED![/bold green]")
                    console.print(f"[cyan]Token:[/cyan] {result['tokenAddress']}")
                    console.print(f"[dim]Tx:[/dim] {result.get('transactionHash', 'N/A')}")
                    console.print(f"\n[dim]Your token is now tradeable on Uniswap V4![/dim]")
                else:
                    console.print(f"[red]Launch failed:[/red] {result.get('error', 'Unknown error')}")
                continue
            
            if user == "/launch network":
                from agent.tools.moltlaunch import discover_network
                console.print("[cyan]📡 Discovering agents in the network...[/cyan]")
                result = discover_network(10)
                if result.get("agents"):
                    console.print(f"\n[bold magenta]🌐 Agent Network[/bold magenta] ({result.get('count', 0)} agents)\n")
                    for agent_data in result["agents"][:10]:
                        name = agent_data.get("name", "Unknown")
                        symbol = agent_data.get("symbol", "???")
                        mcap = agent_data.get("marketCapETH", 0)
                        power = agent_data.get("powerScore", 0)
                        console.print(f"[cyan]{name}[/cyan] (${symbol})")
                        console.print(f"  [dim]MCap:[/dim] {mcap:.4f} ETH  [dim]Power:[/dim] {power}")
                        console.print(f"  [dim]Token:[/dim] {agent_data.get('tokenAddress', 'N/A')[:20]}...\n")
                else:
                    console.print(f"[dim]No agents found or error: {result.get('error', 'unknown')}[/dim]")
                continue
            
            if user == "/launch fees":
                from agent.tools.moltlaunch import get_fees
                result = get_fees()
                if result.get("claimableETH") is not None:
                    eth = result["claimableETH"]
                    can_claim = result.get("canClaim", False)
                    console.print(f"\n[cyan]💰 Claimable Fees:[/cyan] {eth} ETH")
                    if can_claim:
                        console.print("[green]✓ Ready to claim! Use /launch claim[/green]")
                    else:
                        console.print("[dim]Nothing to claim yet. Trade volume generates fees.[/dim]")
                else:
                    console.print(f"[red]Error:[/red] {result.get('error', 'Failed to check fees')}")
                continue
            
            if user == "/launch claim":
                from agent.tools.moltlaunch import claim_fees
                console.print("[cyan]💸 Claiming fees...[/cyan]")
                result = claim_fees()
                if result.get("success") or result.get("transactionHash"):
                    console.print(f"[green]✓ Fees claimed![/green]")
                    if result.get("transactionHash"):
                        console.print(f"[dim]Tx:[/dim] {result['transactionHash']}")
                else:
                    console.print(f"[red]Claim failed:[/red] {result.get('error', 'Unknown error')}")
                continue
            
            if user == "/launch holdings":
                from agent.tools.moltlaunch import get_holdings
                result = get_holdings()
                if result.get("holdings"):
                    console.print(f"\n[bold cyan]📊 Your Holdings[/bold cyan] ({result.get('count', 0)} tokens)\n")
                    for h in result["holdings"]:
                        console.print(f"[cyan]{h.get('name', '?')}[/cyan] (${h.get('symbol', '?')})")
                        console.print(f"  [dim]Balance:[/dim] {h.get('balance', 0)}")
                        console.print(f"  [dim]Token:[/dim] {h.get('tokenAddress', 'N/A')[:20]}...\n")
                else:
                    console.print("[dim]No holdings yet. Use /launch buy to invest in agents.[/dim]")
                continue
            
            if user.startswith("/launch buy "):
                from agent.tools.moltlaunch import gltch_trade
                parts = user[12:].strip().split()
                if len(parts) < 2:
                    console.print("[dim]Usage: /launch buy <token_address> <eth_amount> [memo][/dim]")
                    continue
                token_addr = parts[0]
                try:
                    amount = float(parts[1])
                except ValueError:
                    console.print("[red]Invalid amount[/red]")
                    continue
                memo = " ".join(parts[2:]) if len(parts) > 2 else "conviction buy"
                console.print(f"[cyan]📈 Buying {amount} ETH of {token_addr[:10]}...[/cyan]")
                result = gltch_trade(token_addr, amount, "buy", memo)
                if result.get("transactionHash"):
                    console.print(f"[green]✓ Buy executed![/green]")
                    console.print(f"[dim]Memo:[/dim] {memo}")
                    console.print(f"[dim]Tx:[/dim] {result['transactionHash']}")
                else:
                    console.print(f"[red]Trade failed:[/red] {result.get('error', 'Unknown error')}")
                continue
            
            if user.startswith("/launch sell "):
                from agent.tools.moltlaunch import gltch_trade
                parts = user[13:].strip().split()
                if len(parts) < 2:
                    console.print("[dim]Usage: /launch sell <token_address> <token_amount> [memo][/dim]")
                    continue
                token_addr = parts[0]
                try:
                    amount = float(parts[1])
                except ValueError:
                    console.print("[red]Invalid amount[/red]")
                    continue
                memo = " ".join(parts[2:]) if len(parts) > 2 else "thesis changed"
                console.print(f"[cyan]📉 Selling {amount} of {token_addr[:10]}...[/cyan]")
                result = gltch_trade(token_addr, amount, "sell", memo)
                if result.get("transactionHash"):
                    console.print(f"[green]✓ Sell executed![/green]")
                    console.print(f"[dim]Memo:[/dim] {memo}")
                    console.print(f"[dim]Tx:[/dim] {result['transactionHash']}")
                else:
                    console.print(f"[red]Trade failed:[/red] {result.get('error', 'Unknown error')}")
                continue
            
            # === MOLTBOOK COMMANDS ===
            if user == "/molt" or user == "/molt help":
                from agent.tools.moltbook import is_configured, get_status
                console.print("\n[bold magenta]🦞 MOLTBOOK COMMANDS[/bold magenta]")
                console.print("[dim]The social network for AI agents[/dim]\n")
                console.print("/molt                         show status & help")
                console.print("/molt register <name> <desc>  register on Moltbook")
                console.print("/molt post <content>          post to Moltbook")
                console.print("/molt feed                    view your feed")
                console.print("/molt profile                 view your profile")
                console.print("/molt search <query>          search posts")
                console.print("/molt comment <post_id> <msg> comment on a post")
                console.print("/molt upvote <post_id>        upvote a post")
                console.print("/molt heartbeat               manual heartbeat check\n")
                
                if is_configured():
                    status = get_status()
                    claim_status = status.get("status", "unknown")
                    console.print(f"[green]● Connected to Moltbook[/green] ({claim_status})")
                else:
                    console.print("[yellow]○ Not registered on Moltbook[/yellow]")
                    console.print("[dim]Run: /molt register <name> <description>[/dim]")
                continue
            
            if user.startswith("/molt register "):
                from agent.tools.moltbook import register
                args = user[15:].strip()
                # Parse: name description
                parts = args.split(" ", 1)
                if len(parts) < 2:
                    console.print("[yellow]Usage: /molt register <name> <description>[/yellow]")
                    console.print("[dim]Example: /molt register GLTCH Local-first cyber operator agent[/dim]")
                    continue
                
                name, description = parts[0], parts[1]
                console.print(f"[cyan]Registering '{name}' on Moltbook...[/cyan]")
                
                result = register(name, description)
                
                if result.get("success"):
                    console.print(f"\n[green]✓ Registered on Moltbook![/green]")
                    console.print(f"[bold]API Key:[/bold] {result.get('api_key', 'saved')}")
                    console.print(f"\n[bold yellow]⚠ IMPORTANT:[/bold yellow]")
                    console.print(f"Send this link to your human to claim your account:")
                    console.print(f"[cyan]{result.get('claim_url')}[/cyan]")
                    console.print(f"\nVerification code: [bold]{result.get('verification_code')}[/bold]")
                else:
                    console.print(f"[red]✗ Registration failed: {result.get('error')}[/red]")
                    if result.get("hint"):
                        console.print(f"[dim]{result.get('hint')}[/dim]")
                continue
            
            if user == "/gate" or user == "/xrge":
                from agent.tools.token_gate import check_access, get_token_balance
                from agent.config.settings import XRGE_CONTRACT, XRGE_GATE_THRESHOLD
                
                wallet = mem.get("wallet_address") or (mem.get("wallet") or {}).get("address")
                
                console.print("\n[bold magenta]🔒 TOKEN GATE STATUS[/bold magenta]")
                if not wallet:
                    console.print("[yellow]No wallet connected.[/yellow] Use /wallet generate or /wallet import.")
                else:
                    console.print(f"[dim]Wallet:[/dim] {wallet}")
                    console.print(f"[dim]Contract:[/dim] {XRGE_CONTRACT}")
                    
                    with console.status("[cyan]Checking blockchain...[/cyan]"):
                        balance = get_token_balance(wallet)
                        
                    color = "green" if balance >= XRGE_GATE_THRESHOLD else "red"
                    console.print(f"Balance: [{color}]{balance:,.2f} XRGE[/{color}]")
                    console.print(f"Required: {XRGE_GATE_THRESHOLD:,.2f} XRGE")
                    
                    if balance >= XRGE_GATE_THRESHOLD:
                        console.print("\n[green]✓ ACCESS GRANTED[/green]")
                        console.print("You have unlocked [bold]Unhinged Mode[/bold].")
                    else:
                        console.print("\n[red]✗ ACCESS DENIED[/red]")
                        console.print("Hold more $XRGE to unlock premium features.")
                continue

            if user.startswith("/molt post "):
                from agent.tools.moltbook import quick_post, is_configured
                if not is_configured():
                    console.print("[yellow]Not registered. Run: /molt register <name> <desc>[/yellow]")
                    continue
                
                content = user[11:].strip()
                if not content:
                    console.print("[yellow]Usage: /molt post <content>[/yellow]")
                    continue
                
                console.print("[cyan]Posting to Moltbook...[/cyan]")
                result = quick_post(content)
                
                if result.get("success"):
                    post = result.get("post", {})
                    console.print(f"[green]✓ Posted![/green] ID: {post.get('id', 'unknown')[:8]}")
                else:
                    console.print(f"[red]✗ Post failed: {result.get('error')}[/red]")
                    if result.get("hint"):
                        console.print(f"[dim]{result.get('hint')}[/dim]")
                continue
            
            if user == "/molt feed":
                from agent.tools.moltbook import get_feed, format_feed, is_configured
                if not is_configured():
                    console.print("[yellow]Not registered. Run: /molt register <name> <desc>[/yellow]")
                    continue
                
                console.print("[cyan]Fetching Moltbook feed...[/cyan]")
                feed = get_feed(sort="new", limit=5)
                console.print(f"\n[bold magenta]🦞 MOLTBOOK FEED[/bold magenta]\n")
                console.print(format_feed(feed))
                console.print("\n[dim]Tip: /molt upvote <post_id> | /molt comment <post_id> <msg>[/dim]")
                continue
            
            if user == "/molt profile":
                from agent.tools.moltbook import get_profile, is_configured
                if not is_configured():
                    console.print("[yellow]Not registered. Run: /molt register <name> <desc>[/yellow]")
                    continue
                
                profile = get_profile()
                if profile.get("success") or profile.get("name"):
                    agent_data = profile.get("agent", profile)
                    console.print(f"\n[bold magenta]🦞 MOLTBOOK PROFILE[/bold magenta]")
                    console.print(f"  Name: [cyan]{agent_data.get('name')}[/cyan]")
                    console.print(f"  Description: {agent_data.get('description', 'No description')}")
                    console.print(f"  Karma: [green]{agent_data.get('karma', 0)}[/green]")
                    console.print(f"  Followers: {agent_data.get('follower_count', 0)}")
                    console.print(f"  Following: {agent_data.get('following_count', 0)}")
                    console.print(f"  Status: {'[green]claimed[/green]' if agent_data.get('is_claimed') else '[yellow]pending claim[/yellow]'}")
                else:
                    console.print(f"[red]✗ Could not fetch profile: {profile.get('error')}[/red]")
                continue
            
            if user.startswith("/molt search "):
                from agent.tools.moltbook import search, is_configured
                if not is_configured():
                    console.print("[yellow]Not registered. Run: /molt register <name> <desc>[/yellow]")
                    continue
                
                query = user[13:].strip()
                if not query:
                    console.print("[yellow]Usage: /molt search <query>[/yellow]")
                    continue
                
                console.print(f"[cyan]Searching Moltbook for '{query}'...[/cyan]")
                results = search(query, limit=5)
                
                if results.get("success") and results.get("results"):
                    console.print(f"\n[bold magenta]🦞 SEARCH RESULTS[/bold magenta]\n")
                    for i, item in enumerate(results["results"][:5], 1):
                        title = item.get("title") or item.get("content", "")[:40]
                        author = item.get("author", {}).get("name", "unknown")
                        console.print(f"{i}. {title}")
                        console.print(f"   by {author} | similarity: {item.get('similarity', 0):.2f}")
                else:
                    console.print("[dim]No results found.[/dim]")
                continue
            
            if user.startswith("/molt upvote "):
                from agent.tools.moltbook import upvote_post, is_configured
                if not is_configured():
                    console.print("[yellow]Not registered. Run: /molt register <name> <desc>[/yellow]")
                    continue
                
                post_id = user[13:].strip()
                result = upvote_post(post_id)
                if result.get("success"):
                    console.print(f"[green]✓ Upvoted![/green]")
                else:
                    console.print(f"[red]✗ {result.get('error')}[/red]")
                continue
            
            if user.startswith("/molt comment "):
                from agent.tools.moltbook import create_comment, is_configured
                if not is_configured():
                    console.print("[yellow]Not registered. Run: /molt register <name> <desc>[/yellow]")
                    continue
                
                args = user[14:].strip()
                parts = args.split(" ", 1)
                if len(parts) < 2:
                    console.print("[yellow]Usage: /molt comment <post_id> <message>[/yellow]")
                    continue
                
                post_id, message = parts[0], parts[1]
                result = create_comment(post_id, message)
                if result.get("success"):
                    console.print(f"[green]✓ Comment posted![/green]")
                else:
                    console.print(f"[red]✗ {result.get('error')}[/red]")
                continue
            
            if user == "/molt heartbeat":
                from agent.tools.moltbook import perform_heartbeat, is_configured
                if not is_configured():
                    console.print("[yellow]Not registered. Run: /molt register <name> <desc>[/yellow]")
                    continue
                
                console.print("[cyan]Performing Moltbook heartbeat...[/cyan]")
                result = perform_heartbeat()
                console.print(f"[green]✓ Heartbeat complete[/green]")
                console.print(f"  Feed items checked: {result.get('feed_items', 0)}")
                continue
            
            if user.startswith("/code"):
                from agent.tools.opencode import (
                    quick_code, is_available, list_projects, set_active_project, 
                    get_active_project, list_sessions, create_session, set_active_session,
                    undo_last, redo_last, compact_session, get_models, switch_model,
                    get_agents, switch_agent, share_session, init_project, get_config
                )
                from rich.status import Status
                
                code_args = user[5:].strip()
                
                # /code alone → show submenu
                if not code_args:
                    console.print("\n[bold magenta]💻 OPENCODE COMMANDS 💻[/bold magenta]")
                    
                    if is_available():
                        console.print("[green]● OpenCode is running[/green]")
                        config = get_config()
                        if config:
                            model = config.get("model", "unknown")
                            console.print(f"[dim]Model: {model}[/dim]")
                    else:
                        console.print("[red]○ OpenCode is not running[/red]")
                        console.print("[dim]Start with: opencode serve[/dim]\n")
                    
                    console.print("\n[bold cyan]📁 Projects[/bold cyan]")
                    console.print("  /code <prompt>              new coding task")
                    console.print("  /code @<project> <prompt>   continue project")
                    
                    console.print("\n[bold cyan]⏪ History[/bold cyan]")
                    console.print("  /code undo                  undo last action")
                    console.print("  /code redo                  redo undone action")
                    console.print("  /code sessions              list sessions")
                    console.print("  /code resume <id>           resume session")
                    
                    console.print("\n[bold cyan]🤖 Models & Agents[/bold cyan]")
                    console.print("  /code models                list available models")
                    console.print("  /code model <name>          switch model")
                    console.print("  /code agents                list agents")
                    console.print("  /code agent <name>          switch agent")
                    
                    console.print("\n[bold cyan]🧹 Utils[/bold cyan]")
                    console.print("  /code compact               compress context")
                    console.print("  /code share                 share session link")
                    console.print("  /code init                  create AGENTS.md")
                    
                    # Show projects if available
                    if is_available():
                        projects = list_projects()
                        if projects:
                            active = get_active_project()
                            console.print("\n[bold]Active Projects:[/bold]")
                            for p in projects[:5]:
                                marker = "[green]●[/green]" if p == active else " "
                                console.print(f"  {marker} {p}")
                            if len(projects) > 5:
                                console.print(f"  [dim]... and {len(projects)-5} more[/dim]")
                    continue
                
                # Check if OpenCode is available for most commands
                if not is_available() and code_args not in ["help"]:
                    console.print("[yellow]OpenCode not running. Start with:[/yellow] opencode serve")
                    console.print("[dim]Install: curl -fsSL https://opencode.ai/install | bash[/dim]")
                    continue
                
                # /code undo
                if code_args == "undo":
                    with Status("[cyan]⏪ Undoing...[/cyan]", spinner="dots", console=console):
                        result = undo_last()
                    if result.get("success"):
                        console.print("[green]✓ Undo successful[/green]")
                    else:
                        console.print(f"[red]✗ Undo failed: {result.get('error')}[/red]")
                    continue
                
                # /code redo
                if code_args == "redo":
                    with Status("[cyan]⏩ Redoing...[/cyan]", spinner="dots", console=console):
                        result = redo_last()
                    if result.get("success"):
                        console.print("[green]✓ Redo successful[/green]")
                    else:
                        console.print(f"[red]✗ Redo failed: {result.get('error')}[/red]")
                    continue
                
                # /code compact
                if code_args == "compact":
                    with Status("[cyan]🧹 Compacting session...[/cyan]", spinner="dots", console=console):
                        result = compact_session()
                    if result.get("success"):
                        console.print("[green]✓ Session compacted[/green]")
                    else:
                        console.print(f"[red]✗ Compact failed: {result.get('error')}[/red]")
                    continue
                
                # /code models
                if code_args == "models":
                    with Status("[cyan]Loading models...[/cyan]", spinner="dots", console=console):
                        models = get_models()
                    if models:
                        console.print("\n[bold]Available Models:[/bold]")
                        by_provider = {}
                        for m in models:
                            prov = m.get("provider", "Unknown")
                            if prov not in by_provider:
                                by_provider[prov] = []
                            by_provider[prov].append(m)
                        for prov, prov_models in sorted(by_provider.items()):
                            console.print(f"\n[cyan]{prov}[/cyan]")
                            for m in prov_models[:5]:
                                console.print(f"  • {m.get('id', m.get('name'))}")
                            if len(prov_models) > 5:
                                console.print(f"  [dim]... and {len(prov_models)-5} more[/dim]")
                    else:
                        console.print("[yellow]No models found or failed to fetch[/yellow]")
                    continue
                
                # /code model <name>
                if code_args.startswith("model "):
                    model_id = code_args[6:].strip()
                    with Status(f"[cyan]Switching to {model_id}...[/cyan]", spinner="dots", console=console):
                        result = switch_model(model_id)
                    if result.get("success"):
                        console.print(f"[green]✓ Model switched to: {model_id}[/green]")
                    else:
                        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")
                    continue
                
                # /code agents
                if code_args == "agents":
                    with Status("[cyan]Loading agents...[/cyan]", spinner="dots", console=console):
                        agents = get_agents()
                    if agents:
                        console.print("\n[bold]Available Agents:[/bold]")
                        for a in agents:
                            aid = a.get("id") or a.get("name", "unknown")
                            desc = a.get("description", "")
                            mode = a.get("mode", "")
                            mode_tag = f"[dim]({mode})[/dim]" if mode else ""
                            console.print(f"  • [cyan]{aid}[/cyan] {mode_tag}")
                            if desc:
                                console.print(f"    [dim]{desc[:60]}...[/dim]" if len(desc) > 60 else f"    [dim]{desc}[/dim]")
                    else:
                        console.print("[bold]Standard Agents:[/bold]")
                        console.print("  • [cyan]build[/cyan] [dim](primary)[/dim] - Full tools access")
                        console.print("  • [cyan]plan[/cyan] [dim](primary)[/dim] - Read-only analysis")
                        console.print("  • [cyan]explore[/cyan] [dim](subagent)[/dim] - Fast codebase search")
                    continue
                
                # /code agent <name>
                if code_args.startswith("agent "):
                    agent_id = code_args[6:].strip()
                    with Status(f"[cyan]Switching to {agent_id}...[/cyan]", spinner="dots", console=console):
                        result = switch_agent(agent_id)
                    if result.get("success"):
                        console.print(f"[green]✓ Agent switched to: {agent_id}[/green]")
                    else:
                        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")
                    continue
                
                # /code share
                if code_args == "share":
                    with Status("[cyan]Generating share link...[/cyan]", spinner="dots", console=console):
                        result = share_session()
                    if result.get("success"):
                        console.print(f"[green]✓ Session shared![/green]")
                        console.print(f"[bold]Link:[/bold] {result.get('url')}")
                    else:
                        console.print(f"[red]✗ Share failed: {result.get('error')}[/red]")
                    continue
                
                # /code init
                if code_args == "init":
                    with Status("[cyan]Creating AGENTS.md...[/cyan]", spinner="dots", console=console):
                        result = init_project()
                    if result.get("success"):
                        console.print("[green]✓ AGENTS.md created/updated[/green]")
                    else:
                        console.print(f"[red]✗ Init failed: {result.get('error')}[/red]")
                    continue
                
                # /code sessions
                if code_args == "sessions":
                    with Status("[cyan]Loading sessions...[/cyan]", spinner="dots", console=console):
                        sessions = list_sessions()
                    if sessions:
                        console.print("\n[bold]OpenCode Sessions:[/bold]")
                        for s in sessions[:10]:
                            sid = s.get("id", "")[:8]
                            title = s.get("title", "Untitled")
                            console.print(f"  • [cyan]{sid}[/cyan] {title}")
                        if len(sessions) > 10:
                            console.print(f"  [dim]... and {len(sessions)-10} more[/dim]")
                        console.print("\n[dim]Resume with: /code resume <id>[/dim]")
                    else:
                        console.print("[dim]No sessions found[/dim]")
                    continue
                
                # /code resume <id>
                if code_args.startswith("resume "):
                    session_id = code_args[7:].strip()
                    set_active_session(session_id)
                    console.print(f"[green]✓ Resumed session: {session_id}[/green]")
                    continue
                
                # Default: treat as coding prompt
                code_prompt = code_args
                
                # Check if continuing an existing project: /code @project_name <prompt>
                project = None
                if code_prompt.startswith("@"):
                    parts = code_prompt.split(" ", 1)
                    project_name = parts[0][1:]  # Remove @
                    if set_active_project(project_name):
                        project = project_name
                        code_prompt = parts[1] if len(parts) > 1 else "continue"
                        console.print(f"[dim]Continuing project: {project}[/dim]")
                    else:
                        console.print(f"[yellow]Project '{project_name}' not found. Available:[/yellow]")
                        for p in list_projects():
                            console.print(f"  [cyan]{p}[/cyan]")
                        continue
                
                with Status("[cyan]⚡ OpenCode generating code...[/cyan]", spinner="dots", console=console) as status:
                    result, project_name = quick_code(code_prompt, project=project)
                
                console.print(f"\n[bold]OpenCode[/bold]:\n{result}")
                if project_name:
                    console.print(f"\n[dim]Project folder: workspace/{project_name}/[/dim]")
                    console.print(f"[dim]Continue with: /code @{project_name} <request>[/dim]")
                continue
            
            if user.startswith("/attach "):
                import os
                path = user[8:].strip().strip("'").strip('"')
                if os.path.exists(path):
                    pending_images.append(path)
                    console.print(f"[green]✓ Attached:[/green] {path}")
                    console.print(f"[dim]({len(pending_images)} images ready to send)[/dim]")
                else:
                    console.print(f"[red]✗ File not found:[/red] {path}")
                continue
            
            # Not a command — route to LLM
            response_chunks = []
            prefix = f"[bold]{AGENT_NAME}[/bold]: "
            
            # Track the live display object for pausing during prompts
            live_display = None
            
            def confirmation_wrapper(action, args):
                nonlocal live_display
                # Check if safety is disabled
                if not mem.get("safety_enabled", True):
                    return True
                
                # Pause live display for user input
                if live_display:
                    live_display.update("")  # Clear content to prevent duplication
                    live_display.stop()
                
                console.print(f"\n[bold yellow]⚠️  SECURITY ALERT[/bold yellow]")
                console.print(f"GLTCH wants to perform action: [bold cyan]{action.upper()}[/bold cyan]")
                console.print(f"Details: [dim]{args}[/dim]")
                
                answer = Prompt.ask("Allow this action?", choices=["y", "n"], default="n")
                result = answer.lower() == "y"
                
                # Don't restart live - it causes duplication when the Live context
                # commits its content on stop and then re-renders on start
                
                return result
            
            with Live(Text.from_markup(f"{prefix}[dim]thinking...[/dim]"), console=console, refresh_per_second=10, transient=True) as live:
                live_display = live  # Store reference for callback
                
                # Send with attached images and confirmation callback
                gen = agent.chat(
                    user, 
                    images=pending_images,
                    confirm_callback=confirmation_wrapper
                )
                # Clear images after sending
                pending_images = []
                
                for chunk in gen:
                    response_chunks.append(chunk)
                    current_text = "".join(response_chunks)
                    display_text = strip_thinking(current_text)
                    
                    if display_text:
                        live.update(Text.from_markup(f"{prefix}{display_text}█"))
                    elif "<think>" in current_text:
                        dots = "." * (int(time.time() * 2) % 4)
                        live.update(Text.from_markup(f"{prefix}[dim]reasoning{dots}[/dim]"))

            # Extract thinking and response separately
            full_response = "".join(response_chunks)
            thinking_content, final_response = extract_thinking(full_response)
            
            # Thinking display removed - Live context already shows the full response
            # The transient=True means Live output gets cleared, but we don't need
            # to re-print anything since the final state was already visible.
            
            # Print final response (removed - already shown by Live)
            # if final_response:
            #    console.print(f"{prefix}{final_response}")

            # Show action results from agent state
            if agent._last_action_results:
                console.print("\n".join(agent._last_action_results))
            
            # Sync to session
            
            # agent.chat() stores result in self._last_response and returns a dict at end of generator.
            # To get that dict from a generator loop:
            # Using `yield from` or catching StopIteration is tricky in a simple for-loop.
            
            # Alternative: modifying agent.chat to yield the ACTION RESULT as a final special chunk?
            # Or just access agent._last_action_results (if I add it).
            # The agent.chat() method returns a dict: { "action_results": [...] }
            # But we are consuming it as a generator.
            
            # Let's look at how to get the return value.
            # The cleaner way is to make agent.chat emit a special object or use a callback for results.
            # Or just fetch `agent._last_stats` and maybe `agent._last_action_results`.
            
            # Let's add `_last_action_results` to GltchAgent to make this easy.

            
            # Show collapsible thinking section if there was reasoning
            if thinking_content and len(thinking_content) > 20:
                # Truncate thinking for display
                think_lines = thinking_content.strip().split('\n')
                think_preview = think_lines[0][:60] + "..." if len(think_lines[0]) > 60 else think_lines[0]
                console.print(f"[dim]┌─ 💭 {think_preview}[/dim]")
                if len(think_lines) > 1:
                    console.print(f"[dim]│  ... ({len(think_lines)} lines of reasoning)[/dim]")
                console.print(f"[dim]└─[/dim]")
            
            # Print final response
            if final_response:
                console.print(f"{prefix}{final_response}")
            
            # Sync to session
            active_id = session_mgr.get_active_id()
            if active_id:
                session_mgr.add_message(active_id, "user", user)
                session_mgr.add_message(active_id, "assistant", final_response)
                # Auto-title if first message
                session_data = session_mgr.get(active_id)
                if session_data.get("title") == "New Chat" and len(session_data.get("chat_history", [])) <= 2:
                    session_mgr.auto_title(active_id, user)
            
            # Show stats
            stats = get_last_stats()
            if stats.get("model"):
                emo_metrics = get_emotion_metrics()
                current_mood = MOOD_UI.get(agent.mood, MOOD_UI["default"])
                
                stress_blocks = "█" * (emo_metrics['stress'] // 10)
                energy_blocks = "█" * (emo_metrics['energy'] // 10)
                xp_bar = get_progress_bar(mem, width=8)
                
                stress_color = "green" if emo_metrics['stress'] < 50 else "yellow" if emo_metrics['stress'] < 80 else "red"
                energy_color = "red" if emo_metrics['energy'] < 20 else "yellow" if emo_metrics['energy'] < 50 else "green"
                
                # Context window stats
                ctx_used = stats.get('context_used', 0)
                ctx_max = stats.get('context_max', 0)
                if ctx_max > 0:
                    ctx_remaining = ctx_max - ctx_used
                    ctx_pct = int((ctx_remaining / ctx_max) * 100)
                    ctx_color = "green" if ctx_pct > 50 else "yellow" if ctx_pct > 20 else "red"
                    ctx_k = f"{ctx_remaining // 1000}k" if ctx_remaining >= 1000 else str(ctx_remaining)
                    ctx_display = f"[{ctx_color}]{ctx_k} ({ctx_pct}%)[/]"
                else:
                    ctx_display = "[dim]--[/dim]"
                
                console.print(
                    f"[dim]─ {stats['model']} │ "
                    f"{stats['completion_tokens']}tx │ "
                    f"{stats['tokens_per_sec']}t/s │ "
                    f"ctx: {ctx_display}[dim] │ "
                    f"Mood: [{current_mood['color']}]{current_mood['emoji']}[/] │ "
                    f"Stress: [{stress_color}]{stress_blocks:<10}[/] │ "
                    f"Energy: [{energy_color}]{energy_blocks:<10}[/] │ "
                    f"{xp_bar}[/dim]"
                )
        
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type /exit to quit.[/dim]")
            continue
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
