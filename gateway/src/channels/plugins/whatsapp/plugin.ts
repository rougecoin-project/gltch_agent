/**
 * GLTCH WhatsApp Channel Plugin
 * WhatsApp integration using @whiskeysockets/baileys
 */

import type {
  ChannelMeta,
  ChannelConfigBase,
  OutboundAdapter,
  NormalizeAdapter,
  GatewayAdapter,
  OutboundDeliveryResult,
  AccountSnapshot,
  ChatType
} from '../types.js';
import { BaseChannelPlugin, InMemoryConfigStore, BaseStatusAdapter } from '../base.js';
import type { IncomingMessage } from '../../../routing/router.js';

// ============================================================================
// Config Types
// ============================================================================

export interface WhatsAppConfig extends ChannelConfigBase {
  sessionPath?: string;
  allowedNumbers?: string[];
  allowedGroups?: string[];
  printQRInTerminal?: boolean;
}

// ============================================================================
// WhatsApp Plugin
// ============================================================================

// Placeholder types for baileys
type WASocket = any;
type WAMessage = any;

export class WhatsAppPlugin extends BaseChannelPlugin<WhatsAppConfig> {
  meta: ChannelMeta = {
    id: 'whatsapp',
    name: 'whatsapp',
    displayName: 'WhatsApp',
    deliveryMode: 'gateway',
    chatTypes: ['direct', 'group'],
    capabilities: {
      reactions: true,
      media: true,
      typing: true,
      read_receipts: true,
      polls: true
    },
    version: '1.0.0',
    description: 'WhatsApp Web integration via Baileys',
    icon: '📱'
  };

  private sock: WASocket | null = null;
  private ready: boolean = false;
  private qrCode: string | null = null;
  private configStore: InMemoryConfigStore<WhatsAppConfig>;
  private statusAdapter: BaseStatusAdapter;

  outbound: OutboundAdapter;
  normalize: NormalizeAdapter;
  gateway: GatewayAdapter;

