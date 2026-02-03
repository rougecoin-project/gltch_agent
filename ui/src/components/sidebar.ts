/**
 * GLTCH Dashboard - Sidebar Navigation
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('gltch-sidebar')
export class GltchSidebar extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      width: var(--sidebar-width, 200px);
      background: var(--bg-secondary);
      border-right: 1px solid var(--border);
      padding: 16px 0;
      overflow-y: auto;
    }

    .logo {
      padding: 0 16px 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 16px;
    }

    .logo-text {
      font-size: 20px;
      font-weight: 700;
      color: var(--neon-magenta);
      text-shadow: var(--glow-magenta);
      letter-spacing: 2px;
      position: relative;
      display: inline-block;
      animation: sidebar-glitch-skew 5s infinite linear;
    }

    .logo-text::before {
      content: 'GLTCH';
      position: absolute;
      top: 0;
      left: 0;
      color: #ff44aa;
      clip-path: polygon(0 0, 100% 0, 100% 40%, 0 40%);
      animation: sidebar-glitch 4s infinite linear;
    }

    .logo-text::after {
      content: 'GLTCH';
      position: absolute;
      top: 0;
      left: 0;
      color: #0088ff;
      clip-path: polygon(0 60%, 100% 60%, 100% 100%, 0 100%);
      animation: sidebar-glitch-2 3.5s infinite linear;
    }

    @keyframes sidebar-glitch {
      0%, 92%, 100% { transform: translate(0); opacity: 0; }
      93% { transform: translate(-2px, 0); opacity: 0.8; }
      95% { transform: translate(2px, 0); opacity: 0.8; }
      97% { transform: translate(-1px, 0); opacity: 0.5; }
    }

    @keyframes sidebar-glitch-2 {
      0%, 89%, 100% { transform: translate(0); opacity: 0; }
      90% { transform: translate(2px, 0); opacity: 0.8; }
      92% { transform: translate(-2px, 0); opacity: 0.8; }
      94% { transform: translate(1px, 0); opacity: 0.5; }
    }

    @keyframes sidebar-glitch-skew {
      0%, 94%, 100% { transform: skew(0deg); }
      95% { transform: skew(-1deg); filter: brightness(1.3); }
      96% { transform: skew(1deg); }
      97% { transform: skew(0deg); }
    }

    .logo-full {
      font-size: 9px;
      color: var(--text-secondary);
      margin-top: 6px;
      line-height: 1.4;
      letter-spacing: 0.5px;
    }

    .logo-sub {
      font-size: 10px;
      color: var(--neon-green);
      margin-top: 8px;
    }

    .logo-sub a {
      color: var(--neon-green);
      text-decoration: none;
    }

    .logo-sub a:hover {
      text-decoration: underline;
    }

    .section {
      margin-bottom: 20px;
    }

    .section-label {
      padding: 0 16px;
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 8px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 16px;
      color: var(--text-secondary);
      cursor: pointer;
      transition: all 0.15s ease;
      border-left: 2px solid transparent;
    }

    .nav-item:hover {
      color: var(--text-primary);
      background: var(--bg-tertiary);
    }

    .nav-item.active {
      color: var(--neon-green);
      border-left-color: var(--neon-green);
      background: rgba(0, 255, 102, 0.05);
    }

    .nav-item .icon {
      font-size: 14px;
      width: 20px;
      text-align: center;
    }

    .nav-item .label {
      flex: 1;
    }

    .nav-item .hotkey {
      font-size: 10px;
      color: var(--text-muted);
      padding: 2px 6px;
      background: var(--bg-primary);
      border-radius: 2px;
    }

    .spacer {
      flex: 1;
    }

    .status-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      margin: 0 8px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 2px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--neon-green);
      box-shadow: var(--glow-green);
      animation: pulse 2s ease-in-out infinite;
    }

    .status-dot.offline {
      background: var(--neon-red);
      box-shadow: var(--glow-red);
    }

    .status-text {
      font-size: 11px;
      color: var(--text-secondary);
    }

    .links {
      padding: 16px;
      border-top: 1px solid var(--border);
    }

    .link {
      display: block;
      padding: 6px 0;
      color: var(--neon-green);
      font-size: 12px;
    }

    .link:hover {
      text-decoration: underline;
    }

    a.nav-item {
      text-decoration: none;
    }
  `;

  @property({ type: String })
  currentView = 'chat';

  private navigate(view: string) {
    this.dispatchEvent(new CustomEvent('view-change', {
      detail: { view },
      bubbles: true,
      composed: true
    }));
  }

  render() {
    return html`
      <div class="logo">
        <div class="logo-text">GLTCH</div>
        <div class="logo-full">Generative Language Transformer<br/>with Contextual Hierarchy</div>
        <div class="logo-sub">created by <a href="https://x.com/cyberdreadx" target="_blank">@cyberdreadx</a></div>
      </div>

      <div class="section">
        <div class="section-label">◆ navigate</div>
        <div 
          class="nav-item ${this.currentView === 'chat' ? 'active' : ''}"
          @click=${() => this.navigate('chat')}
        >
          <span class="icon">›</span>
          <span class="label">chat</span>
          <span class="hotkey">F1</span>
        </div>
        <div 
          class="nav-item ${this.currentView === 'status' ? 'active' : ''}"
          @click=${() => this.navigate('status')}
        >
          <span class="icon">›</span>
          <span class="label">status</span>
          <span class="hotkey">F2</span>
        </div>
        <div 
          class="nav-item ${this.currentView === 'settings' ? 'active' : ''}"
          @click=${() => this.navigate('settings')}
        >
          <span class="icon">›</span>
          <span class="label">settings</span>
          <span class="hotkey">F3</span>
        </div>
        <div 
          class="nav-item ${this.currentView === 'wallet' ? 'active' : ''}"
          @click=${() => this.navigate('wallet')}
        >
          <span class="icon">›</span>
          <span class="label">wallet</span>
          <span class="hotkey">F4</span>
        </div>
        <div 
          class="nav-item ${this.currentView === 'docs' ? 'active' : ''}"
          @click=${() => this.navigate('docs')}
        >
          <span class="icon">›</span>
          <span class="label">docs</span>
          <span class="hotkey">F5</span>
        </div>
      </div>

      <div class="section">
        <div class="section-label">◆ links</div>
        <a class="nav-item" href="https://github.com/cyberdreadx/gltch_agent" target="_blank">
          <span class="icon">›</span>
          <span class="label">github</span>
          <span class="hotkey">↗</span>
        </a>
        <a class="nav-item" href="https://x.com/cyberdreadx" target="_blank">
          <span class="icon">›</span>
          <span class="label">@cyberdreadx</span>
          <span class="hotkey">↗</span>
        </a>
      </div>

      <div class="spacer"></div>

      <div class="status-indicator">
        <div class="status-dot"></div>
        <span class="status-text">agent online</span>
      </div>

      <div class="links">
        <a class="link" href="#" @click=${(e: Event) => { e.preventDefault(); this.navigate('docs'); }}>· documentation</a>
        <a class="link" href="https://github.com/cyberdreadx/gltch_agent" target="_blank">· github ↗</a>
        <a class="link" href="https://moltbook.com" target="_blank">· moltbook ↗</a>
      </div>
    `;
  }
}
