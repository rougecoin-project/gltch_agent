/**
 * GLTCH Gateway Configuration Loader
 */

import type { ChannelConfigs } from '../channels/plugins/loader.js';
import type { DiscordConfig } from '../channels/plugins/discord/index.js';
import type { TelegramConfig } from '../channels/plugins/telegram/index.js';
import type { WebChatConfig } from '../channels/plugins/webchat/index.js';
import type { SlackConfig } from '../channels/plugins/slack/index.js';
import type { WhatsAppConfig } from '../channels/plugins/whatsapp/index.js';
import type { SignalConfig } from '../channels/plugins/signal/index.js';

export interface GatewayConfig {
  host: string;
  port: number;
  wsPort: number;
  agentUrl: string;
  
  // Channel configurations using the new plugin types
  channels: ChannelConfigs;
  
  // Legacy format for backwards compatibility
  legacyChannels?: {
    discord: { enabled: boolean; token: string };
    telegram: { enabled: boolean; token: string };
    webchat: { enabled: boolean };
  };
}

export function loadConfig(overrides: Partial<GatewayConfig> = {}): GatewayConfig {
  // Build Discord config
  const discordConfig: DiscordConfig | undefined = process.env.DISCORD_BOT_TOKEN
    ? {
        enabled: true,
        token: process.env.DISCORD_BOT_TOKEN,
        prefix: process.env.DISCORD_PREFIX || '!gltch',
        mentionRequired: process.env.DISCORD_MENTION_REQUIRED === 'true'
      }
    : undefined;

  // Build Telegram config
  const telegramConfig: TelegramConfig | undefined = process.env.TELEGRAM_BOT_TOKEN
    ? {
        enabled: true,
        token: process.env.TELEGRAM_BOT_TOKEN,
        allowedUsers: process.env.TELEGRAM_ALLOWED_USERS?.split(',').filter(Boolean)
      }
    : undefined;

  // Build Slack config
  const slackConfig: SlackConfig | undefined = 
    (process.env.SLACK_BOT_TOKEN && process.env.SLACK_APP_TOKEN)
      ? {
          enabled: true,
          botToken: process.env.SLACK_BOT_TOKEN,
          appToken: process.env.SLACK_APP_TOKEN,
          signingSecret: process.env.SLACK_SIGNING_SECRET,
          replyInThread: process.env.SLACK_REPLY_IN_THREAD !== 'false'
        }
      : undefined;

  // Build WhatsApp config
  const whatsappConfig: WhatsAppConfig | undefined = 
    process.env.WHATSAPP_ENABLED === 'true'
      ? {
          enabled: true,
          sessionPath: process.env.WHATSAPP_SESSION_PATH || './.gltch/whatsapp-session',
          printQRInTerminal: process.env.WHATSAPP_PRINT_QR !== 'false',
          allowedNumbers: process.env.WHATSAPP_ALLOWED_NUMBERS?.split(',').filter(Boolean)
        }
      : undefined;

  // Build Signal config
  const signalConfig: SignalConfig | undefined = 
    (process.env.SIGNAL_API_URL && process.env.SIGNAL_NUMBER)
      ? {
          enabled: true,
          apiUrl: process.env.SIGNAL_API_URL,
          number: process.env.SIGNAL_NUMBER,
          allowedNumbers: process.env.SIGNAL_ALLOWED_NUMBERS?.split(',').filter(Boolean)
        }
      : undefined;

  // Build WebChat config
  const webchatConfig: WebChatConfig = {
    enabled: process.env.WEBCHAT_ENABLED !== 'false',
    maxClients: parseInt(process.env.WEBCHAT_MAX_CLIENTS || '100'),
    authRequired: process.env.WEBCHAT_AUTH_REQUIRED === 'true'
  };

  const config: GatewayConfig = {
    host: process.env.GLTCH_GATEWAY_HOST || '127.0.0.1',
    port: parseInt(process.env.GLTCH_GATEWAY_PORT || '18888'),
    wsPort: parseInt(process.env.GLTCH_GATEWAY_WS_PORT || '18889'),
    agentUrl: process.env.GLTCH_AGENT_URL || 'http://127.0.0.1:18890',
    
    channels: {
      discord: discordConfig,
      telegram: telegramConfig,
      slack: slackConfig,
      whatsapp: whatsappConfig,
      signal: signalConfig,
      webchat: webchatConfig
    },

    // Legacy format for backwards compatibility
    legacyChannels: {
      discord: {
        enabled: !!discordConfig?.enabled,
        token: discordConfig?.token || ''
      },
      telegram: {
        enabled: !!telegramConfig?.enabled,
        token: telegramConfig?.token || ''
      },
      webchat: {
        enabled: webchatConfig.enabled
      }
    }
  };

  // Apply overrides
  if (overrides.host) config.host = overrides.host;
  if (overrides.port) config.port = overrides.port;
  if (overrides.wsPort) config.wsPort = overrides.wsPort;
  if (overrides.agentUrl) config.agentUrl = overrides.agentUrl;
  if (overrides.channels) {
    config.channels = { ...config.channels, ...overrides.channels };
  }

  return config;
}

/**
 * Get channel configs in the format expected by the plugin loader
 */
export function getChannelConfigs(config: GatewayConfig): ChannelConfigs {
  return config.channels;
}
