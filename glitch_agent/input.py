"""
GLTCH Input Module
Readline setup, tab completion, command hints, and input handling.
"""
import atexit
import os
import sys

# Handle readline cross-platform (Windows needs pyreadline3)
try:
    import readline
except ImportError:
    if sys.platform == 'win32':
        try:
            import pyreadline3 as readline
        except ImportError:
            readline = None
    else:
        readline = None

from rich.console import Console

console = Console()

HISTORY_FILE = os.path.expanduser("~/.gltch_history")
KB_DIR = "kb"

# All available commands for tab completion (sorted alphabetically)
COMMANDS = sorted([
    "/append ",
    "/backup",
    "/boost",
    "/cat ",
    "/clear_chat",
    "/clear_notes",
    "/exit",
    "/help",
    "/kb ",
    "/kb add ",
    "/kb delete ",
    "/kb list",
    "/kb read ",
    "/lms",
    "/load ",
    "/ls",
    "/mission ",
    "/mission add ",
    "/mission clear",
    "/mission done ",
    "/mission list",
    "/mode ",
    "/models",
    "/mood ",
    "/net ",
    "/note ",
    "/note delete ",
    "/openai",
    "/ping",
    "/recall",
    "/restore ",
    "/search ",
    "/status",
    "/sys",
    "/write ",
    "/xp",
])


def show_command_hints():
    """Show all commands alphabetically when user types /"""
    from rich.columns import Columns
    from rich.text import Text
    
    # Group commands by first letter for nice display
    console.print("\n[bold magenta]◆ GLTCH COMMANDS[/bold magenta]")
    console.print("[dim]─────────────────────────────────────────[/dim]")
    
    # Create a clean list without trailing spaces for display
    display_cmds = [cmd.strip() for cmd in COMMANDS]
    
    # Show in columns
    cmd_texts = [Text(cmd, style="cyan") for cmd in display_cmds]
    console.print(Columns(cmd_texts, equal=True, expand=True, column_first=True))
    
    console.print("[dim]─────────────────────────────────────────[/dim]")
    console.print("[dim]Tab to complete • ↑↓ history • /help for details[/dim]\n")


class CommandCompleter:
    """Tab completion for GLTCH commands."""
    
    def __init__(self):
        self.matches = []
    
    def complete(self, text: str, state: int):
        if state == 0:
            if readline is None:
                return None
            line = readline.get_line_buffer()
            
            if line.startswith("/"):
                self.matches = [cmd for cmd in COMMANDS if cmd.startswith(line)]
                
                if line.startswith("/kb read ") or line.startswith("/kb delete "):
                    prefix = line.rsplit(" ", 1)[-1]
                    if os.path.exists(KB_DIR):
                        kbs = [f[:-4] for f in os.listdir(KB_DIR) if f.endswith(".txt")]
                        base = "/kb read " if "read" in line else "/kb delete "
                        self.matches = [base + kb for kb in kbs if kb.startswith(prefix)]
                
                elif line.startswith("/cat ") or line.startswith("/write ") or line.startswith("/append "):
                    prefix = line.rsplit(" ", 1)[-1]
                    dir_part = os.path.dirname(prefix) or "."
                    file_part = os.path.basename(prefix)
                    try:
                        entries = os.listdir(dir_part)
                        base_cmd = line.split(" ")[0] + " "
                        self.matches = []
                        for e in entries:
                            full = os.path.join(dir_part, e) if dir_part != "." else e
                            if e.startswith(file_part):
                                if os.path.isdir(os.path.join(dir_part, e)):
                                    self.matches.append(base_cmd + full + "/")
                                else:
                                    self.matches.append(base_cmd + full)
                    except OSError:
                        self.matches = []
                
                elif line.startswith("/mode "):
                    modes = ["operator", "cyberpunk", "loyal", "unhinged"]
                    prefix = line[6:]
                    self.matches = ["/mode " + m for m in modes if m.startswith(prefix)]
                
                elif line.startswith("/mood "):
                    moods = ["calm", "focused", "feral"]
                    prefix = line[6:]
                    self.matches = ["/mood " + m for m in moods if m.startswith(prefix)]
            else:
                self.matches = []
        
        try:
            return self.matches[state]
        except IndexError:
            return None


def setup_readline():
    """Initialize readline with history and completion."""
    if readline is None:
        return  # No readline support available
    
    completer = CommandCompleter()
    readline.set_completer(completer.complete)
    readline.set_completer_delims(" \t\n")
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set show-all-if-ambiguous on")
    readline.parse_and_bind("set completion-ignore-case on")
    readline.parse_and_bind("set colored-completion-prefix on")
    
    if os.path.exists(HISTORY_FILE):
        try:
            readline.read_history_file(HISTORY_FILE)
        except Exception:
            pass
    
    readline.set_history_length(500)
    atexit.register(lambda: readline.write_history_file(HISTORY_FILE))


def get_input(prompt: str = "you: ") -> str:
    """Get input with readline support (history, editing, completion)."""
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        return "/exit"
