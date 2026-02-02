/**
 * GLTCH Dashboard - Settings Component
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

@customElement('gltch-settings')
export class GltchSettings extends LitElement {
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

    .section {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 20px;
    }

    .section h3 {
      color: var(--accent-cyan);
      margin-bottom: 16px;
      font-size: 14px;
      text-transform: uppercase;
    }

    .setting {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }

    .setting:last-child {
      margin-bottom: 0;
      padding-bottom: 0;
      border-bottom: none;
    }

    .setting-info {
      flex: 1;
    }

    .setting-label {
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    .setting-desc {
      color: var(--text-muted);
      font-size: 12px;
    }

    .setting-control {
      margin-left: 20px;
    }

    select {
      padding: 8px 12px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      color: var(--text-primary);
      border-radius: 4px;
      font-family: var(--font-mono);
    }

    select:focus {
      outline: none;
      border-color: var(--accent-cyan);
    }

    button {
      padding: 8px 16px;
      background: var(--bg-tertiary);
      border: 1px solid var(--border);
      color: var(--text-secondary);
      border-radius: 4px;
    }

    button:hover {
      border-color: var(--text-secondary);
      color: var(--text-primary);
    }

    button.primary {
      background: var(--accent-red);
      border-color: var(--accent-red);
      color: white;
    }

    button.success {
      background: var(--accent-green);
      border-color: var(--accent-green);
      color: black;
    }

    .toggle {
      width: 50px;
      height: 26px;
      background: var(--bg-tertiary);
      border-radius: 13px;
      position: relative;
      cursor: pointer;
      transition: background 0.2s;
    }

    .toggle.on {
      background: var(--accent-green);
    }

    .toggle::after {
      content: '';
      position: absolute;
      width: 22px;
      height: 22px;
      background: white;
      border-radius: 50%;
      top: 2px;
      left: 2px;
      transition: left 0.2s;
    }

    .toggle.on::after {
      left: 26px;
    }

    .message {
      padding: 12px;
      border-radius: 4px;
      margin-top: 16px;
    }

    .message.success {
      background: rgba(0, 255, 0, 0.1);
      border: 1px solid var(--accent-green);
      color: var(--accent-green);
    }

    .message.error {
      background: rgba(255, 0, 64, 0.1);
      border: 1px solid var(--accent-red);
      color: var(--accent-red);
    }
  `;

  @state()
  private mode = 'operator';

  @state()
  private mood = 'focused';

  @state()
  private networkActive = false;

  @state()
  private boost = false;

  @state()
  private message = '';

  @state()
  private messageType: 'success' | 'error' = 'success';

  connectedCallback() {
    super.connectedCallback();
    this.loadSettings();
  }

  async loadSettings() {
    try {
      const res = await fetch('/api/agent/rpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'status', id: 1 })
      });
      const data = await res.json();
      
      if (data.result) {
        this.mode = data.result.mode;
        this.mood = data.result.mood;
        this.networkActive = data.result.network_active;
        this.boost = data.result.boost;
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  }

  async updateSetting(method: string, params: object) {
    try {
      const res = await fetch('/api/agent/rpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', method, params, id: 1 })
      });
      const data = await res.json();
      
      if (data.error) {
        this.showMessage(`Error: ${data.error.message}`, 'error');
      } else {
        this.showMessage('Setting updated!', 'success');
        this.loadSettings();
      }
    } catch (error) {
      this.showMessage('Failed to update setting', 'error');
    }
  }

  showMessage(text: string, type: 'success' | 'error') {
    this.message = text;
    this.messageType = type;
    setTimeout(() => this.message = '', 3000);
  }

  render() {
    return html`
      <h2>Settings</h2>

      <div class="section">
        <h3>Personality</h3>
        
        <div class="setting">
          <div class="setting-info">
            <div class="setting-label">Mode</div>
            <div class="setting-desc">Personality style for responses</div>
          </div>
          <div class="setting-control">
            <select 
              .value=${this.mode}
              @change=${(e: Event) => {
                const value = (e.target as HTMLSelectElement).value;
                this.updateSetting('set_mode', { mode: value });
              }}
            >
              <option value="operator">Operator</option>
              <option value="cyberpunk">Cyberpunk</option>
              <option value="loyal">Loyal</option>
              <option value="unhinged">Unhinged</option>
            </select>
          </div>
        </div>

        <div class="setting">
          <div class="setting-info">
            <div class="setting-label">Mood</div>
            <div class="setting-desc">Current emotional state</div>
          </div>
          <div class="setting-control">
            <select 
              .value=${this.mood}
              @change=${(e: Event) => {
                const value = (e.target as HTMLSelectElement).value;
                this.updateSetting('set_mood', { mood: value });
              }}
            >
              <option value="focused">Focused</option>
              <option value="calm">Calm</option>
              <option value="happy">Happy</option>
              <option value="annoyed">Annoyed</option>
              <option value="feral">Feral</option>
              <option value="affectionate">Affectionate</option>
            </select>
          </div>
        </div>
      </div>

      <div class="section">
        <h3>Network & LLM</h3>

        <div class="setting">
          <div class="setting-info">
            <div class="setting-label">Network Access</div>
            <div class="setting-desc">Allow internet tools (curl, wget, etc.)</div>
          </div>
          <div class="setting-control">
            <div 
              class="toggle ${this.networkActive ? 'on' : ''}"
              @click=${() => this.updateSetting('toggle_network', { state: !this.networkActive })}
            ></div>
          </div>
        </div>

        <div class="setting">
          <div class="setting-info">
            <div class="setting-label">Remote GPU Boost</div>
            <div class="setting-desc">Use remote LLM server for inference</div>
          </div>
          <div class="setting-control">
            <div 
              class="toggle ${this.boost ? 'on' : ''}"
              @click=${() => this.updateSetting('toggle_boost', {})}
            ></div>
          </div>
        </div>
      </div>

      ${this.message ? html`
        <div class="message ${this.messageType}">${this.message}</div>
      ` : ''}
    `;
  }
}
