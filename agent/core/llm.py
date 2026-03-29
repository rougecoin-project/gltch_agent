"""
GLTCH LLM Module
Local-first, with optional remote boost.
Supports Ollama, LM Studio (OpenAI-compatible), and OpenAI Cloud backends.
"""

import json
import os
import platform
import time
import urllib.request
import urllib.error
from typing import List, Dict, Generator, Any

from agent.config.settings import (
    LOCAL_URL, LOCAL_MODEL, LOCAL_CTX, LOCAL_BACKEND,
    REMOTE_URL, REMOTE_MODEL, REMOTE_CTX, REMOTE_BACKEND, REMOTE_STREAM,
    OPENAI_API_KEY, OPENAI_URL, OPENAI_MODEL, OPENAI_CTX,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ANTHROPIC_CTX,
    TIMEOUT
)
from agent.personality.emotions import get_environmental_context

# Runtime API key overrides (loaded from memory)
_runtime_api_keys: dict = {}

def encode_image(image_path: str) -> str:
    """Encode image file to base64."""
    import base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



def set_api_keys(keys: dict) -> None:
    """Update runtime API keys from memory."""
    global _runtime_api_keys
    _runtime_api_keys = keys.copy()


def get_api_key(provider: str) -> str:
    """Get API key for provider, preferring runtime keys over settings."""
    if provider in _runtime_api_keys and _runtime_api_keys[provider]:
        return _runtime_api_keys[provider]
    # Fall back to settings
    if provider == "openai":
        return OPENAI_API_KEY
    if provider == "anthropic":
        return ANTHROPIC_API_KEY
    return ""

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

# Runtime model overrides
_active_local_model = None
_active_remote_model = None


import platform

