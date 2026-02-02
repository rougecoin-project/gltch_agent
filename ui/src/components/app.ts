/**
 * GLTCH Dashboard - Main App Component
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

@customElement('gltch-app')
export class GltchApp extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100vh;
      background: var(--bg-primary);
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 24px;
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
    }

    .logo {
      font-size: 24px;
      font-weight: bold;
      color: var(--accent-red);
    }

    nav {
      display: flex;
      gap: 8px;
    }

    nav button {
      padding: 8px 16px;
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-secondary);
      border-radius: 4px;
      transition: all 0.2s;
    }

    nav button:hover {
      border-color: var(--text-secondary);
      color: var(--text-primary);
    }

    nav button.active {
      background: var(--accent-red);
      border-color: var(--accent-red);
      color: white;
    }

    main {
      flex: 1;
      overflow: hidden;
    }

    .view {
      display: none;
      height: 100%;
    }

    .view.active {
      display: block;
    }
  `;

  @state()
  private activeView = 'chat';

  render() {
    return html`
      <header>
        <div class="logo">GLTCH // DASHBOARD</div>
        <nav>
          <button 
            class=${this.activeView === 'chat' ? 'active' : ''}
            @click=${() => this.activeView = 'chat'}
          >Chat</button>
          <button 
            class=${this.activeView === 'status' ? 'active' : ''}
            @click=${() => this.activeView = 'status'}
          >Status</button>
          <button 
            class=${this.activeView === 'settings' ? 'active' : ''}
            @click=${() => this.activeView = 'settings'}
          >Settings</button>
        </nav>
      </header>
      <main>
        <div class="view ${this.activeView === 'chat' ? 'active' : ''}">
          <gltch-chat></gltch-chat>
        </div>
        <div class="view ${this.activeView === 'status' ? 'active' : ''}">
          <gltch-status></gltch-status>
        </div>
        <div class="view ${this.activeView === 'settings' ? 'active' : ''}">
          <gltch-settings></gltch-settings>
        </div>
      </main>
    `;
  }
}
