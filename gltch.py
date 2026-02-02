#!/usr/bin/env python3
"""
GLTCH - Local-first, command-driven operator agent
Main entry point supporting both terminal UI and RPC modes.
"""

import sys
import argparse


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
        # Run in RPC mode
        from agent.rpc.server import RPCServer
        server = RPCServer()
        
        if args.rpc == "stdio":
            server.run_stdio()
        else:
            server.run_http(args.host, args.port)
    else:
        # Run in terminal UI mode
        run_terminal_ui()


def run_terminal_ui():
    """Run the interactive terminal UI."""
    import time
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
    from agent.tools.actions import strip_thinking, verify_suggestions
    from agent.personality.emotions import get_emotion_metrics
    from agent.personality.moods import MOOD_UI
    from agent.gamification.xp import get_progress_bar
    from agent.gamification.ranks import get_rank_title
    
    console = Console()
    AGENT_NAME = "GLTCH"
    
    # Cyber girl ASCII art frames for animation
    GLTCH_FRAMES = [
        """[bright_magenta]
    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
    █                                                 █
    █   ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗       █
    █  ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║       █
    █  ██║  ███╗██║     ██║   ██║     ███████║       █
    █  ██║   ██║██║     ██║   ██║     ██╔══██║       █
    █  ╚██████╔╝███████╗██║   ╚██████╗██║  ██║       █
    █   ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝       █
    █                                                 █
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀[/bright_magenta]""",
        """[cyan]
    ░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░
    █                                                 █
    █   ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗       █
    █  ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║       █
    █  ██║  ███╗██║     ██║   ██║     ███████║       █
    █  ██║   ██║██║     ██║   ██║     ██╔══██║       █
    █  ╚██████╔╝███████╗██║   ╚██████╗██║  ██║       █
    █   ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝       █
    █                                                 █
    ░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░[/cyan]""",
        """[bright_green]
    ╔═══════════════════════════════════════════════════╗
    ║                                                   ║
    ║   ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗  ✧･ﾟ    ║
    ║  ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║ :*✧    ║
    ║  ██║  ███╗██║     ██║   ██║     ███████║         ║
    ║  ██║   ██║██║     ██║   ██║     ██╔══██║  ⚡     ║
    ║  ╚██████╔╝███████╗██║   ╚██████╗██║  ██║         ║
    ║   ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝  💜     ║
    ║                                                   ║
    ╚═══════════════════════════════════════════════════╝[/bright_green]"""
    ]
    
    TAGLINES = [
        "✨ [italic cyan]cyber operator online[/italic cyan] ✨",
        "💜 [italic magenta]glitching reality since boot[/italic magenta] 💜",
        "⚡ [italic green]local-first • privacy-native • unhinged[/italic green] ⚡",
        "🔮 [italic cyan]your chaos gremlin is ready[/italic cyan] 🔮",
        "💀 [italic red]hack the planet, cuddle the chaos[/italic red] 💀",
    ]
    
    def animate_intro():
        """Play animated intro sequence."""
        import random
        
        # Glitch effect - flash through frames
        for _ in range(3):
            for frame in GLTCH_FRAMES:
                console.clear()
                console.print(frame)
                time.sleep(0.08)
        
        # Final frame with tagline
        console.clear()
        console.print(GLTCH_FRAMES[-1])
        console.print(f"\n          {random.choice(TAGLINES)}\n")
    
    # Command autocomplete (alphabetically sorted)
    COMMANDS = sorted([
        "/backup",
        "/boost",
        "/clear_chat",
        "/code ",
        "/exit",
        "/help",
        "/load ",
        "/mode cyberpunk", "/mode loyal", "/mode operator", "/mode unhinged",
        "/model",
        "/mood affectionate", "/mood calm", "/mood feral", "/mood focused",
        "/net off", "/net on",
        "/openai",
        "/ping",
        "/status",
        "/xp",
    ])
    
    class CommandCompleter(Completer):
        def get_completions(self, document, complete_event):
            text = document.text
            if text.startswith("/"):
                for cmd in COMMANDS:
                    if cmd.startswith(text):
                        yield Completion(cmd, start_position=-len(text))
    
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
        console.print("/backup                       backup memory")
        console.print("/boost                        toggle remote GPU")
        console.print("/clear_chat                   clear chat history")
        console.print("/code                         show OpenCode status & projects")
        console.print("/code <prompt>                new coding project")
        console.print("/code @<project> <prompt>     continue existing project")
        console.print("/exit                         quit")
        console.print("/help                         show commands")
        console.print("/load <model>                 switch model directly")
        console.print("/mode <cyberpunk|loyal|operator|unhinged>")
        console.print("/model                        select from available models")
        console.print("/mood <affectionate|calm|feral|focused>")
        console.print("/net <off|on>                 toggle network")
        console.print("/openai                       toggle OpenAI cloud")
        console.print("/ping                         alive check")
        console.print("/status                       show agent status")
        console.print("/xp                           show rank & unlocks\n")
    
    # Initialize agent
    agent = GltchAgent()
    mem = agent.memory
    kb = KnowledgeBase()
    
    # Animated intro
    animate_intro()
    
    if agent.is_first_boot:
        first_boot(agent)
    
    banner(mem)
    
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
            
            if user == "/clear_chat":
                agent.clear_chat_history()
                console.print("[green]Chat history cleared.[/green]")
                continue
            
            if user == "/backup":
                filename = backup_memory(mem)
                console.print(f"[green]Backup saved:[/green] {filename}")
                continue
            
            if user.startswith("/code "):
                from agent.tools.opencode import quick_code, is_available, list_projects, set_active_project, get_active_project
                code_prompt = user[6:].strip()
                if not code_prompt:
                    console.print("[yellow]Usage: /code <describe what you want>[/yellow]")
                    console.print("[yellow]       /code @<project> <continue working>[/yellow]")
                    continue
                
                if not is_available():
                    console.print("[yellow]OpenCode not running. Start with:[/yellow] opencode serve")
                    console.print("[dim]Install: curl -fsSL https://opencode.ai/install | bash[/dim]")
                    continue
                
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
                
                console.print(f"[cyan]→ Routing to OpenCode...[/cyan]")
                result, project_name = quick_code(code_prompt, project=project)
                console.print(f"\n[bold]OpenCode[/bold]:\n{result}")
                if project_name:
                    console.print(f"\n[dim]Project folder: workspace/{project_name}/[/dim]")
                    console.print(f"[dim]Continue with: /code @{project_name} <request>[/dim]")
                continue
            
            if user == "/code":
                from agent.tools.opencode import is_available, list_projects, get_active_project
                if is_available():
                    console.print("[green]● OpenCode is running[/green]")
                    projects = list_projects()
                    if projects:
                        active = get_active_project()
                        console.print("\n[bold]Projects:[/bold]")
                        for p in projects:
                            marker = "[green]●[/green]" if p == active else " "
                            console.print(f"  {marker} {p}")
                        console.print("\n[dim]Continue: /code @<project> <request>[/dim]")
                else:
                    console.print("[red]○ OpenCode is not running[/red]")
                    console.print("[dim]Start with: opencode serve[/dim]")
                    console.print("[dim]Install: curl -fsSL https://opencode.ai/install | bash[/dim]")
                continue
            
            # Not a command — route to LLM
            response_chunks = []
            prefix = f"[bold]{AGENT_NAME}[/bold]: "
            
            with Live(Text.from_markup(f"{prefix}[dim]thinking...[/dim]"), console=console, refresh_per_second=10, transient=True) as live:
                for chunk in agent.chat(user):
                    response_chunks.append(chunk)
                    current_text = "".join(response_chunks)
                    display_text = strip_thinking(current_text)
                    
                    if display_text:
                        live.update(Text.from_markup(f"{prefix}{display_text}█"))
                    elif "<think>" in current_text:
                        dots = "." * (int(time.time() * 2) % 4)
                        live.update(Text.from_markup(f"{prefix}[dim]reasoning{dots}[/dim]"))
            
            # Print final response
            final_response = strip_thinking("".join(response_chunks))
            if final_response:
                console.print(f"{prefix}{final_response}")
            
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
                
                console.print(
                    f"[dim]─ {stats['model']} │ "
                    f"{stats['completion_tokens']}tx │ "
                    f"{stats['tokens_per_sec']}t/s │ "
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
