/**
 * GLTCH Discord Channel Plugin
 * Discord bot integration using discord.js
 */

import type { 
  ChannelMeta, 
  ChannelConfigBase,
  OutboundAdapter,
  NormalizeAdapter,
  OutboundDeliveryResult,
  ChatType
} from '../types.js';
import { BaseChannelPlugin, InMemoryConfigStore, BaseStatusAdapter } from '../base.js';
import type { IncomingMessage } from '../../../routing/router.js';

// ============================================================================
// Config Types
// ============================================================================

export interface DiscordConfig extends ChannelConfigBase {
  token: string;
  prefix?: string;
  mentionRequired?: boolean;
  allowedGuilds?: string[];
}

// ============================================================================
// Discord Plugin
// ============================================================================

// Placeholder types for discord.js - will be replaced when dependency is available
type Client = any;
type Message = any;
type TextChannel = any;

export class DiscordPlugin extends BaseChannelPlugin<DiscordConfig> {
  meta: ChannelMeta = {
    id: 'discord',
    name: 'discord',
    displayName: 'Discord',
    deliveryMode: 'direct',
    chatTypes: ['direct', 'channel', 'thread'],
    capabilities: {
      reactions: true,
      threads: true,
      media: true,
      typing: true,
      mentions: true
    },
    version: '1.0.0',
    description: 'Discord bot integration',
    icon: '🎮'
  };

  private client: Client | null = null;
  private ready: boolean = false;
  private configStore: InMemoryConfigStore<DiscordConfig>;
  private statusAdapter: BaseStatusAdapter;

  outbound: OutboundAdapter;
  normalize: NormalizeAdapter;

  constructor(initialConfig?: DiscordConfig) {
    super();

    this.configStore = new InMemoryConfigStore<DiscordConfig>();
    this.config = this.configStore;
    
    if (initialConfig) {
      this.configStore.setConfig('default', {
        prefix: '!gltch',
        mentionRequired: false,
        ...initialConfig
      });
    }

    this.statusAdapter = new BaseStatusAdapter();
    this.status = this.statusAdapter;

    // Initialize outbound adapter
    this.outbound = {
      sendText: async (accountId, targetId, text) => this.sendText(targetId, text),
      sendMedia: async (accountId, targetId, media) => this.sendMedia(targetId, media),
      sendReaction: async (accountId, messageId, emoji) => this.sendReaction(messageId, emoji)
    };

    // Initialize normalize adapter
    this.normalize = {
      looksLikeTargetId: (input) => this.looksLikeDiscordId(input),
      normalizeTargetId: (input) => this.normalizeId(input),
      parseTargetId: (targetId) => this.parseId(targetId)
    };
  }

  protected async onInitialize(): Promise<void> {
    const accountIds = await this.config.listAccountIds();
    if (accountIds.length === 0) {
      console.log('ℹ Discord: No accounts configured');
      return;
    }

    for (const accountId of accountIds) {
      const config = await this.config.resolveAccount(accountId);
      if (config?.enabled && config.token) {
        await this.startBot(accountId, config);
      }
    }
  }

  protected async onShutdown(): Promise<void> {
    if (this.client) {
      await this.client.destroy();
      this.client = null;
      this.ready = false;
    }
  }

