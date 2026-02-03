# Installation Guide

Detailed installation instructions for GLTCH on various platforms.

## Quick Install (All Platforms)

```bash
git clone https://github.com/cyberdreadx/gltch_agent.git
cd gltch_agent
pip install -r requirements.txt
```

## Platform-Specific Instructions

### Windows

#### Prerequisites

1. **Python 3.10+**
   - Download from [python.org](https://python.org)
   - Check "Add to PATH" during installation

2. **Node.js 18+**
   - Download from [nodejs.org](https://nodejs.org)

3. **Ollama**
   - Download from [ollama.ai](https://ollama.ai)
   - Run the installer

#### Installation

```powershell
# Clone repository
git clone https://github.com/cyberdreadx/gltch_agent.git
cd gltch_agent

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd gateway
npm install
cd ..\ui
npm install
cd ..

# Pull a model
ollama pull deepseek-r1:8b

# Run GLTCH
python gltch.py
```

### macOS

#### Prerequisites

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 node

# Install Ollama
brew install ollama
```

#### Installation

```bash
# Clone repository
git clone https://github.com/cyberdreadx/gltch_agent.git
cd gltch_agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd gateway && npm install && cd ..
cd ui && npm install && cd ..

# Start Ollama and pull model
ollama serve &
ollama pull deepseek-r1:8b

# Run GLTCH
python gltch.py
```

### Linux (Ubuntu/Debian)

#### Prerequisites

```bash
# Update packages
sudo apt update

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Installation

```bash
# Clone repository
git clone https://github.com/cyberdreadx/gltch_agent.git
cd gltch_agent

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd gateway && npm install && cd ..
cd ui && npm install && cd ..

# Start Ollama and pull model
ollama serve &
ollama pull deepseek-r1:8b

# Run GLTCH
python gltch.py
```

### WSL (Windows Subsystem for Linux)

#### Special Considerations

WSL has its own network stack. To connect to Ollama on Windows:

1. **Configure Ollama on Windows:**
   ```powershell
   $env:OLLAMA_HOST="0.0.0.0"
   ollama serve
   ```

2. **Add Firewall Rule (Admin PowerShell):**
   ```powershell
   New-NetFirewallRule -DisplayName "Ollama WSL" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
   ```

3. **Configure GLTCH in WSL:**
   ```bash
   # Get Windows host IP
   WIN_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
   export GLTCH_LOCAL_URL=http://$WIN_IP:11434/api/chat
   ```

4. **Or run Ollama inside WSL:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama serve
   ```

## Docker (Coming Soon)

```bash
docker-compose up -d
```

## Verifying Installation

### Check Python

```bash
python --version
# Should show Python 3.10+
```

### Check Node

```bash
node --version
# Should show v18+
```

### Check Ollama

```bash
ollama list
# Should show available models
```

### Check GLTCH

```bash
python gltch.py --help
# Should show usage information
```

## Troubleshooting

### "python: command not found"

- Windows: Reinstall Python with "Add to PATH" checked
- macOS/Linux: Use `python3` instead of `python`

### "pip: command not found"

```bash
# Install pip
python -m ensurepip --upgrade
```

### "No module named 'venv'"

```bash
# Ubuntu/Debian
sudo apt install python3.11-venv
```

### "npm: command not found"

Reinstall Node.js from [nodejs.org](https://nodejs.org)

### Ollama Connection Refused

```bash
# Make sure Ollama is running
ollama serve

# Check if it's listening
curl http://localhost:11434/api/tags
```

### Permission Denied

```bash
# If you get permission errors
sudo chown -R $USER:$USER .
```

## Updating GLTCH

```bash
cd gltch_agent
git pull

# Update Python dependencies
pip install -r requirements.txt --upgrade

# Update Node dependencies
cd gateway && npm update && cd ..
cd ui && npm update && cd ..
```

## Uninstalling

```bash
# Remove GLTCH
rm -rf gltch_agent

# Remove virtual environment (if outside project)
rm -rf ~/.gltch-venv

# Optionally remove Ollama
# macOS: brew uninstall ollama
# Linux: sudo rm /usr/local/bin/ollama
```
