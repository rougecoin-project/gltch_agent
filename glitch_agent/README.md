# GLTCH ⚡

> "She's not a chatbot. She's a console with an attitude."

GLTCH is a **local-first, command-driven operator agent** for your terminal. She monitors your system, keeps notes, manages missions, and runs local LLM inference (with optional remote offloading).

She tracks:
- **CPU Stress** & **Battery** (Emotional Engine)
- **Environment** (Day/Night cycle)
- **Missions** & **Notes** (Persistent Memory)

## 📦 Features

- **Offline First**: Uses local Ollama models (Llama 3, Phi-3, etc).
- **Hybrid Inference**: Can offload heavy thinking to a remote machine (e.g., 4090 rig running LM Studio).
- **Emotional Intelligence**: Mood shifts based on system load (High CPU = Stressed/Angry).
- **Personality Modes**: Switch between `Operator`, `Cyberpunk`, `Loyal`, or `Unhinged`.
- **Tool Use**: File operations, system stats, and strictly guarded network commands.

## 🛠️ Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-repo/glitch_agent.git
   cd glitch_agent
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ollama (Required)**
   Ensure [Ollama](https://ollama.ai) is running locally.
   ```bash
   ollama pull llama3.2:3b
   ```

## 🚀 Usage

Run the agent:
```bash
python gltch.py
```

### Core Commands
| Command | Description |
|---------|-------------|
| `/mode <name>` | Change personality (`operator`, `feral`, `cyberpunk`) |
| `/boost` | Toggle Remote GPU (Configured in `config.py`) |
| `/net <on/off>` | Toggle Network Access (Default: OFF) |
| `/note <text>` | Save a persistent note |
| `/mission <text>` | Add a mission objective |
| `/status` | View system & agent health |

## ⚙️ Configuration

Edit `config.py` to change:
- **LLM Endpoints**: Local Ollama URL or Remote LM Studio URL.
- **Model Names**: Which models to target.
- **Giphy API Key**: Required for GIF support (Get one at developers.giphy.com).
- **Agent Identity**: Name and default settings.

## ⚠️ Safety

GLTCH is designed with **Guards**:
- **Network Killswitch**: Internet tools (`curl`, `ping`) are blocked by default.
- **Confirmation**: All file writes and shell commands require active user confirmation (Y/N).

## License

MIT
