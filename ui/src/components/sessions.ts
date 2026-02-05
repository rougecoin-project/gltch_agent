/**
 * GLTCH Dashboard - Sessions Component
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface Session {
    id: string;
    title: string;
    created: string;
    last_active: string;
    message_count?: number;
}

@customElement('gltch-sessions')
export class GltchSessions extends LitElement {
    static styles = css`
    :host {
      display: block;
      height: 100%;
      overflow-y: auto;
      padding: 24px;
    }

    .page-title {
      font-size: 20px;
      font-weight: 600;
      color: var(--neon-magenta);
      text-shadow: var(--glow-magenta);
      margin-bottom: 24px;
      letter-spacing: 2px;
    }

    .section {
      margin-bottom: 32px;
    }

    .actions-bar {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
    }

    .session-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .session-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 2px;
      transition: all 0.2s ease;
    }

    .session-item:hover {
      border-color: var(--neon-cyan);
      box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);
    }

    .session-item.active {
      border-color: var(--neon-green);
      background: rgba(0, 255, 102, 0.05);
    }

    .session-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .session-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .session-meta {
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      gap: 12px;
    }

    .session-actions {
      display: flex;
      gap: 8px;
      opacity: 0.7;
      transition: opacity 0.2s;
    }

    .session-item:hover .session-actions {
      opacity: 1;
    }

    button {
      padding: 8px 16px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 12px;
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 1px;
      transition: all 0.15s ease;
    }

    button:hover {
      border-color: var(--neon-green);
      color: var(--neon-green);
    }

    button.primary {
      background: var(--neon-green);
      color: black;
      border: none;
      font-weight: 600;
    }

    button.primary:hover {
      box-shadow: var(--glow-green);
    }

    button.delete {
      color: var(--neon-red);
      border-color: var(--neon-red);
      background: transparent;
    }

    button.delete:hover {
      background: var(--neon-red);
      color: black;
    }

    .empty-state {
      padding: 40px;
      text-align: center;
      color: var(--text-muted);
      border: 1px dashed var(--border);
      border-radius: 4px;
    }
  `;

    @state()
    private sessions: Session[] = [];

    @state()
    private activeId: string = '';

    @state()
    private loading = true;

    connectedCallback() {
        super.connectedCallback();
        this.loadSessions();
    }

    private async loadSessions() {
        this.loading = true;
        try {
            const response = await fetch('/api/sessions');
            if (response.ok) {
                const data = await response.json();
                this.sessions = data.sessions || [];
                this.activeId = data.active_id || '';
            }
        } catch (e) {
            console.error('Failed to load sessions', e);
        } finally {
            this.loading = false;
        }
    }

    private async createSession() {
        const title = prompt('Session Title:');
        if (!title) return;

        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
            });

            if (response.ok) {
                this.loadSessions();
            }
        } catch (e) {
            console.error('Failed to create session', e);
        }
    }

    private async switchSession(id: string) {
        try {
            // Logic handled via backend switch, but typically specific route needed
            // Actually we just set active here? No, backend needs to know
            // Use existing RPC method via dynamic POST if needed, but since we don't have a direct REST endpoint for switch
            // We might need to implement logic or just use the chat command
            // Wait, `server.py` doesn't expose `switch_session` as a specific REST endpoint other than JSON-RPC.
            // But we can use the generic JSON-RPC endpoint.

            await fetch('/api/chat', { // Hack: sending directly to handle_request via chat endpoint wrapper in server.py isn't ideal
                // Actually server.py do_POST handles arbitrary RPC if we send body with method
                method: 'POST',
                body: JSON.stringify({ method: 'switch_session', params: { session_id: id } })
            });

            this.activeId = id;
            // Notify app to switch view to chat
            this.dispatchEvent(new CustomEvent('view-change', {
                detail: { view: 'chat' },
                bubbles: true,
                composed: true
            }));
        } catch (e) {
            console.error('Failed to switch session', e);
        }
    }

    private async deleteSession(id: string, e: Event) {
        e.stopPropagation();
        if (!confirm('Delete this session?')) return;

        try {
            const response = await fetch(`/api/sessions/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.loadSessions();
            }
        } catch (e) {
            console.error('Failed to delete session', e);
        }
    }

    render() {
        return html`
      <div class="page-title">◆ sessions</div>

      <div class="actions-bar">
        <button class="primary" @click=${this.createSession}>+ New Session</button>
        <button @click=${this.loadSessions}>↻ Refresh</button>
      </div>

      <div class="session-list">
        ${this.loading ? html`<div>Loading...</div>` : ''}
        
        ${!this.loading && this.sessions.length === 0 ? html`
          <div class="empty-state">No sessions found. Create a new one to start chatting.</div>
        ` : ''}

        ${this.sessions.map(session => html`
          <div class="session-item ${session.id === this.activeId ? 'active' : ''}" @click=${() => this.switchSession(session.id)}>
            <div class="session-info">
              <div class="session-title">${session.title || 'Untitled Session'}</div>
              <div class="session-meta">
                <span>ID: ${session.id.substring(0, 8)}</span>
                <span>Created: ${new Date(session.created).toLocaleDateString()}</span>
              </div>
            </div>
            <div class="session-actions">
               ${session.id !== this.activeId ? html`
                  <button class="delete" @click=${(e: Event) => this.deleteSession(session.id, e)}>Delete</button>
               ` : html`
                  <span style="font-size:10px; color:var(--neon-green); align-self:center;">ACTIVE</span>
               `}
            </div>
          </div>
        `)}
      </div>
    `;
    }
}
