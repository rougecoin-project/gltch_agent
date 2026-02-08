/**
 * GLTCH Channel Plugin Registry
 * Manages registration and lookup of channel plugins
 */

import type {
  ChannelPlugin,
  RegisteredPlugin,
  PluginLoadResult,
  ChannelMeta,
  AccountSnapshot
} from './types.js';
import type { MessageRouter } from '../../routing/router.js';

/**
 * Central registry for all channel plugins
 */
export class PluginRegistry {
  private plugins: Map<string, RegisteredPlugin> = new Map();
  private router: MessageRouter | null = null;

  /**
   * Set the message router for plugins to use
   */
  setRouter(router: MessageRouter): void {
    this.router = router;
  }

  /**
   * Register a channel plugin
   */
  async register(plugin: ChannelPlugin): Promise<PluginLoadResult> {
    const channelId = plugin.meta.id;

    if (this.plugins.has(channelId)) {
      return {
        success: false,
        error: `Channel '${channelId}' is already registered`
      };
    }

    try {
      // Initialize plugin if it has an init hook
      if (plugin.initialize && this.router) {
        await plugin.initialize(this.router);
      }

      const entry: RegisteredPlugin = {
        plugin,
        enabled: true,
        loadedAt: new Date()
      };

      this.plugins.set(channelId, entry);
      console.log(`✓ Registered channel plugin: ${plugin.meta.displayName}`);

      return { success: true, plugin };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`✗ Failed to register channel '${channelId}':`, errorMessage);
      return { success: false, error: errorMessage };
    }
  }

  /**
   * Unregister a channel plugin
   */
  async unregister(channelId: string): Promise<boolean> {
    const entry = this.plugins.get(channelId);
    if (!entry) return false;

    try {
      // Shutdown plugin if it has a shutdown hook
      if (entry.plugin.shutdown) {
        await entry.plugin.shutdown();
      }

      this.plugins.delete(channelId);
      console.log(`✓ Unregistered channel plugin: ${channelId}`);
      return true;
    } catch (error) {
      console.error(`✗ Error during unregister of '${channelId}':`, error);
      return false;
    }
  }

  /**
   * Get a registered plugin by ID
   */
  get(channelId: string): ChannelPlugin | null {
    return this.plugins.get(channelId)?.plugin ?? null;
  }

  /**
   * Get all registered plugins
   */
  getAll(): ChannelPlugin[] {
    return Array.from(this.plugins.values()).map(entry => entry.plugin);
  }

  /**
   * Get all enabled plugins
   */
  getEnabled(): ChannelPlugin[] {
    return Array.from(this.plugins.values())
      .filter(entry => entry.enabled)
      .map(entry => entry.plugin);
  }

  /**
   * Get metadata for all registered channels
   */
  getChannelMetas(): ChannelMeta[] {
    return this.getAll().map(plugin => plugin.meta);
  }

  /**
   * Enable/disable a plugin
   */
  setEnabled(channelId: string, enabled: boolean): boolean {
    const entry = this.plugins.get(channelId);
    if (!entry) return false;
    entry.enabled = enabled;
    return true;
  }

  /**
   * Check if a plugin is registered
   */
  has(channelId: string): boolean {
    return this.plugins.has(channelId);
  }

  /**
   * Check if a plugin is enabled
   */
  isEnabled(channelId: string): boolean {
    return this.plugins.get(channelId)?.enabled ?? false;
  }

  /**
   * Get status of all channels
   */
  async getStatus(): Promise<Record<string, AccountSnapshot>> {
    const status: Record<string, AccountSnapshot> = {};

    for (const [channelId, entry] of this.plugins) {
      if (entry.plugin.status) {
        try {
          // Get first account ID if available
          const accountIds = await entry.plugin.config.listAccountIds();
          if (accountIds.length > 0) {
            status[channelId] = await entry.plugin.status.buildAccountSnapshot(accountIds[0]);
          } else {
            status[channelId] = {
              id: channelId,
              status: 'disconnected',
              enabled: entry.enabled
            };
          }
        } catch {
          status[channelId] = {
            id: channelId,
            status: 'error',
            enabled: entry.enabled,
            error: 'Failed to get status'
          };
        }
      } else {
        status[channelId] = {
          id: channelId,
          status: entry.enabled ? 'connected' : 'disconnected',
          enabled: entry.enabled
        };
      }
    }

    return status;
  }

  /**
   * Find plugin by target ID (checks if the target looks like it belongs to any channel)
   */
  findByTargetId(targetId: string): ChannelPlugin | null {
    for (const entry of this.plugins.values()) {
      if (entry.plugin.normalize.looksLikeTargetId(targetId)) {
        return entry.plugin;
      }
    }
    return null;
  }

  /**
   * Shutdown all plugins
   */
  async shutdownAll(): Promise<void> {
    for (const [channelId, entry] of this.plugins) {
      try {
        if (entry.plugin.shutdown) {
          await entry.plugin.shutdown();
        }
      } catch (error) {
        console.error(`Error shutting down '${channelId}':`, error);
      }
    }
    this.plugins.clear();
  }

  /**
   * Get count of registered plugins
   */
  get count(): number {
    return this.plugins.size;
  }
}

// Singleton instance
export const pluginRegistry = new PluginRegistry();
