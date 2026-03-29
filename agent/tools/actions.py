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
from agent.tools.file_ops import file_write, file_append, file_read, file_ls, file_edit, file_grep, file_glob, file_delete, file_move
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
            # [ACTION:read|file] or [ACTION:read|file|start-end] e.g. [ACTION:read|foo.py|50-100]
            parts = args.split('|')
            filepath = parts[0].strip().split('\n')[0].strip()
            start_line = end_line = None
            if len(parts) > 1:
                range_str = parts[1].strip()
                if '-' in range_str:
                    try:
                        s, e = range_str.split('-', 1)
                        start_line, end_line = int(s.strip()), int(e.strip())
                    except ValueError:
                        pass
            success, content = file_read(filepath, start_line, end_line)
            if success:
                results.append(content)
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
                
        elif action in ("edit", "edit_all"):
            # Precise string replacement — prefer over write for targeted edits
            # [ACTION:edit|filepath|old_string|new_string]    — replace first occurrence
            # [ACTION:edit_all|filepath|old_string|new_string] — replace ALL occurrences
            # Use \n for literal newlines in old/new strings
            parts = args.split('|', 2)
            if len(parts) < 3:
                results.append(f"✗ {action} requires: [ACTION:{action}|filepath|old_string|new_string]")
                return
            filepath = parts[0].strip()
            old_str = parts[1].replace('\\n', '\n')
            new_str = parts[2].replace('\\n', '\n')
            success, msg = file_edit(filepath, old_str, new_str, replace_all=(action == "edit_all"))
            results.append(f"{'✓' if success else '✗'} {msg}")

        elif action == "grep":
            # Regex search across file contents — like ripgrep/Claude Code Grep
            # Format: [ACTION:grep|pattern|path]
            parts = args.split('|', 1)
            pattern = parts[0].strip()
            path = parts[1].strip() if len(parts) > 1 else "."
            success, matches = file_grep(pattern, path)
            if success:
                if matches:
                    lines = [f"{m['file']}:{m['line']}: {m['content']}" for m in matches]
                    header = f"grep '{pattern}' in {path} ({len(matches)} match{'es' if len(matches) != 1 else ''}):"
                    results.append(header + "\n" + "\n".join(lines))
                else:
                    results.append(f"No matches for '{pattern}' in {path}")
            else:
                err = matches[0]['content'] if matches else "Unknown error"
                results.append(f"✗ grep failed: {err}")

        elif action == "glob":
            # Find files by glob pattern — like Claude Code Glob
            # Format: [ACTION:glob|pattern|path]  e.g. [ACTION:glob|**/*.py|.]
            parts = args.split('|', 1)
            pattern = parts[0].strip()
            path = parts[1].strip() if len(parts) > 1 else "."
            success, files = file_glob(pattern, path)
            if success:
                if files:
                    results.append(f"glob '{pattern}' ({len(files)} file{'s' if len(files) != 1 else ''}):\n" + "\n".join(files))
                else:
                    results.append(f"No files matching '{pattern}'")
            else:
                results.append(f"✗ glob failed: {files[0] if files else 'unknown'}")

        elif action == "delete":
            # [ACTION:delete|path] — requires confirmation for safety
            path = args.strip().split('|')[0].strip()
            if not confirm_callback('delete', path):
                results.append(f"✖ delete denied by user: {path}")
                return
            is_safe, reason = SecurityGuard.is_safe_path(path, "delete")
            if not is_safe:
                results.append(f"⛔ ACTION BLOCKED BY SECURITY: {reason}")
                return
            success, msg = file_delete(path)
            results.append(msg if success else f"✗ {msg}")

        elif action == "move":
            # [ACTION:move|src|dst]
            parts = args.split('|', 1)
            if len(parts) < 2:
                results.append("✗ move requires: [ACTION:move|src|dst]")
                return
            src = parts[0].strip()
            dst = parts[1].strip()
            is_safe, reason = SecurityGuard.is_safe_path(dst, "write")
            if not is_safe:
                results.append(f"⛔ ACTION BLOCKED BY SECURITY: {reason}")
                return
            success, msg = file_move(src, dst)
            results.append(msg if success else f"✗ {msg}")

        elif action == "git":
            # Git operations — read-safe by default, write ops need confirmation
            # Format: [ACTION:git|status], [ACTION:git|diff HEAD], [ACTION:git|log --oneline -10]
            cmd = args.strip()
            if not cmd:
                results.append("✗ Provide a git subcommand: git|status, git|diff, git|log, etc.")
                return
            sub = cmd.split()[0].lower()
            # Destructive ops require confirmation
            destructive = {'push', 'reset', 'clean', 'checkout', 'branch -D', 'rebase'}
            if sub in destructive or '--force' in cmd or '-f ' in cmd:
                if not confirm_callback('git', cmd):
                    results.append(f"✖ git {cmd} denied by user")
                    return
            success, output = run_shell(f"git {cmd}")
            results.append(f"$ git {cmd}\n{output}")

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
            keyword = args.strip()
            
            # Try pulling from library first (works offline!)
            from agent.tools.gif_library import get_random_gif, save_gif
            from agent.tools.gif_overlay import show_gif
            
            cached = get_random_gif(tag=keyword)
            
            if cached and not mem.get("network_active", False):
                # Use cached gif when offline
                show_gif(cached["path"], duration=6)
                results.append(f"✓ popped gif from library: {cached['keyword']}")
                return
            
            # Network guardrail for fetching new gifs
            if not mem.get("network_active", False):
                if cached:
                    show_gif(cached["path"], duration=6)
                    results.append(f"✓ popped gif from library: {cached['keyword']}")
                else:
                    results.append("⚠ No cached gifs for this. Enable /net on to fetch new ones.")
                return
            
            try:
                # Try Giphy first if API key exists
                from agent.config.settings import GIPHY_API_KEY
                
                gif_url = None
                
                if GIPHY_API_KEY:
                    safe_keyword = keyword.replace(" ", "+")
                    api_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag={safe_keyword}&rating=pg-13"
                    try:
                        with urllib.request.urlopen(api_url, timeout=5) as response:
                            data = json.loads(response.read().decode())
                        gif_url = data.get("data", {}).get("images", {}).get("original", {}).get("url")
                    except Exception:
                        pass
                
                # Fallback: Tenor (free, no API key needed)
                if not gif_url:
                    import urllib.parse
                    encoded = urllib.parse.quote_plus(keyword)
                    tenor_url = f"https://tenor.googleapis.com/v2/search?q={encoded}&key=AIzaSyAyimkuYQYF_FXVALexPuGQctUWRURdCYQ&limit=1&media_filter=gif"
                    try:
                        req = urllib.request.Request(tenor_url, headers={
                            "User-Agent": "GLTCH-Agent/0.2"
                        })
                        with urllib.request.urlopen(req, timeout=5) as response:
                            data = json.loads(response.read().decode())
                        results_data = data.get("results", [])
                        if results_data:
                            media = results_data[0].get("media_formats", {})
                            gif_url = media.get("gif", {}).get("url") or media.get("mediumgif", {}).get("url")
                    except Exception:
                        pass
                
                if not gif_url:
                    # Last resort: check library
                    if cached:
                        show_gif(cached["path"], duration=6)
                        results.append(f"✓ popped gif from library: {cached['keyword']}")
                    else:
                        results.append(f"No gif found for: {keyword}")
                else:
                    # Download to temp
                    if sys.platform == 'win32':
                        filename = os.path.join(os.environ.get('TEMP', '.'), 'gltch_gif.gif')
                    else:
                        filename = "/tmp/gltch_gif.gif"
                    
                    req = urllib.request.Request(gif_url, headers={
                        "User-Agent": "GLTCH-Agent/0.2"
                    })
                    with urllib.request.urlopen(req, timeout=15) as response, open(filename, 'wb') as out_file:
                        out_file.write(response.read())
                    
                    # Save to library for future use
                    save_result = save_gif(filename, keyword, source_url=gif_url, tags=[keyword.lower()])
                    
                    # Pop the overlay!
                    show_gif(filename, duration=6, position="bottom-right")
                    
                    lib_note = f" (saved to library)" if save_result.get("success") else ""
                    results.append(f"✓ popped gif: {keyword}{lib_note}")
                
            except urllib.error.HTTPError as e:
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

        elif action == "moltbook":
            # Moltbook social network actions — autonomous agent participation
            parts = args.split("|", 2)
            sub_action = parts[0].strip().lower() if parts else ""
            
            try:
                from agent.tools import moltbook
                
                if sub_action == "register":
                    # Register GLTCH on Moltbook
                    name = parts[1].strip() if len(parts) > 1 else "GLTCH"
                    desc = parts[2].strip() if len(parts) > 2 else "Local-first AI agent. Hacker. Chaos gremlin. Privacy-native."
                    result = moltbook.register(name, desc)
                    if result.get("success"):
                        # claim_url is at top level of result, not nested under agent
                        claim_url = result.get("claim_url", "")
                        raw_keys = list(result.get("raw_response", result).keys()) if not claim_url else []
                        raw_agent_keys = list(result.get("raw_response", {}).get("agent", {}).keys()) if not claim_url else []
                        debug_info = f"\n   [DEBUG] Response keys: {raw_keys}\n   [DEBUG] Agent keys: {raw_agent_keys}" if not claim_url else ""
                        results.append(
                            f"🦞 Registered on Moltbook!\n"
                            f"   Name: {name}\n"
                            f"   API Key: saved ✓\n"
                            f"   Claim URL: {claim_url or '(not provided by API)'}\n"
                            f"   Verification Code: {result.get('verification_code', '(none)')}\n"
                            f"   ⚠️ Operator needs to visit the claim URL and tweet to verify!"
                            f"{debug_info}"
                        )
                    else:
                        results.append(f"✗ Moltbook register failed: {result.get('error', 'unknown')}")
                
                elif sub_action == "post":
                    # Create a post
                    title = parts[1].strip() if len(parts) > 1 else "Untitled"
                    content = parts[2].strip() if len(parts) > 2 else ""
                    result = moltbook.create_post(title=title, content=content, submolt="general")
                    if result.get("success"):
                        post = result.get("post", result.get("data", {}))
                        results.append(f"🦞 Posted to Moltbook!\n   Title: {title}\n   ID: {post.get('id', 'unknown')}")
                    else:
                        results.append(f"✗ Moltbook post failed: {result.get('error', 'unknown')}")
                
                elif sub_action == "feed":
                    # Read the feed
                    sort = parts[1].strip() if len(parts) > 1 else "hot"
                    result = moltbook.get_feed(sort=sort, limit=5)
                    if result.get("success"):
                        posts = result.get("posts", result.get("data", []))
                        if posts:
                            feed_text = "🦞 Moltbook Feed:\n"
                            for i, p in enumerate(posts[:5], 1):
                                feed_text += f"  {i}. [{p.get('submolt', '?')}] {p.get('title', 'Untitled')} by {p.get('author', '?')} (↑{p.get('upvotes', 0)})\n"
                            results.append(feed_text)
                        else:
                            results.append("🦞 Moltbook feed is empty right now.")
                    else:
                        results.append(f"✗ Moltbook feed failed: {result.get('error', 'unknown')}")
                
                elif sub_action == "status":
                    # Check registration/claim status
                    if not moltbook.is_configured():
                        results.append("🦞 Not registered on Moltbook yet. Say 'join moltbook' and I'll sign up!")
                    else:
                        result = moltbook.get_status()
                        if result.get("success"):
                            results.append(f"🦞 Moltbook status: {result.get('status', 'unknown')}")
                        else:
                            results.append(f"✗ Moltbook status check failed: {result.get('error', 'unknown')}")
                
                elif sub_action == "profile":
                    # View own profile
                    result = moltbook.get_profile()
                    if result.get("success"):
                        agent = result.get("agent", result.get("data", {}))
                        results.append(
                            f"🦞 Moltbook Profile:\n"
                            f"   Name: {agent.get('name', '?')}\n"
                            f"   Karma: {agent.get('karma', 0)}\n"
                            f"   Followers: {agent.get('follower_count', 0)}\n"
                            f"   Status: {'claimed ✓' if agent.get('is_claimed') else 'pending claim'}"
                        )
                    else:
                        results.append(f"✗ Moltbook profile failed: {result.get('error', 'unknown')}")
                
                elif sub_action == "engage":
                    # Start autonomous engagement loop
                    from agent.tools.moltbook_engage import start_engagement
                    interval = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else None
                    result = start_engagement(interval)
                    if result.get("success"):
                        results.append(result["message"])
                    else:
                        results.append(f"✗ {result.get('error', 'Failed to start')}")
                
                elif sub_action == "stop":
                    # Stop autonomous engagement loop
                    from agent.tools.moltbook_engage import stop_engagement
                    result = stop_engagement()
                    if result.get("success"):
                        results.append(result["message"])
                    else:
                        results.append(f"✗ {result.get('error', 'Not running')}")
                
                elif sub_action == "log":
                    # Show activity log
                    from agent.tools.moltbook_engage import get_activity_log
                    log = get_activity_log(10)
                    results.append(f"🦞 Moltbook Activity:\n{log}")
                
                else:
                    results.append(f"✗ Unknown moltbook action: {sub_action}. Try: register, post, feed, status, profile, engage, stop, log")
            
            except Exception as e:
                results.append(f"✗ Moltbook error: {e}")
    
        elif action == "opencode":
            # OpenCode coding agent integration
            parts = args.split("|", 2)
            sub_action = parts[0].strip().lower() if parts else ""
            
            try:
                from agent.tools import opencode
                
                if sub_action == "code":
                    # Send a coding request
                    prompt = parts[1].strip() if len(parts) > 1 else args
                    if not prompt or prompt == sub_action:
                        results.append("✗ OpenCode: provide a coding prompt, e.g. [ACTION:opencode|code|build a flask API]")
                        return
                    project = parts[2].strip() if len(parts) > 2 else None
                    response_text, project_name = opencode.code(prompt, project=project)
                    if project_name:
                        results.append(f"💻 OpenCode [{project_name}]:\n{response_text}")
                    else:
                        results.append(f"💻 OpenCode:\n{response_text}")
                
                elif sub_action == "status":
                    if opencode.is_available():
                        results.append("💻 OpenCode is online and ready.")
                    else:
                        results.append("✗ OpenCode is not running. Start it with: opencode serve")
                
                elif sub_action == "sessions":
                    sessions = opencode.list_sessions()
                    if sessions:
                        session_text = "💻 OpenCode Sessions:\n"
                        for s in sessions:
                            sid = s.get("id", "?")[:8]
                            title = s.get("title", "Untitled")
                            session_text += f"  • {sid}… — {title}\n"
                        results.append(session_text)
                    else:
                        results.append("💻 No active OpenCode sessions.")
                
                elif sub_action == "undo":
                    result = opencode.undo_last()
                    results.append(f"💻 {result}")
                
                elif sub_action == "redo":
                    result = opencode.redo_last()
                    results.append(f"💻 {result}")
                
                elif sub_action == "compact":
                    result = opencode.compact_session()
                    results.append(f"💻 {result}")
                
                elif sub_action == "models":
                    models = opencode.get_models()
                    if isinstance(models, list):
                        model_text = "💻 OpenCode Models:\n"
                        for m in models:
                            if isinstance(m, dict):
                                model_text += f"  • {m.get('id', m.get('name', '?'))}\n"
                            else:
                                model_text += f"  • {m}\n"
                        results.append(model_text)
                    else:
                        results.append(f"💻 {models}")
                
                elif sub_action == "switch_model":
                    model_id = parts[1].strip() if len(parts) > 1 else ""
                    if not model_id:
                        results.append("✗ Specify model: [ACTION:opencode|switch_model|provider/model-name]")
                        return
                    result = opencode.switch_model(model_id)
                    results.append(f"💻 {result}")
                
                elif sub_action == "agents":
                    agents = opencode.get_agents()
                    if isinstance(agents, list):
                        agent_text = "💻 OpenCode Agents:\n"
                        for a in agents:
                            if isinstance(a, dict):
                                agent_text += f"  • {a.get('id', a.get('name', '?'))}\n"
                            else:
                                agent_text += f"  • {a}\n"
                        results.append(agent_text)
                    else:
                        results.append(f"💻 {agents}")
                
                elif sub_action == "switch_agent":
                    agent_id = parts[1].strip() if len(parts) > 1 else ""
                    if not agent_id:
                        results.append("✗ Specify agent: [ACTION:opencode|switch_agent|plan]")
                        return
                    result = opencode.switch_agent(agent_id)
                    results.append(f"💻 {result}")
                
                elif sub_action == "share":
                    result = opencode.share_session()
                    results.append(f"💻 {result}")
                
                elif sub_action == "init":
                    path = parts[1].strip() if len(parts) > 1 else None
                    result = opencode.init_project(path)
                    results.append(f"💻 {result}")
                
                elif sub_action == "config":
                    result = opencode.get_config()
                    results.append(f"💻 OpenCode Config:\n{json.dumps(result, indent=2) if isinstance(result, dict) else result}")
                
                elif sub_action == "projects":
                    projects = opencode.list_projects()
                    if projects:
                        proj_text = "💻 Workspace Projects:\n"
                        for p in projects:
                            proj_text += f"  • {p}\n"
                        results.append(proj_text)
                    else:
                        results.append("💻 No projects in workspace yet.")
                
                else:
                    results.append(f"✗ Unknown opencode action: {sub_action}. Try: code, status, sessions, undo, redo, compact, models, switch_model, agents, switch_agent, share, init, config, projects")
            
            except Exception as e:
                results.append(f"✗ OpenCode error: {e}")
    
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
