#!/usr/bin/env node

import { spawn } from 'child_process';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

console.log('\n\x1b[35m⚡ GLTCH postinstall\x1b[0m\n');

// Check Python
function getPythonCmd() {
  try {
    const result = spawn.sync('python', ['--version']);
    if (result.status === 0) return 'python';
  } catch {}
  try {
    const result = spawn.sync('python3', ['--version']);
    if (result.status === 0) return 'python3';
  } catch {}
  return null;
}

const python = getPythonCmd();

if (!python) {
  console.log('\x1b[33m⚠ Python not found. Please install Python 3.10+\x1b[0m');
  console.log('  https://www.python.org/downloads/\n');
  process.exit(0); // Don't fail install
}

console.log(`\x1b[32m✓\x1b[0m Python found: ${python}`);

// Install Python dependencies
const requirementsPath = join(ROOT, 'requirements.txt');

if (existsSync(requirementsPath)) {
  console.log('\x1b[90mInstalling Python dependencies...\x1b[0m');
  
  const result = spawn.sync(python, ['-m', 'pip', 'install', '-r', requirementsPath, '-q'], {
    cwd: ROOT,
    stdio: 'inherit'
  });
  
  if (result.status === 0) {
    console.log('\x1b[32m✓\x1b[0m Python dependencies installed');
  } else {
    console.log('\x1b[33m⚠ Some Python dependencies may have failed\x1b[0m');
  }
}

// Check for Ollama
try {
  const result = spawn.sync('ollama', ['--version'], { shell: true });
  if (result.status === 0) {
    console.log('\x1b[32m✓\x1b[0m Ollama detected');
  } else {
    throw new Error();
  }
} catch {
  console.log('\x1b[33m⚠\x1b[0m Ollama not found - install from https://ollama.ai');
}

console.log('\n\x1b[35m✨ GLTCH ready! Run "gltch" to start\x1b[0m\n');
