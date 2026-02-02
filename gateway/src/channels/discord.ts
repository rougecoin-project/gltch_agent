/**
 * GLTCH Discord Channel
 * Discord bot integration using discord.js
 * 
 * Note: Requires additional dependency: discord.js
 * npm install discord.js
 */

import type { MessageRouter, IncomingMessage } from '../routing/router.js';

export interface DiscordConfig {
  token: string;
  prefix?: string;
  mentionRequired?: boolean;
}

// Placeholder for discord.js types - will be replaced when dependency is installed
type Client = any;
type Message = any;

export class DiscordChannel {
  private client: Client | null = null;
  private router: MessageRouter;
  private config: DiscordConfig;
  private ready: boolean = false;

  constructor(router: MessageRouter, config: DiscordConfig) {
    this.router = router;
    this.config = {
      prefix: '!gltch',
      mentionRequired: false,
      ...config
    };
  }

  async start(): Promise<void> {
    // Dynamic import to avoid requiring discord.js if not used
    try {
      const { Client, GatewayIntentBits, Partials } = await import('discord.js');

      this.client = new Client({
        intents: [
          GatewayIntentBits.Guilds,
          GatewayIntentBits.GuildMessages,
          GatewayIntentBits.DirectMessages,
          GatewayIntentBits.MessageContent
        ],
        partials: [Partials.Channel, Partials.Message]
      });

      this.client.on('ready', () => {
        console.log(`✓ Discord connected as ${this.client.user?.tag}`);
        this.ready = true;
      });

      this.client.on('messageCreate', (message: Message) => {
        this.handleMessage(message);
      });

      await this.client.login(this.config.token);
    } catch (error) {
      console.error('Failed to start Discord channel:', error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (this.client) {
      await this.client.destroy();
      this.client = null;
      this.ready = false;
    }
  }

  private async handleMessage(message: Message): Promise<void> {
    // Ignore bots
    if (message.author.bot) return;

    // Check if we should respond
    const content = message.content.trim();
    const mentionedBot = message.mentions.has(this.client?.user);
    const hasPrefix = content.startsWith(this.config.prefix!);

    // In DMs, always respond. In guilds, require mention or prefix
    const isDM = !message.guild;
    if (!isDM && !mentionedBot && !hasPrefix) return;

    // Extract the actual message (remove prefix/mention)
    let text = content;
    if (hasPrefix) {
      text = content.slice(this.config.prefix!.length).trim();
    }
    if (mentionedBot) {
      text = text.replace(/<@!?\d+>/g, '').trim();
    }

    if (!text) return;

    // Build session ID
    const sessionId = isDM 
      ? `discord:dm:${message.author.id}`
      : `discord:${message.guild.id}:${message.channel.id}`;

    const incoming: IncomingMessage = {
      text,
      sessionId,
      channel: 'discord',
      user: `${message.author.username}#${message.author.discriminator}`,
      metadata: {
        guildId: message.guild?.id,
        channelId: message.channel.id,
        userId: message.author.id,
        isDM
      }
    };

    try {
      // Show typing indicator
      await message.channel.sendTyping();

      // Route to agent
      const result = await this.router.route(incoming);

      // Send response
      await this.sendResponse(message, result.response);
    } catch (error) {
      console.error('Discord message handling error:', error);
      await message.reply('⚠ Error processing message');
    }
  }

  private async sendResponse(originalMessage: Message, response: string): Promise<void> {
    // Discord has a 2000 character limit
    const MAX_LENGTH = 2000;

    if (response.length <= MAX_LENGTH) {
      await originalMessage.reply(response);
    } else {
      // Split into chunks
      const chunks = this.chunkString(response, MAX_LENGTH - 50);
      for (let i = 0; i < chunks.length; i++) {
        const prefix = chunks.length > 1 ? `[${i + 1}/${chunks.length}] ` : '';
        if (i === 0) {
          await originalMessage.reply(prefix + chunks[i]);
        } else {
          await originalMessage.channel.send(prefix + chunks[i]);
        }
      }
    }
  }

  private chunkString(str: string, size: number): string[] {
    const chunks: string[] = [];
    let i = 0;
    while (i < str.length) {
      chunks.push(str.slice(i, i + size));
      i += size;
    }
    return chunks;
  }

  isReady(): boolean {
    return this.ready;
  }
}
