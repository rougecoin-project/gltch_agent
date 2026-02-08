/**
 * GLTCH Channel Plugin Types
 * Core interfaces for the channel plugin architecture
 * 
 * Based on moltbot's ChannelPlugin pattern, adapted for GLTCH
 */

import type { WebSocket } from 'ws';
import type { MessageRouter, IncomingMessage, OutgoingMessage } from '../../routing/router.js';

// ============================================================================
// Core Types
// ============================================================================

/**
 * Delivery mode determines how messages are sent
 * - 'gateway': Messages routed through a web gateway (WhatsApp, WebChat)
 * - 'direct': Direct API calls to the platform (Discord, Telegram, Slack)
 */
export type DeliveryMode = 'gateway' | 'direct';

/**
 * Chat types supported by a channel
 */
export type ChatType = 'direct' | 'group' | 'channel' | 'thread';

/**
 * Channel capabilities
 */
export interface ChannelCapabilities {
  reactions?: boolean;
  threads?: boolean;
  media?: boolean;
  polls?: boolean;
  voice?: boolean;
  typing?: boolean;
  read_receipts?: boolean;
  mentions?: boolean;
  native_commands?: boolean;
}

/**
 * Channel metadata
 */
export interface ChannelMeta {
  id: string;
  name: string;
  displayName: string;
  deliveryMode: DeliveryMode;
  chatTypes: ChatType[];
  capabilities: ChannelCapabilities;
  version: string;
  description?: string;
  icon?: string;
}

// ============================================================================
// Message Types
// ============================================================================

/**
 * Result from sending a message
 */
export interface OutboundDeliveryResult {
  success: boolean;
  channelMessageId?: string;
  error?: string;
  timestamp?: Date;
}

/**
 * Media attachment
 */
export interface MediaAttachment {
  type: 'image' | 'video' | 'audio' | 'document' | 'sticker';
  url?: string;
  buffer?: Buffer;
  filename?: string;
  mimeType?: string;
  size?: number;
  caption?: string;
}

/**
 * Outbound message request
 */
export interface OutboundMessageRequest {
  targetId: string;
  text?: string;
  media?: MediaAttachment;
  replyToMessageId?: string;
  threadId?: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// Account & Config Types
// ============================================================================

/**
 * Account status
 */
export type AccountStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

/**
 * Account snapshot
 */
export interface AccountSnapshot {
  id: string;
  status: AccountStatus;
  enabled: boolean;
  connectedAt?: Date;
  error?: string;
  metadata?: Record<string, any>;
}

/**
 * Channel configuration (base)
 */
export interface ChannelConfigBase {
  enabled: boolean;
  accountId?: string;
}

// ============================================================================
// DM Policy & Security Types
// ============================================================================

/**
 * DM policy for handling incoming direct messages
 * - 'open': Accept all DMs
 * - 'pairing': Require pairing approval
 * - 'closed': Reject all DMs
 */
export type DmPolicy = 'open' | 'pairing' | 'closed';

/**
 * Allowlist entry
 */
export interface AllowlistEntry {
  id: string;
  addedAt: Date;
  addedBy?: string;
  note?: string;
}

// ============================================================================
// Adapter Interfaces
// ============================================================================

/**
 * Configuration adapter - manages channel accounts
 */
export interface ConfigAdapter<TConfig extends ChannelConfigBase = ChannelConfigBase> {
  /** List all configured account IDs */
  listAccountIds(): Promise<string[]>;
  
  /** Resolve account configuration */
  resolveAccount(accountId: string): Promise<TConfig | null>;
  
  /** Check if account is configured and enabled */
  isConfigured(accountId: string): Promise<boolean>;
  
  /** Enable or disable an account */
  setAccountEnabled(accountId: string, enabled: boolean): Promise<void>;
  
  /** Delete an account configuration */
  deleteAccount(accountId: string): Promise<void>;
}

/**
 * Outbound adapter - sends messages to the platform
 */
export interface OutboundAdapter {
  /** Send a text message */
  sendText(accountId: string, targetId: string, text: string): Promise<OutboundDeliveryResult>;
  
  /** Send a media message */
  sendMedia?(accountId: string, targetId: string, media: MediaAttachment): Promise<OutboundDeliveryResult>;
  
  /** Send a reaction */
  sendReaction?(accountId: string, messageId: string, emoji: string): Promise<OutboundDeliveryResult>;
  
  /** Edit a message */
  editMessage?(accountId: string, messageId: string, newText: string): Promise<OutboundDeliveryResult>;
  
