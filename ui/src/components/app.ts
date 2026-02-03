/**
 * GLTCH Dashboard - Main App Component
 * Cyberpunk UI inspired by MoltLaunch
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import './sidebar.js';
import './header.js';
import './chat.js';
import './status.js';
import './settings.js';
import './wallet.js';
import './docs.js';
import './ticker.js';

type View = 'chat' | 'status' | 'settings' | 'wallet' | 'docs';

@customElement('gltch-app')
export class GltchApp extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100vh;
      height: 100dvh;
      background: var(--bg-primary);
      overflow: hidden;
    }

    .layout {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: relative;
    }

    .view-container {
      flex: 1;
      overflow: hidden;
    }

    /* Scanline effect */
    .scanline {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--neon-green), transparent);
      opacity: 0.1;
      pointer-events: none;
      animation: scanline 8s linear infinite;
      z-index: 9999;
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
      gltch-sidebar {
        display: none;
      }
    }
  `;

  @state()
  private currentView: View = 'chat';

  @state()
  private stats = {
    model: 'loading...',
    tokens: 0,
    speed: 0,
    level: 1,
    xp: 0,
    mood: 'focused'
  };

  private handleViewChange(e: CustomEvent) {
    this.currentView = e.detail.view;
  }

  private renderView() {
    switch (this.currentView) {
      case 'chat':
        return html`<gltch-chat></gltch-chat>`;
      case 'status':
        return html`<gltch-status></gltch-status>`;
      case 'settings':
        return html`<gltch-settings></gltch-settings>`;
      case 'wallet':
        return html`<gltch-wallet></gltch-wallet>`;
      case 'docs':
        return html`<gltch-docs></gltch-docs>`;
      default:
        return html`<gltch-chat></gltch-chat>`;
    }
  }

  connectedCallback() {
    super.connectedCallback();
    // Load initial stats
    this.loadStats();
    setInterval(() => this.loadStats(), 10000);
  }

  private async loadStats() {
    try {
      const res = await fetch('/api/settings');
      if (res.ok) {
        const data = await res.json();
        this.stats = {
          model: data.model || 'unknown',
          tokens: data.tokens || 0,
          speed: data.speed || 0,
          level: data.level || 1,
          xp: data.xp || 0,
          mood: data.mood || 'focused'
        };
      }
    } catch {
      // ignore
    }
  }

  render() {
    return html`
      <div class="scanline"></div>
      <gltch-header .stats=${this.stats}></gltch-header>
      <div class="layout">
        <gltch-sidebar 
          .currentView=${this.currentView}
          @view-change=${this.handleViewChange}
        ></gltch-sidebar>
        <div class="main-content">
          <div class="view-container">
            ${this.renderView()}
          </div>
        </div>
      </div>
      <gltch-ticker></gltch-ticker>
    `;
  }
}
