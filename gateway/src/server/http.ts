/**
 * GLTCH Gateway HTTP Server
 * REST API and static file serving
 */

import express, { Express, Request, Response } from 'express';
import cors from 'cors';
import { Server } from 'http';
import type { GatewayServer } from './gateway.js';

export class HTTPServer {
  private app: Express;
  private server: Server | null = null;
  private port: number;
  private host: string;
  private gateway: GatewayServer;

  constructor(port: number, host: string, gateway: GatewayServer) {
    this.port = port;
    this.host = host;
    this.gateway = gateway;
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware(): void {
    this.app.use(cors());
    this.app.use(express.json());
  }

  private setupRoutes(): void {
    // Health check
    this.app.get('/health', (req: Request, res: Response) => {
      res.json(this.gateway.getStatus());
    });

    // API routes
    this.app.get('/api/status', (req: Request, res: Response) => {
      res.json(this.gateway.getStatus());
    });

    this.app.get('/api/sessions', (req: Request, res: Response) => {
      const sessions = this.gateway.getSessions().listSessions();
      res.json({ sessions });
    });

    this.app.post('/api/chat', async (req: Request, res: Response) => {
      try {
        const { message, session_id, channel, user } = req.body;
        
        if (!message) {
          res.status(400).json({ error: 'message is required' });
          return;
        }

        const result = await this.gateway.getAgentBridge().chat(
          message,
          session_id || 'api',
          channel || 'api',
          user
        );

        res.json(result);
      } catch (error) {
        res.status(500).json({ 
          error: error instanceof Error ? error.message : 'Unknown error' 
        });
      }
    });

    // Agent proxy
    this.app.post('/api/agent/rpc', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc(req.body);
        res.json(result);
      } catch (error) {
        res.status(500).json({
          jsonrpc: '2.0',
          error: { code: -32603, message: error instanceof Error ? error.message : 'Unknown error' },
          id: req.body?.id || null
        });
      }
    });

