# Architecture

How GLTCH components fit together.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      User Interfaces                     │
├─────────────┬────────────────┬─────────────────────────┤
│   Discord   │    Telegram    │    WebChat / CLI        │
└──────┬──────┴───────┬────────┴──────────┬──────────────┘
       │              │                    │
       └──────────────┼────────────────────┘
                      │
              ┌───────▼───────┐
              │    Gateway    │  TypeScript
              │  Port: 18888  │  HTTP + WebSocket
              │  Port: 18889  │
              └───────┬───────┘
                      │
                      │  JSON-RPC
                      │
              ┌───────▼───────┐
              │     Agent     │  Python
              │  Port: 18890  │
              └───────────────┘
                      │
              ┌───────▼───────┐
              │     Ollama    │
              │  Port: 11434  │
              └───────────────┘
```

## Components

### Agent (Python)

The brain of GLTCH. Handles:
- LLM inference (via Ollama or remote)
- Memory persistence
- Tool execution
- Personality and emotions
- Gamification

Location: `agent/`

### Gateway (TypeScript)

The communication hub. Handles:
- Channel connections (Discord, Telegram, WebChat)
- WebSocket connections
- Message routing
- Session management
- REST API

Location: `gateway/`

### CLI (TypeScript)

Management toolkit. Handles:
- Gateway control (start/stop)
- Channel configuration
- System diagnostics
- Interactive setup

Location: `cli/`

### UI (TypeScript/Lit)

Web dashboard. Provides:
- Chat interface
- Status monitoring
- Settings management

Location: `ui/`

## Communication

### Gateway ↔ Agent

JSON-RPC 2.0 over HTTP:

```json
// Request
{
  "jsonrpc": "2.0",
  "method": "chat",
  "params": {
    "message": "hello",
    "session_id": "discord:123"
  },
  "id": 1
}

// Response
{
  "jsonrpc": "2.0",
  "result": {
    "response": "Hey there!",
    "mood": "focused"
  },
  "id": 1
}
```

### Client ↔ Gateway

WebSocket with JSON messages:

```json
// Client sends
{"type": "chat", "text": "hello"}

// Server responds
{"type": "response", "response": "Hey!"}
{"type": "typing", "typing": false}
```

## Data Flow

1. User sends message via channel (Discord/Telegram/WebChat)
2. Gateway receives and identifies session
3. Gateway routes to agent via JSON-RPC
4. Agent processes with LLM and tools
5. Agent returns response
6. Gateway formats for channel
7. User receives response

## Sessions

Each channel+user combination gets a session:
- `discord:guild:channel` - Discord server channel
- `discord:dm:user` - Discord DM
- `telegram:group:id` - Telegram group
- `telegram:dm:user` - Telegram DM
- `webchat:client-id` - Browser session

Sessions maintain chat history and context.
