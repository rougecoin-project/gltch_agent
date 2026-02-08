/**
 * GLTCH Channels Index
 * Export all channel implementations
 */

// New plugin-based exports
export * from './plugins/index.js';
export * from './plugins/loader.js';

// Plugin implementations
export { DiscordPlugin, type DiscordConfig } from './plugins/discord/index.js';
export { TelegramPlugin, type TelegramConfig } from './plugins/telegram/index.js';
export { WebChatPlugin, type WebChatConfig } from './plugins/webchat/index.js';

// Legacy exports (deprecated - use plugins instead)
export { DiscordChannel } from './discord.js';
export { TelegramChannel } from './telegram.js';
export { WebChatChannel } from './webchat.js';
