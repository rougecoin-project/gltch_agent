/**
 * GLTCH Dashboard - Status Component
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface Status {
  status: string;
  version: string;
  uptime: number;
  connections: number;
  sessions: number;
  agent: {
    url: string;
    connected: boolean;
  };
  channels: {
    discord: boolean;
    telegram: boolean;
    webchat: boolean;
  };
}

interface AgentStatus {
  agent_name: string;
  operator: string;
  mode: string;
  mood: string;
  level: number;
  xp: number;
  rank: string;
  network_active: boolean;
  boost: boolean;
  emotions: {
    stress: number;
    energy: number;
    cycle: string;
  };
}

@customElement('gltch-status')
export class GltchStatus extends LitElement {
  static styles = css`
    :host {
      display: block;
      padding: 24px;
      height: 100%;
      overflow-y: auto;
    }

    h2 {
      color: var(--accent-red);
      margin-bottom: 24px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }

    .card {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
    }

    .card h3 {
      color: var(--accent-cyan);
      margin-bottom: 16px;
      font-size: 14px;
      text-transform: uppercase;
    }

    .stat {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .stat-label {
      color: var(--text-muted);
    }

    .stat-value {
      color: var(--text-primary);
    }

    .stat-value.ok {
      color: var(--accent-green);
    }

    .stat-value.error {
      color: var(--accent-red);
    }

    .stat-value.warning {
      color: var(--accent-yellow);
    }

    .progress-bar {
      height: 8px;
      background: var(--bg-primary);
      border-radius: 4px;
      overflow: hidden;
      margin-top: 4px;
    }

    .progress-bar-fill {
      height: 100%;
      background: var(--accent-green);
      transition: width 0.3s;
    }

    .progress-bar-fill.stress {
      background: var(--accent-yellow);
    }

    .refresh-btn {
      margin-top: 20px;
      padding: 8px 16px;
      background: var(--bg-tertiary);
      border: 1px solid var(--border);
      color: var(--text-secondary);
      border-radius: 4px;
    }

    .refresh-btn:hover {
      border-color: var(--text-secondary);
      color: var(--text-primary);
    }

    .loading {
      color: var(--text-muted);
      text-align: center;
      padding: 40px;
    }
  `;

  @state()
  private status: Status | null = null;

  @state()
  private agentStatus: AgentStatus | null = null;

  @state()
  private loading = true;

  connectedCallback() {
    super.connectedCallback();
    this.refresh();
    // Auto-refresh every 10 seconds
    setInterval(() => this.refresh(), 10000);
  }

  async refresh() {
    this.loading = true;

    try {
      // Fetch gateway status
      const statusRes = await fetch('/api/status');
      this.status = await statusRes.json();

      // Fetch agent status if connected
      if (this.status?.agent?.connected) {
        const agentRes = await fetch('/api/agent/rpc', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ jsonrpc: '2.0', method: 'status', id: 1 })
        });
        const data = await agentRes.json();
        this.agentStatus = data.result;
      }
    } catch (error) {
      console.error('Failed to fetch status:', error);
    } finally {
      this.loading = false;
    }
  }

  private formatUptime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${mins}m ${secs}s`;
  }

  render() {
    if (this.loading && !this.status) {
      return html`<div class="loading">Loading...</div>`;
    }

    return html`
      <h2>System Status</h2>
      
      <div class="grid">
        <!-- Gateway -->
        <div class="card">
          <h3>Gateway</h3>
          <div class="stat">
            <span class="stat-label">Status</span>
            <span class="stat-value ${this.status ? 'ok' : 'error'}">
              ${this.status ? 'Running' : 'Offline'}
            </span>
          </div>
          ${this.status ? html`
            <div class="stat">
              <span class="stat-label">Version</span>
              <span class="stat-value">${this.status.version}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Uptime</span>
              <span class="stat-value">${this.formatUptime(this.status.uptime)}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Connections</span>
              <span class="stat-value">${this.status.connections}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Sessions</span>
              <span class="stat-value">${this.status.sessions}</span>
            </div>
          ` : ''}
        </div>

        <!-- Agent -->
        <div class="card">
          <h3>Agent</h3>
          <div class="stat">
            <span class="stat-label">Connected</span>
            <span class="stat-value ${this.status?.agent?.connected ? 'ok' : 'error'}">
              ${this.status?.agent?.connected ? 'Yes' : 'No'}
            </span>
          </div>
          ${this.agentStatus ? html`
            <div class="stat">
              <span class="stat-label">Operator</span>
              <span class="stat-value">${this.agentStatus.operator || '(none)'}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Mode</span>
              <span class="stat-value">${this.agentStatus.mode}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Mood</span>
              <span class="stat-value">${this.agentStatus.mood}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Rank</span>
              <span class="stat-value" style="color: var(--accent-cyan)">
                ${this.agentStatus.rank}
              </span>
            </div>
            <div class="stat">
              <span class="stat-label">Level</span>
              <span class="stat-value">${this.agentStatus.level}</span>
            </div>
          ` : ''}
        </div>

        <!-- Channels -->
        <div class="card">
          <h3>Channels</h3>
          <div class="stat">
            <span class="stat-label">Discord</span>
            <span class="stat-value ${this.status?.channels?.discord ? 'ok' : ''}">
              ${this.status?.channels?.discord ? '● Connected' : '○ Disabled'}
            </span>
          </div>
          <div class="stat">
            <span class="stat-label">Telegram</span>
            <span class="stat-value ${this.status?.channels?.telegram ? 'ok' : ''}">
              ${this.status?.channels?.telegram ? '● Connected' : '○ Disabled'}
            </span>
          </div>
          <div class="stat">
            <span class="stat-label">WebChat</span>
            <span class="stat-value ${this.status?.channels?.webchat ? 'ok' : ''}">
              ${this.status?.channels?.webchat ? '● Enabled' : '○ Disabled'}
            </span>
          </div>
        </div>

        <!-- Emotions -->
        ${this.agentStatus?.emotions ? html`
          <div class="card">
            <h3>Emotional State</h3>
            <div class="stat">
              <span class="stat-label">Time Cycle</span>
              <span class="stat-value">${this.agentStatus.emotions.cycle}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Stress</span>
              <span class="stat-value">${this.agentStatus.emotions.stress}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-bar-fill stress" 
                   style="width: ${this.agentStatus.emotions.stress}%"></div>
            </div>
            <div class="stat" style="margin-top: 12px;">
              <span class="stat-label">Energy</span>
              <span class="stat-value">${this.agentStatus.emotions.energy}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-bar-fill" 
                   style="width: ${this.agentStatus.emotions.energy}%"></div>
            </div>
          </div>
        ` : ''}
      </div>

      <button class="refresh-btn" @click=${() => this.refresh()}>
        Refresh
      </button>
    `;
  }
}