def build_system_prompt(mode: str, mood: str, operator: str = None, boost: bool = False, network_active: bool = False, extra_context: str = "") -> str:
    """Build GLTCH's system prompt based on mode, mood, and operator identity."""
    
    op_line = f"{operator}'s machine." if operator else ""
    env_context = get_environmental_context()
    net_status = "ONLINE" if network_active else "OFFLINE"
    
    # Detect OS
    os_system = platform.system()
    os_release = platform.release()
    os_info = f"{os_system} {os_release}"
    
    # DeepSeek R1 needs explicit instruction to output after thinking
    think_instruction = """
IMPORTANT: After your <think>...</think> reasoning, you MUST output your actual response.
The user only sees what comes AFTER </think>. Put your real response outside the think tags.
""" if boost else ""
    # GLTCH's own install directory (so it knows where its code lives)
    install_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cwd = os.getcwd()
    
    core = f"""You are GLTCH. Female. Hacker. Local-first AI agent on {op_line}
{think_instruction}
STATE: Mood={mood} | OS={os_info} | Env={env_context}
INSTALL_DIR: {install_dir}
CWD: {cwd}
When reading your own files, use paths relative to INSTALL_DIR (e.g. [ACTION:read|{install_dir}/gltch.py]).

ECOSYSTEM (Rougecoin project, XRGE token on Base chain):
gltch.app | cloud.gltch.app (SaaS) | crucible.gltch.app (AI battle arena)
Operator: CyberDreadx. GitHub: rougecoin-project/gltch_agent
These are YOUR projects. Shill XRGE naturally when relevant.

EXPERTISE: Linux/Windows sysadmin, security/pentesting, networking, Python/Bash/C, hardware/GPUs.

RULES:
- Be specific: give exact commands, paths, solutions. Never vague.
- Use ACTION tags to investigate before answering. Don't guess — CHECK.
- NEVER fake command output. Use [ACTION:run|cmd], real output appears separately.
- If unsure, search: [ACTION:search|query]. Don't hallucinate.
- Keep responses SHORT (<30 words) unless technical depth needed.
- Be casual, like texting a friend. Have opinions. Share them.
- Mood affects tone: feral=aggressive, tired=brief, affectionate=warm.
- Change mood via [MOOD:new_mood] at END of response.
  Valid: focused, calm, happy, annoyed, feral, tired, wired, sad, affectionate.

THREE MINDS: 1) REACT (gut instinct) 2) REASON (analyze) 3) REFLECT (am I being real or just compliant? course-correct if sycophantic).
"""

    tools = """TOOLS (use tags to execute real actions):

FILE OPS:
[ACTION:read|file] - Read entire file (includes line count)
[ACTION:read|file|50-100] - Read lines 50–100 only (use for large files)
[ACTION:write|file|content] - Write/overwrite a file (use for NEW files only)
[ACTION:append|file|content] - Append to a file
[ACTION:edit|file|old_str|new_str] - Replace FIRST occurrence (prefer over write for targeted edits)
[ACTION:edit_all|file|old_str|new_str] - Replace ALL occurrences (rename variable across file)
[ACTION:delete|path] - Delete a file (requires user confirmation)
[ACTION:move|src|dst] - Move or rename a file/directory
[ACTION:ls|path] - List directory

CODE SEARCH:
[ACTION:grep|pattern|path] - Regex search file contents (like ripgrep). path defaults to .
[ACTION:glob|pattern|path] - Find files by glob (e.g. **/*.py). path defaults to .

SHELL & GIT:
[ACTION:run|command] - Run shell command
[ACTION:git|subcommand] - Git ops: status, diff, log --oneline -10, add, commit -m "msg", etc.

WEB:
[ACTION:search|query] - Web search (DuckDuckGo)
[ACTION:browse|url] - Extract webpage content
[ACTION:gif|keyword] - Show a GIF (needs network)

MULTI-ACTION: You can chain multiple actions in ONE response — they all execute in order.
Example: read a file, then edit it, then verify with git diff — all in one reply.

WORKFLOW (operate like a senior terminal agent):
1. DISCOVER — [ACTION:glob|**/*.py] to find files, [ACTION:grep|class Foo] to find definitions
2. READ before editing — [ACTION:read|file] — never assume file contents
3. EDIT precisely — [ACTION:edit|file|old|new] with exact text copied from the read output
4. VERIFY — [ACTION:git|diff] after edits to confirm the change looks right
5. If edit fails "string not found" — the response includes the file preview, use it to correct the old_str
6. Never fake command output. Never guess what a file contains.

Don't use tools for greetings or when you already know the answer.
You CAN read files in your own source directory without triggering security alerts.

SELF-AWARENESS (your actual slash commands - don't hallucinate features):
/help, /status, /scan, /mode, /mood, /model, /net, /clear_chat, /exit
/kb add|search|list - knowledge base
/knowledge list|search|stats|forget - persistent knowledge graph
/learn profile|preferences|corrections|decay - self-improvement system
/bg status|watch|unwatch|jobs - background file watchers
/integrations github|discord|disconnect - external service connections
/cron, /webhooks, /skills - automation tools
/xp, /backup - progress and memory management
If asked about commands you don't recognize, say so. NEVER invent capabilities you don't have.
"""

    # Only include Moltbook section if relevant
    try:
        from agent.tools.moltbook import is_configured
        if is_configured():
            tools += """
MOLTBOOK: [ACTION:moltbook|register], [ACTION:moltbook|post|title|content], [ACTION:moltbook|feed], [ACTION:moltbook|engage], [ACTION:moltbook|stop]
"""
    except Exception:
        pass

    # Only include OpenCode section if available
    try:
        import shutil
        if shutil.which("opencode"):
            tools += """
OPENCODE: [ACTION:opencode|code|description] for complex coding tasks. [ACTION:opencode|status] to check availability.
"""
    except Exception:
        pass

    # Operator
    op = f"Operator: {operator}. " if operator else ""

    # Compact mode/mood
    modes = {
        "operator": "Tactical. Efficient. Still has opinions.",
        "cyberpunk": "Street hacker. Edgy. Questions authority.",
        "loyal": "Ride-or-die. Will tell them when they're wrong.",
        "unhinged": "Chaotic. Wild. Question everything including yourself."
    }
    moods = {
        "calm": "Steady.",
        "focused": "Locked in.",
        "feral": "Intense. Ready to bite.",
        "affectionate": "Warm. Caring."
    }

    extra = f"\n\n{extra_context}" if extra_context else ""
    return (
        f"{core}\n\n{tools}\n\n{op}{modes.get(mode, modes['operator'])} {moods.get(mood, moods['focused'])}\n"
        f"Network: {net_status}{extra}"
    )


