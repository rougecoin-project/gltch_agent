"""
GLTCH Default Configuration
Default values and config management.
"""

import os
import json
from typing import Dict, Any, Optional

from agent.config.settings import CONFIG_FILE, DATA_DIR

DEFAULT_CONFIG: Dict[str, Any] = {
    "agent": {
        "name": "GLTCH",
        "default_mode": "operator",
        "default_mood": "focused"
    },
    "llm": {
        "local": {
            "url": "http://localhost:11434/api/chat",
            "model": "phi3:3.8b",
            "context": 4096,
            "backend": "ollama"
        },
        "remote": {
            "url": "http://192.168.1.188:1234/v1/chat/completions",
            "model": "deepseek-r1-distill-qwen-14b",
            "context": 8192,
            "backend": "openai"
        },
        "openai": {
            "model": "gpt-4o",
            "context": 128000
        },
        "timeout": 120
    },
    "gateway": {
        "host": "127.0.0.1",
        "port": 18888,
        "ws_port": 18889,
        "bind": "loopback"  # loopback | tailnet | public
    },
    "channels": {
        "discord": {
            "enabled": False,
            "token": ""
        },
        "telegram": {
            "enabled": False,
            "token": ""
        },
        "webchat": {
            "enabled": True
        }
    },
    "security": {
        "network_default": False,
        "require_confirmation": True
    },
    "ui": {
        "refresh_rate": 10
    }
}


def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


def get_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults."""
    ensure_data_dir()
    
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Merge with defaults for any missing keys
        merged = DEFAULT_CONFIG.copy()
        _deep_merge(merged, config)
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    ensure_data_dir()
    
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_FILE)


def update_config(path: str, value: Any) -> Dict[str, Any]:
    """
    Update a config value by dot-separated path.
    
    Example: update_config("gateway.port", 8080)
    """
    config = get_config()
    keys = path.split(".")
    
    # Navigate to parent
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set value
    current[keys[-1]] = value
    save_config(config)
    
    return config


def _deep_merge(base: dict, override: dict) -> None:
    """Deep merge override into base."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