  private async startBot(accountId: string, config: DiscordConfig): Promise<void> {
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
        this.statusAdapter.setStatus(accountId, {
          id: accountId,
          status: 'connected',
          enabled: true,
          connectedAt: new Date(),
          metadata: { username: this.client.user?.tag }
        });
      });

      this.client.on('messageCreate', async (message: Message) => {
        await this.handleMessage(message, config);
      });

      this.client.on('error', (error: Error) => {
        console.error('Discord error:', error);
        this.statusAdapter.setStatus(accountId, {
          id: accountId,
          status: 'error',
          enabled: true,
          error: error.message
        });
      });

      await this.client.login(config.token);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to start Discord:', errorMessage);
      this.statusAdapter.setStatus(accountId, {
        id: accountId,
        status: 'error',
        enabled: true,
        error: errorMessage
      });
      throw error;
    }
  }

  private async handleMessage(message: Message, config: DiscordConfig): Promise<void> {
    // Ignore bots
    if (message.author.bot) return;

    const content = message.content.trim();
    const mentionedBot = message.mentions.has(this.client?.user);
    const hasPrefix = content.startsWith(config.prefix ?? '!gltch');

    // In DMs, always respond. In guilds, require mention or prefix
    const isDM = !message.guild;
    if (!isDM && !mentionedBot && !hasPrefix) return;

    // Check guild allowlist if configured
    if (config.allowedGuilds && config.allowedGuilds.length > 0 && message.guild) {
      if (!config.allowedGuilds.includes(message.guild.id)) {
        return;
      }
    }

    // Extract the actual message (remove prefix/mention)
    let text = content;
    if (hasPrefix) {
      text = content.slice((config.prefix ?? '!gltch').length).trim();
    }
    if (mentionedBot) {
      text = text.replace(/<@!?\d+>/g, '').trim();
    }

    if (!text) return;

    // Build session ID
    const sessionId = isDM
      ? this.buildSessionId('direct', message.author.id)
      : this.buildSessionId('channel', message.guild.id, message.channel.id);

    const incoming: IncomingMessage = {
      text,
      sessionId,
      channel: 'discord',
      user: `${message.author.username}#${message.author.discriminator}`,
      metadata: {
        guildId: message.guild?.id,
        channelId: message.channel.id,
        userId: message.author.id,
        messageId: message.id,
        isDM
      }
    };

    try {
      // Show typing indicator
      await message.channel.sendTyping();

      // Route to agent
      const result = await this.router!.route(incoming);

      // Send response
      await this.sendResponseToMessage(message, result.response);
    } catch (error) {
      console.error('Discord message handling error:', error);
      await message.reply('⚠ Error processing message');
    }
  }

  private async sendResponseToMessage(originalMessage: Message, response: string): Promise<void> {
    const MAX_LENGTH = 2000;
    const chunks = this.chunkMessage(response, MAX_LENGTH - 50);

    for (let i = 0; i < chunks.length; i++) {
      const prefix = chunks.length > 1 ? `[${i + 1}/${chunks.length}] ` : '';
      if (i === 0) {
        await originalMessage.reply(prefix + chunks[i]);
      } else {
        await originalMessage.channel.send(prefix + chunks[i]);
      }
    }
  }

  // ============================================================================
  // Outbound Methods
  // ============================================================================

  private async sendText(targetId: string, text: string): Promise<OutboundDeliveryResult> {
    if (!this.client || !this.ready) {
      return this.createErrorResult('Discord not connected');
    }

    try {
      const channel = await this.client.channels.fetch(targetId);
      if (!channel || !channel.isTextBased()) {
        return this.createErrorResult('Invalid channel');
      }

      const chunks = this.chunkMessage(text, 2000);
      let lastMessageId: string | undefined;

      for (const chunk of chunks) {
        const sent = await (channel as TextChannel).send(chunk);
        lastMessageId = sent.id;
      }

      return this.createSuccessResult(lastMessageId);
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendMedia(targetId: string, media: any): Promise<OutboundDeliveryResult> {
    if (!this.client || !this.ready) {
      return this.createErrorResult('Discord not connected');
    }

    try {
      const channel = await this.client.channels.fetch(targetId);
      if (!channel || !channel.isTextBased()) {
        return this.createErrorResult('Invalid channel');
      }

      const attachment: any = {
        files: [{
          attachment: media.buffer || media.url,
          name: media.filename || 'file'
        }]
      };

      if (media.caption) {
        attachment.content = media.caption;
      }

      const sent = await (channel as TextChannel).send(attachment);
      return this.createSuccessResult(sent.id);
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendReaction(messageId: string, emoji: string): Promise<OutboundDeliveryResult> {
    // Discord reactions require the channel, which we'd need to track
    // For now, return not implemented
    return this.createErrorResult('Reactions require message context');
  }

  // ============================================================================
  // Normalize Methods
  // ============================================================================

  private looksLikeDiscordId(input: string): boolean {
    // Discord IDs are snowflakes (numeric strings 17-19 digits)
    // Or channel mentions: <#123456789>
    // Or user mentions: <@123456789>
    return /^(\d{17,19}|<[#@!]\d{17,19}>|discord:[a-z]+:\d{17,19})$/i.test(input);
  }

  private normalizeId(input: string): string | null {
    // Extract numeric ID from various formats
    const match = input.match(/(\d{17,19})/);
    return match ? match[1] : null;
  }

  private parseId(targetId: string): { type: ChatType; id: string } | null {
    // Format: discord:type:id
    const parts = targetId.split(':');
    if (parts.length >= 3 && parts[0] === 'discord') {
      const type = parts[1] as ChatType;
      const id = parts.slice(2).join(':');
      return { type, id };
    }
    return null;
  }

  // ============================================================================
  // Status Methods
  // ============================================================================

  isReady(): boolean {
    return this.ready;
  }

  getClient(): Client | null {
    return this.client;
  }
}
