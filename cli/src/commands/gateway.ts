/**
 * GLTCH CLI - Gateway Commands
 * Start, stop, and manage the gateway server
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { spawn, ChildProcess } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

let gatewayProcess: ChildProcess | null = null;

export function registerGatewayCommands(program: Command): void {
  const gateway = program
    .command('gateway')
    .description('Manage the gateway server');

  gateway
    .command('start')
    .description('Start the gateway server')
    .option('-p, --port <port>', 'HTTP port', '18888')
    .option('-w, --ws-port <port>', 'WebSocket port', '18889')
    .option('-h, --host <host>', 'Host to bind to', '127.0.0.1')
    .option('--agent-url <url>', 'Agent RPC URL', 'http://127.0.0.1:18890')
    .option('-d, --detach', 'Run in background')
    .action(async (options) => {
      console.log(chalk.cyan('Starting GLTCH Gateway...'));
      
      const gatewayPath = resolve(dirname(fileURLToPath(import.meta.url)), '../../../gateway');
      
      const args = [
        'start',
        '--port', options.port,
        '--ws-port', options.wsPort,
        '--host', options.host,
        '--agent-url', options.agentUrl
      ];

      if (options.detach) {
        // Run in background
        const child = spawn('npx', ['tsx', 'src/index.ts', ...args], {
          cwd: gatewayPath,
          detached: true,
          stdio: 'ignore'
        });
        child.unref();
        console.log(chalk.green(`Gateway started in background (PID: ${child.pid})`));
        console.log(chalk.dim(`HTTP:      http://${options.host}:${options.port}`));
        console.log(chalk.dim(`WebSocket: ws://${options.host}:${options.wsPort}`));
      } else {
        // Run in foreground
        gatewayProcess = spawn('npx', ['tsx', 'src/index.ts', ...args], {
          cwd: gatewayPath,
          stdio: 'inherit'
        });

        gatewayProcess.on('exit', (code) => {
          console.log(chalk.yellow(`Gateway exited with code ${code}`));
          process.exit(code || 0);
        });

        // Handle Ctrl+C
        process.on('SIGINT', () => {
          if (gatewayProcess) {
            gatewayProcess.kill('SIGINT');
          }
        });
      }
    });

  gateway
    .command('stop')
    .description('Stop the gateway server')
    .action(async () => {
      console.log(chalk.cyan('Stopping GLTCH Gateway...'));
      
      // Try to find and kill gateway process
      // This is a simple implementation - could be improved with PID file
      try {
        const response = await fetch('http://127.0.0.1:18888/health');
        if (response.ok) {
          console.log(chalk.yellow('Gateway is running. Use Ctrl+C if running in foreground.'));
          console.log(chalk.dim('For background processes, use: pkill -f "gltch-gateway"'));
        }
      } catch {
        console.log(chalk.green('Gateway is not running.'));
      }
    });

  gateway
    .command('status')
    .description('Check gateway status')
    .option('-p, --port <port>', 'Gateway port', '18888')
    .option('-h, --host <host>', 'Gateway host', '127.0.0.1')
    .action(async (options) => {
      try {
        const url = `http://${options.host}:${options.port}/health`;
        const response = await fetch(url);
        const data = await response.json();
        
        console.log(chalk.green('Gateway Status: ') + chalk.bold('RUNNING'));
        console.log('');
        console.log(chalk.dim('Version:     ') + data.version);
        console.log(chalk.dim('Uptime:      ') + Math.floor(data.uptime) + 's');
        console.log(chalk.dim('Connections: ') + data.connections);
        console.log(chalk.dim('Sessions:    ') + data.sessions);
        console.log('');
        console.log(chalk.dim('Agent:'));
        console.log(`  URL:       ${data.agent?.url}`);
        console.log(`  Connected: ${data.agent?.connected ? chalk.green('Yes') : chalk.red('No')}`);
        console.log('');
        console.log(chalk.dim('Channels:'));
        console.log(`  Discord:   ${data.channels?.discord ? chalk.green('Enabled') : chalk.dim('Disabled')}`);
        console.log(`  Telegram:  ${data.channels?.telegram ? chalk.green('Enabled') : chalk.dim('Disabled')}`);
        console.log(`  WebChat:   ${data.channels?.webchat ? chalk.green('Enabled') : chalk.dim('Disabled')}`);
      } catch {
        console.log(chalk.red('Gateway Status: ') + chalk.bold('NOT RUNNING'));
        console.log(chalk.dim('Start with: gltch gateway start'));
      }
    });

  gateway
    .command('logs')
    .description('Show gateway logs')
    .option('-f, --follow', 'Follow log output')
    .option('-n, --lines <n>', 'Number of lines', '50')
    .action(async (options) => {
      console.log(chalk.yellow('Gateway logs are output to stdout when running in foreground.'));
      console.log(chalk.dim('For background processes, check your system logs or redirect output.'));
    });
}
