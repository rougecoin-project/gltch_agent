"""
GLTCH Configuration
"""

# Agent Identity
AGENT_NAME = "GLTCH"

# Local LLM (Ollama)
LOCAL_URL = "http://localhost:11434/api/chat"
LOCAL_MODEL = "phi3:3.8b" 
LOCAL_CTX = 4096 
LOCAL_BACKEND = "ollama"

# Remote LLM (LM Studio - NEW API)
# LM Studio 0.3+ uses /api/v1/chat endpoint
# Start with: lms server start
REMOTE_URL = "http://localhost:1234/api/v1/chat" 
REMOTE_MODEL = "auto"  # "auto" = use currently loaded model
REMOTE_CTX = 8192
REMOTE_BACKEND = "lmstudio"  # New backend type for LM Studio API

# Legacy LM Studio (OpenAI-compatible, for older versions)
LMSTUDIO_LEGACY_URL = "http://localhost:1234/v1/chat/completions"

# OpenAI API (Cloud)
# Set your OpenAI API key here or use environment variable OPENAI_API_KEY
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # Set your key here or export OPENAI_API_KEY
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o"  # or "gpt-4o-mini" for cheaper option
OPENAI_CTX = 128000

# Network Timeout
TIMEOUT = 120

# UI Settings
REFRESH_RATE = 10

# Fun
# 1. Log in to https://developers.giphy.com/dashboard/
# 2. Create an App -> Select 'API' -> Copy the Key
GIPHY_API_KEY = "jzWGk9fn3u9fcckMiyqYNekZOBHQCDYg"
