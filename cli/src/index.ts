#!/usr/bin/env node
/**
 * GLTCH CLI - Command-line toolkit
 * Manage gateway, channels, config, and more
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { config } from 'dotenv';

import { registerGatewayCommands } from './commands/gateway.js';
import { registerChannelsCommands } from './commands/channels.js';
import { registerConfigCommands } from './commands/config.js';
import { registerStatusCommands } from './commands/status.js';
import { registerDoctorCommands } from './commands/doctor.js';

// Load environment variables
config();

const program = new Command();

program
  .name('gltch')
  .description('GLTCH CLI - Command-line toolkit for managing GLTCH')
  .version('0.2.0');

// Add banner
program.hook('preAction', () => {
  console.log(chalk.red.bold(`
   ██████  ██      ████████  ██████ ██   ██ 
  ██       ██         ██    ██      ██   ██ 
  ██   ███ ██         ██    ██      ███████ 
  ██    ██ ██         ██    ██      ██   ██ 
   ██████  ███████    ██     ██████ ██   ██ 
  `));
});

// Register command groups
registerGatewayCommands(program);
registerChannelsCommands(program);
registerConfigCommands(program);
registerStatusCommands(program);
registerDoctorCommands(program);

// Default action - show help
program.action(() => {
  program.help();
});

program.parse();
