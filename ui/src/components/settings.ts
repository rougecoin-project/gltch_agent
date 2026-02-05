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
      padding: 20px;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 2px;
    }

    .section-title {
      font-size: 12px;
      color: var(--neon-green);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
    }

    .setting-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid var(--border);
    }

    .setting-row:last-child {
      border-bottom: none;
    }

    .setting-info {
      flex: 1;
    }

    .setting-label {
      font-size: 14px;
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    .setting-desc {
      font-size: 11px;
      color: var(--text-muted);
    }

    .setting-control {
      margin-left: 20px;
      display: flex;
      align-items: center;
    }

    /* Toggle switch */
    .toggle {
      position: relative;
      display: inline-block;
      width: 48px;
      height: 26px;
      cursor: pointer;
    }

    .toggle input {
      position: absolute;
      opacity: 0;
      width: 0;
      height: 0;
    }

    .toggle-track {
      position: absolute;
      top: 0;
      left: 0;
      width: 48px;
      height: 26px;
      background: var(--bg-primary);
      border: 2px solid var(--text-muted);
      border-radius: 13px;
      transition: all 0.25s ease;
    }

    .toggle-thumb {
      position: absolute;
      top: 4px;
      left: 4px;
      width: 18px;
      height: 18px;
      background: var(--text-muted);
      border-radius: 50%;
      transition: all 0.25s ease;
    }

    .toggle input:checked ~ .toggle-track {
      background: rgba(0, 255, 102, 0.2);
      border-color: var(--neon-green);
    }

    .toggle input:checked ~ .toggle-track .toggle-thumb {
      left: 26px;
      background: var(--neon-green);
      box-shadow: 0 0 8px var(--neon-green);
    }

    /* Select dropdown */
    select {
      padding: 8px 12px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      color: var(--text-primary);
      border-radius: 2px;
      font-family: var(--font-mono);
      font-size: 12px;
      cursor: pointer;
      min-width: 150px;
    }

    select:focus {
      outline: none;
      border-color: var(--neon-green);
    }

    /* Input field */
    input[type="text"], input[type="url"], input[type="password"] {
      padding: 8px 12px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      color: var(--text-primary);
      border-radius: 2px;
      font-family: var(--font-mono);
      font-size: 12px;
      min-width: 200px;
    }

    input:focus {
      outline: none;
      border-color: var(--neon-green);
    }

    /* Buttons */
    .button-row {
      display: flex;
      gap: 12px;
      margin-top: 16px;
    }

    button {
      padding: 10px 20px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    button.primary {
      background: var(--neon-green);
      color: black;
      border: none;
    }

    button.primary:hover {
      box-shadow: var(--glow-green);
    }

    button.danger {
      background: transparent;
      color: var(--neon-red);
      border: 1px solid var(--neon-red);
    }

    button.danger:hover {
      background: var(--neon-red);
      color: black;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 2px;
      font-size: 11px;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    .status-dot.online {
      background: var(--neon-green);
      box-shadow: var(--glow-green);
    }

    .status-dot.offline {
      background: var(--neon-red);
    }

    /* API Key rows */
    .key-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid var(--border);
    }

    .key-row:last-child {
      border-bottom: none;
    }

    .key-info {
      flex: 1;
    }

    .key-name {
      font-size: 14px;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .key-name .icon {
      font-size: 16px;
    }

    .key-desc {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
    }

    .key-status {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .key-masked {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--neon-green);
      background: var(--bg-primary);
      padding: 4px 8px;
      border-radius: 2px;
    }

    .key-actions {
      display: flex;
      gap: 6px;
    }

    .key-btn {
      padding: 6px 12px;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      cursor: pointer;
      border-radius: 2px;
      transition: all 0.15s ease;
    }

    .key-btn.add {
      background: transparent;
      color: var(--neon-green);
      border: 1px solid var(--neon-green);
    }

    .key-btn.add:hover {
      background: var(--neon-green);
      color: black;
    }

    .key-btn.edit {
      background: transparent;
      color: var(--neon-cyan);
      border: 1px solid var(--neon-cyan);
    }

    .key-btn.edit:hover {
      background: var(--neon-cyan);
      color: black;
    }

    .key-btn.remove {
      background: transparent;
      color: var(--neon-red);
      border: 1px solid var(--neon-red);
    }

    .key-btn.remove:hover {
      background: var(--neon-red);
      color: black;
    }

    .key-input-row {
      display: flex;
      gap: 8px;
      margin-top: 8px;
    }

    .key-input-row input {
      flex: 1;
      padding: 8px 12px;
      background: var(--bg-primary);
      border: 1px solid var(--neon-green);
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 12px;
      border-radius: 2px;
    }

    .key-input-row input:focus {
      outline: none;
      box-shadow: 0 0 8px rgba(0, 255, 102, 0.3);
    }

    .key-btn.save {
      background: var(--neon-green);
      color: black;
      border: none;
    }

    .key-btn.cancel {
      background: transparent;
      color: var(--text-muted);
      border: 1px solid var(--text-muted);
    }

    .provider-section {
      margin-bottom: 16px;
    }

    .provider-header {
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 8px;
      padding-bottom: 4px;
      border-bottom: 1px dashed var(--border);
    }
  `;

  @state()
  private settings = {
    boost: false,
    openai_mode: false,
    network_active: false,
    opencode: true,
    mode: 'cyberpunk',
    mood: 'focused',
    localUrl: 'http://localhost:11434',
    remoteUrl: 'http://localhost:1234',
    model: ''
  };

  @state()
  private apiKeys: Record<string, { set: boolean; masked: string }> = {
    openai: { set: false, masked: '' },
    anthropic: { set: false, masked: '' },
    gemini: { set: false, masked: '' },
    groq: { set: false, masked: '' },
    perplexity: { set: false, masked: '' },
    brave: { set: false, masked: '' },
    serper: { set: false, masked: '' },
    tavily: { set: false, masked: '' },
    twitter: { set: false, masked: '' },
    telegram: { set: false, masked: '' },
    discord: { set: false, masked: '' },
    moltbook: { set: false, masked: '' },
    tikclaw: { set: false, masked: '' },
  };

  @state()
  private availableModels: string[] = [];

  @state()
  private editingKey: string | null = null;

  @state()
  private keyInput = '';

  @state()
  private moltStatus = {
    connected: false,
    registered: false,
    claimed: false,
    name: '',
    karma: 0,
    followers: 0
  };

  @state()
  private moltRegName = '';

  @state()
  private moltRegDesc = '';

  @state()
  private moltPostContent = '';

  @state()
  private loading = true;

  @state()
  private saving = false;

  connectedCallback() {
    super.connectedCallback();
    this.loadSettings();
    this.loadApiKeys();
    this.loadMoltStatus();
  }

  // Hook into loadSettings to also load models
  override async performUpdate() {
    if (!this.hasUpdated) {
      this.loadModels();
    }
    super.performUpdate();
  }

  private async loadSettings() {
    try {
      const response = await fetch('/api/settings');
      if (response.ok) {
        const data = await response.json();
        this.settings = { ...this.settings, ...data };
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      this.loading = false;
    }
  }

  private async loadModels() {
    try {
      // Pass empty object as payload if server expects POST body
      const response = await fetch('/api/settings/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (response.ok) {
        const data = await response.json();
        this.availableModels = data.models || [];
        // Update current model if returned
        if (data.current) {
          this.settings = { ...this.settings, model: data.current };
        }
      }
    } catch (e) {
      console.error("Failed to load models", e);
    }
  }

  private async setModel(model: string) {
    try {
      await fetch('/api/settings/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, boost: this.settings.boost })
      });
      this.settings = { ...this.settings, model: model };
    } catch (e) {
      console.error("Failed to set model", e);
    }
  }

  private async loadApiKeys() {
    try {
      const response = await fetch('/api/keys');
      if (response.ok) {
        const data = await response.json();
        this.apiKeys = { ...this.apiKeys, ...data };
      }
    } catch (error) {
      console.error('Failed to load API keys:', error);
    }
  }

  private startEditKey(key: string) {
    this.editingKey = key;
    this.keyInput = '';
  }

  private cancelEditKey() {
    this.editingKey = null;
    this.keyInput = '';
  }

  private async saveApiKey(key: string) {
    if (!this.keyInput.trim()) {
      this.cancelEditKey();
      return;
    }

    try {
      const response = await fetch(`/api/keys/${key}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: this.keyInput })
      });

      if (response.ok) {
        const masked = '••••' + this.keyInput.slice(-4);
        this.apiKeys = {
          ...this.apiKeys,
          [key]: { set: true, masked }
        };
      }
    } catch (error) {
      console.error('Failed to save API key:', error);
    }

    this.cancelEditKey();
  }

  private async removeApiKey(key: string) {
    try {
      await fetch(`/api/keys/${key}`, { method: 'DELETE' });
      this.apiKeys = {
        ...this.apiKeys,
        [key]: { set: false, masked: '' }
      };
    } catch (error) {
      console.error('Failed to remove API key:', error);
    }
  }

  private async loadMoltStatus() {
    try {
      const response = await fetch('/api/moltbook/status');
      if (response.ok) {
        const data = await response.json();
        this.moltStatus = { ...this.moltStatus, ...data };
      }
    } catch (error) {
      console.error('Failed to load Moltbook status:', error);
    }
  }

  private async autoRegisterMoltbook() {
    try {
      const response = await fetch('/api/moltbook/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'GLTCH',
          description: 'Generative Language Transformer with Contextual Hierarchy — Local-first cyber agent running on your machine. Created by @cyberdreadx'
        })
      });

      const result = await response.json();

      if (result.success) {
        alert(`GLTCH registered! 🎉\n\nClaim your account by visiting:\n${result.claim_url}`);
        this.loadMoltStatus();
        this.loadApiKeys();
      } else {
        alert(`Registration failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Failed to auto-register on Moltbook:', error);
    }
  }

  private async registerMoltbook() {
    if (!this.moltRegName.trim() || !this.moltRegDesc.trim()) {
      alert('Please enter both name and description');
      return;
    }

    try {
      const response = await fetch('/api/moltbook/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: this.moltRegName,
          description: this.moltRegDesc
        })
      });

      const result = await response.json();

      if (result.success) {
        alert(`Registered! Send this link to claim your account:\n${result.claim_url}`);
        this.moltRegName = '';
        this.moltRegDesc = '';
        this.loadMoltStatus();
        this.loadApiKeys();
      } else {
        alert(`Registration failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Failed to register on Moltbook:', error);
    }
  }

  private async postToMoltbook() {
    if (!this.moltPostContent.trim()) {
      alert('Please enter content to post');
      return;
    }

    try {
      const response = await fetch('/api/moltbook/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: this.moltPostContent })
      });

      const result = await response.json();

      if (result.success) {
        alert('Posted to Moltbook!');
        this.moltPostContent = '';
      } else {
        alert(`Post failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Failed to post to Moltbook:', error);
    }
  }

  private async toggleSetting(key: string) {
    const newValue = !this.settings[key as keyof typeof this.settings];
    this.settings = { ...this.settings, [key]: newValue };

    try {
      await fetch(`/api/toggle/${key}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: newValue })
      });
    } catch (error) {
      console.error('Failed to toggle setting:', error);
      // Revert on error
      this.settings = { ...this.settings, [key]: !newValue };
    }
  }

  private async updateSetting(key: string, value: any) {
    this.settings = { ...this.settings, [key]: value };

    try {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value })
      });
    } catch (error) {
      console.error('Failed to update setting:', error);
    }
  }

  private renderApiKey(key: string, name: string, desc: string, icon: string) {
    const keyData = this.apiKeys[key] || { set: false, masked: '' };
    const isEditing = this.editingKey === key;

    return html`
      <div class="key-row">
        <div class="key-info">
          <div class="key-name">
            <span class="icon">${icon}</span>
            ${name}
          </div>
          <div class="key-desc">${desc}</div>
          ${isEditing ? html`
            <div class="key-input-row">
              <input 
                type="password" 
                placeholder="paste api key..."
                .value=${this.keyInput}
                @input=${(e: Event) => this.keyInput = (e.target as HTMLInputElement).value}
                @keydown=${(e: KeyboardEvent) => {
          if (e.key === 'Enter') this.saveApiKey(key);
          if (e.key === 'Escape') this.cancelEditKey();
        }}
              />
              <button class="key-btn save" @click=${() => this.saveApiKey(key)}>save</button>
              <button class="key-btn cancel" @click=${() => this.cancelEditKey()}>cancel</button>
            </div>
          ` : ''}
        </div>
        <div class="key-status">
          ${keyData.set ? html`
            <span class="key-masked">${keyData.masked}</span>
          ` : ''}
          <div class="key-actions">
            ${!isEditing ? html`
              ${keyData.set ? html`
                <button class="key-btn edit" @click=${() => this.startEditKey(key)}>edit</button>
                <button class="key-btn remove" @click=${() => this.removeApiKey(key)}>remove</button>
              ` : html`
                <button class="key-btn add" @click=${() => this.startEditKey(key)}>add key</button>
              `}
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }

  render() {
    return html`
      <div class="page-title">◆ settings</div>

      <div class="section">
        <div class="section-title">llm configuration</div>
        
        <!-- Model Selection Dropdown -->
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">active model</div>
            <div class="setting-desc">current llm (local or remote)</div>
          </div>
          <div class="setting-control">
             <select 
               .value=${this.settings.model}
               @change=${(e: Event) => this.setModel((e.target as HTMLSelectElement).value)}
            >
              <option value="" disabled>Select a model...</option>
              ${this.availableModels.map(m => html`
                <option value=${m}>${m}</option>
              `)}
            </select>
            <button class="key-btn add" style="margin-left:8px" @click=${() => this.loadModels()}>↻</button>
          </div>
        </div>

        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">boost mode (remote gpu)</div>
            <div class="setting-desc">use remote lm studio on 4090</div>
          </div>
          <div class="setting-control">
            <label class="toggle">
              <input 
                type="checkbox" 
                .checked=${this.settings.boost}
                @change=${() => this.toggleSetting('boost')}
              />
              <div class="toggle-track">
                <div class="toggle-thumb"></div>
              </div>
            </label>
          </div>
        </div>

        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">openai mode</div>
            <div class="setting-desc">use openai api (cloud)</div>
          </div>
          <div class="setting-control">
            <label class="toggle">
              <input 
                type="checkbox" 
                .checked=${this.settings.openai_mode}
                @change=${() => this.toggleSetting('openai')}
              />
              <div class="toggle-track">
                <div class="toggle-thumb"></div>
              </div>
            </label>
          </div>
        </div>

        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">local ollama url</div>
            <div class="setting-desc">ollama api endpoint</div>
          </div>
          <div class="setting-control">
            <input type="url" .value=${this.settings.localUrl} />
          </div>
        </div>

        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">remote lm studio url</div>
            <div class="setting-desc">lm studio api endpoint</div>
          </div>
          <div class="setting-control">
            <input type="url" .value=${this.settings.remoteUrl} />
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">personality</div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">mode</div>
            <div class="setting-desc">gltch's personality mode</div>
          </div>
          <div class="setting-control">
            <select 
              .value=${this.settings.mode}
              @change=${(e: Event) => this.updateSetting('mode', (e.target as HTMLSelectElement).value)}
            >
              <option value="cyberpunk">cyberpunk</option>
              <option value="operator">operator</option>
              <option value="loyal">loyal</option>
              <option value="unhinged">unhinged</option>
            </select>
          </div>
        </div>

        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">mood</div>
            <div class="setting-desc">current emotional state</div>
          </div>
          <div class="setting-control">
            <select 
              .value=${this.settings.mood}
              @change=${(e: Event) => this.updateSetting('mood', (e.target as HTMLSelectElement).value)}
            >
              <option value="focused">focused</option>
              <option value="calm">calm</option>
              <option value="feral">feral</option>
              <option value="affectionate">affectionate</option>
            </select>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">integrations</div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">opencode</div>
            <div class="setting-desc">ai coding agent integration</div>
          </div>
          <div class="setting-control">
            <span class="status-badge">
              <span class="status-dot ${this.settings.opencode ? 'online' : 'offline'}"></span>
              ${this.settings.opencode ? 'connected' : 'offline'}
            </span>
          </div>
        </div>

        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">network</div>
            <div class="setting-desc">allow network-based commands</div>
          </div>
          <div class="setting-control">
            <label class="toggle">
              <input 
                type="checkbox" 
                .checked=${this.settings.network_active}
                @change=${() => this.toggleSetting('network_active')}
              />
              <div class="toggle-track">
                <div class="toggle-thumb"></div>
              </div>
            </label>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">model api keys</div>
        ${this.renderApiKey('openai', 'OpenAI', 'for gpt-4, dall-e', '🤖')}
        ${this.renderApiKey('anthropic', 'Anthropic', 'for claude-3', '🧠')}
        ${this.renderApiKey('gemini', 'Google Gemini', 'for gemini pro/ultra', '✨')}
        ${this.renderApiKey('groq', 'Groq', 'for ultra-fast inference', '⚡')}
        ${this.renderApiKey('perplexity', 'Perplexity', 'for research/search', '🔍')}
    </div>

    <div class="section">
        <div class="section-title">tool api keys</div>
        ${this.renderApiKey('serper', 'Serper.dev', 'google search api', '🔎')}
        ${this.renderApiKey('tavily', 'Tavily', 'ai search api', '🕵️')}
        ${this.renderApiKey('brave', 'Brave Search', 'privacy search', '🦁')}
    </div>

    <div class="section">
        <div class="section-title">social integrations</div>
        ${this.renderApiKey('twitter', 'Twitter/X', 'api v2 access', '🐦')}
        ${this.renderApiKey('discord', 'Discord', 'bot token', '🎮')}
        ${this.renderApiKey('telegram', 'Telegram', 'bot token', '✈️')}
        ${this.renderApiKey('tikclaw', 'TikClaw', 'tiktok integration', '🎵')}
    </div>

    <div class="section">
        <div class="section-title">moltbook</div>
        
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-label">status</div>
            <div class="setting-desc">moltbook connection status</div>
          </div>
          <div class="setting-control">
            <span class="status-badge">
              <span class="status-dot ${this.moltStatus.connected ? 'online' : 'offline'}"></span>
              ${this.moltStatus.connected ? 'connected' : 'offline'}
            </span>
          </div>
        </div>

        ${!this.moltStatus.registered && this.moltStatus.connected ? html`
            <div class="provider-header">registration</div>
            <div class="setting-row">
                <div class="setting-info">
                    <div class="setting-label">auto-register</div>
                    <div class="setting-desc">create standard gltch account</div>
                </div>
                <div class="setting-control">
                    <button class="primary" @click=${() => this.autoRegisterMoltbook()}>register gltch</button>
                </div>
            </div>
        ` : ''}

        ${this.moltStatus.registered ? html`
             <div class="provider-header">profile</div>
             <div class="setting-row">
                <div class="setting-info">
                    <div class="setting-label">account</div>
                    <div class="setting-desc">@${this.moltStatus.name || 'unknown'}</div>
                </div>
                <div class="setting-control">
                    <span class="status-badge">karma: ${this.moltStatus.karma}</span>
                </div>
            </div>
            
            <div class="provider-header">create post</div>
            <div class="key-input-row">
                 <input 
                    type="text" 
                    placeholder="what's on your mind?"
                    .value=${this.moltPostContent}
                    @input=${(e: Event) => this.moltPostContent = (e.target as HTMLInputElement).value}
                    @keydown=${(e: KeyboardEvent) => {
          if (e.key === 'Enter') this.postToMoltbook();
        }}
                 />
                 <button class="primary" @click=${() => this.postToMoltbook()}>post</button>
            </div>
        ` : ''}
    </div>
    `;
  }
}
