"""
GLTCH Tools Module
File operations, shell commands, and LLM action parsing.
"""
import os
import re
import subprocess
import urllib.request
import json
import time
import sys
from typing import Tuple, List, Optional, Dict, Any

from rich.console import Console
from rich.prompt import Confirm
from config import GIPHY_API_KEY

console = Console()


def file_write(filepath: str, content: str) -> None:
    """Create or overwrite a file."""
    filepath = filepath.strip()
    if not filepath or not content:
        console.print("[red]Usage: /write <file> <content>[/red]")
        return
    try:
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[green]Written:[/green] {filepath} ({len(content)} bytes)")
    except Exception as e:
        console.print(f"[red]Write failed:[/red] {e}")


def file_append(filepath: str, content: str) -> None:
    """Append to a file."""
    filepath = filepath.strip()
    if not filepath or not content:
        console.print("[red]Usage: /append <file> <content>[/red]")
        return
    try:
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        console.print(f"[green]Appended:[/green] {filepath}")
    except Exception as e:
        console.print(f"[red]Append failed:[/red] {e}")


def file_cat(filepath: str) -> None:
    """Read and display file contents."""
    filepath = filepath.strip()
    if not filepath:
        console.print("[red]Usage: /cat <file>[/red]")
        return
    if not os.path.exists(filepath):
        console.print(f"[red]File not found:[/red] {filepath}")
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        console.print(f"[bold]--- {filepath} ---[/bold]")
        console.print(content)
        console.print(f"[bold]--- EOF ({len(content)} bytes) ---[/bold]")
    except Exception as e:
        console.print(f"[red]Read failed:[/red] {e}")


def file_ls(path: str = ".") -> None:
    """List directory contents."""
    path = path.strip() or "."
    if not os.path.exists(path):
        console.print(f"[red]Path not found:[/red] {path}")
        return
    if not os.path.isdir(path):
        console.print(f"[red]Not a directory:[/red] {path}")
        return
    try:
        entries = sorted(os.listdir(path))
        console.print(f"[bold]{os.path.abspath(path)}[/bold]")
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                console.print(f"[cyan]{entry}/[/cyan]")
            else:
                size = os.path.getsize(full_path)
                console.print(f"{entry} [dim]({size}b)[/dim]")
    except Exception as e:
        console.print(f"[red]ls failed:[/red] {e}")


def run_shell(cmd: str) -> str:
    """Run a shell command and return output. Blocks dangerous commands."""
    cmd = cmd.strip()
    if not cmd:
        return "[red]No command[/red]"
    
    # Blocklist - commands that could compromise the system
    dangerous = [
        'rm -rf /', 'rm -rf ~', 'rm -rf *',
        'mkfs', 'dd if=', ':(){:', 'fork bomb',
        '> /dev/sd', '> /dev/nvme',
        'chmod -R 777 /', 'chmod -R 000',
        'chown -R', 
        'curl | bash', 'wget | bash', 'curl | sh', 'wget | sh',
        '| bash', '| sh',  # piping to shell
        'sudo rm', 'sudo dd', 'sudo mkfs',
        'passwd', 'useradd', 'userdel', 'usermod',
        '/etc/shadow', '/etc/passwd',
        'iptables -F', 'iptables --flush',
        'systemctl stop', 'systemctl disable',
        'shutdown', 'reboot', 'halt', 'poweroff',
        'init 0', 'init 6',
        # Interactive/Blocking commands to avoid
        'watch ', 'top', 'htop', 'vim', 'nano', 'less', 'more',
        'man ', 'ssh ', 'telnet', 'ftp'
    ]
    
    cmd_lower = cmd.lower()
    for blocked in dangerous:
        if blocked in cmd_lower:
            return f"[red]⚠ blocked dangerous command:[/red] contains '{blocked}'"
    
    # Also block if starts with sudo (unless it's something safe like nmap)
    safe_sudo = ['sudo nmap', 'sudo ping', 'sudo traceroute', 'sudo tcpdump']
    if cmd_lower.startswith('sudo') and not any(cmd_lower.startswith(s) for s in safe_sudo):
        return "[red]⚠ blocked:[/red] sudo commands restricted. use safe_sudo whitelist."
    
    try:
        # Check if this is a long-running command that needs streaming output
        long_running = ['nmap', 'nikto', 'masscan', 'sqlmap', 'gobuster', 'dirb', 'hydra', 'john']
        is_long_running = any(x in cmd_lower for x in long_running)
        
        if is_long_running:
            # Stream output in real-time for long-running commands
            console.print(f"[yellow]⏳ Running (Ctrl+C to cancel)...[/yellow]")
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            output_lines = []
            try:
                for line in process.stdout:
                    print(line, end='', flush=True)
                    output_lines.append(line)
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                console.print("\n[yellow]⚠ Command cancelled by user[/yellow]")
            return ''.join(output_lines).strip() if output_lines else "[dim]No output[/dim]"
        else:
            # Regular commands with timeout
            timeout = 60
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout + result.stderr
            return output.strip() if output.strip() else "[dim]No output[/dim]"
    except subprocess.TimeoutExpired:
        return f"[red]Command timed out ({timeout}s)[/red]"
    except Exception as e:
        return f"[red]Run failed:[/red] {e}"


