# CLI Reference

GLTCH provides command-line interfaces for both the terminal and the gateway.

## Terminal Commands

When running `python gltch.py`, these commands are available:

### System Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/status` | Display agent status, model info, and connection state |
| `/exit` or `/quit` | Exit GLTCH |
| `/clear` | Clear chat history |
| `/save` | Force save memory to disk |

### Personality Commands

| Command | Description |
|---------|-------------|
| `/mode <name>` | Change personality mode |
| `/mood <name>` | Change current mood |

**Available modes:**
- `operator` — Tactical, efficient (default)
- `cyberpunk` — Street hacker, edgy
- `loyal` — Ride-or-die, got your back
- `unhinged` — Chaotic, wild, functional (unlock at level 5)

**Available moods:**
- `focused` — Locked in (default)
- `calm` — Steady
- `feral` — Intense, ready to bite
- `affectionate` — Warm, caring

### LLM Commands

| Command | Description |
|---------|-------------|
| `/boost` | Toggle remote GPU (LM Studio) |
| `/openai` | Toggle OpenAI cloud mode |
| `/model` | Show model selection menu |

### Network Commands

| Command | Description |
|---------|-------------|
| `/net on` | Enable network tools |
| `/net off` | Disable network tools |

### Gamification Commands

| Command | Description |
|---------|-------------|
| `/xp` | Show XP, level, rank, and progress |

### OpenCode Commands

| Command | Description |
|---------|-------------|
| `/code` | Check OpenCode status, list projects |
| `/code <prompt>` | Start new coding project |
| `/code @project <prompt>` | Continue existing project |

## Startup Options

```bash
python gltch.py [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--rpc <mode>` | Run in RPC mode (`http` or `stdio`) |
| `--port <port>` | RPC server port (default: 18890) |
| `--host <host>` | RPC server host (default: 127.0.0.1) |

### Examples

```bash
# Interactive terminal mode
python gltch.py

# HTTP RPC server
python gltch.py --rpc http --port 18890

# HTTP RPC on all interfaces
python gltch.py --rpc http --host 0.0.0.0

# Stdio RPC (for subprocess communication)
python gltch.py --rpc stdio
```

## Gateway CLI

The gateway also has a CLI:

```bash
cd gateway
npx gltch-gateway [COMMAND] [OPTIONS]
```

### Commands

| Command | Description |
|---------|-------------|
| `start` | Start the gateway server |
| `status` | Check gateway status |

### Start Options

| Option | Description |
|--------|-------------|
| `--port <port>` | HTTP port (default: 18888) |
| `--host <host>` | Host to bind (default: 127.0.0.1) |
| `--agent-url <url>` | Agent RPC URL |

### Examples

```bash
# Start gateway
npx gltch-gateway start

# Start on all interfaces
npx gltch-gateway start --host 0.0.0.0

# Custom port
npx gltch-gateway start --port 8080

# Development mode
npm run dev
```

## Environment Variables

Both CLI tools respect these environment variables:

### Agent

```bash
# LLM Configuration
GLTCH_LOCAL_URL=http://localhost:11434/api/chat
GLTCH_LOCAL_MODEL=deepseek-r1:8b
GLTCH_REMOTE_URL=http://100.92.52.78:1234/v1/chat/completions
GLTCH_REMOTE_MODEL=deepseek-r1-distill-qwen-32b

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# OpenCode
OPENCODE_ENABLED=true
OPENCODE_URL=http://localhost:4096
```

### Gateway

```bash
GLTCH_GATEWAY_PORT=18888
GLTCH_GATEWAY_HOST=0.0.0.0
GLTCH_AGENT_URL=http://localhost:18890

# Channel tokens
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Connection error |

## Tips

### Command Autocomplete

Type `/` and use Tab for command autocompletion in terminal mode.

### Model Selection Menu

Type `/model` to see an interactive menu of available models from Ollama or LM Studio.

### Quick Status Check

```bash
# Check if agent is healthy
curl http://localhost:18890/health

# Check if gateway is healthy
curl http://localhost:18888/health
```
