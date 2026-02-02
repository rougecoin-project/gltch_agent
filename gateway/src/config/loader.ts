/**
 * GLTCH Gateway Configuration Loader
 */

export interface GatewayConfig {
  host: string;
  port: number;
  wsPort: number;
  agentUrl: string;
  channels: {
    discord: {
      enabled: boolean;
      token: string;
    };
    telegram: {
      enabled: boolean;
      token: string;
    };
    webchat: {
      enabled: boolean;
    };
  };
}

export function loadConfig(overrides: Partial<GatewayConfig> = {}): GatewayConfig {
  const config: GatewayConfig = {
    host: process.env.GLTCH_GATEWAY_HOST || '127.0.0.1',
    port: parseInt(process.env.GLTCH_GATEWAY_PORT || '18888'),
    wsPort: parseInt(process.env.GLTCH_GATEWAY_WS_PORT || '18889'),
    agentUrl: process.env.GLTCH_AGENT_URL || 'http://127.0.0.1:18890',
    channels: {
      discord: {
        enabled: !!process.env.DISCORD_BOT_TOKEN,
        token: process.env.DISCORD_BOT_TOKEN || ''
      },
      telegram: {
        enabled: !!process.env.TELEGRAM_BOT_TOKEN,
        token: process.env.TELEGRAM_BOT_TOKEN || ''
      },
      webchat: {
        enabled: true
      }
    }
  };

  // Apply overrides
  if (overrides.host) config.host = overrides.host;
  if (overrides.port) config.port = overrides.port;
  if (overrides.wsPort) config.wsPort = overrides.wsPort;
  if (overrides.agentUrl) config.agentUrl = overrides.agentUrl;

  return config;
}
