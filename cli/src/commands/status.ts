/**
 * GLTCH CLI - Status Commands
 * Check system and agent status
 */

import { Command } from 'commander';
import chalk from 'chalk';

export function registerStatusCommands(program: Command): void {
  program
    .command('status')
    .description('Show overall GLTCH status')
    .option('-a, --all', 'Show detailed status')
    .action(async (options) => {
      console.log(chalk.bold('GLTCH Status\n'));
      
      // Check gateway
      let gatewayStatus: any = null;
      try {
        const response = await fetch('http://127.0.0.1:18888/health');
        gatewayStatus = await response.json();
      } catch {
        // Gateway not running
      }
      
      // Gateway
      console.log(chalk.dim('Gateway:'));
      if (gatewayStatus) {
        console.log(`  Status:      ${chalk.green('● Running')}`);
        console.log(`  Connections: ${gatewayStatus.connections}`);
        console.log(`  Sessions:    ${gatewayStatus.sessions}`);
      } else {
        console.log(`  Status:      ${chalk.red('○ Not running')}`);
        console.log(chalk.dim('  Start with: gltch gateway start'));
      }
      console.log('');
      
      // Agent
      console.log(chalk.dim('Agent:'));
      if (gatewayStatus?.agent) {
        console.log(`  URL:       ${gatewayStatus.agent.url}`);
        console.log(`  Connected: ${gatewayStatus.agent.connected ? chalk.green('Yes') : chalk.red('No')}`);
      } else {
        // Try direct agent connection
        try {
          const response = await fetch('http://127.0.0.1:18890', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'ping', id: 1 })
          });
          if (response.ok) {
            console.log(`  Status: ${chalk.green('● Running')}`);
          }
        } catch {
          console.log(`  Status: ${chalk.red('○ Not running')}`);
          console.log(chalk.dim('  Start with: python gltch.py --rpc http'));
        }
      }
      console.log('');
      
      // Channels
      if (gatewayStatus?.channels) {
        console.log(chalk.dim('Channels:'));
        console.log(`  Discord:  ${gatewayStatus.channels.discord ? chalk.green('●') : chalk.dim('○')}`);
        console.log(`  Telegram: ${gatewayStatus.channels.telegram ? chalk.green('●') : chalk.dim('○')}`);
        console.log(`  WebChat:  ${gatewayStatus.channels.webchat ? chalk.green('●') : chalk.dim('○')}`);
        console.log('');
      }
      
      // Detailed status
      if (options.all && gatewayStatus?.agent?.connected) {
        try {
          const response = await fetch('http://127.0.0.1:18888/api/agent/rpc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'status', id: 1 })
          });
          const data = await response.json();
          
          if (data.result) {
            const agent = data.result;
            console.log(chalk.dim('Agent Details:'));
            console.log(`  Name:     ${chalk.bold(agent.agent_name)}`);
            console.log(`  Operator: ${agent.operator || chalk.dim('(not set)')}`);
            console.log(`  Mode:     ${agent.mode}`);
            console.log(`  Mood:     ${agent.mood}`);
            console.log(`  Rank:     ${chalk.magenta(agent.rank)}`);
            console.log(`  Level:    ${agent.level}`);
            console.log(`  Network:  ${agent.network_active ? chalk.green('ON') : chalk.dim('OFF')}`);
            console.log('');
          }
        } catch {
          // Ignore
        }
      }
    });

  program
    .command('ping')
    .description('Quick health check')
    .action(async () => {
      let ok = true;
      
      // Check gateway
      try {
        await fetch('http://127.0.0.1:18888/health');
        console.log(chalk.green('✓ Gateway'));
      } catch {
        console.log(chalk.red('✗ Gateway'));
        ok = false;
      }
      
      // Check agent
      try {
        const response = await fetch('http://127.0.0.1:18890', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ jsonrpc: '2.0', method: 'ping', id: 1 })
        });
        if (response.ok) {
          console.log(chalk.green('✓ Agent'));
        } else {
          throw new Error();
        }
      } catch {
        console.log(chalk.red('✗ Agent'));
        ok = false;
      }
      
      process.exit(ok ? 0 : 1);
    });
}
