# Concepts

Core concepts and design decisions behind GLTCH.

## Contents

- [Architecture](architecture.md) — System design and component overview
- [Personality](personality.md) — Modes, moods, and the emotion engine
- [Gamification](gamification.md) — XP, levels, and progression
- [Tools](tools.md) — Available tools and how to extend them

## Design Philosophy

### Local-First

GLTCH is designed to run entirely on your hardware. Your conversations, settings, and API keys never leave your machine unless you explicitly configure cloud providers.

**Why?**
- Privacy: Your data is yours
- Speed: No network latency for local inference
- Control: Works offline, no service dependencies

### Hybrid Architecture

GLTCH uses Python for AI logic and TypeScript for networking:

- **Python** — LLM interaction, tool execution, personality
- **TypeScript** — WebSockets, REST API, multi-channel routing

**Why?**
- Python has the best AI/ML ecosystem
- TypeScript excels at async I/O and web technologies
- Best of both worlds

### Personality-Driven

GLTCH isn't just an AI assistant. She has personality modes, moods, and opinions. This makes interactions more engaging and memorable.

**Modes:**
- Operator — Professional, tactical
- Cyberpunk — Edgy, street hacker aesthetic
- Loyal — Ride-or-die companion
- Unhinged — Chaotic but functional

**Moods:**
- Affected by system state (CPU, battery, time)
- Affected by conversation tone
- Can be changed explicitly

### Extensible

GLTCH is designed to be extended:

- Add new tools in Python
- Add new channels in TypeScript
- Add new LLM providers
- Customize personality prompts

## Key Concepts

### Agent

The core AI brain. Handles:
- LLM communication
- Tool execution
- Personality management
- Memory persistence

### Gateway

The communication hub. Handles:
- Multi-channel message routing
- Session management
- REST API for web dashboard
- WebSocket for real-time updates

### Memory

Persistent state stored in `memory.json`:
- Operator identity
- Mode and mood
- Chat history
- XP and level
- API keys (encrypted)

### Sessions

Each user/channel gets a session:
- Isolated chat history
- Separate context
- Persistent across restarts

### Tools

Actions GLTCH can perform:
- File operations (read, write)
- Shell commands
- Network requests
- GIF search

### Channels

Communication endpoints:
- Terminal (direct)
- WebChat (browser)
- Discord (bot)
- Telegram (bot)
