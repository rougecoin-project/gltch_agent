/**
 * GLTCH Telegram Channel
 * Telegram bot integration using grammY
 * 
 * Note: Requires additional dependency: grammy
 * npm install grammy
 */

import type { MessageRouter, IncomingMessage } from '../routing/router.js';

export interface TelegramConfig {
  token: string;
  allowedUsers?: string[]; // Optional whitelist of usernames
}

// Placeholder types - will be replaced when dependency is installed
type Bot = any;
type Context = any;

export class TelegramChannel {
  private bot: Bot | null = null;
  private router: MessageRouter;
  private config: TelegramConfig;
  private ready: boolean = false;

  constructor(router: MessageRouter, config: TelegramConfig) {
    this.router = router;
    this.config = config;
  }

  async start(): Promise<void> {
    try {
      const { Bot } = await import('grammy');

      this.bot = new Bot(this.config.token);

      // Handle all text messages
      this.bot.on('message:text', async (ctx: Context) => {
        await this.handleMessage(ctx);
      });

      // Handle errors
      this.bot.catch((error: any) => {
        console.error('Telegram error:', error);
      });

      // Start polling
      this.bot.start({
        onStart: (botInfo: any) => {
          console.log(`✓ Telegram connected as @${botInfo.username}`);
          this.ready = true;
        }
      });
    } catch (error) {
      console.error('Failed to start Telegram channel:', error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (this.bot) {
      await this.bot.stop();
      this.bot = null;
      this.ready = false;
    }
  }

  private async handleMessage(ctx: Context): Promise<void> {
    const message = ctx.message;
    const text = message.text?.trim();
    
    if (!text) return;

    // Optional: Check allowlist
    if (this.config.allowedUsers && this.config.allowedUsers.length > 0) {
      const username = message.from?.username;
      if (!username || !this.config.allowedUsers.includes(username)) {
        await ctx.reply('⚠ Unauthorized user');
        return;
      }
    }

    // Build session ID
    const chatId = message.chat.id;
    const isGroup = message.chat.type === 'group' || message.chat.type === 'supergroup';
    const sessionId = isGroup 
      ? `telegram:group:${chatId}`
      : `telegram:dm:${message.from?.id || chatId}`;

    // In groups, only respond if mentioned or replied to
    if (isGroup) {
      const botUsername = (await this.bot?.api.getMe())?.username;
      const isMentioned = text.includes(`@${botUsername}`);
      const isReply = message.reply_to_message?.from?.is_bot;
      
      if (!isMentioned && !isReply) return;
    }

    const incoming: IncomingMessage = {
      text: text.replace(/@\w+/g, '').trim(), // Remove mentions
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
      const result = await this.router.route(incoming);

      // Send response
      await this.sendResponse(ctx, result.response);
    } catch (error) {
      console.error('Telegram message handling error:', error);
      await ctx.reply('⚠ Error processing message');
    }
  }

  private async sendResponse(ctx: Context, response: string): Promise<void> {
    // Telegram has a 4096 character limit
    const MAX_LENGTH = 4096;

    if (response.length <= MAX_LENGTH) {
      await ctx.reply(response, { parse_mode: 'Markdown' }).catch(() => {
        // Fallback without markdown if parsing fails
        ctx.reply(response);
      });
    } else {
      // Split into chunks
      const chunks = this.chunkString(response, MAX_LENGTH - 50);
      for (const chunk of chunks) {
        await ctx.reply(chunk);
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
