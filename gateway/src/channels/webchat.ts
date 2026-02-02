/**
 * GLTCH WebChat Channel
 * Browser-based chat interface via WebSocket
 * 
 * This channel is built into the gateway - no additional dependencies needed.
 * The actual UI is served by the HTTP server.
 */

import type { MessageRouter, IncomingMessage } from '../routing/router.js';
import type { WebSocket } from 'ws';

export interface WebChatConfig {
  enabled: boolean;
}

interface WebChatClient {
  id: string;
  ws: WebSocket;
  sessionId: string;
  user?: string;
  connectedAt: Date;
}

export class WebChatChannel {
  private clients: Map<string, WebChatClient> = new Map();
  private router: MessageRouter;
  private config: WebChatConfig;
  private nextClientId = 1;

  constructor(router: MessageRouter, config: WebChatConfig) {
    this.router = router;
    this.config = config;
  }

  /**
   * Handle a new WebSocket connection for webchat
   */
  handleConnection(ws: WebSocket, sessionId?: string, user?: string): string {
    const clientId = `webchat-${this.nextClientId++}`;
    const actualSessionId = sessionId || `webchat:${clientId}`;

    const client: WebChatClient = {
      id: clientId,
      ws,
      sessionId: actualSessionId,
      user,
      connectedAt: new Date()
    };

    this.clients.set(clientId, client);

    // Send welcome
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

    return clientId;
  }

  private async handleMessage(client: WebChatClient, message: any): Promise<void> {
    // Handle different message types
    switch (message.type) {
      case 'chat':
      case 'message':
        await this.handleChat(client, message.text || message.message);
        break;
      case 'typing':
        // Client is typing - could broadcast to other clients if needed
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
      const result = await this.router.route(incoming);

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

  broadcast(data: object): void {
    const message = JSON.stringify(data);
    for (const client of this.clients.values()) {
      if (client.ws.readyState === 1) {
        client.ws.send(message);
      }
    }
  }

  getClientCount(): number {
    return this.clients.size;
  }

  getClients(): WebChatClient[] {
    return Array.from(this.clients.values());
  }

  disconnect(clientId: string): boolean {
    const client = this.clients.get(clientId);
    if (client) {
      client.ws.close();
      this.clients.delete(clientId);
      return true;
    }
    return false;
  }
}
