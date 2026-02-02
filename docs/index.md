# GLTCH Documentation

> "She's not a chatbot. She's a console with an attitude."

Welcome to the GLTCH documentation. GLTCH is a local-first, command-driven operator agent that bridges messaging platforms to a personality-driven AI assistant.

## Quick Links

- [Getting Started](getting-started.md) - Get GLTCH running in 5 minutes
- [Installation](install/index.md) - Detailed installation guide
- [CLI Reference](cli/index.md) - Command-line toolkit
- [Channels](channels/index.md) - Discord, Telegram, WebChat setup
- [Concepts](concepts/index.md) - Architecture and design

## What is GLTCH?

GLTCH is a multi-component AI agent ecosystem:

- **Python Agent Core** - The brain with personality, memory, and tools
- **TypeScript Gateway** - WebSocket hub connecting channels to the agent
- **Multi-Channel Support** - Discord, Telegram, and browser-based WebChat
- **CLI Toolkit** - Manage everything from the command line
- **Web Dashboard** - Visual interface for chat and configuration

## Key Features

- **Local-First**: Runs on Ollama by default. No cloud required.
- **Personality-Driven**: Modes (Operator, Cyberpunk, Loyal, Unhinged) and dynamic moods
- **Gamification**: XP, levels, ranks, and feature unlocks
- **Tool Execution**: File operations, shell commands, GIFs
- **Emotional Engine**: Mood shifts based on system load and battery

## Architecture

```
Discord / Telegram / WebChat
           │
           ▼
    ┌─────────────┐
    │   Gateway   │  (TypeScript)
    │  WebSocket  │
    └──────┬──────┘
           │ JSON-RPC
           ▼
    ┌─────────────┐
    │    Agent    │  (Python)
    │    Core     │
    └─────────────┘
```

## Support

- GitHub Issues: Report bugs and request features
- Discord: Join the community (coming soon)
