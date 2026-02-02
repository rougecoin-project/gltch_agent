# CLI Reference

The `gltch` command-line interface for managing GLTCH.

## Installation

```bash
cd cli && npm install
npm link  # Makes 'gltch' available globally
```

## Commands

### Gateway

```bash
# Start the gateway
gltch gateway start [options]
  -p, --port <port>       HTTP port (default: 18888)
  -w, --ws-port <port>    WebSocket port (default: 18889)
  -h, --host <host>       Host to bind (default: 127.0.0.1)
  --agent-url <url>       Agent RPC URL (default: http://127.0.0.1:18890)
  -d, --detach            Run in background

# Stop the gateway
gltch gateway stop

# Check gateway status
gltch gateway status
```

### Channels

```bash
# Check all channel status
gltch channels status

# Configure a channel
gltch channels login <channel>

# Disconnect a channel
gltch channels logout <channel>
```

### Configuration

```bash
# Get a config value
gltch config get <key>

# Set a config value
gltch config set <key> <value>

# Remove a config value
gltch config unset <key>

# List all config
gltch config list

# Show config file path
gltch config path

# Open config in editor
gltch config edit
```

### Status

```bash
# Overall status
gltch status
gltch status --all  # Detailed

# Quick health check
gltch ping
```

### Doctor

```bash
# Diagnose issues
gltch doctor

# Interactive setup wizard
gltch onboard
```

## Examples

### Start Everything

```bash
# Terminal 1: Agent
python gltch.py --rpc http

# Terminal 2: Gateway
gltch gateway start

# Check it's working
gltch ping
```

### Configure Discord

```bash
gltch channels login discord
# Follow the prompts to enter your token

# Verify
gltch channels status
```

### Check System Health

```bash
gltch doctor
```

Output:
```
GLTCH Doctor

Checking system configuration...

  Node.js version... ✓ v20.10.0
  Python version... ✓ Python 3.11.5
  Ollama... ✓ Running (3 models)
  Config directory... ✓ ~/.gltch
  Gateway dependencies... ✓ Installed
  Agent dependencies... ✓ Installed
  Environment file... ✓ Found

All checks passed! GLTCH is ready.
```
