# Getting Started

Get GLTCH running in under 5 minutes.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** — [Download](https://python.org)
- **Node.js 18+** — [Download](https://nodejs.org)
- **Ollama** — [Download](https://ollama.ai)
- **Git** — [Download](https://git-scm.com)

## Step 1: Clone the Repository

```bash
git clone https://github.com/cyberdreadx/gltch_agent.git
cd gltch_agent
```

## Step 2: Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Pull an LLM Model

GLTCH uses Ollama for local inference. Pull a model:

```bash
# Recommended (8B parameters, good balance)
ollama pull deepseek-r1:8b

# Lightweight option (3.8B parameters)
ollama pull phi3:3.8b

# Powerful option (if you have GPU)
ollama pull llama3.2:latest
```

## Step 4: Run GLTCH

### Terminal Mode (Quick Start)

```bash
python gltch.py
```

You'll see the animated intro and can start chatting immediately!

### First Boot

On first run, GLTCH will ask for your **callsign** (operator name). This personalizes your experience.

```
What's your callsign, operator?
> dreadx
```

## Step 5: Basic Commands

Try these commands:

```
/help          # Show all commands
/status        # Check system status
/mode cyberpunk # Change personality
/boost         # Toggle remote GPU (if configured)
```

## Next Steps

### Run the Full Stack

For the complete experience with web UI:

**Terminal 1 — Agent (RPC Mode):**
```bash
python gltch.py --rpc http
```

**Terminal 2 — Gateway:**
```bash
cd gateway
npm install
npm run dev
```

**Terminal 3 — Web UI:**
```bash
cd ui
npm install
npm run dev
```

Then open http://localhost:3000

### Configure Remote LLM

To use a more powerful remote GPU:

1. Set up [LM Studio](https://lmstudio.ai) on your GPU machine
2. Enable the server (port 1234)
3. Configure GLTCH:

```bash
export GLTCH_REMOTE_URL=http://<gpu-ip>:1234/v1/chat/completions
export GLTCH_REMOTE_MODEL=your-model-name
```

4. Toggle boost mode: `/boost`

### Add API Keys

For cloud LLM providers (OpenAI, Claude, etc.):

1. Open the web UI: http://localhost:3000
2. Go to **Settings**
3. Scroll to **API Keys**
4. Click **Add Key** next to your provider
5. Paste your API key

### Connect Channels

See the [Channels documentation](channels/index.md) for:
- [Discord Bot](channels/discord.md)
- [Telegram Bot](channels/telegram.md)
- [WebChat](channels/webchat.md)

## Troubleshooting

### Ollama Connection Failed

```
FATAL LLM ERROR: <urlopen error [Errno 111] Connection refused>
```

**Solution:** Make sure Ollama is running:
```bash
ollama serve
```

### Model Not Found

```
FATAL LLM ERROR: HTTP Error 404: Not Found
```

**Solution:** Pull the model first:
```bash
ollama pull deepseek-r1:8b
```

### WSL Network Issues

If running in WSL and can't connect to Ollama on Windows:

1. Set Ollama to listen on all interfaces:
   ```powershell
   $env:OLLAMA_HOST="0.0.0.0"
   ollama serve
   ```

2. Add firewall rule (Admin PowerShell):
   ```powershell
   New-NetFirewallRule -DisplayName "Ollama WSL" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
   ```

3. Use Windows IP from WSL:
   ```bash
   export GLTCH_LOCAL_URL=http://$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):11434/api/chat
   ```
