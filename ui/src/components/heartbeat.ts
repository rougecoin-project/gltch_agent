/**
 * GLTCH Dashboard - Heartbeat Component
 * Multi-site heartbeat monitoring and control
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface HeartbeatSite {
    site_id: string;
    display_name: string;
    interval_hours: number;
    enabled: boolean;
    last_heartbeat: string | null;
    should_run: boolean;
}

@customElement('gltch-heartbeat')
export class GltchHeartbeat extends LitElement {
    static styles = css`
    :host {
      display: block;
      padding: 24px;
      height: 100%;
      overflow-y: auto;
      background: var(--bg-primary);
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }

    h1 {
      font-size: 18px;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
    }

    .refresh-btn {
      padding: 8px 16px;
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-secondary);
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s;
    }

    .refresh-btn:hover {
      border-color: var(--neon-cyan);
      color: var(--neon-cyan);
    }

    .sites-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    }

    .site-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      transition: all 0.2s;
    }

    .site-card:hover {
      border-color: var(--neon-magenta);
    }

    .site-card.pending {
      border-color: var(--neon-yellow);
      box-shadow: 0 0 16px rgba(255, 215, 0, 0.1);
    }

    .site-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
    }

    .site-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .site-name {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .site-id {
      font-size: 11px;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }

    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .status-dot.ok {
      background: var(--neon-green);
      box-shadow: 0 0 8px var(--neon-green);
    }

    .status-dot.pending {
      background: var(--neon-yellow);
      box-shadow: 0 0 8px var(--neon-yellow);
    }

    .status-dot.disabled {
      background: var(--text-muted);
    }

    .meta-row {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 8px;
    }

    .meta-label {
      color: var(--text-muted);
    }

    .meta-value {
      color: var(--text-secondary);
    }

    .run-btn {
      width: 100%;
      margin-top: 16px;
      padding: 10px;
      background: linear-gradient(135deg, var(--neon-magenta), var(--neon-cyan));
      border: none;
      border-radius: 8px;
      color: white;
      font-weight: 600;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s;
      opacity: 0.9;
    }

    .run-btn:hover {
      opacity: 1;
      transform: translateY(-1px);
    }

    .run-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    .run-btn.running {
      background: var(--bg-tertiary);
      animation: pulse 1s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 1; }
    }

    .empty-state {
      text-align: center;
      padding: 48px;
      color: var(--text-muted);
    }

    .empty-state p {
      margin: 8px 0;
    }

    .empty-state code {
      background: var(--bg-secondary);
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
    }

    .result-toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 13px;
      z-index: 1000;
      animation: slideIn 0.3s ease;
    }

    .result-toast.success {
      background: var(--neon-green);
      color: black;
    }

    .result-toast.error {
      background: var(--neon-red);
      color: white;
    }

    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `;

    @state() private sites: HeartbeatSite[] = [];
    @state() private loading = false;
    @state() private runningId: string | null = null;
    @state() private toast: { message: string; type: 'success' | 'error' } | null = null;

    connectedCallback() {
        super.connectedCallback();
        this.loadSites();
        setInterval(() => this.loadSites(), 30000); // Refresh every 30s
    }

    private async loadSites() {
        try {
            this.loading = true;
            const res = await fetch('/api/heartbeat/list');
            if (res.ok) {
                const data = await res.json();
                this.sites = data.sites || [];
            }
        } catch (e) {
            console.error('Failed to load heartbeat sites:', e);
        } finally {
            this.loading = false;
        }
    }

    private async runHeartbeat(siteId: string) {
        if (this.runningId) return;

        this.runningId = siteId;
        try {
            const res = await fetch('/api/heartbeat/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ site_id: siteId, force: true })
            });

            const result = await res.json();

            if (result.success) {
                this.showToast(`✓ ${siteId} heartbeat complete`, 'success');
                await this.loadSites(); // Refresh
            } else {
                this.showToast(`✗ ${result.error || 'Failed'}`, 'error');
            }
        } catch (e) {
            this.showToast('Network error', 'error');
        } finally {
            this.runningId = null;
        }
    }

    private showToast(message: string, type: 'success' | 'error') {
        this.toast = { message, type };
        setTimeout(() => { this.toast = null; }, 3000);
    }

    private formatTime(iso: string | null): string {
        if (!iso) return 'never';
        const d = new Date(iso);
        const now = new Date();
        const diff = (now.getTime() - d.getTime()) / 1000;

        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }

    render() {
        return html`
      <div class="header">
        <h1>💓 Heartbeat Monitor</h1>
        <button class="refresh-btn" @click=${this.loadSites} ?disabled=${this.loading}>
          ${this.loading ? 'Loading...' : '↻ Refresh'}
        </button>
      </div>

      ${this.sites.length === 0 ? html`
        <div class="empty-state">
          <p>No heartbeat sites configured.</p>
          <p>Add YAML files to <code>heartbeats/</code></p>
        </div>
      ` : html`
        <div class="sites-grid">
          ${this.sites.map(site => html`
            <div class="site-card ${site.should_run ? 'pending' : ''}">
              <div class="site-header">
                <div class="site-info">
                  <span class="site-name">${site.display_name}</span>
                  <span class="site-id">${site.site_id}</span>
                </div>
                <div class="status-dot ${!site.enabled ? 'disabled' : site.should_run ? 'pending' : 'ok'}"></div>
              </div>
              
              <div class="meta-row">
                <span class="meta-label">Interval</span>
                <span class="meta-value">${site.interval_hours}h</span>
              </div>
              
              <div class="meta-row">
                <span class="meta-label">Last Run</span>
                <span class="meta-value">${this.formatTime(site.last_heartbeat)}</span>
              </div>
              
              <div class="meta-row">
                <span class="meta-label">Status</span>
                <span class="meta-value">${!site.enabled ? 'Disabled' : site.should_run ? 'Due' : 'OK'}</span>
              </div>
              
              <button 
                class="run-btn ${this.runningId === site.site_id ? 'running' : ''}"
                @click=${() => this.runHeartbeat(site.site_id)}
                ?disabled=${!site.enabled || this.runningId !== null}
              >
                ${this.runningId === site.site_id ? 'Running...' : 'Run Heartbeat'}
              </button>
            </div>
          `)}
        </div>
      `}

      ${this.toast ? html`
        <div class="result-toast ${this.toast.type}">${this.toast.message}</div>
      ` : ''}
    `;
    }
}
