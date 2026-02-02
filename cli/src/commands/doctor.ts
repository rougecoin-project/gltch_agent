/**
 * GLTCH CLI - Doctor Commands
 * Diagnose and fix common issues
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { existsSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';
import { execSync } from 'child_process';

interface Check {
  name: string;
  check: () => Promise<{ ok: boolean; message: string; fix?: string }>;
}

const checks: Check[] = [
  {
    name: 'Node.js version',
    check: async () => {
      const version = process.version;
      const major = parseInt(version.slice(1).split('.')[0]);
      if (major >= 18) {
        return { ok: true, message: `${version}` };
      }
      return {
        ok: false,
        message: `${version} (requires 18+)`,
        fix: 'Update Node.js: https://nodejs.org/'
      };
    }
  },
  {
    name: 'Python version',
    check: async () => {
      try {
        const version = execSync('python --version 2>&1', { encoding: 'utf-8' }).trim();
        const match = version.match(/Python (\d+)\.(\d+)/);
        if (match && parseInt(match[1]) >= 3 && parseInt(match[2]) >= 10) {
          return { ok: true, message: version };
        }
        return {
          ok: false,
          message: `${version} (requires 3.10+)`,
          fix: 'Update Python: https://python.org/'
        };
      } catch {
        return {
          ok: false,
          message: 'Not found',
          fix: 'Install Python 3.10+: https://python.org/'
        };
      }
    }
  },
  {
    name: 'Ollama',
    check: async () => {
      try {
        const response = await fetch('http://localhost:11434/api/tags');
        if (response.ok) {
          const data = await response.json();
          const count = data.models?.length || 0;
          return { ok: true, message: `Running (${count} models)` };
        }
        return { ok: false, message: 'Not responding' };
      } catch {
        return {
          ok: false,
          message: 'Not running',
          fix: 'Start Ollama or install from: https://ollama.ai/'
        };
      }
    }
  },
  {
    name: 'Config directory',
    check: async () => {
      const dir = join(homedir(), '.gltch');
      if (existsSync(dir)) {
        return { ok: true, message: dir };
      }
      return {
        ok: true,
        message: `${dir} (will be created)`
      };
    }
  },
  {
    name: 'Gateway dependencies',
    check: async () => {
      const gatewayPkg = join(process.cwd(), 'gateway', 'node_modules');
      if (existsSync(gatewayPkg)) {
        return { ok: true, message: 'Installed' };
      }
      return {
        ok: false,
        message: 'Not installed',
        fix: 'Run: cd gateway && npm install'
      };
    }
  },
  {
    name: 'Agent dependencies',
    check: async () => {
      try {
        execSync('python -c "import rich; import psutil"', { encoding: 'utf-8' });
        return { ok: true, message: 'Installed' };
      } catch {
        return {
          ok: false,
          message: 'Missing packages',
          fix: 'Run: pip install -r requirements.txt'
        };
      }
    }
  },
  {
    name: 'Environment file',
    check: async () => {
      if (existsSync('.env')) {
        return { ok: true, message: 'Found' };
      }
      if (existsSync('.env.example')) {
        return {
          ok: false,
          message: 'Not found',
          fix: 'Copy .env.example to .env and configure'
        };
      }
      return { ok: true, message: 'Not required' };
    }
  }
];

export function registerDoctorCommands(program: Command): void {
  program
    .command('doctor')
    .description('Diagnose and fix common issues')
    .option('--fix', 'Attempt to fix issues')
    .action(async (options) => {
      console.log(chalk.bold('GLTCH Doctor\n'));
      console.log(chalk.dim('Checking system configuration...\n'));
      
      let hasErrors = false;
      
      for (const check of checks) {
        process.stdout.write(`  ${check.name}... `);
        
        try {
          const result = await check.check();
          
          if (result.ok) {
            console.log(chalk.green('✓') + ' ' + chalk.dim(result.message));
          } else {
            console.log(chalk.red('✗') + ' ' + chalk.yellow(result.message));
            if (result.fix) {
              console.log(chalk.dim(`    Fix: ${result.fix}`));
            }
            hasErrors = true;
          }
        } catch (error) {
          console.log(chalk.red('✗') + ' ' + chalk.dim('Error checking'));
          hasErrors = true;
        }
      }
      
      console.log('');
      
      if (hasErrors) {
        console.log(chalk.yellow('Some issues were found. Review the fixes above.'));
        process.exit(1);
      } else {
        console.log(chalk.green('All checks passed! GLTCH is ready.'));
      }
    });

  program
    .command('onboard')
    .description('Interactive setup wizard')
    .action(async () => {
      const p = await import('@clack/prompts');
      
      console.log('');
      p.intro(chalk.red.bold('GLTCH Setup Wizard'));
      
      // Check Ollama
      const ollamaOk = await (async () => {
        try {
          const response = await fetch('http://localhost:11434/api/tags');
          return response.ok;
        } catch {
          return false;
        }
      })();
      
      if (!ollamaOk) {
        p.note(
          'Ollama is not running.\n' +
          'GLTCH uses Ollama for local LLM inference.\n\n' +
          'Install from: https://ollama.ai/',
          'Ollama Required'
        );
        
        const continueAnyway = await p.confirm({
          message: 'Continue without Ollama?'
        });
        
        if (p.isCancel(continueAnyway) || !continueAnyway) {
          p.cancel('Setup cancelled');
          process.exit(0);
        }
      } else {
        p.log.success('Ollama is running');
      }
      
      // Configure channels
      const channels = await p.multiselect({
        message: 'Which channels do you want to set up?',
        options: [
          { value: 'discord', label: 'Discord' },
          { value: 'telegram', label: 'Telegram' },
          { value: 'webchat', label: 'WebChat (browser)', hint: 'recommended' }
        ],
        initialValues: ['webchat']
      });
      
      if (p.isCancel(channels)) {
        p.cancel('Setup cancelled');
        process.exit(0);
      }
      
      // Show next steps
      const steps = [
        '1. Start the agent: python gltch.py --rpc http',
        '2. Start the gateway: gltch gateway start',
        '3. Open http://localhost:18888 for WebChat'
      ];
      
      if ((channels as string[]).includes('discord')) {
        steps.push('4. Run: gltch channels login discord');
      }
      if ((channels as string[]).includes('telegram')) {
        steps.push('5. Run: gltch channels login telegram');
      }
      
      p.note(steps.join('\n'), 'Next Steps');
      
      p.outro(chalk.green('Setup complete! Run the commands above to start.'));
    });
}
