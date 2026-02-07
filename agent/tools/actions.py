"""
GLTCH Action Parser
Parse and execute [ACTION:...] tags from LLM responses.
"""

import os
import re
import json
import time
import urllib.request
import urllib.error
import subprocess
import sys
from typing import Tuple, List, Optional, Dict, Any

from agent.tools.shell import run_shell
from agent.tools.file_ops import file_write, file_append, file_read, file_ls
from agent.tools.security import SecurityGuard


def extract_thinking(response: str) -> tuple[str, str]:
    """
    Extract thinking content and response separately.
    Returns (thinking_content, response_content).
    """
    thinking = ""
    clean_response = response
    
    # Extract thinking content
    think_match = re.search(r'<think>(.*?)</think>', response, flags=re.DOTALL)
    if think_match:
        thinking = think_match.group(1).strip()
        # Get content after </think>
        parts = response.split('</think>')
        if len(parts) > 1:
            clean_response = parts[-1].strip()
        else:
            clean_response = ""
    else:
        # Handle unclosed think block (still streaming)
        if '<think>' in response:
            parts = response.split('<think>')
            thinking = parts[-1].strip() if len(parts) > 1 else ""
            clean_response = ""
    
    return thinking, clean_response


def strip_thinking(response: str) -> str:
    """
    Remove <think>...</think> blocks from reasoning models like DeepSeek R1.
    Handles both closed and unclosed think blocks.
    """
    _, clean = extract_thinking(response)
    
    if clean:
        # Clean up any orphan tags that slipped through
        clean = re.sub(r'</?think>', '', clean)
        return clean.strip()
    
    # If no response after thinking, try to extract something meaningful
    think_match = re.search(r'<think>(.*?)</think>', response, flags=re.DOTALL)
    if think_match:
        think_content = think_match.group(1).strip()
        lines = [l.strip() for l in think_content.split('\n') if l.strip()]
        for line in reversed(lines):
            if any(x in line.lower() for x in ['should i', 'let me', 'i need to', 'thinking', 'the user']):
                continue
            if len(line) > 5 and len(line) < 200:
                return line
        if lines:
            return lines[-1][:150]
    
    # Final fallback: clean any remaining tags
    return re.sub(r'</?think>', '', response).strip()


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
        # Skip common well-known paths
        known_paths = ['/etc/passwd', '/etc/hosts', '/etc/fstab', '/etc/resolv.conf',
                       '/etc/systemd/', '/usr/bin/', '/var/log/', '/home/']
        if any(f.startswith(k) for k in known_paths):
            continue
        if not os.path.exists(f) and not os.path.exists(os.path.dirname(f)):
            warnings.append(f"⚠ Verify: {f} does not exist on this system")
    
    # Look for systemctl commands with service names
    service_pattern = r'systemctl\s+(?:enable|start|restart|status)\s+([a-zA-Z0-9\-_@]+(?:\.service)?)'
    services = re.findall(service_pattern, response)
    for svc in set(services):
        svc_name = svc if svc.endswith('.service') else f"{svc}.service"
        result = subprocess.run(
            f"systemctl list-unit-files {svc_name} 2>/dev/null | grep -q {svc_name.replace('.service', '')}",
            shell=True, capture_output=True
        )
        if result.returncode != 0 and '@' not in svc:
            warnings.append(f"⚠ Verify: service '{svc}' not found in systemctl")
    
    return warnings


