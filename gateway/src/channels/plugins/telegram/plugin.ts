/**
 * GLTCH Telegram Channel Plugin
 * Telegram bot integration using grammY
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

export interface TelegramConfig extends ChannelConfigBase {
  token: string;
  allowedUsers?: string[];
  allowedGroups?: string[];
  webhookUrl?: string;
  webhookSecret?: string;
}

// ============================================================================
// Telegram Plugin
// ============================================================================

// Placeholder types for grammy
type Bot = any;
type Context = any;

export class TelegramPlugin extends BaseChannelPlugin<TelegramConfig> {
  meta: ChannelMeta = {
    id: 'telegram',
    name: 'telegram',
    displayName: 'Telegram',
    deliveryMode: 'direct',
    chatTypes: ['direct', 'group'],
    capabilities: {
      reactions: true,
      media: true,
      typing: true,
      polls: true,
      mentions: true
    },
    version: '1.0.0',
    description: 'Telegram bot integration',
    icon: '✈️'
  };

  private bot: Bot | null = null;
  private ready: boolean = false;
  private configStore: InMemoryConfigStore<TelegramConfig>;
  private statusAdapter: BaseStatusAdapter;

  outbound: OutboundAdapter;
  normalize: NormalizeAdapter;

  constructor(initialConfig?: TelegramConfig) {
    super();

    this.configStore = new InMemoryConfigStore<TelegramConfig>();
    this.config = this.configStore;

    if (initialConfig) {
      this.configStore.setConfig('default', initialConfig);
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
      looksLikeTargetId: (input) => this.looksLikeTelegramId(input),
      normalizeTargetId: (input) => this.normalizeId(input),
      parseTargetId: (targetId) => this.parseId(targetId)
    };
  }

  protected async onInitialize(): Promise<void> {
    const accountIds = await this.config.listAccountIds();
    if (accountIds.length === 0) {
      console.log('ℹ Telegram: No accounts configured');
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
    if (this.bot) {
      await this.bot.stop();
      this.bot = null;
      this.ready = false;
    }
  }

  private async startBot(accountId: string, config: TelegramConfig): Promise<void> {
    try {
      const { Bot } = await import('grammy');

      this.bot = new Bot(config.token);

      // Handle all text messages
      this.bot.on('message:text', async (ctx: Context) => {
        await this.handleMessage(ctx, config);
      });

      // Handle errors
      this.bot.catch((error: any) => {
        console.error('Telegram error:', error);
        this.statusAdapter.setStatus(accountId, {
          id: accountId,
          status: 'error',
          enabled: true,
          error: error.message || 'Unknown error'
        });
      });

      // Start polling
      this.bot.start({
        onStart: (botInfo: any) => {
          console.log(`✓ Telegram connected as @${botInfo.username}`);
          this.ready = true;
          this.statusAdapter.setStatus(accountId, {
            id: accountId,
            status: 'connected',
            enabled: true,
            connectedAt: new Date(),
            metadata: { username: botInfo.username }
          });
        }
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to start Telegram:', errorMessage);
      this.statusAdapter.setStatus(accountId, {
        id: accountId,
        status: 'error',
        enabled: true,
        error: errorMessage
      });
      throw error;
    }
  }

  private async handleMessage(ctx: Context, config: TelegramConfig): Promise<void> {
    const message = ctx.message;
    const text = message.text?.trim();

    if (!text) return;

    // Check user allowlist if configured
    if (config.allowedUsers && config.allowedUsers.length > 0) {
      const username = message.from?.username;
      if (!username || !config.allowedUsers.includes(username)) {
        await ctx.reply('⚠ Unauthorized user');
        return;
      }
    }

    // Build session ID
    const chatId = message.chat.id;
    const isGroup = message.chat.type === 'group' || message.chat.type === 'supergroup';

    // Check group allowlist if configured
    if (isGroup && config.allowedGroups && config.allowedGroups.length > 0) {
      if (!config.allowedGroups.includes(String(chatId))) {
        return;
      }
    }

    const sessionId = isGroup
      ? this.buildSessionId('group', String(chatId))
      : this.buildSessionId('direct', String(message.from?.id || chatId));

    // In groups, only respond if mentioned or replied to
    if (isGroup) {
      const botUsername = (await this.bot?.api.getMe())?.username;
      const isMentioned = text.includes(`@${botUsername}`);
      const isReply = message.reply_to_message?.from?.is_bot;

      if (!isMentioned && !isReply) return;
    }

    const incoming: IncomingMessage = {
      text: text.replace(/@\w+/g, '').trim(),
      sessionId,
      channel: 'telegram',
      user: message.from?.username || String(message.from?.id),
      metadata: {
        chatId,
        userId: message.from?.id,
        isGroup,
        messageId: message.message_id
      }
    };

    try {
      // Show typing indicator
      await ctx.api.sendChatAction(chatId, 'typing');

      // Route to agent
      const result = await this.router!.route(incoming);

      // Send response
      await this.sendResponseToContext(ctx, result.response);
    } catch (error) {
      console.error('Telegram message handling error:', error);
      await ctx.reply('⚠ Error processing message');
    }
  }

  private async sendResponseToContext(ctx: Context, response: string): Promise<void> {
    const MAX_LENGTH = 4096;
    const chunks = this.chunkMessage(response, MAX_LENGTH - 50);

    for (const chunk of chunks) {
      try {
        await ctx.reply(chunk, { parse_mode: 'Markdown' });
      } catch {
        // Fallback without markdown if parsing fails
        await ctx.reply(chunk);
      }
    }
  }

  // ============================================================================
  // Outbound Methods
  // ============================================================================

  private async sendText(targetId: string, text: string): Promise<OutboundDeliveryResult> {
    if (!this.bot || !this.ready) {
      return this.createErrorResult('Telegram not connected');
    }

    try {
      const chatId = parseInt(targetId, 10);
      if (isNaN(chatId)) {
        return this.createErrorResult('Invalid chat ID');
      }

      const chunks = this.chunkMessage(text, 4096);
      let lastMessageId: number | undefined;

      for (const chunk of chunks) {
        const sent = await this.bot.api.sendMessage(chatId, chunk);
        lastMessageId = sent.message_id;
      }

      return this.createSuccessResult(String(lastMessageId));
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendMedia(targetId: string, media: any): Promise<OutboundDeliveryResult> {
    if (!this.bot || !this.ready) {
      return this.createErrorResult('Telegram not connected');
    }

    try {
      const chatId = parseInt(targetId, 10);
      if (isNaN(chatId)) {
        return this.createErrorResult('Invalid chat ID');
      }

      let sent: any;
      const source = media.buffer || media.url;

      switch (media.type) {
        case 'image':
          sent = await this.bot.api.sendPhoto(chatId, source, { caption: media.caption });
          break;
        case 'video':
          sent = await this.bot.api.sendVideo(chatId, source, { caption: media.caption });
          break;
        case 'audio':
          sent = await this.bot.api.sendAudio(chatId, source, { caption: media.caption });
          break;
        case 'document':
        default:
          sent = await this.bot.api.sendDocument(chatId, source, { caption: media.caption });
          break;
      }

      return this.createSuccessResult(String(sent.message_id));
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendReaction(messageId: string, emoji: string): Promise<OutboundDeliveryResult> {
    // Telegram reactions require chat ID + message ID
    return this.createErrorResult('Reactions require chat context');
  }

  // ============================================================================
  // Normalize Methods
  // ============================================================================

  private looksLikeTelegramId(input: string): boolean {
    // Telegram chat IDs are numeric (positive for users, negative for groups)
    // Or usernames: @username
    return /^(-?\d+|@\w{5,}|telegram:(direct|group):-?\d+)$/.test(input);
  }

  private normalizeId(input: string): string | null {
    // Extract numeric ID
    if (input.startsWith('@')) {
      return input; // Keep username format
    }
    const match = input.match(/(-?\d+)/);
    return match ? match[1] : null;
  }

  private parseId(targetId: string): { type: ChatType; id: string } | null {
    // Format: telegram:type:id
    const parts = targetId.split(':');
    if (parts.length >= 3 && parts[0] === 'telegram') {
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

  getBot(): Bot | null {
    return this.bot;
  }
}
