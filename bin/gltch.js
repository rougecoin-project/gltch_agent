#!/usr/bin/env node

import { spawn } from 'child_process';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const BANNER = `
\x1b[35m   ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗\x1b[0m
\x1b[35m  ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║\x1b[0m
\x1b[36m  ██║  ███╗██║     ██║   ██║     ███████║\x1b[0m
\x1b[36m  ██║   ██║██║     ██║   ██║     ██╔══██║\x1b[0m
\x1b[35m  ╚██████╔╝███████╗██║   ╚██████╗██║  ██║\x1b[0m
\x1b[35m   ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝\x1b[0m
`;

const HELP = `
${BANNER}
\x1b[90mLocal-first AI agent with personality\x1b[0m

\x1b[33mUsage:\x1b[0m
  gltch                    Start terminal chat
  gltch serve              Start gateway + web UI
  gltch chat               Terminal chat (alias)
  gltch web                Open web UI only
  gltch doctor             Check system requirements
  gltch --help             Show this help

\x1b[33mRequirements:\x1b[0m
  • Python 3.10+
  • Ollama (for local LLM)
  • Node.js 18+ (for gateway)

\x1b[90mhttps://github.com/cyberdreadx/gltch_agent\x1b[0m
`;

const args = process.argv.slice(2);
const command = args[0] || 'chat';

// Check Python
function checkPython() {
  try {
    const result = spawn.sync('python', ['--version']);
    return result.status === 0;
  } catch {
    try {
      const result = spawn.sync('python3', ['--version']);
      return result.status === 0;
    } catch {
      return false;
    }
  }
}

function getPythonCmd() {
  try {
    const result = spawn.sync('python', ['--version']);
    if (result.status === 0) return 'python';
  } catch {}
  return 'python3';
}

function runPython(script, extraArgs = []) {
  const python = getPythonCmd();
  const scriptPath = join(ROOT, script);
  
  if (!existsSync(scriptPath)) {
    console.error(`\x1b[31mScript not found: ${scriptPath}\x1b[0m`);
    process.exit(1);
  }
  
  const child = spawn(python, [scriptPath, ...extraArgs], {
    cwd: ROOT,
    stdio: 'inherit',
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });
  
  child.on('close', (code) => process.exit(code || 0));
}

function runGateway() {
  const gatewayPath = join(ROOT, 'gateway');
  
  if (!existsSync(join(gatewayPath, 'node_modules'))) {
    console.log('\x1b[33mInstalling gateway dependencies...\x1b[0m');
    spawn.sync('npm', ['install'], { cwd: gatewayPath, stdio: 'inherit', shell: true });
  }
  
  const child = spawn('npm', ['run', 'dev'], {
    cwd: gatewayPath,
    stdio: 'inherit',
    shell: true
  });
  
  child.on('close', (code) => process.exit(code || 0));
}

function doctor() {
  console.log(BANNER);
  console.log('\x1b[33mChecking system requirements...\x1b[0m\n');
  
  // Python
  const hasPython = checkPython();
  console.log(`  ${hasPython ? '\x1b[32m✓\x1b[0m' : '\x1b[31m✗\x1b[0m'} Python 3.10+`);
  
  // Ollama
  try {
    const result = spawn.sync('ollama', ['--version'], { shell: true });
    const hasOllama = result.status === 0;
    console.log(`  ${hasOllama ? '\x1b[32m✓\x1b[0m' : '\x1b[31m✗\x1b[0m'} Ollama`);
  } catch {
    console.log('  \x1b[31m✗\x1b[0m Ollama');
  }
  
  // Node
  console.log('  \x1b[32m✓\x1b[0m Node.js ' + process.version);
  
  // Gateway
  const hasGateway = existsSync(join(ROOT, 'gateway', 'package.json'));
  console.log(`  ${hasGateway ? '\x1b[32m✓\x1b[0m' : '\x1b[31m✗\x1b[0m'} Gateway`);
  
  // UI
  const hasUI = existsSync(join(ROOT, 'ui', 'dist', 'index.html'));
  console.log(`  ${hasUI ? '\x1b[32m✓\x1b[0m' : '\x1b[33m○\x1b[0m'} UI (built)`);
  
  console.log('\n\x1b[90mRun "gltch" to start the agent\x1b[0m');
}

// Main
switch (command) {
  case 'chat':
  case '':
    runPython('gltch.py');
    break;
    
  case 'serve':
  case 'server':
  case 'gateway':
    console.log(BANNER);
    console.log('\x1b[33mStarting GLTCH gateway...\x1b[0m\n');
    runGateway();
    break;
    
  case 'web':
  case 'ui':
    console.log(BANNER);
    console.log('\x1b[33mOpening web UI...\x1b[0m');
    runGateway();
    break;
    
  case 'doctor':
  case 'check':
    doctor();
    break;
    
  case '--help':
  case '-h':
  case 'help':
    console.log(HELP);
    break;
    
  default:
    // Pass unknown commands to Python
    runPython('gltch.py', args);
}