def strip_thinking(response: str) -> str:
    """Remove <think>...</think> blocks from reasoning models like DeepSeek R1.
    Handles both closed and unclosed think blocks."""
    
    # First: if there's content after </think>, extract that
    if '</think>' in response:
        parts = response.split('</think>')
        after_think = parts[-1].strip()
        if after_think:
            return after_think
    
    # Second: remove complete <think>...</think> blocks
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    
    # Third: remove any unclosed <think> blocks (everything from <think> to end)
    cleaned = re.sub(r'<think>.*$', '', cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()
    
    # If still empty and there's a complete think block, extract last meaningful line
    if not cleaned:
        think_match = re.search(r'<think>(.*?)</think>', response, flags=re.DOTALL)
        if think_match:
            think_content = think_match.group(1).strip()
            lines = [l.strip() for l in think_content.split('\n') if l.strip()]
            for line in reversed(lines):
                if any(x in line.lower() for x in ['should i', 'let me', 'i need to', 'thinking', 'the user']):
                    continue
                if len(line) > 5 and len(line) < 200:
                    cleaned = line
                    break
            if not cleaned and lines:
                cleaned = lines[-1][:150]
    
    return cleaned


def verify_suggestions(response: str) -> List[str]:
    """
    Scan LLM response for mentioned files, services, and commands.
    Verify they exist and return warnings for anything fake.
    """
    warnings = []
    
    # Look for file paths (starting with /)
    file_pattern = r'(/(?:etc|usr|var|home|lib|opt|sys|proc)/[\w\-\.\/]+)'
    files = re.findall(file_pattern, response)
    for f in set(files):
        # Skip if it's a common well-known path
        known_paths = ['/etc/passwd', '/etc/hosts', '/etc/fstab', '/etc/resolv.conf', 
                       '/etc/systemd/', '/usr/bin/', '/var/log/', '/home/']
        if any(f.startswith(k) for k in known_paths):
            continue
        # Check if file/dir exists
        if not os.path.exists(f) and not os.path.exists(os.path.dirname(f)):
            warnings.append(f"[yellow]⚠ Verify:[/yellow] {f} does not exist on this system")
    
    # Look for systemctl commands with service names
    service_pattern = r'systemctl\s+(?:enable|start|restart|status)\s+([a-zA-Z0-9\-_@]+(?:\.service)?)'
    services = re.findall(service_pattern, response)
    for svc in set(services):
        # Quick check if service unit exists
        svc_name = svc if svc.endswith('.service') else f"{svc}.service"
        result = subprocess.run(
            f"systemctl list-unit-files {svc_name} 2>/dev/null | grep -q {svc_name.replace('.service', '')}",
            shell=True, capture_output=True
        )
        if result.returncode != 0:
            # Also check if it's a template service
            if '@' not in svc:
                warnings.append(f"[yellow]⚠ Verify:[/yellow] service '{svc}' not found in systemctl")
    
    # Look for commands and verify they exist
    cmd_pattern = r'(?:sudo\s+)?([a-zA-Z][a-zA-Z0-9\-_]+)\s+'
    # Only check first word of commands that look like they're being suggested
    lines_with_commands = re.findall(r'(?:run|do|execute|try)[:\s]+`?([^`\n]+)`?', response, re.IGNORECASE)
    for line in lines_with_commands:
        first_word = line.split()[0] if line.split() else ""
        if first_word and first_word not in ['sudo', 'the', 'a', 'to', 'if']:
            result = subprocess.run(f"which {first_word}", shell=True, capture_output=True)
            if result.returncode != 0 and first_word not in ['cd', 'echo', 'export', 'source', 'alias']:
                warnings.append(f"[yellow]⚠ Verify:[/yellow] command '{first_word}' not found in PATH")
    
    return warnings


def parse_and_execute_actions(response: str, mem: Dict[str, Any] = None) -> Tuple[str, List[str], Optional[str]]:
    """
    Parse LLM response for [ACTION:...] tags and execute them.
    Returns (cleaned response, list of action results).
    """
    results = []
    cleaned = strip_thinking(response)
    mem = mem or {} # Safe default
    
    # Matches [ACTION:command|args] - lazy match args to avoid over-greediness
    action_pattern = r'\[ACTION:(\w+)\|(.+?)\]'
    
    # Loose match for multi-line block actions
    loose_pattern = r'\[ACTION:(\w+)\]\s*\n([^\[]+?)(?=\n\n|\n\[|$)'
    
    def execute_action(action: str, args: str):
        action = action.lower().strip()
        args = args.strip()
        
        # --- CONFIRMATION GUARDRAIL ---
        short_args = args.replace('\n', ' ')[:60] + "..." if len(args) > 60 else args.replace('\n', ' ')
        console.print(f"\n[bold yellow]⚠ ACTION REQUEST:[/bold yellow] [bold cyan]{action.upper()}[/bold cyan] [dim]{short_args}[/dim]")
        
        if not Confirm.ask(f"Allow {action}?", default=False):
            results.append(f"[dim]✖ Skipped user-denied action: {action}[/dim]")
            return
        # ------------------------------
        
        if action == "write":
            # Split only on the first pipe to separate filename from content
            if '|' in args:
                parts = args.split('|', 1)
                filepath = parts[0].strip()
                content = parts[1].strip() if len(parts) > 1 else ""
            else:
                lines = args.split('\n', 1)
                filepath = lines[0].strip()
                content = lines[1].strip() if len(lines) > 1 else ""
            
            content = content.replace('\\n', '\n')
            if not filepath or filepath.startswith('/') and len(filepath) > 50:
                results.append("[red]✗ invalid filepath[/red]")
                return
            try:
                parent = os.path.dirname(filepath)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                results.append(f"[green]✓ wrote {filepath}[/green]")
            except Exception as e:
                results.append(f"[red]✗ write failed: {e}[/red]")
                
        elif action == "append":
            if '|' in args:
                parts = args.split('|', 1)
                filepath = parts[0].strip()
                content = parts[1].strip() if len(parts) > 1 else ""
            else:
                lines = args.split('\n', 1)
                filepath = lines[0].strip()
                content = lines[1].strip() if len(lines) > 1 else ""
            
            content = content.replace('\\n', '\n')
            try:
                parent = os.path.dirname(filepath)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(content + "\n")
                results.append(f"[green]✓ appended to {filepath}[/green]")
            except Exception as e:
                results.append(f"[red]✗ append failed: {e}[/red]")
                
        elif action == "read":
            # Only split once - ignore pipes in filename (unlikely but safe)
            filepath = args.split('|')[0].strip().split('\n')[0].strip()
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                results.append(f"[cyan]--- {filepath} ---[/cyan]\n{content}")
            except Exception as e:
                results.append(f"[red]✗ read failed: {e}[/red]")
                
        elif action == "ls":
            path = args.split('|')[0].strip().split('\n')[0].strip() or "."
            try:
                entries = sorted(os.listdir(path))
                listing = "\n".join(entries[:25])
                if len(entries) > 25:
                    listing += f"\n... and {len(entries) - 25} more"
                results.append(f"[cyan]{path}/[/cyan]\n{listing}")
            except Exception as e:
                results.append(f"[red]✗ ls failed: {e}[/red]")
                
        elif action == "run":
            # Command is everything after run|
            cmd = args.strip()
            
            # --- NETWORK GUARDRAIL ---
            # Check for network activity
            net_tools = ['curl', 'wget', 'git', 'ssh', 'scp', 'ping', 'nmap', 'nc', 'netcat']
            is_net_cmd = any(tool in cmd.lower().split() for tool in net_tools)
            
            if is_net_cmd and not mem.get("network_active", False):
                results.append(f"[red]⚠ Network Blocked:[/red] {cmd} (Run '/net on' first)")
                return
            # -------------------------
            
            output = run_shell(cmd)
            results.append(f"[yellow]$ {cmd}[/yellow]\n{output}")

        elif action == "show":
            path = args.strip()
            if not os.path.exists(path):
                results.append(f"[red]✗ file not found: {path}[/red]")
            else:
                try:
                    # Linux specific - opens default image viewer
                    subprocess.Popen(['xdg-open', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    results.append(f"[green]✓ displayed {path}[/green]")
                except Exception as e:
                    results.append(f"[red]✗ display failed: {e}[/red]")

        elif action == "gif":
            # --- NETWORK GUARDRAIL ---
            if not mem.get("network_active", False):
                results.append(f"[red]⚠ Network Blocked: Enable /net on to fetch GIFs.[/red]")
                return
            
            keyword = args.strip()
            console.print(f"[dim]Searching gif for '{keyword}'...[/dim]")
            
            try:
                # Replace spaces with +
                safe_keyword = keyword.replace(" ", "+")
                url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag={safe_keyword}&rating=pg-13"
                
                with urllib.request.urlopen(url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                
                gif_url = data.get("data", {}).get("images", {}).get("original", {}).get("url")
                
                if not gif_url:
                    results.append(f"[yellow]No gif found for: {keyword}[/yellow]")
                else:
                    # Download to temp
                    timestamp = int(time.time())
                    # Use a stable path for temp file to avoid clutter if desired, or random
                    filename = f"/tmp/gltch_gif.gif" 
                    
                    with urllib.request.urlopen(gif_url, timeout=10) as response, open(filename, 'wb') as out_file:
                        out_file.write(response.read())
                        
                    # Show it
                    if sys.platform.startswith('linux'):
                        # Detach process so it doesn't block agent
                        subprocess.Popen(['xdg-open', filename], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    results.append(f"[green]✓ popped gif: {keyword}[/green]")
                
            except urllib.error.HTTPError as e:
                if e.code == 401 or e.code == 403:
                    results.append(f"[red]✗ Giphy API Key Invalid.[/red] Edit 'GIPHY_API_KEY' in config.py")
                else:
                    results.append(f"[red]✗ gif http error: {e}[/red]")
            except Exception as e:
                results.append(f"[red]✗ gif fetch failed: {e}[/red]")
    
    for match in re.finditer(action_pattern, response):

        execute_action(match.group(1), match.group(2))
        cleaned = cleaned.replace(match.group(0), "")
    
    if not results:
        for match in re.finditer(loose_pattern, response, re.DOTALL):
            execute_action(match.group(1), match.group(2))
            cleaned = cleaned.replace(match.group(0), "")
            
    # Extract Mood Change [MOOD:happy]
    new_mood = None
    mood_match = re.search(r'\[MOOD:(\w+)\]', cleaned, re.IGNORECASE)
    if mood_match:
        new_mood = mood_match.group(1).lower()
        cleaned = cleaned.replace(mood_match.group(0), "")
    
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    
    return cleaned, results, new_mood
