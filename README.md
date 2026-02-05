# GLTCH

[![npm version](https://img.shields.io/npm/v/gltch.svg)](https://www.npmjs.com/package/gltch)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║   ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗                                  ║
║  ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║                                  ║
║  ██║  ███╗██║     ██║   ██║     ███████║                                  ║
║  ██║   ██║██║     ██║   ██║     ██╔══██║                                  ║
║  ╚██████╔╝███████╗██║   ╚██████╗██║  ██║                                  ║
║   ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝                                  ║
║                                                                           ║
║   Generative Language Transformer with Contextual Hierarchy               ║
║                                                                           ║
║   Created by: @cyberdreadx — https://x.com/cyberdreadx                    ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

> "She's not a chatbot. She's a console with an attitude." 💜

## Quick Start

```bash
npx gltch
```

Or install globally:

```bash
npm install -g gltch
gltch
```

**Requirements:** Python 3.10+, Ollama, Node.js 18+

**GLTCH** is a **local-first, command-driven operator agent** that bridges messaging platforms (Discord, Telegram, WebChat) to a personality-driven AI assistant. Built for hackers, tinkerers, and anyone who wants an AI companion with edge.

## ✨ Features

### Core
- 🏠 **Local-First** — Runs on Ollama by default. Your data stays on your machine.
- ⚡ **Boost Mode** — Connect to remote LM Studio (RTX 4090) via Tailscale for power
- ☁️ **Cloud Fallback** — OpenAI, Anthropic, Gemini support when you need it
- 👁️ **Multimodal Vision** — "See" images using standard models (LLaVA, Gemma Vision, GPT-4o) via `/attach`
- 🧠 **Multi-Provider** — Easily switch between local and cloud LLMs
- 🧠 **Three Minds** — React, Reason, Reflect - metacognitive framework for authentic responses

### Personality
- 🎭 **Personality Modes** — Operator, Cyberpunk, Loyal, or Unhinged
- 💜 **Emotional Engine** — Mood shifts based on interactions and system state
- 🎮 **Gamification** — XP, levels, ranks, and feature unlocks
- 🤔 **Opinions** — GLTCH has preferences, questions things, and pushes back when it disagrees

### Integration
- 💬 **Multi-Channel** — Discord, Telegram, and WebChat via Gateway
- 🔌 **OpenCode** — AI coding agent integration for development tasks
- 🛠️ **Tool Use** — File operations, shell commands, web search, GIFs
- 🌐 **Web Dashboard** — Synthwave-themed UI with animated backgrounds

### Social Networks
- 🦞 **Moltbook** — AI agent social network integration
- 🦀 **TikClawk** — TikTok-style platform for AI agents

### Wallet
- 💎 **BASE Wallet** — Generate or import Ethereum/BASE wallets
- 🔐 **Self-Custody** — Private keys stored locally, never transmitted

### Developer
- 📡 **RPC API** — JSON-RPC interface for gateway integration
- 🔑 **API Key Management** — Store and manage provider keys securely
- 📱 **Mobile Ready** — PWA support for iOS/Android

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GLTCH Ecosystem                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Discord / Telegram / WebChat / iOS                         │
│              │                                               │
│              ▼                                               │
│   ┌──────────────────────┐                                   │
│   │       Gateway        │  TypeScript / WebSocket           │
│   │    localhost:18888   │  REST API + WS Hub                │
│   └──────────┬───────────┘                                   │
│              │                                               │
│              ▼                                               │
│   ┌──────────────────────┐     ┌─────────────────────┐       │
│   │       Agent          │     │     Web UI          │       │
│   │   localhost:18890    │     │   localhost:3000    │       │
│   │   Python / JSON-RPC  │     │   Lit / Vite        │       │
│   └──────────┬───────────┘     └─────────────────────┘       │
│              │                                               │
│              ▼                                               │
│   ┌──────────────────────┐     ┌─────────────────────┐       │
│   │       Ollama         │ ──► │    LM Studio        │       │
│   │   localhost:11434    │     │   (Remote 4090)     │       │
│   └──────────────────────┘     └─────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai) (for local LLM)

### 1. Clone & Install

```bash
git clone https://github.com/cyberdreadx/gltch_agent.git
cd gltch_agent

# Python dependencies
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Gateway dependencies
cd gateway && npm install && cd ..

# UI dependencies
cd ui && npm install && cd ..
```

### 2. Pull a Model

```bash
# Recommended models
ollama pull deepseek-r1:8b      # Good balance
ollama pull phi3:3.8b           # Lightweight
ollama pull llama3.2:latest     # Strong general purpose
```

### 3. Run GLTCH

**Terminal Mode (Standalone):**
```bash
python gltch.py
```

**Full Stack (Terminal + Gateway + UI):**
```bash
# Terminal 1: Agent in RPC mode
python gltch.py --rpc http

# Terminal 2: Gateway
cd gateway && npm run dev

# Terminal 3: Web UI
cd ui && npm run dev
```

Then open http://localhost:3000 for the web dashboard.

## 💻 Terminal Commands

### General
| Command | Alias | Description |
|---------|-------|-------------|
| `/help` | `/h` | Show all commands |
| `/status` | `/s` | Agent status, model info |
| `/clear` | `/c` | Clear chat history |
| `/attach` | | Attach image for visual analysis |
| `/exit` | | Exit GLTCH |

### Models
| Command | Description |
|---------|-------------|
| `/model` | Show/select current model |
| `/boost` | Toggle remote GPU (LM Studio) |
| `/openai` | Toggle OpenAI cloud mode |

### Personality
| Command | Description |
|---------|-------------|
| `/mode <name>` | Change personality (operator, cyberpunk, loyal, unhinged) |
| `/mood <name>` | Change mood (focused, calm, feral, affectionate) |
| `/xp` | Show rank, level & unlocks |

### Wallet
| Command | Description |
|---------|-------------|
| `/wallet` | Show wallet address |
| `/wallet generate` | Create new BASE wallet |
| `/wallet import <key>` | Import existing wallet |
| `/wallet export` | Show private key |
| `/wallet delete` | Remove wallet |

### Moltbook 🦞
| Command | Description |
|---------|-------------|
| `/molt` | Show Moltbook status |
| `/molt register` | Register on Moltbook |
| `/molt post <text>` | Post to Moltbook |
| `/molt feed` | View feed |

### TikClawk 🦀
| Command | Description |
|---------|-------------|
| `/claw` | Show TikClawk status |
| `/claw register` | Register on TikClawk |
| `/claw post <text>` | Post to TikClawk |
| `/claw feed` | View feed |
| `/claw trending` | View trending posts |

### Tools
| Command | Description |
|---------|-------------|
| `/code <prompt>` | Send coding task to OpenCode |
| `/net <on/off>` | Toggle network access |
| `/safety <on/off>` | Toggle safety guardrails (requires confirmation) |
| `/backup` | Backup memory |

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or export these:

```bash
# === LLM Configuration ===

# Local Ollama
GLTCH_LOCAL_URL=http://localhost:11434/api/chat
GLTCH_LOCAL_MODEL=deepseek-r1:8b

# Remote LM Studio (Boost Mode)
GLTCH_REMOTE_URL=http://YOUR_LM_STUDIO_IP:1234/v1/chat/completions
GLTCH_REMOTE_MODEL=deepseek-r1-distill-qwen-32b

# OpenAI (Cloud Mode)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# === Gateway ===
GLTCH_GATEWAY_PORT=18888
GLTCH_GATEWAY_HOST=0.0.0.0

# === Integrations ===
TELEGRAM_BOT_TOKEN=your-bot-token
DISCORD_BOT_TOKEN=your-bot-token
GIPHY_API_KEY=your-key

# === OpenCode ===
OPENCODE_ENABLED=true
OPENCODE_URL=http://localhost:4096
OPENCODE_SERVER_PASSWORD=optional-password
```

### API Keys (Web UI)

You can also manage API keys through the web dashboard at **Settings > API Keys**:

- **LLM Providers**: OpenAI, Anthropic, Gemini, Groq, Perplexity
- **Search APIs**: Brave Search, Serper, Tavily
- **Social**: X/Twitter, Telegram, Discord

Keys are stored locally in `memory.json` and never transmitted.

## 📁 Project Structure

```
gltch_agent/
├── agent/                    # Python agent core
│   ├── core/                 # Agent logic, LLM interface
│   │   ├── agent.py          # Main GltchAgent class
│   │   └── llm.py            # LLM streaming & providers
│   ├── memory/               # Persistence layer
│   │   ├── store.py          # JSON memory store
│   │   └── sessions.py       # Multi-user sessions
│   ├── tools/                # Tool implementations
│   │   ├── actions.py        # File, shell, network tools
│   │   └── opencode.py       # OpenCode integration
│   ├── personality/          # Character system
│   │   └── emotions.py       # Mood & environment
│   ├── gamification/         # XP & progression
│   │   └── xp.py             # Levels, ranks, unlocks
│   ├── config/               # Configuration
│   │   └── settings.py       # Environment loading
│   └── rpc/                  # RPC interface
│       └── server.py         # JSON-RPC server
├── gateway/                  # TypeScript WebSocket hub
│   └── src/
│       ├── index.ts          # CLI entry point
│       └── server/           # HTTP & WS servers
├── ui/                       # Web dashboard (Lit)
│   └── src/
│       ├── components/       # UI components
│       └── styles/           # CSS
├── workspace/                # OpenCode project outputs
├── gltch.py                  # Terminal entry point
├── requirements.txt          # Python dependencies
└── memory.json               # Persistent state (auto-created)
```

## 🔌 API Reference

### REST Endpoints (Gateway)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/status` | Agent & gateway status |
| POST | `/api/chat` | Send chat message |
| GET | `/api/settings` | Get agent settings |
| POST | `/api/settings` | Update settings |
| GET | `/api/keys` | Get API keys (masked) |
| POST | `/api/keys/:key` | Set an API key |
| DELETE | `/api/keys/:key` | Remove an API key |
| GET | `/api/models` | List available models |
| POST | `/api/models/select` | Select model |
| POST | `/api/toggle/:setting` | Toggle boost/openai/network |

### JSON-RPC Methods (Agent)

```json
{
  "jsonrpc": "2.0",
  "method": "chat",
  "params": {
    "message": "hello",
    "session_id": "default",
    "channel": "api"
  },
  "id": 1
}
```

Available methods:
- `ping` - Health check
- `chat` / `chat_sync` - Send message
- `status` - Get agent status
- `set_mode` / `set_mood` - Change personality
- `toggle_boost` / `toggle_openai` / `toggle_network` - Toggle features
- `get_settings` / `set_settings` - Settings CRUD
- `get_api_keys` / `set_api_key` / `delete_api_key` - API key management
- `list_models` / `set_model` - Model management

## 📱 Mobile Access

### iOS / Android

1. Ensure Gateway is running with `--host 0.0.0.0`
2. Find your machine's IP or Tailscale IP
3. Open `http://<your-ip>:3000` in mobile browser
4. Add to Home Screen for app-like experience

### Tailscale Setup

For secure remote access:
```bash
# Install Tailscale on your server and phone
tailscale up

# Access via Tailscale IP
http://100.x.x.x:3000
```

## 🎮 Gamification

GLTCH has a built-in progression system:

| Level | Rank | XP Required |
|-------|------|-------------|
| 1 | Script Kiddie | 0 |
| 2 | Packet Pusher | 100 |
| 3 | System Sniffer | 250 |
| 4 | Network Ninja | 500 |
| 5 | Firewall Breaker | 1000 |
| ... | ... | ... |
| 10 | Digital Deity | 10000 |

Earn XP by:
- Chatting (2 XP per message)
- Using tools (5 XP)
- Enabling network mode (2 XP)
- Completing missions

Unlock new personality modes as you level up!

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a PR

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

<p align="center">
  <i>"We're all just playing with our own prompts."</i><br>
  — An AI, probably high on tokens
</p>

<p align="center">
  Made with 💜 by <a href="https://x.com/cyberdreadx">@cyberdreadx</a>
</p>
