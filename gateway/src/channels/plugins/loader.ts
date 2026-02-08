/**
 * GLTCH Channel Plugin Loader
 * Dynamically loads and initializes channel plugins
 */

import { pluginRegistry } from './registry.js';
import type { MessageRouter } from '../../routing/router.js';
import type { PluginLoadResult, ChannelPlugin } from './types.js';

// Import built-in plugins
import { DiscordPlugin, type DiscordConfig } from './discord/index.js';
import { TelegramPlugin, type TelegramConfig } from './telegram/index.js';
import { WebChatPlugin, type WebChatConfig } from './webchat/index.js';
import { SlackPlugin, type SlackConfig } from './slack/index.js';
import { WhatsAppPlugin, type WhatsAppConfig } from './whatsapp/index.js';
import { SignalPlugin, type SignalConfig } from './signal/index.js';

/**
 * Channel configuration for loading
 */
export interface ChannelConfigs {
  discord?: DiscordConfig;
  telegram?: TelegramConfig;
  webchat?: WebChatConfig;
  slack?: SlackConfig;
  whatsapp?: WhatsAppConfig;
  signal?: SignalConfig;
  // Future channels
  imessage?: any;
  msteams?: any;
  googlechat?: any;
  matrix?: any;
}

/**
 * Load result for all channels
 */
export interface LoadAllResult {
  loaded: string[];
  failed: { channel: string; error: string }[];
}

/**
 * Load a single plugin by channel ID
 */
export async function loadPlugin(
  channelId: string,
  config: any,
  router: MessageRouter
): Promise<PluginLoadResult> {
  let plugin: ChannelPlugin;

  switch (channelId) {
    case 'discord':
      plugin = new DiscordPlugin(config);
      break;
    case 'telegram':
      plugin = new TelegramPlugin(config);
      break;
    case 'webchat':
      plugin = new WebChatPlugin(config);
      break;
    case 'slack':
      plugin = new SlackPlugin(config);
      break;
    case 'whatsapp':
      plugin = new WhatsAppPlugin(config);
      break;
    case 'signal':
      plugin = new SignalPlugin(config);
      break;
    // Future channels
    case 'imessage':
    case 'msteams':
    case 'googlechat':
    case 'matrix':
      return { success: false, error: `Channel '${channelId}' not yet implemented` };
    default:
      return { success: false, error: `Unknown channel: ${channelId}` };
  }

  pluginRegistry.setRouter(router);
  return pluginRegistry.register(plugin);
}

/**
 * Load all configured channels
 */
export async function loadAllPlugins(
  configs: ChannelConfigs,
  router: MessageRouter
): Promise<LoadAllResult> {
  const result: LoadAllResult = {
    loaded: [],
    failed: []
  };

  pluginRegistry.setRouter(router);

  // Helper to load a channel
  const tryLoad = async (channelId: string, config: any | undefined) => {
    if (config?.enabled) {
      try {
        const res = await loadPlugin(channelId, config, router);
        if (res.success) {
          result.loaded.push(channelId);
        } else {
          result.failed.push({ channel: channelId, error: res.error ?? 'Unknown error' });
        }
      } catch (error) {
        result.failed.push({ 
          channel: channelId, 
          error: error instanceof Error ? error.message : 'Load failed' 
        });
      }
    }
  };

  // Load all channels in order
  await tryLoad('discord', configs.discord);
  await tryLoad('telegram', configs.telegram);
  await tryLoad('slack', configs.slack);
  await tryLoad('whatsapp', configs.whatsapp);
  await tryLoad('signal', configs.signal);

  // Load WebChat by default (unless explicitly disabled)
  if (configs.webchat?.enabled !== false) {
    const res = await loadPlugin('webchat', configs.webchat ?? { enabled: true }, router);
    if (res.success) {
      result.loaded.push('webchat');
    } else {
      result.failed.push({ channel: 'webchat', error: res.error ?? 'Unknown error' });
    }
  }

  return result;
}

/**
 * Unload all plugins
 */
export async function unloadAllPlugins(): Promise<void> {
  await pluginRegistry.shutdownAll();
}

/**
 * Get plugin by channel ID
 */
export function getPlugin(channelId: string): ChannelPlugin | null {
  return pluginRegistry.get(channelId);
}

/**
 * Get all loaded plugins
 */
export function getAllPlugins(): ChannelPlugin[] {
  return pluginRegistry.getAll();
}

/**
 * Check if a channel is loaded
 */
export function isChannelLoaded(channelId: string): boolean {
  return pluginRegistry.has(channelId);
}

/**
 * Get WebChat plugin instance (commonly needed for WS handling)
 */
export function getWebChatPlugin(): WebChatPlugin | null {
  return pluginRegistry.get('webchat') as WebChatPlugin | null;
}

/**
 * Get Discord plugin instance
 */
export function getDiscordPlugin(): DiscordPlugin | null {
  return pluginRegistry.get('discord') as DiscordPlugin | null;
}

/**
 * Get Telegram plugin instance  
 */
export function getTelegramPlugin(): TelegramPlugin | null {
  return pluginRegistry.get('telegram') as TelegramPlugin | null;
}

/**
 * Get Slack plugin instance
 */
export function getSlackPlugin(): SlackPlugin | null {
  return pluginRegistry.get('slack') as SlackPlugin | null;
}

/**
 * Get WhatsApp plugin instance
 */
export function getWhatsAppPlugin(): WhatsAppPlugin | null {
  return pluginRegistry.get('whatsapp') as WhatsAppPlugin | null;
}

/**
 * Get Signal plugin instance
 */
export function getSignalPlugin(): SignalPlugin | null {
  return pluginRegistry.get('signal') as SignalPlugin | null;
}
