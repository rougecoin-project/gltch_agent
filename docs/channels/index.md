# Channels

GLTCH can communicate through multiple channels simultaneously. Each channel connects through the Gateway, which routes messages to the Agent.

## Available Channels

| Channel | Status | Description |
|---------|--------|-------------|
| [Terminal](../getting-started.md) | ✅ Ready | Direct command-line interface |
| [WebChat](webchat.md) | ✅ Ready | Browser-based chat via Web UI |
| [Discord](discord.md) | 🔧 Config needed | Discord bot integration |
| [Telegram](telegram.md) | 🔧 Config needed | Telegram bot integration |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Discord   │     │  Telegram   │     │   WebChat   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │     Gateway     │
                  │   (Port 18888)  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │      Agent      │
                  │   (Port 18890)  │
                  └─────────────────┘
```

## Common Configuration

All channels share these configuration options:

```bash
# Gateway settings
GLTCH_GATEWAY_PORT=18888
GLTCH_GATEWAY_HOST=0.0.0.0

# Agent RPC settings
GLTCH_RPC_HOST=127.0.0.1
GLTCH_RPC_PORT=18890
```

## Session Management

Each channel maintains separate sessions:

- **Terminal**: Single session per instance
- **WebChat**: Session per browser connection
- **Discord**: Session per server + user
- **Telegram**: Session per chat

Sessions preserve:
- Chat history
- User context
- Conversation state

## Adding a New Channel

To add a custom channel:

1. Create adapter in `gateway/src/channels/`
2. Implement message handler interface
3. Register with gateway on startup
4. Handle incoming/outgoing message translation

Example adapter structure:

```typescript
interface ChannelAdapter {
  name: string;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  onMessage(handler: MessageHandler): void;
  send(sessionId: string, message: string): Promise<void>;
}
```
