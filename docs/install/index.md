# Installation

Detailed installation instructions for all components.

## Requirements

| Component | Minimum Version |
|-----------|----------------|
| Node.js | 18.0.0 |
| Python | 3.10 |
| Ollama | Latest |

## Installation Methods

### From Source (Recommended)

1. **Clone the repository**

```bash
git clone https://github.com/your-org/glitch_agent.git
cd glitch_agent
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Install Gateway dependencies**

```bash
cd gateway
npm install
cd ..
```

4. **Install CLI dependencies**

```bash
cd cli
npm install
cd ..
```

5. **Install UI dependencies (optional)**

```bash
cd ui
npm install
cd ..
```

### Using pip

```bash
pip install gltch
```

### Using npm (CLI + Gateway)

```bash
npm install -g @gltch/cli
```

## Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# LLM Settings
GLTCH_LOCAL_MODEL=phi3:3.8b

# Channel Tokens (optional)
DISCORD_BOT_TOKEN=your-token
TELEGRAM_BOT_TOKEN=your-token

# Giphy (optional, for GIF support)
GIPHY_API_KEY=your-key
```

## Verifying Installation

Run the doctor command:

```bash
gltch doctor
```

This checks all dependencies and configuration.

## Updating

```bash
# From source
git pull
pip install -r requirements.txt
cd gateway && npm install && cd ..

# From pip
pip install --upgrade gltch

# From npm
npm update -g @gltch/cli
```
