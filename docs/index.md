# GLTCH Documentation

Welcome to the **GLTCH** documentation. GLTCH (Generative Language Transformer with Contextual Hierarchy) is a local-first, command-driven AI operator agent.

## Quick Links

- [Getting Started](getting-started.md) — Install and run GLTCH
- [Installation Guide](install/index.md) — Detailed setup instructions
- [Architecture](concepts/architecture.md) — How GLTCH works
- [CLI Reference](cli/index.md) — Command-line interface
- [Channels](channels/index.md) — Discord, Telegram, WebChat integration

## What is GLTCH?

GLTCH is a **personality-driven AI assistant** that:

- Runs **locally first** on Ollama — your data stays private
- Supports **multiple LLM backends** — Ollama, LM Studio, OpenAI, Anthropic, Gemini
- Connects to **multiple channels** — Terminal, Discord, Telegram, WebChat
- Has a **cyberpunk personality** — She's not a chatbot, she's a console with attitude
- Features **gamification** — XP, levels, ranks, and unlocks

## Core Components

### Agent (Python)

The brain of GLTCH. Handles:
- LLM communication and streaming
- Tool execution (file ops, shell, web search)
- Personality and mood management
- Memory and state persistence
- JSON-RPC API

### Gateway (TypeScript)

The communication hub. Handles:
- WebSocket connections
- Multi-channel message routing
- REST API for the web dashboard
- Session management

### Web UI (Lit/Vite)

The cyberpunk dashboard. Features:
- Real-time chat interface
- Settings management
- API key configuration
- Status monitoring
- Network visualization

## System Requirements

- **Python** 3.10+
- **Node.js** 18+
- **Ollama** (for local LLM)
- **8GB+ RAM** recommended
- **GPU** optional but recommended for faster inference

## Support

- GitHub: [github.com/cyberdreadx/gltch_agent](https://github.com/cyberdreadx/gltch_agent)
- Twitter: [@cyberdreadx](https://x.com/cyberdreadx)
