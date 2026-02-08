/**
 * GLTCH Channel Plugin Base
 * Abstract base class providing common plugin functionality
 */

import type {
  ChannelPlugin,
  ChannelMeta,
  ChannelConfigBase,
  ConfigAdapter,
  OutboundAdapter,
  NormalizeAdapter,
  SecurityAdapter,
  GatewayAdapter,
  StatusAdapter,
  OutboundDeliveryResult,
  AccountSnapshot,
  DmPolicy,
  AllowlistEntry,
  ChatType
} from './types.js';
import type { MessageRouter, IncomingMessage } from '../../routing/router.js';

/**
 * In-memory config store for simple channels
 */
export class InMemoryConfigStore<TConfig extends ChannelConfigBase> implements ConfigAdapter<TConfig> {
  protected configs: Map<string, TConfig> = new Map();

  constructor(initialConfigs?: Record<string, TConfig>) {
    if (initialConfigs) {
      for (const [id, config] of Object.entries(initialConfigs)) {
        this.configs.set(id, config);
      }
    }
  }

  async listAccountIds(): Promise<string[]> {
    return Array.from(this.configs.keys());
  }

  async resolveAccount(accountId: string): Promise<TConfig | null> {
    return this.configs.get(accountId) ?? null;
  }

  async isConfigured(accountId: string): Promise<boolean> {
    const config = this.configs.get(accountId);
    return config?.enabled ?? false;
  }

  async setAccountEnabled(accountId: string, enabled: boolean): Promise<void> {
    const config = this.configs.get(accountId);
    if (config) {
      config.enabled = enabled;
    }
  }

  async deleteAccount(accountId: string): Promise<void> {
    this.configs.delete(accountId);
  }

  // Helper to add/update configs
  setConfig(accountId: string, config: TConfig): void {
    this.configs.set(accountId, config);
  }
}

/**
 * In-memory security store
 */
export class InMemorySecurityStore implements SecurityAdapter {
  private policies: Map<string, DmPolicy> = new Map();
  private allowlists: Map<string, AllowlistEntry[]> = new Map();
  private defaultPolicy: DmPolicy;

  constructor(defaultPolicy: DmPolicy = 'open') {
    this.defaultPolicy = defaultPolicy;
  }

  async resolveDmPolicy(accountId: string): Promise<DmPolicy> {
    return this.policies.get(accountId) ?? this.defaultPolicy;
  }

  async isAllowed(accountId: string, senderId: string): Promise<boolean> {
    const policy = await this.resolveDmPolicy(accountId);
    if (policy === 'open') return true;
    if (policy === 'closed') return false;

    // For 'pairing' policy, check allowlist
    const allowlist = this.allowlists.get(accountId) ?? [];
    return allowlist.some(entry => entry.id === senderId);
  }

  async getAllowlist(accountId: string): Promise<AllowlistEntry[]> {
    return this.allowlists.get(accountId) ?? [];
  }

  async addToAllowlist(accountId: string, entry: AllowlistEntry): Promise<void> {
    const list = this.allowlists.get(accountId) ?? [];
    if (!list.some(e => e.id === entry.id)) {
      list.push(entry);
      this.allowlists.set(accountId, list);
    }
  }

  async removeFromAllowlist(accountId: string, senderId: string): Promise<void> {
    const list = this.allowlists.get(accountId) ?? [];
    this.allowlists.set(accountId, list.filter(e => e.id !== senderId));
  }

  setPolicy(accountId: string, policy: DmPolicy): void {
    this.policies.set(accountId, policy);
  }
}

/**
 * Base status implementation
 */
export class BaseStatusAdapter implements StatusAdapter {
  private statuses: Map<string, AccountSnapshot> = new Map();

  setStatus(accountId: string, snapshot: AccountSnapshot): void {
    this.statuses.set(accountId, snapshot);
  }

