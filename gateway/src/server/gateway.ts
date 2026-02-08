/**
 * GLTCH Gateway Server
 * Main gateway orchestrator
 */

import { HTTPServer } from './http.js';
import { WebSocketHub } from './websocket.js';
import { AgentBridge } from './agent-bridge.js';
import { MessageRouter } from '../routing/router.js';
import { SessionManager } from '../sessions/manager.js';
import type { GatewayConfig } from '../config/loader.js';
import { getChannelConfigs } from '../config/loader.js';
import { 
  loadAllPlugins, 
  unloadAllPlugins, 
  pluginRegistry,
  getWebChatPlugin
} from '../channels/plugins/index.js';

export class GatewayServer {
  private config: GatewayConfig;
  private httpServer: HTTPServer;
  private wsHub: WebSocketHub;
  private agentBridge: AgentBridge;
  private router: MessageRouter;
  private sessions: SessionManager;

  constructor(config: GatewayConfig) {
    this.config = config;
    this.sessions = new SessionManager();
    this.agentBridge = new AgentBridge(config.agentUrl);
    this.router = new MessageRouter(this.agentBridge, this.sessions);
    this.wsHub = new WebSocketHub(config.wsPort, config.host, this.router);
    this.httpServer = new HTTPServer(config.port, config.host, this);
  }

  async start(): Promise<void> {
    // Start agent bridge
    const agentOk = await this.agentBridge.ping();
    if (!agentOk) {
      console.warn('⚠ Agent not reachable at', this.config.agentUrl);
      console.warn('  Gateway will start, but chat will fail until agent is running');
    } else {
      console.log('✓ Agent connected');
    }

    // Load channel plugins
    console.log('');
    console.log('Loading channel plugins...');
    const channelConfigs = getChannelConfigs(this.config);
    const loadResult = await loadAllPlugins(channelConfigs, this.router);
    
    if (loadResult.loaded.length > 0) {
      console.log(`✓ Loaded channels: ${loadResult.loaded.join(', ')}`);
    }
    if (loadResult.failed.length > 0) {
      for (const failure of loadResult.failed) {
        console.warn(`✗ Failed to load ${failure.channel}: ${failure.error}`);
      }
    }

    // Connect WebSocket hub to WebChat plugin
    const webchatPlugin = getWebChatPlugin();
    if (webchatPlugin) {
      this.wsHub.setWebChatPlugin(webchatPlugin);
    }

    // Start servers
    await this.httpServer.start();
    await this.wsHub.start();

    console.log('');
    console.log('✓ Gateway ready');
    console.log(`  HTTP:      http://${this.config.host}:${this.config.port}`);
    console.log(`  WebSocket: ws://${this.config.host}:${this.config.wsPort}`);
    console.log(`  Dashboard: http://${this.config.host}:${this.config.port}/`);
    console.log('');
  }

  async stop(): Promise<void> {
    // Unload all channel plugins
    await unloadAllPlugins();
    
    await this.wsHub.stop();
    await this.httpServer.stop();
  }

  async getStatus(): Promise<object> {
    // Get channel status from plugin registry
    const channelStatus = await pluginRegistry.getStatus();
    
    return {
      status: 'running',
      version: '0.3.0',
      uptime: process.uptime(),
      connections: this.wsHub.getConnectionCount(),
      sessions: this.sessions.getSessionCount(),
      agent: {
        url: this.config.agentUrl,
        connected: this.agentBridge.isConnected()
      },
      channels: channelStatus,
      plugins: {
        loaded: pluginRegistry.count,
        list: pluginRegistry.getChannelMetas().map(m => ({
          id: m.id,
          name: m.displayName,
          icon: m.icon
        }))
      }
    };
  }

  getRouter(): MessageRouter {
    return this.router;
  }

  getAgentBridge(): AgentBridge {
    return this.agentBridge;
  }

  getSessions(): SessionManager {
    return this.sessions;
  }

  getPluginRegistry() {
    return pluginRegistry;
  }
}