  constructor(initialConfig?: WhatsAppConfig) {
    super();

    this.configStore = new InMemoryConfigStore<WhatsAppConfig>();
    this.config = this.configStore;

    if (initialConfig) {
      this.configStore.setConfig('default', {
        sessionPath: './.gltch/whatsapp-session',
        printQRInTerminal: true,
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
      looksLikeTargetId: (input) => this.looksLikeWhatsAppId(input),
      normalizeTargetId: (input) => this.normalizeId(input),
      parseTargetId: (targetId) => this.parseId(targetId)
    };

    // Initialize gateway adapter
    this.gateway = {
      startAccount: async (accountId) => this.startAccount(accountId),
      stopAccount: async (accountId) => this.stopAccount(accountId),
      getAccountStatus: async (accountId) => this.getAccountStatus(accountId)
    };
  }

  protected async onInitialize(): Promise<void> {
    const accountIds = await this.config.listAccountIds();
    if (accountIds.length === 0) {
      console.log('ℹ WhatsApp: No accounts configured');
      return;
    }

    for (const accountId of accountIds) {
      const config = await this.config.resolveAccount(accountId);
      if (config?.enabled) {
        await this.startAccount(accountId);
      }
    }
  }

  protected async onShutdown(): Promise<void> {
    if (this.sock) {
      this.sock.end();
      this.sock = null;
      this.ready = false;
    }
  }

  // ============================================================================
  // Gateway Methods
  // ============================================================================

  private async startAccount(accountId: string): Promise<void> {
    const config = await this.config.resolveAccount(accountId);
    if (!config) {
      throw new Error(`Account ${accountId} not configured`);
    }

    try {
      const { 
        default: makeWASocket, 
        useMultiFileAuthState, 
        DisconnectReason 
      } = await import('@whiskeysockets/baileys');
      const { Boom } = await import('@hapi/boom');

      const sessionPath = config.sessionPath || `./.gltch/whatsapp-${accountId}`;
      const { state, saveCreds } = await useMultiFileAuthState(sessionPath);

      this.sock = makeWASocket({
        auth: state,
        printQRInTerminal: config.printQRInTerminal ?? true
      });

      // Handle connection updates
      this.sock.ev.on('connection.update', (update: any) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
          this.qrCode = qr;
          console.log('WhatsApp: Scan QR code to login');
        }

        if (connection === 'close') {
          const shouldReconnect = (lastDisconnect?.error as Boom)?.output?.statusCode !== DisconnectReason.loggedOut;
          console.log('WhatsApp: Connection closed, reconnecting:', shouldReconnect);
          
          this.ready = false;
          this.statusAdapter.setStatus(accountId, {
            id: accountId,
            status: 'disconnected',
            enabled: true
          });

          if (shouldReconnect) {
            setTimeout(() => this.startAccount(accountId), 5000);
          }
        } else if (connection === 'open') {
          console.log('✓ WhatsApp connected');
          this.ready = true;
          this.qrCode = null;
          this.statusAdapter.setStatus(accountId, {
            id: accountId,
            status: 'connected',
            enabled: true,
            connectedAt: new Date()
          });
        }
      });

      // Save credentials on update
      this.sock.ev.on('creds.update', saveCreds);

      // Handle incoming messages
      this.sock.ev.on('messages.upsert', async ({ messages }: { messages: WAMessage[] }) => {
        for (const msg of messages) {
          if (!msg.key.fromMe && msg.message) {
            await this.handleMessage(msg, config);
          }
        }
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to start WhatsApp:', errorMessage);
      this.statusAdapter.setStatus(accountId, {
        id: accountId,
        status: 'error',
        enabled: true,
        error: errorMessage
      });
      throw error;
    }
  }

  private async stopAccount(accountId: string): Promise<void> {
    if (this.sock) {
      this.sock.end();
      this.sock = null;
      this.ready = false;
      this.statusAdapter.setStatus(accountId, {
        id: accountId,
        status: 'disconnected',
        enabled: false
      });
    }
  }

  private async getAccountStatus(accountId: string): Promise<AccountSnapshot> {
    return this.statusAdapter.buildAccountSnapshot(accountId);
  }

  private async handleMessage(msg: WAMessage, config: WhatsAppConfig): Promise<void> {
    const jid = msg.key.remoteJid;
    if (!jid) return;

    // Extract text from various message types
    const text = 
      msg.message?.conversation ||
      msg.message?.extendedTextMessage?.text ||
      msg.message?.imageMessage?.caption ||
      msg.message?.videoMessage?.caption;

    if (!text) return;

    const isGroup = jid.endsWith('@g.us');
    const senderId = msg.key.participant || jid;
    const senderNumber = senderId.split('@')[0];

    // Check allowlists if configured
    if (!isGroup && config.allowedNumbers && config.allowedNumbers.length > 0) {
      if (!config.allowedNumbers.includes(senderNumber)) {
        return;
      }
    }

    if (isGroup && config.allowedGroups && config.allowedGroups.length > 0) {
      const groupId = jid.split('@')[0];
      if (!config.allowedGroups.includes(groupId)) {
        return;
      }
    }

    // In groups, only respond if mentioned (check for @ mention)
    if (isGroup) {
      const botNumber = this.sock?.user?.id?.split(':')[0];
      const isMentioned = msg.message?.extendedTextMessage?.contextInfo?.mentionedJid?.some(
        (m: string) => m.includes(botNumber)
      );
      if (!isMentioned) return;
    }

    const sessionId = this.buildSessionId(
      isGroup ? 'group' : 'direct',
      jid
    );

    const incoming: IncomingMessage = {
      text: text.replace(/@\d+/g, '').trim(),
      sessionId,
      channel: 'whatsapp',
      user: senderNumber,
      metadata: {
        jid,
        messageId: msg.key.id,
        isGroup,
        senderId,
        timestamp: msg.messageTimestamp
      }
    };

    try {
      // Send typing indicator
      await this.sock?.sendPresenceUpdate('composing', jid);

      // Route to agent
      const result = await this.router!.route(incoming);

      // Send response
      await this.sock?.sendMessage(jid, { text: result.response });

      // Clear typing indicator
      await this.sock?.sendPresenceUpdate('paused', jid);
    } catch (error) {
      console.error('WhatsApp message handling error:', error);
      await this.sock?.sendMessage(jid, { text: '⚠ Error processing message' });
    }
  }

  // ============================================================================
  // Outbound Methods
  // ============================================================================

  private async sendText(targetId: string, text: string): Promise<OutboundDeliveryResult> {
    if (!this.sock || !this.ready) {
      return this.createErrorResult('WhatsApp not connected');
    }

    try {
      const jid = this.normalizeToJid(targetId);
      if (!jid) {
        return this.createErrorResult('Invalid target ID');
      }

      const chunks = this.chunkMessage(text, 4096);
      let lastMessageId: string | undefined;

      for (const chunk of chunks) {
        const result = await this.sock.sendMessage(jid, { text: chunk });
        lastMessageId = result?.key?.id;
      }

      return this.createSuccessResult(lastMessageId);
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendMedia(targetId: string, media: any): Promise<OutboundDeliveryResult> {
    if (!this.sock || !this.ready) {
      return this.createErrorResult('WhatsApp not connected');
    }

    try {
      const jid = this.normalizeToJid(targetId);
      if (!jid) {
        return this.createErrorResult('Invalid target ID');
      }

      let messageContent: any;

      switch (media.type) {
        case 'image':
          messageContent = { 
            image: media.buffer || { url: media.url }, 
            caption: media.caption 
          };
          break;
        case 'video':
          messageContent = { 
            video: media.buffer || { url: media.url }, 
            caption: media.caption 
          };
          break;
        case 'audio':
          messageContent = { 
            audio: media.buffer || { url: media.url },
            mimetype: media.mimeType || 'audio/mp4'
          };
          break;
        case 'document':
        default:
          messageContent = { 
            document: media.buffer || { url: media.url },
            fileName: media.filename,
            caption: media.caption
          };
          break;
      }

      const result = await this.sock.sendMessage(jid, messageContent);
      return this.createSuccessResult(result?.key?.id);
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  private async sendReaction(messageId: string, emoji: string): Promise<OutboundDeliveryResult> {
    if (!this.sock || !this.ready) {
      return this.createErrorResult('WhatsApp not connected');
    }

    try {
      // messageId format: jid:msgId
      const [jid, msgId] = messageId.split(':');
      if (!jid || !msgId) {
        return this.createErrorResult('Invalid message ID format (expected jid:msgId)');
      }

      await this.sock.sendMessage(jid, {
        react: { text: emoji, key: { remoteJid: jid, id: msgId } }
      });

      return this.createSuccessResult();
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Reaction failed');
    }
  }

  // ============================================================================
  // Normalize Methods
  // ============================================================================

  private looksLikeWhatsAppId(input: string): boolean {
    // Phone numbers (with or without + and country code)
    // Or JIDs: number@s.whatsapp.net or groupid@g.us
    return /^(\+?\d{10,15}|\d+@[sg]\.whatsapp\.net|whatsapp:(direct|group):\d+)$/i.test(input);
  }

  private normalizeId(input: string): string | null {
    // Extract phone number
    const match = input.match(/(\d{10,15})/);
    return match ? match[1] : null;
  }

  private normalizeToJid(input: string): string | null {
    // If already a JID, return it
    if (input.includes('@')) {
      return input;
    }

    // Normalize to JID format
    const number = this.normalizeId(input);
    if (!number) return null;

    return `${number}@s.whatsapp.net`;
  }

  private parseId(targetId: string): { type: ChatType; id: string } | null {
    // Format: whatsapp:type:id or JID
    const parts = targetId.split(':');
    if (parts.length >= 3 && parts[0] === 'whatsapp') {
      return { type: parts[1] as ChatType, id: parts.slice(2).join(':') };
    }

    // Parse JID
    if (targetId.includes('@')) {
      const isGroup = targetId.endsWith('@g.us');
      return { 
        type: isGroup ? 'group' : 'direct', 
        id: targetId.split('@')[0] 
      };
    }

    return null;
  }

  // ============================================================================
  // Public Methods
  // ============================================================================

  isReady(): boolean {
    return this.ready;
  }

  getQRCode(): string | null {
    return this.qrCode;
  }

  getSocket(): WASocket | null {
    return this.sock;
  }
}
