/**
 * GLTCH Dashboard - Header with Stats
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('gltch-header')
export class GltchHeader extends LitElement {
  static styles = css`
    :host {
      display: flex;
      align-items: center;
      height: var(--header-height, 50px);
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      padding: 0 20px;
      gap: 30px;
    }

    .stat {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .stat-label {
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .stat-value {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .stat-value.green {
      color: var(--neon-green);
    }

    .stat-value.red {
      color: var(--neon-red);
    }

    .stat-value.magenta {
      color: var(--neon-magenta);
    }

    .spacer {
      flex: 1;
    }

    .live-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 2px;
    }

    .live-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--neon-red);
      animation: pulse 1s ease-in-out infinite;
    }

    .live-text {
      font-size: 11px;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .refresh-btn {
      padding: 6px 12px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--neon-green);
      border: none;
      background: transparent;
    }

    .refresh-btn:hover {
      text-decoration: underline;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }

    /* Mobile */
    @media (max-width: 768px) {
      :host {
        padding: 0 12px;
        gap: 16px;
        overflow-x: auto;
      }

      .stat {
        min-width: 60px;
      }

      .stat-label {
        font-size: 9px;
      }

      .stat-value {
        font-size: 12px;
      }
    }
  `;

  @state()
  private stats = {
    model: 'loading...',
    tokens: 0,
    speed: 0,
    level: 1,
    xp: 0,
    mood: 'focused',
    contextUsed: 0,
    contextMax: 0
  };

  @state()
  private agentStatus = 'connecting...';

  connectedCallback() {
    super.connectedCallback();
    this.loadAllData();
    setInterval(() => this.loadAllData(), 5000);
  }

  private async loadAllData() {
    await Promise.all([
      this.checkAgentStatus(),
      this.loadSettings(),
      this.loadOllamaStatus()
    ]);
  }

  private async checkAgentStatus() {
    try {
      const response = await fetch('/api/status');
      if (response.ok) {
        const data = await response.json();
        if (data.agent?.connected) {
          this.agentStatus = 'online';
        } else {
          this.agentStatus = 'gateway only';
        }
      } else {
        this.agentStatus = 'offline';
      }
    } catch {
      this.agentStatus = 'offline';
    }
  }

  private async loadSettings() {
    try {
      const response = await fetch('/api/settings');
      if (response.ok) {
        const data = await response.json();
        this.stats = {
          ...this.stats,
          model: data.model || this.stats.model,
          tokens: data.tokens || 0,
          speed: data.speed || 0,
          level: data.level || 1,
          xp: data.xp || 0,
          mood: data.mood || 'focused',
          contextUsed: data.context_used || 0,
          contextMax: data.context_max || 0
        };
      }
    } catch {
      // Ignore errors
    }
  }

  private async loadOllamaStatus() {
    try {
      const response = await fetch('/api/ollama/status');
      if (response.ok) {
        const data = await response.json();
        if (data.connected && data.model) {
          this.stats = { ...this.stats, model: data.model };
        }
      }
    } catch {
      // Ignore errors
    }
  }

  private refresh() {
    this.checkAgentStatus();
    this.loadSettings();
  }

  private formatContext(): string {
    const { contextUsed, contextMax } = this.stats;
    if (!contextMax) return '--';
    const remaining = contextMax - contextUsed;
    const pct = Math.round((remaining / contextMax) * 100);
    const k = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n.toString();
    return `${k(remaining)} (${pct}%)`;
  }

  render() {
    const contextPct = this.stats.contextMax ? 
      Math.round(((this.stats.contextMax - this.stats.contextUsed) / this.stats.contextMax) * 100) : 100;
    const contextClass = contextPct < 20 ? 'red' : contextPct < 50 ? '' : 'green';

    return html`
      <div class="stat">
        <span class="stat-label">model</span>
        <span class="stat-value">${this.stats.model}</span>
      </div>

      <div class="stat">
        <span class="stat-label">tokens</span>
        <span class="stat-value green">${this.stats.tokens.toLocaleString()}</span>
      </div>

      <div class="stat">
        <span class="stat-label">speed</span>
        <span class="stat-value">${this.stats.speed.toFixed(1)} t/s</span>
      </div>

      <div class="stat">
        <span class="stat-label">context</span>
        <span class="stat-value ${contextClass}">${this.formatContext()}</span>
      </div>

      <div class="stat">
        <span class="stat-label">level</span>
        <span class="stat-value magenta">LVL ${this.stats.level}</span>
      </div>

      <div class="spacer"></div>

      <div class="live-indicator">
        <div class="live-dot"></div>
        <span class="live-text">${this.agentStatus}</span>
      </div>

      <button class="refresh-btn" @click=${this.refresh}>refresh</button>
    `;
  }
}
