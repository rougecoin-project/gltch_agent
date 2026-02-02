# Channels

GLTCH supports multiple messaging channels. Each channel connects to the gateway, which routes messages to the agent.

## Available Channels

| Channel | Status | Setup |
|---------|--------|-------|
| [Discord](discord.md) | Ready | Bot token required |
| [Telegram](telegram.md) | Ready | Bot token required |
| [WebChat](webchat.md) | Ready | Built-in |

## Channel Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Discord   │     │  Telegram   │     │   WebChat   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Gateway   │
                    │   Router    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Agent    │
                    └─────────────┘
```

## Checking Channel Status

```bash
# Via CLI
gltch channels status

# Via API
curl http://localhost:18888/api/status
```

## Adding a New Channel

1. Configure the channel token in `.env`
2. Restart the gateway
3. Verify with `gltch channels status`
