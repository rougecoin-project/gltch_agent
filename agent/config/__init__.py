"""
GLTCH Configuration Module
Settings management and defaults.
"""

from agent.config.settings import (
    AGENT_NAME,
    LOCAL_URL, LOCAL_MODEL, LOCAL_CTX, LOCAL_BACKEND,
    REMOTE_URL, REMOTE_MODEL, REMOTE_CTX, REMOTE_BACKEND,
    OPENAI_API_KEY, OPENAI_URL, OPENAI_MODEL, OPENAI_CTX,
    TIMEOUT, REFRESH_RATE, GIPHY_API_KEY
)
from agent.config.defaults import DEFAULT_CONFIG, get_config, update_config

__all__ = [
    "AGENT_NAME",
    "LOCAL_URL", "LOCAL_MODEL", "LOCAL_CTX", "LOCAL_BACKEND",
    "REMOTE_URL", "REMOTE_MODEL", "REMOTE_CTX", "REMOTE_BACKEND",
    "OPENAI_API_KEY", "OPENAI_URL", "OPENAI_MODEL", "OPENAI_CTX",
    "TIMEOUT", "REFRESH_RATE", "GIPHY_API_KEY",
    "DEFAULT_CONFIG", "get_config", "update_config"
]
