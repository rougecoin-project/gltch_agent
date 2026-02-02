/**
 * GLTCH CLI - Channels Commands
 * Manage channel connections (Discord, Telegram, WebChat)
 */

import { Command } from 'commander';
import chalk from 'chalk';
import * as p from '@clack/prompts';

export function registerChannelsCommands(program: Command): void {
  const channels = program
    .command('channels')
    .description('Manage messaging channels');

  channels
    .command('status')
    .description('Check status of all channels')
    .action(async () => {
      try {
        const response = await fetch('http://127.0.0.1:18888/health');
        const data = await response.json();
        
        console.log(chalk.bold('Channel Status'));
        console.log('');
        
        // Discord
        const discordStatus = data.channels?.discord;
        console.log(
          chalk.blue('Discord:  ') + 
          (discordStatus ? chalk.green('● Connected') : chalk.dim('○ Not configured'))
        );
        
        // Telegram
        const telegramStatus = data.channels?.telegram;
        console.log(
          chalk.blue('Telegram: ') + 
          (telegramStatus ? chalk.green('● Connected') : chalk.dim('○ Not configured'))
        );
        
        // WebChat
        const webchatStatus = data.channels?.webchat;
        console.log(
          chalk.cyan('WebChat:  ') + 
          (webchatStatus ? chalk.green('● Enabled') : chalk.dim('○ Disabled'))
        );
        
      } catch {
        console.log(chalk.red('Cannot reach gateway. Is it running?'));
        console.log(chalk.dim('Start with: gltch gateway start'));
      }
    });

  channels
    .command('login <channel>')
    .description('Configure and connect a channel (discord, telegram)')
    .action(async (channel: string) => {
      const channelLower = channel.toLowerCase();
      
      if (channelLower === 'discord') {
        await configureDiscord();
      } else if (channelLower === 'telegram') {
        await configureTelegram();
      } else {
        console.log(chalk.red(`Unknown channel: ${channel}`));
        console.log(chalk.dim('Available channels: discord, telegram'));
      }
    });

  channels
    .command('logout <channel>')
    .description('Disconnect a channel')
    .action(async (channel: string) => {
      console.log(chalk.yellow(`To disconnect ${channel}, remove the token from your .env file and restart the gateway.`));
    });

  channels
    .command('test <channel>')
    .description('Send a test message through a channel')
    .option('-m, --message <msg>', 'Test message', 'Hello from GLTCH!')
    .action(async (channel: string, options) => {
      console.log(chalk.cyan(`Sending test message via ${channel}...`));
      console.log(chalk.dim('(This would send a test message through the channel)'));
    });
}

async function configureDiscord(): Promise<void> {
  console.log(chalk.bold.blue('\nDiscord Bot Setup\n'));
  console.log(chalk.dim('To create a Discord bot:'));
  console.log(chalk.dim('1. Go to https://discord.com/developers/applications'));
  console.log(chalk.dim('2. Create a new application'));
  console.log(chalk.dim('3. Go to Bot section and create a bot'));
  console.log(chalk.dim('4. Copy the bot token'));
  console.log(chalk.dim('5. Enable MESSAGE CONTENT INTENT'));
  console.log('');

  const token = await p.text({
    message: 'Enter your Discord bot token:',
    placeholder: 'paste token here',
    validate: (value) => {
      if (!value) return 'Token is required';
      if (value.length < 50) return 'Token seems too short';
    }
  });

  if (p.isCancel(token)) {
    console.log(chalk.yellow('Cancelled'));
    return;
  }

  console.log('');
  console.log(chalk.green('Token received!'));
  console.log(chalk.dim('Add this to your .env file:'));
  console.log('');
  console.log(chalk.cyan(`DISCORD_BOT_TOKEN=${token}`));
  console.log('');
  console.log(chalk.dim('Then restart the gateway.'));
  
  // Generate invite link
  console.log('');
  console.log(chalk.dim('Invite your bot to a server:'));
  console.log(chalk.dim('Go to OAuth2 > URL Generator, select bot scope, and these permissions:'));
  console.log(chalk.dim('- Read Messages/View Channels'));
  console.log(chalk.dim('- Send Messages'));
  console.log(chalk.dim('- Read Message History'));
}

async function configureTelegram(): Promise<void> {
  console.log(chalk.bold.blue('\nTelegram Bot Setup\n'));
  console.log(chalk.dim('To create a Telegram bot:'));
  console.log(chalk.dim('1. Message @BotFather on Telegram'));
  console.log(chalk.dim('2. Send /newbot'));
  console.log(chalk.dim('3. Follow the prompts'));
  console.log(chalk.dim('4. Copy the HTTP API token'));
  console.log('');

  const token = await p.text({
    message: 'Enter your Telegram bot token:',
    placeholder: '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',
    validate: (value) => {
      if (!value) return 'Token is required';
      if (!value.includes(':')) return 'Token should be in format 123456789:ABC...';
    }
  });

  if (p.isCancel(token)) {
    console.log(chalk.yellow('Cancelled'));
    return;
  }

  console.log('');
  console.log(chalk.green('Token received!'));
  console.log(chalk.dim('Add this to your .env file:'));
  console.log('');
  console.log(chalk.cyan(`TELEGRAM_BOT_TOKEN=${token}`));
  console.log('');
  console.log(chalk.dim('Then restart the gateway.'));
  console.log('');
  console.log(chalk.dim('Message your bot on Telegram to start chatting!'));
}