  async buildAccountSnapshot(accountId: string): Promise<AccountSnapshot> {
    return this.statuses.get(accountId) ?? {
      id: accountId,
      status: 'disconnected',
      enabled: false
    };
  }

  async probeAccount(accountId: string): Promise<boolean> {
    const snapshot = this.statuses.get(accountId);
    return snapshot?.status === 'connected';
  }

  async collectStatusIssues(accountId: string): Promise<string[]> {
    const snapshot = this.statuses.get(accountId);
    const issues: string[] = [];

    if (!snapshot) {
      issues.push('Account not found');
    } else if (snapshot.status === 'error') {
      issues.push(snapshot.error ?? 'Unknown error');
    } else if (snapshot.status === 'disconnected') {
      issues.push('Account is disconnected');
    }

    return issues;
  }
}

/**
 * Abstract base class for channel plugins
 * Provides sensible defaults and common functionality
 */
export abstract class BaseChannelPlugin<TConfig extends ChannelConfigBase = ChannelConfigBase> 
  implements ChannelPlugin<TConfig> {
  
  abstract meta: ChannelMeta;
  
  // Adapters - subclasses should override these
  config: ConfigAdapter<TConfig>;
  outbound!: OutboundAdapter;
  normalize!: NormalizeAdapter;
  
  security?: SecurityAdapter;
  gateway?: GatewayAdapter;
  status?: StatusAdapter;

  protected router: MessageRouter | null = null;

  constructor() {
    this.config = new InMemoryConfigStore<TConfig>();
  }

  /**
   * Initialize the plugin with the message router
   */
  async initialize(router: MessageRouter): Promise<void> {
    this.router = router;
    await this.onInitialize();
  }

  /**
   * Override this in subclasses for custom initialization
   */
  protected async onInitialize(): Promise<void> {
    // Default: no-op
  }

  /**
   * Shutdown the plugin
   */
  async shutdown(): Promise<void> {
    await this.onShutdown();
    this.router = null;
  }

  /**
   * Override this in subclasses for custom shutdown
   */
  protected async onShutdown(): Promise<void> {
    // Default: no-op
  }

  /**
   * Route an incoming message to the agent
   */
  protected async routeMessage(message: IncomingMessage): Promise<void> {
    if (!this.router) {
      console.error(`${this.meta.id}: Router not initialized`);
      return;
    }

    try {
      await this.router.route(message);
    } catch (error) {
      console.error(`${this.meta.id}: Error routing message:`, error);
    }
  }

  /**
   * Helper to create a standard outbound delivery result
   */
  protected createSuccessResult(channelMessageId?: string): OutboundDeliveryResult {
    return {
      success: true,
      channelMessageId,
      timestamp: new Date()
    };
  }

  protected createErrorResult(error: string): OutboundDeliveryResult {
    return {
      success: false,
      error,
      timestamp: new Date()
    };
  }

  /**
   * Helper to chunk long messages
   */
  protected chunkMessage(text: string, maxLength: number): string[] {
    if (text.length <= maxLength) {
      return [text];
    }

    const chunks: string[] = [];
    let remaining = text;

    while (remaining.length > 0) {
      if (remaining.length <= maxLength) {
        chunks.push(remaining);
        break;
      }

      // Try to split at a natural break point
      let splitIndex = remaining.lastIndexOf('\n', maxLength);
      if (splitIndex === -1 || splitIndex < maxLength * 0.5) {
        splitIndex = remaining.lastIndexOf(' ', maxLength);
      }
      if (splitIndex === -1 || splitIndex < maxLength * 0.5) {
        splitIndex = maxLength;
      }

      chunks.push(remaining.slice(0, splitIndex));
      remaining = remaining.slice(splitIndex).trimStart();
    }

    return chunks;
  }

  /**
   * Build a session ID from components
   */
  protected buildSessionId(chatType: ChatType, ...parts: string[]): string {
    return [this.meta.id, chatType, ...parts].join(':');
  }
}