  /** Delete a message */
  deleteMessage?(accountId: string, messageId: string): Promise<OutboundDeliveryResult>;
}

/**
 * Normalize adapter - validates and normalizes target IDs
 */
export interface NormalizeAdapter {
  /** Check if a string looks like a valid target ID for this channel */
  looksLikeTargetId(input: string): boolean;
  
  /** Normalize a target ID to canonical format */
  normalizeTargetId(input: string): string | null;
  
  /** Parse a target ID into components */
  parseTargetId(targetId: string): { type: ChatType; id: string } | null;
}

/**
 * Security adapter - handles DM policies and allowlists
 */
export interface SecurityAdapter {
  /** Resolve DM policy for an account */
  resolveDmPolicy(accountId: string): Promise<DmPolicy>;
  
  /** Check if a sender is allowed */
  isAllowed(accountId: string, senderId: string): Promise<boolean>;
  
  /** Get allowlist entries */
  getAllowlist(accountId: string): Promise<AllowlistEntry[]>;
  
  /** Add to allowlist */
  addToAllowlist(accountId: string, entry: AllowlistEntry): Promise<void>;
  
  /** Remove from allowlist */
  removeFromAllowlist(accountId: string, senderId: string): Promise<void>;
}

/**
 * Gateway adapter - manages channel lifecycle (for gateway-mode channels)
 */
export interface GatewayAdapter {
  /** Start the account (begin monitoring) */
  startAccount(accountId: string): Promise<void>;
  
  /** Stop the account */
  stopAccount(accountId: string): Promise<void>;
  
  /** Get account status */
  getAccountStatus(accountId: string): Promise<AccountSnapshot>;
}

/**
 * Status adapter - health checks and monitoring
 */
export interface StatusAdapter {
  /** Build current account snapshot */
  buildAccountSnapshot(accountId: string): Promise<AccountSnapshot>;
  
  /** Probe account health */
  probeAccount(accountId: string): Promise<boolean>;
  
  /** Collect status issues */
  collectStatusIssues(accountId: string): Promise<string[]>;
}

/**
 * Pairing adapter - handles pairing flow for DM approval
 */
export interface PairingAdapter {
  /** Generate a pairing code for a sender */
  generatePairingCode(accountId: string, senderId: string): Promise<string>;
  
  /** Verify a pairing code */
  verifyPairingCode(accountId: string, senderId: string, code: string): Promise<boolean>;
  
  /** Approve a sender after pairing */
  approveSender(accountId: string, senderId: string): Promise<void>;
}

/**
 * Actions adapter - message actions (react, edit, delete, etc.)
 */
export interface ActionsAdapter {
  /** React to a message */
  react?(accountId: string, messageId: string, emoji: string): Promise<void>;
  
  /** Remove a reaction */
  unreact?(accountId: string, messageId: string, emoji: string): Promise<void>;
  
  /** Edit a message */
  edit?(accountId: string, messageId: string, newText: string): Promise<void>;
  
  /** Delete a message */
  delete?(accountId: string, messageId: string): Promise<void>;
  
  /** Pin a message */
  pin?(accountId: string, messageId: string): Promise<void>;
  
  /** Unpin a message */
  unpin?(accountId: string, messageId: string): Promise<void>;
}

// ============================================================================
// Channel Plugin Interface
// ============================================================================

/**
 * Main channel plugin interface
 * Each channel implements this to integrate with GLTCH
 */
export interface ChannelPlugin<TConfig extends ChannelConfigBase = ChannelConfigBase> {
  /** Channel metadata */
  meta: ChannelMeta;
  
  /** Required adapters */
  config: ConfigAdapter<TConfig>;
  outbound: OutboundAdapter;
  normalize: NormalizeAdapter;
  
  /** Optional adapters */
  security?: SecurityAdapter;
  gateway?: GatewayAdapter;
  status?: StatusAdapter;
  pairing?: PairingAdapter;
  actions?: ActionsAdapter;
  
  /** Lifecycle hooks */
  initialize?(router: MessageRouter): Promise<void>;
  shutdown?(): Promise<void>;
}

// ============================================================================
// Plugin Registry Types
// ============================================================================

/**
 * Registered plugin entry
 */
export interface RegisteredPlugin {
  plugin: ChannelPlugin;
  enabled: boolean;
  loadedAt: Date;
}

/**
 * Plugin load result
 */
export interface PluginLoadResult {
  success: boolean;
  plugin?: ChannelPlugin;
  error?: string;
}
