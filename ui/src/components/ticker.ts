/**
 * GLTCH Dashboard - Bottom Ticker
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface TickerItem {
  type: 'chat' | 'command' | 'tool' | 'xp';
  text: string;
  timestamp: Date;
}

@customElement('gltch-ticker')
export class GltchTicker extends LitElement {
  static styles = css`
    :host {
      display: flex;
      align-items: center;
      height: var(--ticker-height, 32px);
      background: var(--bg-secondary);
      border-top: 1px solid var(--border);
      padding: 0 16px;
      overflow: hidden;
    }

    .ticker-label {
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-right: 16px;
      white-space: nowrap;
    }

    .ticker-content {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 24px;
      overflow: hidden;
      animation: scroll 30s linear infinite;
    }

    .ticker-item {
      display: flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
      font-size: 11px;
    }

    .ticker-item .type {
      color: var(--neon-green);
      text-transform: uppercase;
      font-weight: 600;
    }

    .ticker-item .type.command {
      color: var(--neon-cyan);
    }

    .ticker-item .type.tool {
      color: var(--neon-magenta);
    }

    .ticker-item .type.xp {
      color: var(--neon-yellow);
    }

    .ticker-item .text {
      color: var(--text-secondary);
    }

    .ticker-item .separator {
      color: var(--text-muted);
      margin: 0 8px;
    }

    .version {
      font-size: 10px;
      color: var(--text-muted);
      margin-left: auto;
      white-space: nowrap;
    }

    @keyframes scroll {
      0% { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }

    /* Mobile */
    @media (max-width: 768px) {
      .ticker-label {
        display: none;
      }
    }
  `;

  @state()
  private items: TickerItem[] = [
    { type: 'chat', text: 'dashboard loaded', timestamp: new Date() },
  ];

  connectedCallback() {
    super.connectedCallback();
    this.checkStatus();
    setInterval(() => this.checkStatus(), 10000);
  }

  private async checkStatus() {
    try {
      const response = await fetch('/api/status');
      if (response.ok) {
        const data = await response.json();
        
        // Add status update to ticker
        if (data.agent?.connected) {
          this.addItem('chat', 'agent connected');
        }
        
        if (data.sessions > 0) {
          this.addItem('command', `${data.sessions} active sessions`);
        }
      }
    } catch {
      // Ignore
    }
  }

  private addItem(type: TickerItem['type'], text: string) {
    // Avoid duplicates
    if (this.items.some(i => i.text === text)) return;
    
    this.items = [
      { type, text, timestamp: new Date() },
      ...this.items.slice(0, 9) // Keep last 10
    ];
  }

  render() {
    return html`
      <span class="ticker-label">◆ activity</span>
      <div class="ticker-content">
        ${this.items.map(item => html`
          <div class="ticker-item">
            <span class="type ${item.type}">${item.type}</span>
            <span class="text">${item.text}</span>
          </div>
          <span class="separator">·</span>
        `)}
        ${this.items.map(item => html`
          <div class="ticker-item">
            <span class="type ${item.type}">${item.type}</span>
            <span class="text">${item.text}</span>
          </div>
          <span class="separator">·</span>
        `)}
      </div>
      <span class="version">v0.2.0</span>
    `;
  }
}