def parse_and_execute_actions(
    response: str,
    mem: Optional[Dict[str, Any]] = None,
    confirm_callback=None
) -> Tuple[str, List[str], Optional[str]]:
    """
    Parse LLM response for [ACTION:...] tags and execute them.
    
    Args:
        response: The LLM response to parse
        mem: Memory dict (for network state check)
        confirm_callback: Optional callback for user confirmation (receives action, args)
                         Should return True to allow, False to deny
    
    Returns:
        (cleaned_response, list_of_action_results, new_mood_or_none)
    """
    results = []
    cleaned = strip_thinking(response)
    mem = mem or {}
    
    # Default confirm callback (always True for headless/RPC mode)
    if confirm_callback is None:
        confirm_callback = lambda action, args: True
    
    # Matches [ACTION:command|args]
    action_pattern = r'\[ACTION:(\w+)\|(.+?)\]'
    
    # Loose match for multi-line block actions
    loose_pattern = r'\[ACTION:(\w+)\]\s*\n([^\[]+?)(?=\n\n|\n\[|$)'
    
    def execute_action(action: str, args: str):
        action = action.lower().strip()
        args = args.strip()
        
        # 1. Hard Guardrails (Always Active)
        is_safe, reason = SecurityGuard.validate_action(action, args)
        if not is_safe:
            results.append(f"⛔ ACTION BLOCKED BY SECURITY: {reason}")
            return

        # 2. User Confirmation (Safety Layer)
        # If callback returns False, user denied action
        if not confirm_callback(action, args):
            results.append(f"✖ Skipped user-denied action: {action}")
            return
        
        if action == "write":
            if '|' in args:
                parts = args.split('|', 1)
                filepath = parts[0].strip()
                content = parts[1].strip() if len(parts) > 1 else ""
            else:
                lines = args.split('\n', 1)
                filepath = lines[0].strip()
                content = lines[1].strip() if len(lines) > 1 else ""
            
            content = content.replace('\\n', '\n')
            success, msg = file_write(filepath, content)
            results.append(f"{'✓' if success else '✗'} {msg}")
                
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
            success, msg = file_append(filepath, content)
            results.append(f"{'✓' if success else '✗'} {msg}")
                
        elif action == "read":
            filepath = args.split('|')[0].strip().split('\n')[0].strip()
            success, content = file_read(filepath)
            if success:
                results.append(f"--- {filepath} ---\n{content}")
            else:
                results.append(f"✗ {content}")
                
        elif action == "ls":
            path = args.split('|')[0].strip().split('\n')[0].strip() or "."
            success, entries = file_ls(path)
            if success:
                listing = "\n".join([
                    f"{'📁 ' if e['is_dir'] else ''}{e['name']}" + 
                    (f" ({e['size']}b)" if not e['is_dir'] else "/")
                    for e in entries[:25]
                ])
                if len(entries) > 25:
                    listing += f"\n... and {len(entries) - 25} more"
                results.append(f"{path}/\n{listing}")
            else:
                results.append(f"✗ {entries}")
                
        elif action == "run":
            cmd = args.strip()
            
            # Network guardrail
            net_tools = ['curl', 'wget', 'git', 'ssh', 'scp', 'ping', 'nmap', 'nc', 'netcat']
            is_net_cmd = any(tool in cmd.lower().split() for tool in net_tools)
            
            if is_net_cmd and not mem.get("network_active", False):
                results.append(f"⚠ Network Blocked: {cmd} (Run '/net on' first)")
                return
            
            # Tool availability check
            import shutil
            cmd_parts = cmd.split()
            if cmd_parts:
                tool_name = cmd_parts[0]
                if not shutil.which(tool_name):
                    results.append(f"⚠ Tool not found: '{tool_name}' is not installed or not in PATH.")
                    results.append(f"💡 Install it first, then try again.")
                    return
            
            success, output = run_shell(cmd)
            results.append(f"$ {cmd}\n{output}")

        elif action == "show":
            path = args.strip()
            if not os.path.exists(path):
                results.append(f"✗ file not found: {path}")
            else:
                try:
                    if sys.platform.startswith('linux'):
                        subprocess.Popen(['xdg-open', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif sys.platform == 'win32':
                        os.startfile(path)
                    results.append(f"✓ displayed {path}")
                except Exception as e:
                    results.append(f"✗ display failed: {e}")

        elif action == "gif":
            # Network guardrail
            if not mem.get("network_active", False):
                results.append("⚠ Network Blocked: Enable /net on to fetch GIFs.")
                return
            
            keyword = args.strip()
            try:
                from agent.config.settings import GIPHY_API_KEY
                safe_keyword = keyword.replace(" ", "+")
                url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag={safe_keyword}&rating=pg-13"
                
                with urllib.request.urlopen(url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                
                gif_url = data.get("data", {}).get("images", {}).get("original", {}).get("url")
                
                if not gif_url:
                    results.append(f"No gif found for: {keyword}")
                else:
                    # Download to temp
                    if sys.platform == 'win32':
                        filename = os.path.join(os.environ.get('TEMP', '.'), 'gltch_gif.gif')
                    else:
                        filename = "/tmp/gltch_gif.gif"
                    
                    with urllib.request.urlopen(gif_url, timeout=10) as response, open(filename, 'wb') as out_file:
                        out_file.write(response.read())
                    
                    # Show it
                    if sys.platform.startswith('linux'):
                        subprocess.Popen(['xdg-open', filename], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif sys.platform == 'win32':
                        os.startfile(filename)
                    
                    results.append(f"✓ popped gif: {keyword}")
                
            except urllib.error.HTTPError as e:
                if e.code == 401 or e.code == 403:
                    results.append("✗ Giphy API Key Invalid. Edit 'GIPHY_API_KEY' in config.")
                else:
                    results.append(f"✗ gif http error: {e}")
            except Exception as e:
                results.append(f"✗ gif fetch failed: {e}")

        elif action == "search":
            # Web search - works even with network "off" (it's knowledge, not a tool)
            query = args.strip()
            try:
                from agent.tools.web_search import web_search
                result = web_search(query)
                if result["success"]:
                    results.append(result["formatted"])
                else:
                    results.append(f"✗ Search failed: {result['formatted']}")
            except Exception as e:
                results.append(f"✗ Search error: {e}")

        elif action == "browse":
            # Browse a web page for content
            if not mem.get("network_active", False):
                results.append("⚠ Network Blocked: Enable /net on to browse.")
                return
            
            url_to_browse = args.strip()
            try:
                from agent.tools.browser import browse_url
                result = browse_url(url_to_browse)
                if result["success"]:
                    content = result.get("content", "")[:3000]
                    results.append(f"🌐 {result.get('title', 'Page')}\n{result.get('url', url_to_browse)}\n\n{content}")
                else:
                    # Fallback to simple urllib fetch
                    req = urllib.request.Request(url_to_browse, headers={
                        "User-Agent": "GLTCH-Agent/0.2"
                    })
                    with urllib.request.urlopen(req, timeout=10) as response:
                        html = response.read().decode('utf-8', errors='replace')
                    # Strip HTML tags for basic text extraction
                    text = re.sub(r'<[^>]+>', ' ', html)
                    text = re.sub(r'\s+', ' ', text)[:3000]
                    results.append(f"🌐 {url_to_browse}\n{text}")
            except Exception as e:
                results.append(f"✗ Browse failed: {e}")
    
    # Execute inline actions (deduplicated)
    seen_actions = set()
    for match in re.finditer(action_pattern, response):
        action_key = (match.group(1).lower(), match.group(2).strip())
        if action_key not in seen_actions:
            seen_actions.add(action_key)
            execute_action(match.group(1), match.group(2))
        cleaned = cleaned.replace(match.group(0), "")
    
    # Execute block actions if no inline found
    if not results:
        for match in re.finditer(loose_pattern, response, re.DOTALL):
            action_key = (match.group(1).lower(), match.group(2).strip())
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                execute_action(match.group(1), match.group(2))
            cleaned = cleaned.replace(match.group(0), "")
    
    # Extract mood change [MOOD:happy]
    new_mood = None
    mood_match = re.search(r'\[MOOD:(\w+)\]', cleaned, re.IGNORECASE)
    if mood_match:
        new_mood = mood_match.group(1).lower()
        cleaned = cleaned.replace(mood_match.group(0), "")
    
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    
    return cleaned, results, new_mood
