/**
 * GLTCH WebChat Channel Plugin
 * Browser-based chat interface via WebSocket
 */

import type { WebSocket } from 'ws';
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

export interface WebChatConfig extends ChannelConfigBase {
  maxClients?: number;
  authRequired?: boolean;
}

// ============================================================================
// Client Types
// ============================================================================

interface WebChatClient {
  id: string;
  ws: WebSocket;
  sessionId: string;
  user?: string;
  connectedAt: Date;
}

// ============================================================================
// WebChat Plugin
// ============================================================================

export class WebChatPlugin extends BaseChannelPlugin<WebChatConfig> {
  meta: ChannelMeta = {
    id: 'webchat',
    name: 'webchat',
    displayName: 'WebChat',
    deliveryMode: 'gateway',
    chatTypes: ['direct'],
    capabilities: {
      typing: true,
      media: false // Can be extended later
    },
    version: '1.0.0',
    description: 'Browser-based WebSocket chat',
    icon: '💬'
  };

  private clients: Map<string, WebChatClient> = new Map();
  private nextClientId = 1;
  private configStore: InMemoryConfigStore<WebChatConfig>;
  private statusAdapter: BaseStatusAdapter;

  outbound: OutboundAdapter;
  normalize: NormalizeAdapter;

  constructor(initialConfig?: WebChatConfig) {
    super();

    this.configStore = new InMemoryConfigStore<WebChatConfig>();
    this.config = this.configStore;

    if (initialConfig) {
      this.configStore.setConfig('default', {
        maxClients: 100,
        authRequired: false,
        ...initialConfig
      });
    } else {
      this.configStore.setConfig('default', {
        enabled: true,
        maxClients: 100,
        authRequired: false
      });
    }

    this.statusAdapter = new BaseStatusAdapter();
    this.status = this.statusAdapter;

    // Update status
    this.statusAdapter.setStatus('default', {
      id: 'default',
      status: 'connected',
      enabled: true,
      connectedAt: new Date()
    });

    // Initialize outbound adapter
    this.outbound = {
      sendText: async (accountId, targetId, text) => this.sendText(targetId, text)
    };

    // Initialize normalize adapter
    this.normalize = {
      looksLikeTargetId: (input) => this.looksLikeWebChatId(input),
      normalizeTargetId: (input) => this.normalizeId(input),
      parseTargetId: (targetId) => this.parseId(targetId)
    };
  }

  protected async onInitialize(): Promise<void> {
    console.log('✓ WebChat plugin initialized');
  }

  protected async onShutdown(): Promise<void> {
    // Disconnect all clients
    for (const client of this.clients.values()) {
      try {
        client.ws.close(1001, 'Server shutting down');
      } catch {
        // Ignore errors during shutdown
      }
    }
    this.clients.clear();
  }

  // ============================================================================
  // Connection Handling
  // ============================================================================

  /**
   * Handle a new WebSocket connection
   */
  handleConnection(ws: WebSocket, sessionId?: string, user?: string): string {
    const config = this.configStore.configs.get('default');
    const maxClients = config?.maxClients ?? 100;

    if (this.clients.size >= maxClients) {
      ws.close(1013, 'Maximum clients reached');
      return '';
    }

    const clientId = `webchat-${this.nextClientId++}`;
    const actualSessionId = sessionId || this.buildSessionId('direct', clientId);

    const client: WebChatClient = {
      id: clientId,
      ws,
      sessionId: actualSessionId,
      user,
      connectedAt: new Date()
    };

    this.clients.set(clientId, client);

    // Send welcome message
    this.send(client, {
      type: 'connected',
      clientId,
      sessionId: actualSessionId,
      agent: 'GLTCH',
      message: 'Connected to GLTCH. Type to chat.'
    });

    // Handle messages
    ws.on('message', async (data) => {
      try {
        const message = JSON.parse(data.toString());
        await this.handleMessage(client, message);
      } catch (error) {
        this.send(client, {
          type: 'error',
          error: 'Invalid message format'
        });
      }
    });

    // Handle disconnect
    ws.on('close', () => {
      this.clients.delete(clientId);
    });

    ws.on('error', (error) => {
      console.error(`WebChat client ${clientId} error:`, error);
      this.clients.delete(clientId);
    });

    return clientId;
  }

