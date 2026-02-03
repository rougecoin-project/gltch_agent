# Architecture

GLTCH is a hybrid Python/TypeScript system designed for flexibility and extensibility.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GLTCH ECOSYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Discord   │  │  Telegram   │  │   WebChat   │  │    iOS      │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │                │            │
│         └────────────────┴────────────────┴────────────────┘            │
│                                   │                                      │
│                                   ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         GATEWAY                                    │  │
│  │                    TypeScript / Express                            │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐    │  │
│  │  │  HTTP API   │  │  WebSocket  │  │   Channel Adapters      │    │  │
│  │  │  REST/JSON  │  │  Real-time  │  │  Discord/Telegram/Web   │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘    │  │
│  │                                                                    │  │
│  │  Port: 18888                                                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│                                   ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                          AGENT                                     │  │
│  │                       Python / asyncio                             │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐    │  │
│  │  │  JSON-RPC   │  │    Core     │  │        Tools            │    │  │
│  │  │   Server    │  │   Logic     │  │  File/Shell/Network     │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘    │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐    │  │
│  │  │  Memory     │  │ Personality │  │     Gamification        │    │  │
│  │  │  Store      │  │   Engine    │  │    XP / Levels          │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘    │  │
│  │                                                                    │  │
│  │  Port: 18890                                                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│                                   ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                       LLM BACKENDS                                 │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐    │  │
│  │  │   Ollama    │  │  LM Studio  │  │   Cloud Providers       │    │  │
│  │  │   (Local)   │  │  (Remote)   │  │  OpenAI/Anthropic/etc   │    │  │
│  │  │  :11434     │  │   :1234     │  │                         │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### Agent (Python)

The core intelligence of GLTCH. Responsible for:

#### Core Module (`agent/core/`)
- **agent.py** — Main `GltchAgent` class, orchestrates all systems
- **llm.py** — LLM interface with streaming, multi-backend support, fallbacks

#### Memory Module (`agent/memory/`)
- **store.py** — JSON-based persistent storage
- **sessions.py** — Multi-user session management

#### Tools Module (`agent/tools/`)
- **actions.py** — Action parser and executor (file, shell, network, gif)
- **opencode.py** — OpenCode AI coding integration

#### Personality Module (`agent/personality/`)
- **emotions.py** — Mood management, environmental awareness

#### Gamification Module (`agent/gamification/`)
- **xp.py** — XP system, levels, ranks, unlocks

#### RPC Module (`agent/rpc/`)
- **server.py** — JSON-RPC 2.0 server (HTTP and stdio modes)

### Gateway (TypeScript)

The communication hub. Responsible for:

- **HTTP API** — REST endpoints for web dashboard
- **WebSocket** — Real-time bidirectional communication
- **Agent Bridge** — Proxies requests to Python agent via RPC
- **Session Management** — Tracks connected clients

### Web UI (Lit/Vite)

The user interface. Components:

- **app.ts** — Main application shell
- **sidebar.ts** — Navigation
- **header.ts** — Stats display
- **chat.ts** — Chat interface
- **settings.ts** — Configuration panel
- **status.ts** — Network visualization
- **ticker.ts** — Activity feed

## Data Flow

### Chat Message Flow

```
User Input (Terminal/Discord/Telegram/Web)
    │
    ▼
Gateway (if not terminal)
    │ HTTP POST /api/chat
    ▼
Agent RPC Server
    │ JSON-RPC "chat"
    ▼
GltchAgent.chat()
    │
    ├─► Build System Prompt (mode, mood, operator)
    │
    ├─► Prepare Messages (history + new message)
    │
    ▼
LLM Backend (stream_llm)
    │ Streaming response
    ▼
Parse Actions ([ACTION:...])
    │
    ├─► Execute Tools (file, shell, etc.)
    │
    ▼
Response + Action Results
    │
    ▼
Update Memory (history, XP, mood changes)
    │
    ▼
Return to User
```

### Settings Flow

```
Web UI Settings Panel
    │
    ▼
HTTP POST /api/settings
    │
    ▼
Gateway
    │ JSON-RPC "set_settings"
    ▼
Agent RPC Server
    │
    ▼
Update Memory
    │
    ▼
Save to disk (memory.json)
```

## LLM Backend Selection

GLTCH supports multiple LLM backends with automatic fallback:

```
┌─────────────────────────────────────────────────────┐
│              Backend Selection Logic                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  if openai_mode AND has_openai_key:                 │
│      use OpenAI Cloud                               │
│  elif boost_mode:                                    │
│      try Remote LM Studio                           │
│      fallback to Local Ollama                       │
│  else:                                              │
│      use Local Ollama                               │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Memory Structure

All state is persisted in `memory.json`:

```json
{
  "created": "2024-01-01T00:00:00",
  "operator": "dreadx",
  "mode": "cyberpunk",
  "mood": "focused",
  "boost": false,
  "openai_mode": false,
  "network_active": false,
  "xp": 1250,
  "level": 3,
  "chat_history": [...],
  "notes": [...],
  "missions": [...],
  "api_keys": {
    "openai": "sk-...",
    "anthropic": "sk-ant-..."
  }
}
```

## Security Considerations

- **Local-First**: By default, all data stays on your machine
- **API Keys**: Stored encrypted in memory.json, never transmitted
- **No Telemetry**: GLTCH doesn't phone home
- **Network Tools**: Disabled by default, require explicit `/net on`
- **RPC**: By default, only listens on localhost

## Extensibility

### Adding New Tools

1. Create function in `agent/tools/actions.py`
2. Register in `ACTION_HANDLERS` dict
3. Add documentation to system prompt

### Adding New LLM Providers

1. Update `agent/core/llm.py` with new backend logic
2. Add configuration to `agent/config/settings.py`
3. Update API key handling in `agent/rpc/server.py`

### Adding New Channels

1. Create adapter in `gateway/src/channels/`
2. Register in gateway startup
3. Handle message routing
