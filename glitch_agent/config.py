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

# Remote LLM (LM Studio / OpenAI Compatible)
# Set your remote IP here (e.g. 192.168.1.188)
REMOTE_URL = "http://192.168.1.188:1234/v1/chat/completions" 
REMOTE_MODEL = "deepseek-r1-distill-qwen-14b"
REMOTE_CTX = 8192
REMOTE_BACKEND = "openai"

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
