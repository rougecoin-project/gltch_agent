# Tools

GLTCH can execute real actions on your system using tools. Tools are invoked via special `[ACTION:...]` tags in responses.

## Available Tools

### File Read

Read the contents of a file.

**Syntax:**
```
[ACTION:read|path/to/file.txt]
```

**Example:**
```
User: What's in my config file?
GLTCH: [ACTION:read|~/.config/app/config.json]
Here's your config: {"theme": "dark", "lang": "en"}
```

### File Write

Write content to a file.

**Syntax:**
```
[ACTION:write|path/to/file.txt|content here]
```

**Example:**
```
User: Create a hello world script
GLTCH: [ACTION:write|hello.py|print("Hello, World!")]
Done! Created hello.py
```

### Shell Command

Execute a shell command.

**Syntax:**
```
[ACTION:run|command here]
```

**Example:**
```
User: Check disk space
GLTCH: [ACTION:run|df -h]
Filesystem   Size  Used  Avail  Use%
/dev/sda1    100G   45G   55G   45%
```

### GIF Search

Search and display a GIF (requires network mode).

**Syntax:**
```
[ACTION:gif|search terms]
```

**Example:**
```
User: Show me a celebration gif
GLTCH: Nice work! [ACTION:gif|celebration dance]
```

### Web Search (Planned)

Search the web for information.

**Syntax:**
```
[ACTION:search|query here]
```

### API Call (Planned)

Make HTTP requests.

**Syntax:**
```
[ACTION:api|METHOD|url|body]
```

## Network Tools

Some tools require network access. Enable with:

```
/net on
```

Network-dependent tools:
- `gif` — Giphy API
- `search` — Web search
- `api` — HTTP requests

## Tool Execution

### How It Works

1. GLTCH generates a response with `[ACTION:...]` tags
2. Agent parses the tags
3. Each action is executed
4. Results are returned to GLTCH
5. GLTCH incorporates results into response

### Code Flow

```python
# From actions.py
def parse_and_execute_actions(response: str, network_active: bool) -> Tuple[str, List]:
    actions = re.findall(r'\[ACTION:(.*?)\]', response)
    results = []
    
    for action in actions:
        parts = action.split('|')
        action_type = parts[0]
        
        if action_type in ACTION_HANDLERS:
            result = ACTION_HANDLERS[action_type](parts[1:], network_active)
            results.append(result)
    
    return response, results
```

## Security

### Sandboxing

Actions run with the same permissions as the GLTCH process. Consider:

- Running GLTCH in a container
- Using a restricted user account
- Limiting file system access

### Network Restrictions

Network tools are disabled by default. The LLM knows when network is off:

```
User: Search for Python tutorials
GLTCH: Network is offline. I can't search right now.
Try: /net on
```

### Command Filtering (Planned)

Dangerous commands could be blocked:

```python
BLOCKED_COMMANDS = [
    r'rm\s+-rf\s+/',
    r':(){ :|:& };:',
    r'dd\s+if=',
]
```

## Adding New Tools

### 1. Create Handler

Add to `agent/tools/actions.py`:

```python
def handle_screenshot(args: List[str], network_active: bool) -> str:
    """Take a screenshot."""
    import subprocess
    
    output_path = args[0] if args else "screenshot.png"
    
    # Linux
    subprocess.run(["gnome-screenshot", "-f", output_path])
    
    return f"Screenshot saved to {output_path}"
```

### 2. Register Handler

```python
ACTION_HANDLERS = {
    "read": handle_read,
    "write": handle_write,
    "run": handle_run,
    "gif": handle_gif,
    "screenshot": handle_screenshot,  # New!
}
```

### 3. Update System Prompt

Edit `agent/core/llm.py`:

```python
tools = """TOOLS - You can execute real actions:

TO TAKE A SCREENSHOT:
[ACTION:screenshot|optional-filename.png]
...
"""
```

## OpenCode Integration

GLTCH integrates with OpenCode for advanced coding tasks.

### Enable

```bash
# Start OpenCode server
opencode serve

# GLTCH will auto-detect it
```

### Usage

```
/code create a flask api with user authentication
```

### How It Works

1. `/code` command triggers OpenCode integration
2. Creates a project folder in `workspace/`
3. Sends prompt to OpenCode API
4. OpenCode generates code with its tools
5. Results returned to GLTCH terminal

### Project Continuity

Continue working on existing projects:

```
/code @flask-api add password reset endpoint
```

See `agent/tools/opencode.py` for implementation details.

## Tool Results

### Success

```python
{
    "success": True,
    "output": "Command output here",
    "tool": "run"
}
```

### Failure

```python
{
    "success": False,
    "error": "Permission denied",
    "tool": "write"
}
```

### Display

Results are shown in the terminal:

```
GLTCH: Checking your processes...
[ACTION:run|ps aux | head -5]

┌─ ACTION ─────────────────────────────────────┐
│ > ps aux | head -5                           │
│                                              │
│ USER  PID  %CPU  %MEM  COMMAND               │
│ root    1   0.0   0.1  /sbin/init            │
│ root    2   0.0   0.0  [kthreadd]            │
│ ...                                          │
└──────────────────────────────────────────────┘

Looks like your system is running normally.
```
