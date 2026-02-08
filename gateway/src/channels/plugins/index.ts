/**
 * GLTCH Channel Plugins
 * Export all plugin types and utilities
 */

// Core types
export type {
  DeliveryMode,
  ChatType,
  ChannelCapabilities,
  ChannelMeta,
  OutboundDeliveryResult,
  MediaAttachment,
  OutboundMessageRequest,
  AccountStatus,
  AccountSnapshot,
  ChannelConfigBase,
  DmPolicy,
  AllowlistEntry,
  ConfigAdapter,
  OutboundAdapter,
  NormalizeAdapter,
  SecurityAdapter,
  GatewayAdapter,
  StatusAdapter,
  PairingAdapter,
  ActionsAdapter,
  ChannelPlugin,
  RegisteredPlugin,
  PluginLoadResult
} from './types.js';

// Base classes
export {
  BaseChannelPlugin,
  InMemoryConfigStore,
  InMemorySecurityStore,
  BaseStatusAdapter
} from './base.js';

// Registry
export { PluginRegistry, pluginRegistry } from './registry.js';

// Loader
export {
  loadPlugin,
  loadAllPlugins,
  unloadAllPlugins,
  getPlugin,
  getAllPlugins,
  isChannelLoaded,
  getWebChatPlugin,
  getDiscordPlugin,
  getTelegramPlugin,
  type ChannelConfigs,
  type LoadAllResult
} from './loader.js';
