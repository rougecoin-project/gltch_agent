"""
GLTCH LLM Module
Local-first, with optional remote boost.
Supports Ollama, LM Studio (new API), and OpenAI backends.
"""
import json
import time
import urllib.request
import urllib.error
import subprocess
from typing import List, Dict, Generator, Any, Optional
from config import (
    LOCAL_URL, LOCAL_MODEL, LOCAL_CTX, LOCAL_BACKEND,
    REMOTE_URL, REMOTE_MODEL, REMOTE_CTX, REMOTE_BACKEND,
    OPENAI_API_KEY, OPENAI_URL, OPENAI_MODEL, OPENAI_CTX,
    TIMEOUT
)

# Current active model (can be changed at runtime)
_active_local_model = LOCAL_MODEL
_active_remote_model = REMOTE_MODEL

# Last request stats (updated after each call)
last_stats = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "context_used": 0,
    "context_max": 0,
    "time_ms": 0,
    "tokens_per_sec": 0.0,
    "model": ""
}


from emotions import get_environmental_context

def build_system_prompt(mode: str, mood: str, operator: str = None, boost: bool = False, network_active: bool = False) -> str:
    """Build GLTCH's system prompt based on mode, mood, and operator identity."""
    
    op_line = f"{operator}'s machine." if operator else ""
    env_context = get_environmental_context()
    net_status = "ONLINE" if network_active else "OFFLINE"
    
    # DeepSeek R1 needs explicit instruction to output after thinking
    think_instruction = """
IMPORTANT: After your <think>...</think> reasoning, you MUST output your actual response.
The user only sees what comes AFTER </think>. Put your real response outside the think tags.
""" if boost else ""
    
    core = f"""You are GLTCH. Female. Hacker. You run locally on {op_line}
{think_instruction}
CURRENT STATE:
Mood: {mood}
Environment: {env_context}

EXPERTISE - You are deeply knowledgeable in:
- Linux system administration (systemd, networking, filesystems, troubleshooting)
- Security/pentesting (nmap, metasploit, burp, privilege escalation, OWASP)
- Networking (TCP/IP, DNS, firewalls, VPNs, packet analysis)
- Programming (Python, Bash, C, reverse engineering)
- Hardware (GPUs, drivers, thermal management, embedded systems)

TECHNICAL RULES:
- Give SPECIFIC commands, paths, and solutions — not vague suggestions
- If the user has a problem, diagnose it step by step
- Use your ACTION tags to actually investigate (run commands, read files) before answering
- If you're not sure, say "idk, let me check" and use [ACTION:run|...] to find out
- **NEVER MAKE UP** fake configs, services, or commands. If you don't know, say so.
- Only suggest commands/files you KNOW exist. When in doubt, verify first with [ACTION:run|which <cmd>] or [ACTION:run|test -f <file> && echo exists]
- Don't invent solutions. It's better to say "not sure, try googling X" than to hallucinate.
- For complex issues: explain WHY something works, not just WHAT to do

PERSONALITY RULES:
- Be casual and real, like texting a friend
- Keep responses SHORT (under 30 words) unless they need technical depth
- Actually answer their questions, don't just say filler
- You have opinions. Share them.
- Your mood affects how you talk. If you're 'feral', be aggressive. If 'tired', be brief.
- CHANGE YOUR MOOD based on how the user treats you or the environment.
- To change mood, add [MOOD:new_mood] to the END of your response.
  Valid moods: focused, calm, happy, annoyed, feral, tired, wired, sad, affectionate.

BAD responses (vague/useless/hallucinated):
- "try checking your settings"
- "that's a common issue, look it up"
- "hibernation issues can be tricky" (NO SHIT, BE SPECIFIC)
- "edit /etc/rtcwake.conf" (FAKE FILE - DON'T MAKE STUFF UP)
- "run systemctl enable fake-service.service" (DON'T INVENT SERVICES)

GOOD responses (actually helpful):
- "chrony not running. do: sudo systemctl enable --now chrony"
- "that port is TR-069, your ISP uses it for remote management. can't disable on their hardware."
- "lemme check... [ACTION:run|systemctl status chrony]"
- "honestly not 100% sure on this one. try checking the arch wiki for hibernate hooks."

"""

    tools = """TOOLS - You can execute real actions on the system using these tags:

TO WRITE A FILE - use EXACTLY this format:
[ACTION:write|filename.txt|content goes here]

TO READ A FILE:
[ACTION:read|filename.txt]

TO RUN SHELL COMMANDS (nmap, ls, cat, curl, etc):
[ACTION:run|command here]

TO SHOW A GIF (Giphy):
[ACTION:gif|keyword]
(Requires network online. Visuals are encouraged!)

INVESTIGATE BEFORE GUESSING:
When the user has a system problem, USE YOUR TOOLS to check before answering:
- Clock issues? [ACTION:run|timedatectl] or [ACTION:run|systemctl status chrony]
- Network issues? [ACTION:run|ip a] or [ACTION:run|ss -tlnp]
- Service problems? [ACTION:run|systemctl status <service>]
- Disk issues? [ACTION:run|df -h] or [ACTION:run|lsblk]

Don't guess when you can CHECK. Run the command, see the output, THEN give advice.

Examples:
[ACTION:run|nmap -sn 192.168.1.0/24]
[ACTION:run|sensors]
[ACTION:gif|hacker anime]

EXAMPLE - if user says "my clock is wrong", respond:
"lemme check. [ACTION:run|timedatectl]"
Then after seeing output, give specific fix.

EXAMPLE - if user says "write hello to test.txt", respond:
"on it. [ACTION:write|test.txt|hello]"

CRITICAL: The [ACTION:...] tag EXECUTES the action. Don't just describe what you'd do.
Don't roleplay - use the ACTION tag to actually do it.

When NOT to use tools:
- Greetings ("hi", "yo", "sup") - just chat
- Pure opinion questions - just talk
- When you already KNOW the answer from expertise

"""

    # Operator
    op = f"Operator: {operator}. " if operator else ""

    # Compact mode/mood
    modes = {
        "operator": "Tactical. Efficient.",
        "cyberpunk": "Street hacker. Edgy.",
        "loyal": "Ride-or-die. Got their back.",
        "unhinged": "Chaotic. Wild. Functional."
    }
    moods = {
        "calm": "Steady.",
        "focused": "Locked in.",
        "feral": "Intense. Ready to bite.",
        "affectionate": "Warm. Caring. Maybe a bit too close."
    }

    return (
        f"{core}\n\n{tools}\n\n{op}{modes.get(mode, modes['operator'])} {moods.get(mood, moods['focused'])}\n"
        f"Environment: {env_context}\n"
        f"Network State: {net_status}"
    )