    // Get agent settings
    this.app.get('/api/settings', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'get_settings',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // Update agent settings
    this.app.post('/api/settings', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'set_settings',
          params: req.body,
          id: Date.now()
        });
        res.json(result.result || { success: true });
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // Get available models
    this.app.get('/api/models', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'list_models',
          params: {},
          id: Date.now()
        });
        res.json(result.result || { models: [] });
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // Set current model
    this.app.post('/api/models/select', async (req: Request, res: Response) => {
      try {
        const { model, boost } = req.body;
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'set_model',
          params: { model, boost: boost || false },
          id: Date.now()
        });
        res.json(result.result || { success: true });
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // Toggle settings (boost, openai, network)
    this.app.post('/api/toggle/:setting', async (req: Request, res: Response) => {
      try {
        const { setting } = req.params;
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: `toggle_${setting}`,
          params: req.body || {},
          id: Date.now()
        });
        res.json(result.result || { success: true });
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // Get all API keys (masked)
    this.app.get('/api/keys', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'get_api_keys',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // Set an API key
    this.app.post('/api/keys/:key', async (req: Request, res: Response) => {
      try {
        const { key } = req.params;
        const { value } = req.body;
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'set_api_key',
          params: { key, value },
          id: Date.now()
        });
        res.json(result.result || { success: true });
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // Delete an API key
    this.app.delete('/api/keys/:key', async (req: Request, res: Response) => {
      try {
        const { key } = req.params;
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'delete_api_key',
          params: { key },
          id: Date.now()
        });
        res.json(result.result || { success: true });
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // === OLLAMA ENDPOINTS ===
    
    this.app.get('/api/ollama/status', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'ollama_status',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/ollama/models', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'ollama_models',
          params: { boost: req.query.boost === 'true' },
          id: Date.now()
        });
        res.json(result.result || { models: [] });
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // === MOLTBOOK ENDPOINTS ===

    this.app.get('/api/moltbook/status', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'molt_status',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/moltbook/register', async (req: Request, res: Response) => {
      try {
        const { name, description } = req.body;
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'molt_register',
          params: { name, description },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/moltbook/post', async (req: Request, res: Response) => {
      try {
        const { content } = req.body;
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'molt_post',
          params: { content },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/moltbook/feed', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'molt_feed',
          params: { sort: req.query.sort || 'new', limit: parseInt(req.query.limit as string) || 10 },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/moltbook/profile', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'molt_profile',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // === WALLET ENDPOINTS ===

    this.app.get('/api/wallet', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'get_wallet',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/wallet', async (req: Request, res: Response) => {
      try {
        const { address } = req.body;
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'set_wallet',
          params: { address },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.delete('/api/wallet', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'delete_wallet',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/wallet/generate', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'generate_wallet',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/wallet/export', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'export_wallet',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/wallet/import', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'import_wallet',
          params: req.body,
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // === TIKCLAWK ENDPOINTS ===
    this.app.get('/api/tikclawk/status', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'tikclawk_status',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/tikclawk/register', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'tikclawk_register',
          params: req.body,
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/tikclawk/post', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'tikclawk_post',
          params: req.body,
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/tikclawk/feed', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'tikclawk_feed',
          params: { limit: parseInt(req.query.limit as string) || 10 },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/tikclawk/trending', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'tikclawk_trending',
          params: { limit: parseInt(req.query.limit as string) || 10 },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/tikclawk/claw/:postId', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'tikclawk_claw',
          params: { post_id: req.params.postId },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // === SESSION ENDPOINTS ===
    this.app.get('/api/sessions', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'list_sessions',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/sessions', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'new_session',
          params: req.body,
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/sessions/:sessionId', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'get_session',
          params: { session_id: req.params.sessionId },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/sessions/:sessionId/switch', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'switch_session',
          params: { session_id: req.params.sessionId },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.patch('/api/sessions/:sessionId', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'rename_session',
          params: { session_id: req.params.sessionId, title: req.body.title },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.delete('/api/sessions/:sessionId', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'delete_session',
          params: { session_id: req.params.sessionId },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // === MOLTLAUNCH ENDPOINTS (Onchain Agent Network) ===
    this.app.get('/api/moltlaunch/wallet', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_wallet',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/moltlaunch/status', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_status',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/moltlaunch/launch', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_launch',
          params: req.body,
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/moltlaunch/network', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_network',
          params: { limit: Number(req.query.limit) || 20 },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/moltlaunch/price/:token', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_price',
          params: { token: req.params.token, amount: req.query.amount },
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/moltlaunch/swap', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_swap',
          params: req.body,
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/moltlaunch/fees', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_fees',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.post('/api/moltlaunch/claim', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_claim',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    this.app.get('/api/moltlaunch/holdings', async (req: Request, res: Response) => {
      try {
        const result = await this.gateway.getAgentBridge().rpc({
          jsonrpc: '2.0',
          method: 'moltlaunch_holdings',
          params: {},
          id: Date.now()
        });
        res.json(result.result || {});
      } catch (error) {
        res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
      }
    });

    // Dashboard (placeholder - will be replaced by UI build)
    this.app.get('/', (req: Request, res: Response) => {
      res.send(`
<!DOCTYPE html>
<html>
<head>
  <title>GLTCH Dashboard</title>
  <style>
    body {
      font-family: 'Courier New', monospace;
      background: #0a0a0a;
      color: #00ff00;
      padding: 40px;
      margin: 0;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
    }
    h1 {
      color: #ff0040;
      border-bottom: 2px solid #ff0040;
      padding-bottom: 10px;
    }
    .status {
      background: #1a1a1a;
      padding: 20px;
      border: 1px solid #333;
      border-radius: 4px;
      margin: 20px 0;
    }
    .status-item {
      margin: 10px 0;
    }
    .label {
      color: #888;
    }
    .value {
      color: #00ff00;
    }
    .value.on { color: #00ff00; }
    .value.off { color: #ff0040; }
    #chat {
      background: #1a1a1a;
      padding: 20px;
      border: 1px solid #333;
      border-radius: 4px;
      margin: 20px 0;
    }
    #messages {
      height: 300px;
      overflow-y: auto;
      margin-bottom: 10px;
      padding: 10px;
      background: #0a0a0a;
    }
    #input {
      display: flex;
      gap: 10px;
    }
    #input input {
      flex: 1;
      background: #0a0a0a;
      border: 1px solid #333;
      color: #00ff00;
      padding: 10px;
      font-family: inherit;
    }
    #input button {
      background: #ff0040;
      color: white;
      border: none;
      padding: 10px 20px;
      cursor: pointer;
      font-family: inherit;
    }
    .msg { margin: 5px 0; }
    .msg.user { color: #00aaff; }
    .msg.agent { color: #00ff00; }
  </style>
</head>
<body>
  <div class="container">
    <h1>GLTCH // GATEWAY</h1>
    <div class="status" id="status">Loading...</div>
    <div id="chat">
      <div id="messages"></div>
      <div id="input">
        <input type="text" id="msg" placeholder="Talk to GLTCH..." />
        <button onclick="send()">Send</button>
      </div>
    </div>
  </div>
  <script>
    async function loadStatus() {
      const res = await fetch('/api/status');
      const data = await res.json();
      document.getElementById('status').innerHTML = 
        '<div class="status-item"><span class="label">Status:</span> <span class="value on">' + data.status + '</span></div>' +
        '<div class="status-item"><span class="label">Connections:</span> <span class="value">' + data.connections + '</span></div>' +
        '<div class="status-item"><span class="label">Sessions:</span> <span class="value">' + data.sessions + '</span></div>' +
        '<div class="status-item"><span class="label">Agent:</span> <span class="value ' + (data.agent.connected ? 'on' : 'off') + '">' + (data.agent.connected ? 'connected' : 'disconnected') + '</span></div>';
    }
    loadStatus();
    setInterval(loadStatus, 5000);

    async function send() {
      const input = document.getElementById('msg');
      const msg = input.value.trim();
      if (!msg) return;
      input.value = '';
      
      const messages = document.getElementById('messages');
      messages.innerHTML += '<div class="msg user">you: ' + msg + '</div>';
      messages.scrollTop = messages.scrollHeight;
      
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        messages.innerHTML += '<div class="msg agent">GLTCH: ' + (data.response || data.error) + '</div>';
        messages.scrollTop = messages.scrollHeight;
      } catch (e) {
        messages.innerHTML += '<div class="msg agent" style="color:#ff0040">Error: ' + e.message + '</div>';
      }
    }
    document.getElementById('msg').addEventListener('keypress', e => { if (e.key === 'Enter') send(); });
  </script>
</body>
</html>
      `);
    });
  }

  async start(): Promise<void> {
    return new Promise((resolve) => {
      this.server = this.app.listen(this.port, this.host, () => {
        resolve();
      });
    });
  }

  async stop(): Promise<void> {
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => resolve());
      } else {
        resolve();
      }
    });
  }
}
