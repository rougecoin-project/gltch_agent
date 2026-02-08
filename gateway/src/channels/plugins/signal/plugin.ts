/**
 * GLTCH Signal Channel Plugin
 * Signal integration using signal-cli REST API
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

export interface SignalConfig extends ChannelConfigBase {
  /** signal-cli REST API base URL */
  apiUrl: string;
  /** Registered phone number (E.164 format) */
  number: string;
  /** Allowed sender numbers */
  allowedNumbers?: string[];
  /** Allowed group IDs */
  allowedGroups?: string[];
}

// ============================================================================
// Signal Plugin
// ============================================================================

interface SignalMessage {
  envelope: {
    source: string;
    sourceNumber: string;
    sourceDevice: number;
    timestamp: number;
    dataMessage?: {
      timestamp: number;
      message: string;
      groupInfo?: {
        groupId: string;
        type: string;
      };
    };
  };
}

export class SignalPlugin extends BaseChannelPlugin<SignalConfig> {
  meta: ChannelMeta = {
    id: 'signal',
    name: 'signal',
    displayName: 'Signal',
    deliveryMode: 'direct',
    chatTypes: ['direct', 'group'],
    capabilities: {
      reactions: true,
      media: true,
      read_receipts: true
    },
    version: '1.0.0',
    description: 'Signal messaging via signal-cli',
    icon: '🔒'
  };

  private ready: boolean = false;
  private eventSource: any = null;
  private configStore: InMemoryConfigStore<SignalConfig>;
  private statusAdapter: BaseStatusAdapter;

  outbound: OutboundAdapter;
  normalize: NormalizeAdapter;

  constructor(initialConfig?: SignalConfig) {
    super();

    this.configStore = new InMemoryConfigStore<SignalConfig>();
    this.config = this.configStore;

    if (initialConfig) {
      this.configStore.setConfig('default', initialConfig);
    }

    this.statusAdapter = new BaseStatusAdapter();
    this.status = this.statusAdapter;

    // Initialize outbound adapter
    this.outbound = {
      sendText: async (accountId, targetId, text) => this.sendText(accountId, targetId, text),
      sendMedia: async (accountId, targetId, media) => this.sendMedia(accountId, targetId, media),
      sendReaction: async (accountId, messageId, emoji) => this.sendReaction(accountId, messageId, emoji)
    };

    // Initialize normalize adapter
    this.normalize = {
      looksLikeTargetId: (input) => this.looksLikeSignalId(input),
      normalizeTargetId: (input) => this.normalizeId(input),
      parseTargetId: (targetId) => this.parseId(targetId)
    };
  }

  protected async onInitialize(): Promise<void> {
    const accountIds = await this.config.listAccountIds();
    if (accountIds.length === 0) {
      console.log('ℹ Signal: No accounts configured');
      return;
    }

    for (const accountId of accountIds) {
      const config = await this.config.resolveAccount(accountId);
      if (config?.enabled && config.apiUrl && config.number) {
        await this.startMonitor(accountId, config);
      }
    }
  }