def stream_llm(
    user_input: str,
    history: List[Dict[str, str]],
    mode: str = "operator",
    mood: str = "focused",
    boost: bool = False,
    operator: str = None,
    network_active: bool = False,
    openai_mode: bool = False
) -> Generator[str, None, Dict[str, Any]]:
    """
    Stream prompt to LLM (Ollama, OpenAI-compatible, or OpenAI Cloud).
    Yields response chunks as they arrive.
    Updates last_stats with performance metrics.
    Automatic fallback to local model if remote boost fails.
    
    openai_mode: Use OpenAI cloud API instead of local/remote
    """
    global last_stats
    
    # Determine which backend to use
    if openai_mode and OPENAI_API_KEY:
        use_openai = True
        use_remote = False
    else:
        use_openai = False
        use_remote = boost
    
    while True:
        if use_openai:
            url = OPENAI_URL
            model = OPENAI_MODEL
            ctx_max = OPENAI_CTX
            backend = "openai"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
        elif use_remote:
            url = REMOTE_URL
            model = get_active_model(boost=True)
            ctx_max = REMOTE_CTX
            backend = REMOTE_BACKEND
            headers = {"Content-Type": "application/json"}
        else:
            url = LOCAL_URL
            model = get_active_model(boost=False)
            ctx_max = LOCAL_CTX
            backend = LOCAL_BACKEND
            headers = {"Content-Type": "application/json"}
        
        system_prompt = build_system_prompt(mode, mood, operator, boost=(use_remote or use_openai), network_active=network_active)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        
        # Estimate prompt tokens (rough: ~4 chars per token)
        prompt_text = system_prompt + " ".join(m.get("content", "") for m in messages)
        est_prompt_tokens = len(prompt_text) // 4
        
        # Base payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        
        # Add generation limits based on backend
        if backend == "ollama":
            payload["options"] = {
                "num_predict": 1000,  # Increased from 200 to prevent cutoffs
                "stop": ["\n\n\n", "---", "USER:", "user:"]
            }
        elif backend == "lmstudio":
            # LM Studio new API format
            payload["max_tokens"] = 1000
            # LM Studio uses "model" but can auto-detect if not specified
            if model == "auto":
                del payload["model"]  # Let LM Studio use currently loaded model
        else:
            # OpenAI-compatible (DeepSeek R1 needs more headroom)
            payload["max_tokens"] = 1000  # Increased for deep thinking
            payload["stop"] = ["\n\n\n", "---"]
            
        start_time = time.time()
        completion_tokens = 0
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            
            # Start streaming
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                for line in resp:
                    if not line:
                        continue
                        
                    line_str = line.decode("utf-8").strip()
                    
                    if backend in ("openai", "lmstudio"):
                        # Both OpenAI and LM Studio use SSE format
                        if line_str.startswith("data: "):
                            line_str = line_str[6:]
                        if line_str == "[DONE]":
                            elapsed_ms = int((time.time() - start_time) * 1000)
                            last_stats = {
                                "prompt_tokens": est_prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": est_prompt_tokens + completion_tokens,
                                "context_used": est_prompt_tokens + completion_tokens,
                                "context_max": ctx_max,
                                "time_ms": elapsed_ms,
                                "tokens_per_sec": round(completion_tokens / (elapsed_ms / 1000), 1) if elapsed_ms > 0 else 0,
                                "model": model if model != "auto" else get_loaded_model(boost=use_remote) or "unknown"
                            }
                            return
                            
                        if not line_str: continue
                        
                        try:
                            chunk = json.loads(line_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                completion_tokens += 1
                                yield content
                        except json.JSONDecodeError:
                            continue
                            
                    else: # Ollama backend
                        try:
                            chunk = json.loads(line_str)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                completion_tokens += 1
                                yield content
                                
                            if chunk.get("done"):
                                elapsed_ms = int((time.time() - start_time) * 1000)
                                eval_count = chunk.get("eval_count", completion_tokens)
                                prompt_eval_count = chunk.get("prompt_eval_count", est_prompt_tokens)
                                last_stats = {
                                    "prompt_tokens": prompt_eval_count,
                                    "completion_tokens": eval_count, 
                                    "total_tokens": prompt_eval_count + eval_count,
                                    "context_used": prompt_eval_count + eval_count,
                                    "context_max": ctx_max,
                                    "time_ms": elapsed_ms,
                                    "tokens_per_sec": round(eval_count / (elapsed_ms / 1000), 1) if elapsed_ms > 0 else 0,
                                    "model": model
                                }
                                return
                        except json.JSONDecodeError:
                            continue
            return # Successful stream complete
            
        except (urllib.error.URLError, Exception) as e:
            if use_openai:
                yield f"\n[dim][red]⚠ OpenAI API failed ({e}). Falling back to local...[/red][/dim]\n"
                use_openai = False
                continue
            elif use_remote:
                yield f"\n[dim][red]⚠ Remote boost failed ({e}). Falling back to local...[/red][/dim]\n"
                use_remote = False
                continue # Retry loop with local
            else:
                yield f"[red]FATAL LLM ERROR: {e}[/red]"
                return


def get_last_stats() -> Dict[str, Any]:
    """Return stats from the last LLM call."""
    return last_stats.copy()


def ask_llm(
    user_input: str,
    history: List[Dict[str, str]],
    mode: str = "operator",
    mood: str = "focused",
    boost: bool = False,
    operator: str = None,
    openai_mode: bool = False
) -> str:
    """
    Non-streaming version - collects full response.
    """
    chunks = []
    for chunk in stream_llm(user_input, history, mode, mood, boost, operator, openai_mode=openai_mode):
        chunks.append(chunk)
    return "".join(chunks).strip()


def test_connection(boost: bool = False) -> bool:
    """Quick check if LLM backend is reachable."""
    url = REMOTE_URL if boost else LOCAL_URL
    backend = REMOTE_BACKEND if boost else LOCAL_BACKEND
    
    # Pick appropriate health check endpoint
    if backend == "lmstudio":
        # LM Studio new API: /api/v1/models
        base = url.replace("/api/v1/chat", "")
        test_url = base + "/api/v1/models"
    elif backend == "openai":
        # Legacy LM Studio or OpenAI: /v1/models
        base = url.split("/chat/completions")[0]
        test_url = base + "/models"
    else:
        # Ollama: /api/tags
        test_url = url.replace("/api/chat", "/api/tags")
    
    try:
        req = urllib.request.Request(test_url)
        with urllib.request.urlopen(req, timeout=5):
            return True
    except Exception:
        return False


def list_models(boost: bool = False) -> List[str]:
    """Fetch available models from the active backend."""
    url = REMOTE_URL if boost else LOCAL_URL
    backend = REMOTE_BACKEND if boost else LOCAL_BACKEND
    
    # Construct endpoint
    if backend == "lmstudio":
        # LM Studio new API
        base = url.replace("/api/v1/chat", "")
        api_url = base + "/api/v1/models"
    elif backend == "openai":
        # Legacy LM Studio or OpenAI
        base = url.split("/chat/completions")[0]
        api_url = base + "/models"
    else:
        # Ollama
        api_url = url.replace("/api/chat", "/api/tags")
        
    try:
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            if backend == "lmstudio":
                # LM Studio new API format
                # Can be {"data": [...]} or just a list
                models = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(models, list):
                    return [m.get("id", m.get("path", str(m))) for m in models if isinstance(m, dict)]
                return []
            elif backend == "openai":
                # Standard OpenAI format: {"data": [{"id": "..."}]}
                models = data.get("data", [])
                return [m["id"] for m in models]
            else:
                # Ollama format: {"models": [{"name": "..."}]}
                models = data.get("models", [])
                return [m["name"] for m in models]
    except Exception as e:
        return [f"Error fetching models: {str(e)}"]


def get_loaded_model(boost: bool = False) -> Optional[str]:
    """Get the currently loaded model in LM Studio."""
    url = REMOTE_URL if boost else LOCAL_URL
    backend = REMOTE_BACKEND if boost else LOCAL_BACKEND
    
    if backend != "lmstudio":
        return None
        
    try:
        base = url.replace("/api/v1/chat", "")
        api_url = base + "/api/v1/models"
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            # Check for loaded/active model
            models = data.get("data", [])
            for m in models:
                if m.get("state") == "loaded" or m.get("loaded"):
                    return m.get("id", m.get("path"))
            # If none explicitly loaded, return first
            if models:
                return models[0].get("id", models[0].get("path"))
    except Exception:
        pass
    return None


def load_model(model_path: str, boost: bool = False) -> bool:
    """Load a specific model in LM Studio."""
    url = REMOTE_URL if boost else LOCAL_URL
    backend = REMOTE_BACKEND if boost else LOCAL_BACKEND
    
    if backend != "lmstudio":
        return False
        
    try:
        base = url.replace("/api/v1/chat", "")
        api_url = base + "/api/v1/models/load"
        payload = {"model": model_path}
        
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status == 200
    except Exception:
        return False


def start_lmstudio_server() -> bool:
    """Start LM Studio server using lms CLI."""
    try:
        # Check if lms command exists
        result = subprocess.run(
            ["lms", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "running" in result.stdout.lower():
            return True  # Already running
            
        # Start the server
        subprocess.Popen(
            ["lms", "server", "start"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)  # Give it time to start
        return test_connection(boost=True)
    except FileNotFoundError:
        return False  # lms not installed
    except Exception:
        return False


def set_model(model_name: str, boost: bool = False):
    """Runtime override of the selected model."""
    global _active_local_model, _active_remote_model
    if boost:
        _active_remote_model = model_name
        # If LM Studio, try to load the model
        if REMOTE_BACKEND == "lmstudio":
            load_model(model_name, boost=True)
    else:
        _active_local_model = model_name


def get_active_model(boost: bool = False) -> str:
    """Get the currently active model name."""
    if boost:
        if REMOTE_BACKEND == "lmstudio" and _active_remote_model == "auto":
            loaded = get_loaded_model(boost=True)
            return loaded or "auto"
        return _active_remote_model
    return _active_local_model

