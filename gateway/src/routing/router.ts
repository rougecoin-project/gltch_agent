/**
 * GLTCH Message Router
 * Routes messages from channels to agent and back
 */

import type { AgentBridge } from '../server/agent-bridge.js';
import type { SessionManager } from '../sessions/manager.js';

export interface IncomingMessage {
  text: string;
  sessionId: string;
  channel: string;
  user?: string;
  clientId?: string;
  metadata?: Record<string, any>;
}

export interface OutgoingMessage {
  response: string;
  sessionId: string;
  channel: string;
  mood?: string;
  xp_gained?: number;
  action_results?: string[];
}

export class MessageRouter {
  private agentBridge: AgentBridge;
  private sessions: SessionManager;

  constructor(agentBridge: AgentBridge, sessions: SessionManager) {
    this.agentBridge = agentBridge;
    this.sessions = sessions;
  }

  async route(message: IncomingMessage): Promise<OutgoingMessage> {
    // Build session ID based on channel and user
    const sessionId = this.buildSessionId(message);

    // Record the incoming message
    this.sessions.recordMessage(sessionId, 'user', message.text);

    try {
      // Route to agent
      const result = await this.agentBridge.chat(
        message.text,
        sessionId,
        message.channel,
        message.user
      );

      // Record agent response
      this.sessions.recordMessage(sessionId, 'assistant', result.response);

      return {
        response: result.response,
        sessionId,
        channel: message.channel,
        mood: result.mood,
        xp_gained: result.xp_gained,
        action_results: result.action_results
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return {
        response: `[Connection Error] ${errorMessage}`,
        sessionId,
        channel: message.channel
      };
    }
  }

  private buildSessionId(message: IncomingMessage): string {
    // If explicit session ID is provided, use it
    if (message.sessionId && message.sessionId !== 'default') {
      return message.sessionId;
    }

    // Otherwise build from channel and user
    const parts = [message.channel];
    if (message.user) {
      parts.push(message.user);
    }
    if (message.clientId) {
      parts.push(message.clientId);
    }

    return parts.join(':');
  }

  async getAgentStatus(): Promise<any> {
    try {
      return await this.agentBridge.getStatus();
    } catch {
      return { error: 'Agent not connected' };
    }
  }
}
