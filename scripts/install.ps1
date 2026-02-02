# GLTCH Installer Script (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║                    GLTCH INSTALLER                        ║" -ForegroundColor Red
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

function Check-Command {
    param($Command)
    if (Get-Command $Command -ErrorAction SilentlyContinue) {
        Write-Host "✓ $Command found" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ $Command not found" -ForegroundColor Red
        return $false
    }
}

Write-Host "Checking dependencies..."
Write-Host ""

# Check Python
if (-not (Check-Command "python")) {
    Write-Host "Please install Python 3.10+: https://python.org/" -ForegroundColor Yellow
    exit 1
}

# Check Node.js
if (-not (Check-Command "node")) {
    Write-Host "Please install Node.js 18+: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check pip
if (-not (Check-Command "pip")) {
    Write-Host "Please install pip" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Installing GLTCH..."
Write-Host ""

# Clone or update
if (Test-Path "glitch_agent") {
    Write-Host "Updating existing installation..."
    Set-Location "glitch_agent"
    git pull
} else {
    Write-Host "Cloning repository..."
    git clone https://github.com/your-org/glitch_agent.git
    Set-Location "glitch_agent"
}

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..."
pip install -r requirements.txt

# Install Gateway dependencies
Write-Host ""
Write-Host "Installing Gateway dependencies..."
Set-Location "gateway"
npm install
Set-Location ".."

# Install CLI dependencies
Write-Host ""
Write-Host "Installing CLI dependencies..."
Set-Location "cli"
npm install
try { npm link } catch { }
Set-Location ".."

# Check Ollama
Write-Host ""
if (Check-Command "ollama") {
    Write-Host "Pulling default model..."
    try { ollama pull phi3:3.8b } catch { }
} else {
    Write-Host "Ollama not found. Install from: https://ollama.ai/" -ForegroundColor Yellow
}

# Create config
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "Creating default configuration..."
    Copy-Item ".env.example" ".env"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "                  INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "To start GLTCH:"
Write-Host ""
Write-Host "  1. Start the agent:   python gltch.py --rpc http"
Write-Host "  2. Start the gateway: gltch gateway start"
Write-Host "  3. Open:              http://localhost:18888"
Write-Host ""
Write-Host "Or run in terminal mode: python gltch.py"
Write-Host ""
