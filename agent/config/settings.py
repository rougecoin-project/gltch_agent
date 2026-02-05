"""
GLTCH Settings
Core configuration values.
"""

import os

# Agent Identity
AGENT_NAME = "GLTCH"

# Local LLM (Ollama)
LOCAL_URL = os.environ.get("GLTCH_LOCAL_URL", "http://localhost:11434/api/chat")
LOCAL_MODEL = os.environ.get("GLTCH_LOCAL_MODEL", "deepseek-r1:8b")
LOCAL_CTX = int(os.environ.get("GLTCH_LOCAL_CTX", "4096"))
LOCAL_BACKEND = "ollama"

# Remote LLM (LM Studio / OpenAI Compatible)
REMOTE_URL = os.environ.get("GLTCH_REMOTE_URL", "http://localhost:1234/v1/chat/completions")
REMOTE_MODEL = os.environ.get("GLTCH_REMOTE_MODEL", "deepseek-r1-distill-qwen-32b-uncensored")
REMOTE_CTX = int(os.environ.get("GLTCH_REMOTE_CTX", "8192"))
REMOTE_BACKEND = "openai"

# Vision Model (for image analysis)
VISION_MODEL = os.environ.get("GLTCH_VISION_MODEL", "gemma-3-12b-it")

# OpenAI API (Cloud)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.environ.get("GLTCH_OPENAI_MODEL", "gpt-4o")
# OpenAI API (Cloud)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.environ.get("GLTCH_OPENAI_MODEL", "gpt-4o")
OPENAI_CTX = 128000

# Token Gating (Base / XRGE)
BASE_RPC_URL = os.environ.get("GLTCH_BASE_RPC", "https://mainnet.base.org")
XRGE_CONTRACT = os.environ.get("XRGE_CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000") # Replace with real contract
XRGE_GATE_THRESHOLD = float(os.environ.get("GLTCH_GATE_THRESHOLD", "1000"))


# OpenCode Integration (coding agent)
OPENCODE_ENABLED = os.environ.get("OPENCODE_ENABLED", "true").lower() == "true"
OPENCODE_URL = os.environ.get("OPENCODE_URL", "http://localhost:4096")
OPENCODE_PASSWORD = os.environ.get("OPENCODE_SERVER_PASSWORD", "")

# Network Timeout
TIMEOUT = int(os.environ.get("GLTCH_TIMEOUT", "120"))

# LLM Temperature (lower = more deterministic, less hallucination)
TEMPERATURE = float(os.environ.get("GLTCH_TEMPERATURE", "0.4"))

# UI Settings
REFRESH_RATE = 10

# Giphy API Key (for GIF support)
GIPHY_API_KEY = os.environ.get("GIPHY_API_KEY", "")

# Gateway Settings
GATEWAY_HOST = os.environ.get("GLTCH_GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.environ.get("GLTCH_GATEWAY_PORT", "18888"))
GATEWAY_WS_PORT = int(os.environ.get("GLTCH_GATEWAY_WS_PORT", "18889"))

# Data Directories
DATA_DIR = os.environ.get("GLTCH_DATA_DIR", os.path.expanduser("~/.gltch"))
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
KB_DIR = os.path.join(DATA_DIR, "kb")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
