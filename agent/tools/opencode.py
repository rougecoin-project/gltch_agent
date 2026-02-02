"""
GLTCH OpenCode Integration
Route coding tasks to OpenCode for specialized assistance.
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

import os
from pathlib import Path

from agent.config.settings import OPENCODE_URL, OPENCODE_PASSWORD, OPENCODE_ENABLED

# Workspace folder for OpenCode generated files
OPENCODE_WORKSPACE = os.environ.get("OPENCODE_WORKSPACE", "workspace")

# Track active project for continuous work
_active_project: Optional[str] = None


def slugify(text: str) -> str:
    """Convert text to a folder-safe slug."""
    import re
    # Extract key words, lowercase, replace spaces with underscores
    text = text.lower()
    # Remove common filler words
    for word in ["write", "create", "make", "build", "a", "an", "the", "me", "please"]:
        text = text.replace(word, "")
    # Keep only alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Collapse whitespace and convert to underscores
    text = re.sub(r'\s+', '_', text.strip())
    # Limit length
    return text[:40] or "project"


def ensure_workspace() -> Path:
    """Ensure the workspace folder exists and return its path."""
    workspace = Path(OPENCODE_WORKSPACE)
    workspace.mkdir(exist_ok=True)
    return workspace.resolve()


def ensure_project_folder(prompt: str) -> tuple[Path, str]:
    """Create a project-specific folder based on the prompt. Returns (path, folder_name)."""
    global _active_project
    
    workspace = ensure_workspace()
    folder_name = slugify(prompt)
    
    # Make unique if exists (append number)
    base_name = folder_name
    counter = 1
    while (workspace / folder_name).exists() and folder_name != _active_project:
        folder_name = f"{base_name}_{counter}"
        counter += 1
    
    project_path = workspace / folder_name
    project_path.mkdir(exist_ok=True)
    
    _active_project = folder_name
    return project_path, folder_name


def set_active_project(name: str) -> bool:
    """Set the active project to continue working on."""
    global _active_project
    workspace = ensure_workspace()
    project_path = workspace / name
    if project_path.exists():
        _active_project = name
        return True
    return False


def get_active_project() -> Optional[str]:
    """Get the current active project name."""
    return _active_project


def list_projects() -> List[str]:
    """List all project folders in workspace."""
    workspace = Path(OPENCODE_WORKSPACE)
    if not workspace.exists():
        return []
    return sorted([p.name for p in workspace.iterdir() if p.is_dir()])


def is_available() -> bool:
    """Check if OpenCode server is running."""
    if not OPENCODE_ENABLED:
        return False
    
    try:
        url = f"{OPENCODE_URL}/global/health"
        req = urllib.request.Request(url)
        if OPENCODE_PASSWORD:
            import base64
            credentials = base64.b64encode(f"opencode:{OPENCODE_PASSWORD}".encode()).decode()
            req.add_header("Authorization", f"Basic {credentials}")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def _add_auth(req: urllib.request.Request) -> None:
    """Add authentication header if password is set."""
    if OPENCODE_PASSWORD:
        import base64
        credentials = base64.b64encode(f"opencode:{OPENCODE_PASSWORD}".encode()).decode()
        req.add_header("Authorization", f"Basic {credentials}")


def list_sessions() -> List[Dict[str, Any]]:
    """List active OpenCode sessions."""
    try:
        url = f"{OPENCODE_URL}/session"
        req = urllib.request.Request(url)
        _add_auth(req)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            # API returns Session[] directly
            return data if isinstance(data, list) else []
    except Exception as e:
        return []


def create_session(title: str = "GLTCH Session") -> Optional[str]:
    """Create a new OpenCode session. Returns session ID."""
    try:
        url = f"{OPENCODE_URL}/session"
        payload = {"title": title}
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        _add_auth(req)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("id")
    except Exception as e:
        return None


def send_prompt(session_id: str, prompt: str, project_folder: Optional[str] = None) -> Optional[str]:
    """Send a prompt to OpenCode and get the response."""
    try:
        # Determine project folder
        if project_folder:
            folder_path = f"{OPENCODE_WORKSPACE}/{project_folder}"
        else:
            _, folder_name = ensure_project_folder(prompt)
            folder_path = f"{OPENCODE_WORKSPACE}/{folder_name}"
        
        # Prepend workspace instructions
        enhanced_prompt = f"""IMPORTANT: Save all generated files in the '{folder_path}/' folder.
Use paths like '{folder_path}/filename.py' for any files you create.
Create the folder structure as needed.

User request: {prompt}"""
        
        url = f"{OPENCODE_URL}/session/{session_id}/message"
        # Message body requires 'parts' array with text content
        payload = {
            "parts": [
                {"type": "text", "text": enhanced_prompt}
            ]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        _add_auth(req)
        
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode())
            # Response: { info: Message, parts: Part[] }
            parts = data.get("parts", [])
            output = []
            files_created = []
            
            for part in parts:
                ptype = part.get("type", "")
                
                # Text content
                if ptype == "text":
                    text = part.get("text", "")
                    if text:
                        output.append(text)
                
                # Tool calls (file writes, etc.)
                elif ptype == "tool-invocation":
                    tool_name = part.get("toolInvocation", {}).get("toolName", "")
                    tool_input = part.get("toolInvocation", {}).get("input", {})
                    
                    if tool_name in ["write", "file_write", "edit"]:
                        filepath = tool_input.get("filePath") or tool_input.get("path", "")
                        if filepath:
                            files_created.append(filepath)
            
            # Build response
            result = "\n".join(output)
            
            if files_created:
                result += "\n\n[dim]Files created/modified:[/dim]"
                for f in files_created:
                    result += f"\n  → {f}"
            
            return result if result.strip() else None
    except Exception as e:
        return f"OpenCode error: {str(e)}"


def code(prompt: str, session_id: Optional[str] = None, project: Optional[str] = None) -> tuple[str, Optional[str]]:
    """
    Send a coding request to OpenCode.
    Creates a new session if none provided.
    Returns (response, project_folder_name).
    """
    if not is_available():
        return "OpenCode is not running. Start it with: opencode serve", None
    
    # Create session if needed
    if not session_id:
        session_id = create_session("GLTCH Coding")
        if not session_id:
            return "Failed to create OpenCode session", None
    
    # Send prompt
    response = send_prompt(session_id, prompt, project)
    project_name = get_active_project()
    
    if response:
        return response, project_name
    return "No response from OpenCode", project_name


def quick_code(prompt: str, project: Optional[str] = None) -> tuple[str, Optional[str]]:
    """
    Quick one-shot coding request.
    Creates a new session, sends prompt, returns response and project name.
    """
    return code(prompt, project=project)


# Keywords that suggest a coding request
CODE_KEYWORDS = [
    "write a script", "write code", "create a function", "create a class",
    "implement", "code this", "write me a", "python script", "bash script",
    "javascript", "typescript", "function that", "program that",
    "refactor", "fix this code", "debug this", "optimize this code"
]


def is_coding_request(text: str) -> bool:
    """Heuristic to detect if a message is a coding request."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in CODE_KEYWORDS)