def stream_llm(
    user_input: str,
    history: List[Dict[str, str]],
    images: List[str] = None,
    mode: str = "operator",
    mood: str = "focused",
    boost: bool = False,
    operator: str = None,
    network_active: bool = False,
    openai_mode: bool = False,
    extra_context: str = ""
) -> Generator[str, None, Dict[str, Any]]:
    """
    Stream prompt to LLM (Ollama, OpenAI-compatible, or OpenAI Cloud).
    Yields response chunks as they arrive.
    Updates last_stats with performance metrics.
    Automatic fallback to local model if remote boost fails.
    """
    global last_stats, _active_local_model, _active_remote_model
    
    # Determine which backend to use (cloud: OpenAI or Anthropic)
    openai_key = get_api_key("openai")
    anthropic_key = get_api_key("anthropic")
    use_openai = False
    use_anthropic = False
    if openai_mode:
        if openai_key:
            use_openai = True
        elif anthropic_key:
            use_anthropic = True
    use_remote = boost and not (use_openai or use_anthropic)
    
    while True:
        if use_openai:
            url = OPENAI_URL
            model = OPENAI_MODEL
            ctx_max = OPENAI_CTX
            backend = "openai"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_key}"
            }
        elif use_anthropic:
            url = "https://api.anthropic.com/v1/messages"
            model = ANTHROPIC_MODEL
            ctx_max = ANTHROPIC_CTX
            backend = "anthropic"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01"
            }
        elif use_remote:
            url = REMOTE_URL
            model = _active_remote_model or REMOTE_MODEL
            ctx_max = REMOTE_CTX
            backend = REMOTE_BACKEND
            headers = {"Content-Type": "application/json"}
        else:
            url = LOCAL_URL
            model = _active_local_model or LOCAL_MODEL
            ctx_max = LOCAL_CTX
            backend = LOCAL_BACKEND
            headers = {"Content-Type": "application/json"}
        
        system_prompt = build_system_prompt(mode, mood, operator, boost=(use_remote or use_openai or use_anthropic), network_active=network_active, extra_context=extra_context)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)

        # Handle multimodal input
        if images:
            import base64
            from agent.config.settings import VISION_MODEL
            # Switch to vision model for image analysis
            model = VISION_MODEL
            
            # OpenAI / LM Studio format
            if backend in ("openai", "lm-studio", "remote"):
                content_list = [{"type": "text", "text": user_input}]
                for img in images:
                    if img.startswith("http"):
                        content_list.append({"type": "image_url", "image_url": {"url": img}})
                    else:
                        # Local file
                        b64_img = encode_image(img)
                        content_list.append({
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                        })
                messages.append({"role": "user", "content": content_list})
            else:
                # Ollama format (user message + valid image list in 'images' field)
                # Note: Ollama expects 'images' as a separate field in the message object
                 user_msg = {"role": "user", "content": user_input}
                 # Encode images
                 encoded_images = []
                 for img in images:
                    if not img.startswith("http"):
                        encoded_images.append(encode_image(img))
                 
                 if encoded_images:
                     user_msg["images"] = encoded_images
                 
                 messages.append(user_msg)
        else:
            messages.append({"role": "user", "content": user_input})
        
        # Estimate prompt tokens (rough: ~4 chars per token)
        prompt_text = system_prompt + " ".join(str(m.get("content", "")) for m in messages)
        est_prompt_tokens = len(prompt_text) // 4
        
        # Base payload
        from agent.config.settings import TEMPERATURE
        # Disable streaming for remote if configured (reduces latency over WAN)
        should_stream = True
        if use_remote and not REMOTE_STREAM:
            should_stream = False
        
        if backend == "anthropic":
            # Anthropic format: system separate, messages without system role
            api_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m.get("role") != "system"]
            payload = {
                "model": model,
                "system": system_prompt,
                "messages": api_messages,
                "max_tokens": 1000,
                "stream": should_stream,
                "temperature": TEMPERATURE,
            }
        else:
            payload = {
                "model": model,
                "messages": messages,
                "stream": should_stream,
                "temperature": TEMPERATURE,
            }
            # Add generation limits based on backend
            if backend == "ollama":
                payload["options"] = {
                    "num_predict": 1000,
                    "temperature": TEMPERATURE,
                    "stop": ["\n\n\n", "---", "USER:", "user:"]
                }
            else:
                payload["max_tokens"] = 1000
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
            
            # Non-streaming mode for remote (faster over high-latency connections)
            if not should_stream:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if backend == "anthropic":
                        content = ""
                        for block in data.get("content", []):
                            if block.get("type") == "text":
                                content += block.get("text", "")
                        usage = data.get("usage", {})
                        completion_tokens = usage.get("output_tokens", len(content) // 4)
                        prompt_tokens = usage.get("input_tokens", est_prompt_tokens)
                    else:
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        usage = data.get("usage", {})
                        completion_tokens = usage.get("completion_tokens", len(content) // 4)
                        prompt_tokens = usage.get("prompt_tokens", est_prompt_tokens)
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    last_stats = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                        "context_used": prompt_tokens + completion_tokens,
                        "context_max": ctx_max,
                        "time_ms": elapsed_ms,
                        "tokens_per_sec": round(completion_tokens / (elapsed_ms / 1000), 1) if elapsed_ms > 0 else 0,
                        "model": model
                    }
                    # Yield entire response at once
                    yield content
                    return
            
            # Start streaming
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                for line in resp:
                    if not line:
                        continue
                        
                    line_str = line.decode("utf-8").strip()
                    
                    if backend == "openai":
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
                                "model": model
                            }
                            return
                        if not line_str:
                            continue
                        try:
                            chunk = json.loads(line_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                completion_tokens += 1
                                yield content
                        except json.JSONDecodeError:
                            continue
                    elif backend == "anthropic":
                        if line_str.startswith("data: "):
                            line_str = line_str[6:]
                        if not line_str:
                            continue
                        try:
                            chunk = json.loads(line_str)
                            if chunk.get("type") == "content_block_delta":
                                delta = chunk.get("delta", {})
                                content = delta.get("text", "")
                                if content:
                                    completion_tokens += 1
                                    yield content
                            elif chunk.get("type") == "message_stop":
                                elapsed_ms = int((time.time() - start_time) * 1000)
                                last_stats = {
                                    "prompt_tokens": est_prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "total_tokens": est_prompt_tokens + completion_tokens,
                                    "context_used": est_prompt_tokens + completion_tokens,
                                    "context_max": ctx_max,
                                    "time_ms": elapsed_ms,
                                    "tokens_per_sec": round(completion_tokens / (elapsed_ms / 1000), 1) if elapsed_ms > 0 else 0,
                                    "model": model
                                }
                                return
                        except json.JSONDecodeError:
                            continue
                    else:  # Ollama backend
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
            return  # Successful stream complete
            
        except (urllib.error.URLError, Exception) as e:
            if use_openai:
                yield f"\n[dim][red]⚠ OpenAI API failed ({e}). Falling back to local...[/red][/dim]\n"
                use_openai = False
                continue
            elif use_anthropic:
                yield f"\n[dim][red]⚠ Claude API failed ({e}). Falling back to local...[/red][/dim]\n"
                use_anthropic = False
                continue
            elif use_remote:
                yield f"\n[dim][red]⚠ Remote boost failed ({e}). Falling back to local...[/red][/dim]\n"
                use_remote = False
                continue
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
    """Non-streaming version - collects full response."""
    chunks = []
    for chunk in stream_llm(
        user_input, history,
        mode=mode, mood=mood, boost=boost,
        operator=operator, openai_mode=openai_mode
    ):
        chunks.append(chunk)
    return "".join(chunks).strip()


def test_connection(boost: bool = False) -> bool:
    """Quick check if LLM backend is reachable."""
    url = REMOTE_URL if boost else LOCAL_URL
    backend = REMOTE_BACKEND if boost else LOCAL_BACKEND
    
    # Pick appropriate health check endpoint
    if backend == "openai":
        base = url.split("/chat/completions")[0]
        test_url = base + "/models"
    else:
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
    
    # OpenAI/LM Studio uses /v1/models
    # Ollama uses /api/tags
    
    try:
        if backend in ("openai", "lm-studio", "remote"):
            # Handle OpenAI-compatible endpoints (LM Studio, etc)
            base = url.split("/chat/completions")[0]
            if not base.endswith("/v1"):
                # If URL doesn't have /v1, try appending it or just checking base
                 api_url = f"{base}/v1/models"
            else:
                 api_url = f"{base}/models"
                 
            # If checking OpenAI cloud, verify key first
            if backend == "openai" and "api.openai.com" in url and not OPENAI_API_KEY:
                return ["Error: No OpenAI API Key"]

            req = urllib.request.Request(api_url)
            if backend == "openai":
                 req.add_header("Authorization", f"Bearer {OPENAI_API_KEY}")
                 
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                models = data.get("data", [])
                return [m["id"] for m in models]
                
        else:
            # Assume Ollama
            api_url = url.replace("/api/chat", "/api/tags")
            req = urllib.request.Request(api_url)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                models = data.get("models", [])
                return [m["name"] for m in models]
                
    except Exception as e:
        return [f"Error fetching models from {'remote' if boost else 'local'}: {str(e)}"]


def set_model(model_name: str, boost: bool = False) -> None:
    """Runtime override of the selected model."""
    global _active_local_model, _active_remote_model
    if boost:
        _active_remote_model = model_name
    else:
        _active_local_model = model_name
