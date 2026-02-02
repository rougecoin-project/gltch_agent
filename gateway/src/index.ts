#!/usr/bin/env node
/**
 * GLTCH Gateway - Main Entry Point
 * WebSocket hub for multi-channel messaging
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { config } from 'dotenv';

import { GatewayServer } from './server/gateway.js';
import { loadConfig } from './config/loader.js';

// Load environment variables
config();

const program = new Command();

program
  .name('gltch-gateway')
  .description('GLTCH Gateway - WebSocket hub for multi-channel messaging')
  .version('0.2.0');

program
  .command('start')
  .description('Start the gateway server')
  .option('-p, --port <port>', 'HTTP port', '18888')
  .option('-w, --ws-port <port>', 'WebSocket port', '18889')
  .option('-h, --host <host>', 'Host to bind to', '127.0.0.1')
  .option('--agent-url <url>', 'Agent RPC URL', 'http://127.0.0.1:18890')
  .action(async (options) => {
    console.log(chalk.red.bold(`
╔═══════════════════════════════════════════════════════════╗
║                    GLTCH GATEWAY                          ║
╚═══════════════════════════════════════════════════════════╝
    `));

    const config = loadConfig({
      port: parseInt(options.port),
      wsPort: parseInt(options.wsPort),
      host: options.host,
      agentUrl: options.agentUrl
    });

    console.log(chalk.cyan(`Starting gateway on ${config.host}:${config.port}`));
    console.log(chalk.cyan(`WebSocket on ${config.host}:${config.wsPort}`));
    console.log(chalk.cyan(`Agent RPC at ${config.agentUrl}`));
    console.log('');

    const gateway = new GatewayServer(config);
    await gateway.start();

    // Graceful shutdown
    process.on('SIGINT', async () => {
      console.log(chalk.yellow('\nShutting down...'));
      await gateway.stop();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      await gateway.stop();
      process.exit(0);
    });
  });

program
  .command('status')
  .description('Check gateway status')
  .option('-p, --port <port>', 'Gateway port', '18888')
  .option('-h, --host <host>', 'Gateway host', '127.0.0.1')
  .action(async (options) => {
    try {
      const url = `http://${options.host}:${options.port}/health`;
      const response = await fetch(url);
      const data = await response.json();
      
      console.log(chalk.green('Gateway Status:'));
      console.log(JSON.stringify(data, null, 2));
    } catch (error) {
      console.log(chalk.red('Gateway is not running or unreachable'));
      process.exit(1);
    }
  });

program.parse();
