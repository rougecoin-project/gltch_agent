"""
Heartbeat Configuration
Per-website heartbeat configuration management.
"""

import os
import json
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


# Default heartbeats directory relative to project root
HEARTBEATS_DIR = "heartbeats"


@dataclass
class HeartbeatTask:
    """A single task within a heartbeat."""
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass 
class HeartbeatConfig:
    """Configuration for a website's heartbeat."""
    site_id: str
    display_name: str
    interval_hours: float = 4.0
    api_key_name: Optional[str] = None
    tasks: List[HeartbeatTask] = field(default_factory=list)
    enabled: bool = True
    api_base_url: Optional[str] = None
    
    # Security settings
    max_requests_per_heartbeat: int = 10
    timeout_seconds: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "site_id": self.site_id,
            "display_name": self.display_name,
            "interval_hours": self.interval_hours,
            "api_key_name": self.api_key_name,
            "tasks": [{"action": t.action, "params": t.params, "description": t.description} for t in self.tasks],
            "enabled": self.enabled,
            "api_base_url": self.api_base_url,
            "max_requests_per_heartbeat": self.max_requests_per_heartbeat,
            "timeout_seconds": self.timeout_seconds,
        }


# Dangerous patterns that are never allowed in configs
BLOCKED_PATTERNS = [
    # Shell command patterns
    r"\$\(",           # Command substitution
    r"`[^`]+`",        # Backtick command substitution
    r"\|\s*\w+",       # Pipe to command
    r";\s*\w+",        # Command chaining
    r"&&\s*\w+",       # AND command chaining
    r"\|\|\s*\w+",     # OR command chaining
    r">\s*/",          # Redirect to root
    r"<\s*/",          # Read from root
    
    # Path traversal
    r"\.\./",          # Directory traversal
    r"\.\.\\",         # Windows directory traversal
    
    # Code injection
    r"__import__",     # Python import injection
    r"eval\s*\(",      # Eval calls
    r"exec\s*\(",      # Exec calls
    r"os\.system",     # System calls
    r"subprocess",     # Subprocess module
    r"import\s+os",    # OS import
    
    # API key exfiltration
    r"api[_-]?key",    # API key references (except in api_key_name field)
    r"secret",         # Secret references
    r"password",       # Password references
    r"token(?!s?\b)",  # Token references (but allow "tokens" as word)
]


def validate_config(config_data: Dict[str, Any], filename: str = "") -> tuple[bool, str]:
    """
    Validate a heartbeat config for security issues.
    Returns (is_valid, error_message).
    """
    # Required fields
    if not config_data.get("site_id"):
        return False, "Missing required field: site_id"
    if not config_data.get("display_name"):
        return False, "Missing required field: display_name"
    
    # Validate site_id format (alphanumeric + underscore only)
    site_id = config_data["site_id"]
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", site_id):
        return False, f"Invalid site_id format: {site_id} (must be alphanumeric, start with letter)"
    
    # Check all string values for dangerous patterns
    def check_value(value: Any, path: str = "") -> Optional[str]:
        if isinstance(value, str):
            # Skip api_key_name field - it's allowed to contain "api_key"
            if path.endswith(".api_key_name"):
                return None
            
            for pattern in BLOCKED_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    return f"Blocked pattern '{pattern}' found in {path}: {value[:50]}"
        elif isinstance(value, dict):
            for k, v in value.items():
                err = check_value(v, f"{path}.{k}" if path else k)
                if err:
                    return err
        elif isinstance(value, list):
            for i, v in enumerate(value):
                err = check_value(v, f"{path}[{i}]")
                if err:
                    return err
        return None
    
    err = check_value(config_data)
    if err:
        return False, f"Security violation in {filename}: {err}"
    
    # Validate tasks
    tasks = config_data.get("tasks", [])
    if not isinstance(tasks, list):
        return False, "tasks must be a list"
    
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            return False, f"Task {i} must be a dict"
        if not task.get("action"):
            return False, f"Task {i} missing 'action' field"
        
        # Action must be alphanumeric + underscore
        action = task["action"]
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", action):
            return False, f"Invalid action format: {action}"
    
    return True, ""


def load_config(filepath: str) -> Optional[HeartbeatConfig]:
    """
    Load a heartbeat config from a YAML or JSON file.
    Returns None if file is invalid or has security issues.
    """
    path = Path(filepath)
    
    if not path.exists():
        return None
    
    try:
        content = path.read_text(encoding="utf-8")
        
        # Parse based on extension
        if path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml
                data = yaml.safe_load(content)
            except ImportError:
                # Fallback: try JSON-style YAML (subset)
                data = json.loads(content)
        else:
            data = json.loads(content)
        
        if not isinstance(data, dict):
            return None
        
        # Validate security
        is_valid, error = validate_config(data, path.name)
        if not is_valid:
            print(f"⚠️  Heartbeat config rejected: {error}")
            return None
        
        # Build config object
        tasks = []
        for task_data in data.get("tasks", []):
            tasks.append(HeartbeatTask(
                action=task_data.get("action", ""),
                params=task_data.get("params", {}),
                description=task_data.get("description", ""),
            ))
        
        return HeartbeatConfig(
            site_id=data["site_id"],
            display_name=data["display_name"],
            interval_hours=float(data.get("interval_hours", 4.0)),
            api_key_name=data.get("api_key_name"),
            tasks=tasks,
            enabled=data.get("enabled", True),
            api_base_url=data.get("api_base_url"),
            max_requests_per_heartbeat=int(data.get("max_requests_per_heartbeat", 10)),
            timeout_seconds=int(data.get("timeout_seconds", 30)),
        )
        
    except Exception as e:
        print(f"⚠️  Failed to load heartbeat config {filepath}: {e}")
        return None


def load_all_configs(heartbeats_dir: str = None) -> Dict[str, HeartbeatConfig]:
    """
    Load all heartbeat configs from the heartbeats directory.
    Returns dict mapping site_id -> config.
    """
    if heartbeats_dir is None:
        # Find project root (where gltch.py is)
        project_root = Path(__file__).parent.parent.parent.parent
        heartbeats_dir = project_root / HEARTBEATS_DIR
    else:
        heartbeats_dir = Path(heartbeats_dir)
    
    configs = {}
    
    if not heartbeats_dir.exists():
        return configs
    
    # Load all .yaml, .yml, .json files
    for ext in ("*.yaml", "*.yml", "*.json"):
        for filepath in heartbeats_dir.glob(ext):
            config = load_config(str(filepath))
            if config:
                configs[config.site_id] = config
    
    return configs
