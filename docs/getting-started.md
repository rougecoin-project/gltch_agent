# Getting Started

Get GLTCH running in 5 minutes.

## Prerequisites

- **Node.js 18+**: For the gateway and CLI
- **Python 3.10+**: For the agent
- **Ollama**: For local LLM inference (recommended)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/glitch_agent.git
cd glitch_agent
```

### 2. Install Dependencies

```bash
# Python agent
pip install -r requirements.txt

# Gateway
cd gateway && npm install && cd ..

# CLI
cd cli && npm install && cd ..
```

### 3. Set Up Ollama

```bash
# Install Ollama (if not already installed)
# See: https://ollama.ai/

# Pull a model
ollama pull phi3:3.8b
```

### 4. Start the Agent

```bash
# Terminal 1: Start the agent RPC server
python gltch.py --rpc http --port 18890
```

### 5. Start the Gateway

```bash
# Terminal 2: Start the gateway
cd gateway
npx tsx src/index.ts start
```

### 6. Open the Dashboard

Open your browser to: http://localhost:18888

You should see the GLTCH dashboard with a chat interface!

## Terminal Mode

If you prefer the terminal, run GLTCH directly:

```bash
python gltch.py
```

This gives you the full terminal UI with streaming responses and all features.

## Next Steps

- [Configure channels](channels/index.md) (Discord, Telegram)
- [Explore CLI commands](cli/index.md)
- [Understand the architecture](concepts/architecture.md)
