/**
 * GLTCH Slack Channel Plugin
 * Slack bot integration using @slack/bolt
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

export interface SlackConfig extends ChannelConfigBase {
  botToken: string;
  appToken: string;
  signingSecret?: string;
  allowedChannels?: string[];
  allowedUsers?: string[];
  replyInThread?: boolean;
}

// ============================================================================
// Slack Plugin
// ============================================================================

// Placeholder types for @slack/bolt
type App = any;
type SlackMessage = any;
type SayFn = any;

export class SlackPlugin extends BaseChannelPlugin<SlackConfig> {
  meta: ChannelMeta = {
    id: 'slack',
    name: 'slack',
    displayName: 'Slack',
    deliveryMode: 'direct',
    chatTypes: ['direct', 'channel', 'thread'],
    capabilities: {
      reactions: true,
      threads: true,
      media: true,
      typing: true,
      mentions: true,
      native_commands: true
    },
    version: '1.0.0',
    description: 'Slack bot integration',
    icon: '💼'
  };

  private app: App | null = null;
  private ready: boolean = false;
  private configStore: InMemoryConfigStore<SlackConfig>;
  private statusAdapter: BaseStatusAdapter;

  outbound: OutboundAdapter;
  normalize: NormalizeAdapter;

  constructor(initialConfig?: SlackConfig) {
    super();

    this.configStore = new InMemoryConfigStore<SlackConfig>();
    this.config = this.configStore;

    if (initialConfig) {
      this.configStore.setConfig('default', {
        replyInThread: true,
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
      looksLikeTargetId: (input) => this.looksLikeSlackId(input),
      normalizeTargetId: (input) => this.normalizeId(input),
      parseTargetId: (targetId) => this.parseId(targetId)
    };
  }

  protected async onInitialize(): Promise<void> {
    const accountIds = await this.config.listAccountIds();
    if (accountIds.length === 0) {
      console.log('ℹ Slack: No accounts configured');
      return;
    }

    for (const accountId of accountIds) {
      const config = await this.config.resolveAccount(accountId);
      if (config?.enabled && config.botToken && config.appToken) {
        await this.startApp(accountId, config);
      }
    }
  }

  protected async onShutdown(): Promise<void> {
    if (this.app) {
      await this.app.stop();
      this.app = null;
      this.ready = false;
    }
  }

  private async startApp(accountId: string, config: SlackConfig): Promise<void> {
    try {
      const { App } = await import('@slack/bolt');

      this.app = new App({
        token: config.botToken,
        appToken: config.appToken,
        socketMode: true,
        signingSecret: config.signingSecret || 'dummy-secret'
      });

      // Handle mentions
      this.app.event('app_mention', async ({ event, say }: { event: any; say: SayFn }) => {
        await this.handleMessage(event, say, config, true);
      });

      // Handle direct messages
      this.app.event('message', async ({ event, say }: { event: SlackMessage; say: SayFn }) => {
        // Skip bot messages and edited messages
        if (event.bot_id || event.subtype) return;
        
        // Only handle DMs (channel type 'im')
        if (event.channel_type === 'im') {
          await this.handleMessage(event, say, config, false);
        }
      });

      // Start the app
      await this.app.start();
      
      console.log('✓ Slack connected');
      this.ready = true;
      this.statusAdapter.setStatus(accountId, {
        id: accountId,
        status: 'connected',
        enabled: true,
        connectedAt: new Date()
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to start Slack:', errorMessage);
      this.statusAdapter.setStatus(accountId, {
        id: accountId,
        status: 'error',
        enabled: true,
        error: errorMessage
      });
      throw error;
    }
  }

  private async handleMessage(
    event: SlackMessage, 
    say: SayFn, 
    config: SlackConfig,
    isMention: boolean
  ): Promise<void> {
    const text = event.text?.replace(/<@[A-Z0-9]+>/g, '').trim();
    if (!text) return;

    // Check user allowlist if configured
    if (config.allowedUsers && config.allowedUsers.length > 0) {
      if (!config.allowedUsers.includes(event.user)) {
        return;
      }
    }

    // Check channel allowlist if configured
    if (config.allowedChannels && config.allowedChannels.length > 0) {
      if (!config.allowedChannels.includes(event.channel)) {
        return;
      }
    }

    // Build session ID
    const isThread = !!event.thread_ts;
    const isDM = event.channel_type === 'im';
    
    let chatType: ChatType = 'channel';
    if (isDM) chatType = 'direct';
    else if (isThread) chatType = 'thread';

    const sessionId = this.buildSessionId(
      chatType, 
      event.channel, 
      isThread ? event.thread_ts : undefined
    );

    const incoming: IncomingMessage = {
      text,
      sessionId,
      channel: 'slack',
      user: event.user,
      metadata: {
        channelId: event.channel,
        userId: event.user,
        threadTs: event.thread_ts,
        messageTs: event.ts,
        isDM,
        isThread,
        isMention
      }
    };

    try {
      // Route to agent
      const result = await this.router!.route(incoming);

      // Send response (in thread if configured or if already in thread)
      const threadTs = config.replyInThread 
        ? (event.thread_ts || event.ts)
        : event.thread_ts;

      await say({
        text: result.response,
        thread_ts: threadTs
      });
    } catch (error) {
      console.error('Slack message handling error:', error);
      await say({
        text: '⚠ Error processing message',
        thread_ts: event.thread_ts || event.ts
      });
    }
  }

  // ============================================================================
  // Outbound Methods
  // ============================================================================

  private async sendText(targetId: string, text: string): Promise<OutboundDeliveryResult> {
    if (!this.app || !this.ready) {
      return this.createErrorResult('Slack not connected');
    }

    try {
      const parsed = this.parseId(targetId);
      if (!parsed) {
        return this.createErrorResult('Invalid target ID');
      }

      const chunks = this.chunkMessage(text, 4000);
      let lastTs: string | undefined;

      for (const chunk of chunks) {
        const result = await this.app.client.chat.postMessage({
          channel: parsed.id,
          text: chunk
        });
        lastTs = result.ts;
      }

      return this.createSuccessResult(lastTs);
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendMedia(targetId: string, media: any): Promise<OutboundDeliveryResult> {
    if (!this.app || !this.ready) {
      return this.createErrorResult('Slack not connected');
    }

    try {
      const parsed = this.parseId(targetId);
      if (!parsed) {
        return this.createErrorResult('Invalid target ID');
      }

      const result = await this.app.client.files.uploadV2({
        channel_id: parsed.id,
        file: media.buffer || media.url,
        filename: media.filename || 'file',
        title: media.caption
      });

      return this.createSuccessResult(result.file?.id);
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendReaction(messageId: string, emoji: string): Promise<OutboundDeliveryResult> {
    if (!this.app || !this.ready) {
      return this.createErrorResult('Slack not connected');
    }

    try {
      // messageId format: channel:timestamp
      const [channel, timestamp] = messageId.split(':');
      if (!channel || !timestamp) {
        return this.createErrorResult('Invalid message ID format (expected channel:timestamp)');
      }

      await this.app.client.reactions.add({
        channel,
        timestamp,
        name: emoji.replace(/:/g, '')
      });

      return this.createSuccessResult();
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Reaction failed');
    }
  }

  // ============================================================================
  // Normalize Methods
  // ============================================================================

  private looksLikeSlackId(input: string): boolean {
    // Slack channel IDs start with C, D (DM), or G (group)
    // User IDs start with U or W
    return /^([CDGUW][A-Z0-9]{8,}|slack:(direct|channel|thread):[CDGUW][A-Z0-9]{8,})$/i.test(input);
  }

  private normalizeId(input: string): string | null {
    const match = input.match(/([CDGUW][A-Z0-9]{8,})/i);
    return match ? match[1].toUpperCase() : null;
  }

  private parseId(targetId: string): { type: ChatType; id: string } | null {
    // Format: slack:type:id or just the ID
    const parts = targetId.split(':');
    if (parts.length >= 3 && parts[0] === 'slack') {
      return { type: parts[1] as ChatType, id: parts.slice(2).join(':') };
    }
    
    // Try to infer type from ID prefix
    const id = this.normalizeId(targetId);
    if (!id) return null;

    let type: ChatType = 'channel';
    if (id.startsWith('D')) type = 'direct';
    else if (id.startsWith('G')) type = 'group' as ChatType;

    return { type, id };
  }

  // ============================================================================
  // Status Methods
  // ============================================================================

  isReady(): boolean {
    return this.ready;
  }

  getApp(): App | null {
    return this.app;
  }
}
