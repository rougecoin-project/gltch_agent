/**
 * GLTCH CLI - Config Commands
 * Manage GLTCH configuration
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

const CONFIG_DIR = join(homedir(), '.gltch');
const CONFIG_FILE = join(CONFIG_DIR, 'config.json');

interface Config {
  [key: string]: any;
}

function loadConfig(): Config {
  try {
    if (existsSync(CONFIG_FILE)) {
      return JSON.parse(readFileSync(CONFIG_FILE, 'utf-8'));
    }
  } catch {
    // Ignore errors
  }
  return {};
}

function saveConfig(config: Config): void {
  const { mkdirSync } = require('fs');
  try {
    mkdirSync(CONFIG_DIR, { recursive: true });
    writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
  } catch (error) {
    console.error(chalk.red('Failed to save config:'), error);
  }
}

function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((acc, key) => acc?.[key], obj);
}

function setNestedValue(obj: any, path: string, value: any): void {
  const keys = path.split('.');
  const last = keys.pop()!;
  const target = keys.reduce((acc, key) => {
    if (!(key in acc)) acc[key] = {};
    return acc[key];
  }, obj);
  target[last] = value;
}

export function registerConfigCommands(program: Command): void {
  const config = program
    .command('config')
    .description('Manage configuration');

  config
    .command('get [key]')
    .description('Get a config value (or all if no key)')
    .action((key?: string) => {
      const cfg = loadConfig();
      
      if (key) {
        const value = getNestedValue(cfg, key);
        if (value === undefined) {
          console.log(chalk.yellow(`Key not found: ${key}`));
        } else {
          console.log(JSON.stringify(value, null, 2));
        }
      } else {
        console.log(JSON.stringify(cfg, null, 2));
      }
    });

  config
    .command('set <key> <value>')
    .description('Set a config value')
    .action((key: string, value: string) => {
      const cfg = loadConfig();
      
      // Try to parse as JSON, otherwise use as string
      let parsedValue: any;
      try {
        parsedValue = JSON.parse(value);
      } catch {
        parsedValue = value;
      }
      
      setNestedValue(cfg, key, parsedValue);
      saveConfig(cfg);
      
      console.log(chalk.green(`Set ${key} = ${JSON.stringify(parsedValue)}`));
    });

  config
    .command('unset <key>')
    .description('Remove a config value')
    .action((key: string) => {
      const cfg = loadConfig();
      const keys = key.split('.');
      const last = keys.pop()!;
      const parent = keys.reduce((acc, k) => acc?.[k], cfg);
      
      if (parent && last in parent) {
        delete parent[last];
        saveConfig(cfg);
        console.log(chalk.green(`Removed: ${key}`));
      } else {
        console.log(chalk.yellow(`Key not found: ${key}`));
      }
    });

  config
    .command('list')
    .description('List all config values')
    .action(() => {
      const cfg = loadConfig();
      
      if (Object.keys(cfg).length === 0) {
        console.log(chalk.dim('No configuration set.'));
        console.log(chalk.dim('Use: gltch config set <key> <value>'));
        return;
      }
      
      console.log(chalk.bold('Configuration'));
      console.log('');
      printConfig(cfg, '');
    });

  config
    .command('path')
    .description('Show config file path')
    .action(() => {
      console.log(CONFIG_FILE);
    });

  config
    .command('edit')
    .description('Open config file in editor')
    .action(() => {
      const editor = process.env.EDITOR || 'notepad';
      const { spawn } = require('child_process');
      
      // Ensure file exists
      if (!existsSync(CONFIG_FILE)) {
        saveConfig({});
      }
      
      spawn(editor, [CONFIG_FILE], { stdio: 'inherit' });
    });
}

function printConfig(obj: any, prefix: string): void {
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      console.log(chalk.cyan(`${fullKey}:`));
      printConfig(value, fullKey);
    } else {
      console.log(`  ${chalk.dim(fullKey)}: ${chalk.white(JSON.stringify(value))}`);
    }
  }
}
