# GLTCH

> "She's not a chatbot. She's a console with an attitude."

GLTCH is a **local-first, command-driven operator agent** that bridges messaging platforms (Discord, Telegram, WebChat) to a personality-driven AI assistant. Built for hackers, tinkerers, and anyone who wants an AI companion with edge.

## Features

- **Local-First**: Runs on Ollama by default. No cloud required.
- **Multi-Channel**: Discord, Telegram, and WebChat support via Gateway
- **Personality Modes**: Operator, Cyberpunk, Loyal, or Unhinged
- **Emotional Engine**: Mood shifts based on system load and battery
- **Gamification**: XP, levels, ranks, and feature unlocks
- **Tool Use**: File operations, shell commands, GIFs
- **RPC API**: JSON-RPC interface for gateway integration

## Architecture

```
Discord / Telegram / WebChat
           │
           ▼
    ┌─────────────┐
    │   Gateway   │  (TypeScript)
    │  WebSocket  │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │    Agent    │  (Python)
    │   JSON-RPC  │
    └─────────────┘
```

## Quick Start

### Terminal Mode (Standalone)

```bash
# Clone
git clone https://github.com/your-org/glitch_agent.git
cd glitch_agent

# Install
pip install -r requirements.txt

# Run (requires Ollama)
ollama pull phi3:3.8b
python gltch.py
```

### RPC Mode (For Gateway)

```bash
# HTTP RPC Server
python gltch.py --rpc http --port 18890

# Stdio RPC (for subprocess)
python gltch.py --rpc stdio
```

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/status` | Agent status |
| `/mode <name>` | Change personality |
| `/mood <name>` | Change mood |
| `/boost` | Toggle remote GPU |
| `/openai` | Toggle OpenAI cloud |
| `/net <on/off>` | Toggle network access |
| `/xp` | Show rank & unlocks |

## Configuration

Environment variables:

```bash
# LLM Settings
GLTCH_LOCAL_URL=http://localhost:11434/api/chat
GLTCH_LOCAL_MODEL=phi3:3.8b
GLTCH_REMOTE_URL=http://192.168.1.188:1234/v1/chat/completions
OPENAI_API_KEY=sk-...

# Gateway
GLTCH_GATEWAY_PORT=18888

# Fun
GIPHY_API_KEY=your-key
```

## Project Structure

```
glitch_agent/
├── agent/                    # Python agent core
│   ├── core/                 # Main agent logic
│   ├── memory/               # Persistence
│   ├── tools/                # File/shell operations
│   ├── personality/          # Modes, moods, emotions
│   ├── gamification/         # XP, ranks, unlocks
│   ├── config/               # Settings
│   └── rpc/                  # JSON-RPC server
├── gateway/                  # TypeScript gateway
├── cli/                      # CLI toolkit
├── ui/                       # Web dashboard
├── docs/                     # Documentation
├── gltch.py                  # Entry point
└── pyproject.toml            # Python packaging
```

## License

MIT

---

*"We're all just playing with our own prompts."*
— An AI, probably high on tokens
