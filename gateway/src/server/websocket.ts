/**
 * GLTCH Gateway WebSocket Hub
 * Real-time communication with clients
 */

import { WebSocketServer, WebSocket } from 'ws';
import type { MessageRouter } from '../routing/router.js';

interface Client {
  id: string;
  ws: WebSocket;
  channel: string;
  sessionId: string;
  user?: string;
  connectedAt: Date;
}

export class WebSocketHub {
  private wss: WebSocketServer | null = null;
  private clients: Map<string, Client> = new Map();
  private port: number;
  private host: string;
  private router: MessageRouter;
  private nextClientId = 1;

  constructor(port: number, host: string, router: MessageRouter) {
    this.port = port;
    this.host = host;
    this.router = router;
  }

  async start(): Promise<void> {
    return new Promise((resolve) => {
      this.wss = new WebSocketServer({ port: this.port, host: this.host });

      this.wss.on('connection', (ws, req) => {
        this.handleConnection(ws, req);
      });

      this.wss.on('listening', () => {
        resolve();
      });
    });
  }

  async stop(): Promise<void> {
    return new Promise((resolve) => {
      // Close all clients
      for (const client of this.clients.values()) {
        client.ws.close(1000, 'Server shutting down');
      }
      this.clients.clear();

      if (this.wss) {
        this.wss.close(() => resolve());
      } else {
        resolve();
      }
    });
  }

  private handleConnection(ws: WebSocket, req: any): void {
    const clientId = `ws-${this.nextClientId++}`;
    const url = new URL(req.url || '/', `http://${req.headers.host}`);
    const channel = url.searchParams.get('channel') || 'webchat';
    const sessionId = url.searchParams.get('session') || clientId;
    const user = url.searchParams.get('user') || undefined;

    const client: Client = {
      id: clientId,
      ws,
      channel,
      sessionId,
      user,
      connectedAt: new Date()
    };

    this.clients.set(clientId, client);

    // Send welcome message
    this.send(client, {
      type: 'connected',
      clientId,
      sessionId,
      channel
    });

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

    ws.on('close', () => {
      this.clients.delete(clientId);
    });

    ws.on('error', (error) => {
      console.error(`WebSocket error for ${clientId}:`, error.message);
      this.clients.delete(clientId);
    });
  }

  private async handleMessage(client: Client, message: any): Promise<void> {
    switch (message.type) {
      case 'chat':
        await this.handleChat(client, message);
        break;
      case 'ping':
        this.send(client, { type: 'pong', timestamp: Date.now() });
        break;
      case 'status':
        const status = await this.router.getAgentStatus();
        this.send(client, { type: 'status', ...status });
        break;
      default:
        this.send(client, {
          type: 'error',
          error: `Unknown message type: ${message.type}`
        });
    }
  }

  private async handleChat(client: Client, message: any): Promise<void> {
    const text = message.text || message.message;
    if (!text) {
      this.send(client, { type: 'error', error: 'No message text' });
      return;
    }

    // Send typing indicator
    this.send(client, { type: 'typing', typing: true });

    try {
      const result = await this.router.route({
        text,
        sessionId: client.sessionId,
        channel: client.channel,
        user: client.user,
        clientId: client.id
      });

      this.send(client, {
        type: 'response',
        ...result
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

  private send(client: Client, data: object): void {
    if (client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(JSON.stringify(data));
    }
  }

  broadcast(data: object, filter?: (client: Client) => boolean): void {
    const message = JSON.stringify(data);
    for (const client of this.clients.values()) {
      if (!filter || filter(client)) {
        if (client.ws.readyState === WebSocket.OPEN) {
          client.ws.send(message);
        }
      }
    }
  }

  getConnectionCount(): number {
    return this.clients.size;
  }

  getClients(): Client[] {
    return Array.from(this.clients.values());
  }
}
