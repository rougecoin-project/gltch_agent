#!/bin/bash
# GLTCH Installer Script (macOS/Linux)

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    GLTCH INSTALLER                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 found"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

echo "Checking dependencies..."
echo ""

# Check Python
if ! check_command python3; then
    echo -e "${YELLOW}Please install Python 3.10+: https://python.org/${NC}"
    exit 1
fi

# Check Node.js
if ! check_command node; then
    echo -e "${YELLOW}Please install Node.js 18+: https://nodejs.org/${NC}"
    exit 1
fi

# Check pip
if ! check_command pip3; then
    echo -e "${YELLOW}Please install pip${NC}"
    exit 1
fi

echo ""
echo "Installing GLTCH..."
echo ""

# Clone or update
if [ -d "glitch_agent" ]; then
    echo "Updating existing installation..."
    cd glitch_agent
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/your-org/glitch_agent.git
    cd glitch_agent
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Gateway dependencies
echo ""
echo "Installing Gateway dependencies..."
cd gateway
npm install
cd ..

# Install CLI dependencies
echo ""
echo "Installing CLI dependencies..."
cd cli
npm install
npm link 2>/dev/null || true
cd ..

# Check Ollama
echo ""
if check_command ollama; then
    echo "Pulling default model..."
    ollama pull phi3:3.8b || true
else
    echo -e "${YELLOW}Ollama not found. Install from: https://ollama.ai/${NC}"
fi

# Create config
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating default configuration..."
    cp .env.example .env
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                  INSTALLATION COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "To start GLTCH:"
echo ""
echo "  1. Start the agent:   python gltch.py --rpc http"
echo "  2. Start the gateway: gltch gateway start"
echo "  3. Open:              http://localhost:18888"
echo ""
echo "Or run in terminal mode: python gltch.py"
echo ""