  private async handleMessage(client: WebChatClient, message: any): Promise<void> {
    switch (message.type) {
      case 'chat':
      case 'message':
        await this.handleChat(client, message.text || message.message);
        break;
      case 'typing':
        // Client is typing - could broadcast if needed
        break;
      case 'ping':
        this.send(client, { type: 'pong', timestamp: Date.now() });
        break;
      default:
        // Assume it's a chat message if no type specified but has text
        if (message.text || message.message) {
          await this.handleChat(client, message.text || message.message);
        }
    }
  }

  private async handleChat(client: WebChatClient, text: string): Promise<void> {
    if (!text || !text.trim()) return;

    const incoming: IncomingMessage = {
      text: text.trim(),
      sessionId: client.sessionId,
      channel: 'webchat',
      user: client.user,
      clientId: client.id
    };

    // Send typing indicator
    this.send(client, { type: 'typing', typing: true });

    try {
      const result = await this.router!.route(incoming);

      this.send(client, {
        type: 'response',
        response: result.response,
        mood: result.mood,
        xp_gained: result.xp_gained
      });
    } catch (error) {
      this.send(client, {
        type: 'error',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      this.send(client, { type: 'typing', typing: false });
    }
  }

  private send(client: WebChatClient, data: object): void {
    if (client.ws.readyState === 1) { // WebSocket.OPEN
      client.ws.send(JSON.stringify(data));
    }
  }

  // ============================================================================
  // Outbound Methods
  // ============================================================================

  private async sendText(targetId: string, text: string): Promise<OutboundDeliveryResult> {
    const client = this.clients.get(targetId);
    if (!client) {
      return this.createErrorResult('Client not connected');
    }

    try {
      this.send(client, {
        type: 'message',
        text,
        timestamp: Date.now()
      });
      return this.createSuccessResult(`webchat-msg-${Date.now()}`);
    } catch (error) {
      return this.createErrorResult(error instanceof Error ? error.message : 'Send failed');
    }
  }

  // ============================================================================
  // Normalize Methods
  // ============================================================================

  private looksLikeWebChatId(input: string): boolean {
    return /^(webchat-\d+|webchat:direct:webchat-\d+)$/.test(input);
  }

  private normalizeId(input: string): string | null {
    const match = input.match(/(webchat-\d+)/);
    return match ? match[1] : null;
  }

  private parseId(targetId: string): { type: ChatType; id: string } | null {
    const parts = targetId.split(':');
    if (parts.length >= 3 && parts[0] === 'webchat') {
      return { type: 'direct', id: parts[2] };
    }
    if (targetId.startsWith('webchat-')) {
      return { type: 'direct', id: targetId };
    }
    return null;
  }

  // ============================================================================
  // Public Methods
  // ============================================================================

  /**
   * Broadcast a message to all connected clients
   */
  broadcast(data: object): void {
    const message = JSON.stringify(data);
    for (const client of this.clients.values()) {
      if (client.ws.readyState === 1) {
        client.ws.send(message);
      }
    }
  }

  /**
   * Get count of connected clients
   */
  getClientCount(): number {
    return this.clients.size;
  }

  /**
   * Get all connected clients
   */
  getClients(): WebChatClient[] {
    return Array.from(this.clients.values());
  }

  /**
   * Disconnect a specific client
   */
  disconnect(clientId: string): boolean {
    const client = this.clients.get(clientId);
    if (client) {
      client.ws.close(1000, 'Disconnected');
      this.clients.delete(clientId);
      return true;
    }
    return false;
  }

  /**
   * Check if plugin is ready (always ready for webchat)
   */
  isReady(): boolean {
    return true;
  }
}