  protected async onShutdown(): Promise<void> {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.ready = false;
    }
  }

  private async startMonitor(accountId: string, config: SignalConfig): Promise<void> {
    try {
      // Verify API is reachable
      const response = await fetch(`${config.apiUrl}/v1/about`);
      if (!response.ok) {
        throw new Error(`Signal API not reachable: ${response.status}`);
      }

      // Start SSE connection for receiving messages
      const receiveUrl = `${config.apiUrl}/v1/receive/${encodeURIComponent(config.number)}`;
      
      // Use native EventSource or polyfill
      const EventSource = globalThis.EventSource || (await import('eventsource')).default;
      this.eventSource = new EventSource(receiveUrl);

      this.eventSource.onopen = () => {
        console.log('✓ Signal connected');
        this.ready = true;
        this.statusAdapter.setStatus(accountId, {
          id: accountId,
          status: 'connected',
          enabled: true,
          connectedAt: new Date(),
          metadata: { number: config.number }
        });
      };

      this.eventSource.onmessage = async (event: MessageEvent) => {
        try {
          const data: SignalMessage = JSON.parse(event.data);
          await this.handleMessage(accountId, data, config);
        } catch (error) {
          console.error('Signal message parse error:', error);
        }
      };

      this.eventSource.onerror = (error: any) => {
        console.error('Signal SSE error:', error);
        this.ready = false;
        this.statusAdapter.setStatus(accountId, {
          id: accountId,
          status: 'error',
          enabled: true,
          error: 'SSE connection error'
        });

        // Reconnect after delay
        setTimeout(() => {
          if (this.eventSource) {
            this.startMonitor(accountId, config);
          }
        }, 5000);
      };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to start Signal:', errorMessage);
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
    accountId: string, 
    data: SignalMessage, 
    config: SignalConfig
  ): Promise<void> {
    const { envelope } = data;
    if (!envelope.dataMessage?.message) return;

    const text = envelope.dataMessage.message;
    const sender = envelope.sourceNumber;
    const isGroup = !!envelope.dataMessage.groupInfo;
    const groupId = envelope.dataMessage.groupInfo?.groupId;

    // Check allowlists
    if (!isGroup && config.allowedNumbers && config.allowedNumbers.length > 0) {
      if (!config.allowedNumbers.includes(sender)) {
        return;
      }
    }

    if (isGroup && config.allowedGroups && config.allowedGroups.length > 0) {
      if (!groupId || !config.allowedGroups.includes(groupId)) {
        return;
      }
    }

    const sessionId = this.buildSessionId(
      isGroup ? 'group' : 'direct',
      isGroup ? groupId! : sender
    );

    const incoming: IncomingMessage = {
      text,
      sessionId,
      channel: 'signal',
      user: sender,
      metadata: {
        sender,
        timestamp: envelope.timestamp,
        isGroup,
        groupId,
        sourceDevice: envelope.sourceDevice
      }
    };

    try {
      // Route to agent
      const result = await this.router!.route(incoming);

      // Send response
      await this.sendText(accountId, isGroup ? groupId! : sender, result.response);
    } catch (error) {
      console.error('Signal message handling error:', error);
    }
  }

  // ============================================================================
  // Outbound Methods
  // ============================================================================

  private async sendText(
    accountId: string, 
    targetId: string, 
    text: string
  ): Promise<OutboundDeliveryResult> {
    const config = await this.config.resolveAccount(accountId);
    if (!config || !this.ready) {
      return this.createErrorResult('Signal not connected');
    }

    try {
      const parsed = this.parseId(targetId);
      const isGroup = parsed?.type === 'group';
      const recipient = parsed?.id || targetId;

      const endpoint = `${config.apiUrl}/v2/send`;
      const body: any = {
        number: config.number,
        message: text
      };

      if (isGroup) {
        body.recipients = [recipient];
      } else {
        body.recipients = [recipient];
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const error = await response.text();
        return this.createErrorResult(`Send failed: ${error}`);
      }

      const result = await response.json();
      return this.createSuccessResult(result.timestamp?.toString());
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendMedia(
    accountId: string, 
    targetId: string, 
    media: any
  ): Promise<OutboundDeliveryResult> {
    const config = await this.config.resolveAccount(accountId);
    if (!config || !this.ready) {
      return this.createErrorResult('Signal not connected');
    }

    try {
      const parsed = this.parseId(targetId);
      const recipient = parsed?.id || targetId;

      // Signal-cli expects base64 encoded attachments
      const attachment = media.buffer 
        ? media.buffer.toString('base64')
        : null;

      if (!attachment && !media.url) {
        return this.createErrorResult('Media buffer or URL required');
      }

      const endpoint = `${config.apiUrl}/v2/send`;
      const body: any = {
        number: config.number,
        recipients: [recipient],
        message: media.caption || '',
        base64_attachments: attachment ? [attachment] : undefined
      };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const error = await response.text();
        return this.createErrorResult(`Send failed: ${error}`);
      }

      const result = await response.json();
      return this.createSuccessResult(result.timestamp?.toString());
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendReaction(
    accountId: string,
    messageId: string, 
    emoji: string
  ): Promise<OutboundDeliveryResult> {
    const config = await this.config.resolveAccount(accountId);
    if (!config || !this.ready) {
      return this.createErrorResult('Signal not connected');
    }

    try {
      // messageId format: recipient:timestamp
      const [recipient, timestamp] = messageId.split(':');
      if (!recipient || !timestamp) {
        return this.createErrorResult('Invalid message ID format');
      }

      const endpoint = `${config.apiUrl}/v1/reactions/${encodeURIComponent(config.number)}`;
      const body = {
        recipient,
        reaction: emoji,
        target_author: recipient,
        target_sent_timestamp: parseInt(timestamp)
      };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const error = await response.text();
        return this.createErrorResult(`Reaction failed: ${error}`);
      }

      return this.createSuccessResult();
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Reaction failed');
    }
  }

  // ============================================================================
  // Normalize Methods
  // ============================================================================

  private looksLikeSignalId(input: string): boolean {
    // E.164 phone numbers or group IDs (base64)
    return /^(\+\d{10,15}|[A-Za-z0-9+/=]{20,}|signal:(direct|group):.+)$/.test(input);
  }

  private normalizeId(input: string): string | null {
    // Extract phone number or group ID
    if (input.startsWith('+')) {
      return input;
    }
    const match = input.match(/(\+\d{10,15})/);
    return match ? match[1] : input;
  }

  private parseId(targetId: string): { type: ChatType; id: string } | null {
    // Format: signal:type:id
    const parts = targetId.split(':');
    if (parts.length >= 3 && parts[0] === 'signal') {
      return { type: parts[1] as ChatType, id: parts.slice(2).join(':') };
    }

    // Infer type: phone numbers are direct, base64 strings are groups
    if (targetId.startsWith('+')) {
      return { type: 'direct', id: targetId };
    }
    
    // Assume base64-like strings are group IDs
    if (/^[A-Za-z0-9+/=]{20,}$/.test(targetId)) {
      return { type: 'group', id: targetId };
    }

    return { type: 'direct', id: targetId };
  }

  // ============================================================================
  // Status Methods
  // ============================================================================

  isReady(): boolean {
    return this.ready;
  }
}
