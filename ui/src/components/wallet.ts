/**
 * GLTCH Dashboard - Wallet Component
 * BASE Network wallet management
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

@customElement('gltch-wallet')
export class GltchWallet extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100%;
      background: var(--bg-primary);
      overflow-y: auto;
      padding: 32px;
    }

    .wallet-container {
      max-width: 600px;
      margin: 0 auto;
    }

    .header {
      margin-bottom: 32px;
    }

    .title {
      font-size: 24px;
      color: var(--neon-magenta);
      text-shadow: var(--glow-magenta);
      margin-bottom: 8px;
    }

    .subtitle {
      font-size: 13px;
      color: var(--text-muted);
    }

    .section {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 24px;
      margin-bottom: 24px;
    }

    .section-title {
      font-size: 12px;
      color: var(--neon-green);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }

    .wallet-display {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 4px;
      margin-bottom: 16px;
    }

    .wallet-icon {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, #0052ff 0%, #3b7eff 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
    }

    .wallet-info {
      flex: 1;
    }

    .wallet-label {
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 4px;
    }

    .wallet-address {
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      color: var(--text-primary);
      word-break: break-all;
    }

    .wallet-address.empty {
      color: var(--text-muted);
      font-style: italic;
    }

    .network-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      background: rgba(0, 82, 255, 0.1);
      border: 1px solid rgba(0, 82, 255, 0.3);
      border-radius: 20px;
      font-size: 11px;
      color: #3b7eff;
    }

    .network-dot {
      width: 6px;
      height: 6px;
      background: #3b7eff;
      border-radius: 50%;
    }

    .form-group {
      margin-bottom: 16px;
    }

    .form-label {
      display: block;
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 8px;
    }

    input {
      width: 100%;
      padding: 12px 16px;
      font-size: 14px;
      font-family: 'JetBrains Mono', monospace;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      color: var(--text-primary);
      border-radius: 4px;
      box-sizing: border-box;
    }

    input:focus {
      border-color: var(--neon-green);
      outline: none;
      box-shadow: var(--glow-green);
    }

    input::placeholder {
      color: var(--text-muted);
    }

    .button-row {
      display: flex;
      gap: 12px;
      margin-top: 20px;
    }

    button {
      padding: 12px 24px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
      border: 1px solid var(--border);
      background: var(--bg-tertiary);
      color: var(--text-primary);
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    button:hover {
      border-color: var(--neon-green);
      color: var(--neon-green);
    }

    button.primary {
      background: var(--neon-green);
      border-color: var(--neon-green);
      color: black;
    }

    button.primary:hover {
      box-shadow: var(--glow-green);
    }

    button.danger {
      border-color: var(--neon-red);
      color: var(--neon-red);
    }

    button.danger:hover {
      background: rgba(255, 51, 102, 0.1);
    }

    .info-box {
      background: rgba(0, 82, 255, 0.05);
      border: 1px solid rgba(0, 82, 255, 0.2);
      border-radius: 4px;
      padding: 16px;
      margin-top: 16px;
    }

    .info-title {
      font-size: 12px;
      color: #3b7eff;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .info-text {
      font-size: 12px;
      color: var(--text-secondary);
      line-height: 1.6;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      margin-top: 16px;
    }

    .stat-card {
      background: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 16px;
      text-align: center;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    .stat-value.blue { color: #3b7eff; }

    .stat-label {
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .success-message {
      background: rgba(0, 255, 102, 0.1);
      border: 1px solid var(--neon-green);
      border-radius: 4px;
      padding: 12px 16px;
      color: var(--neon-green);
      font-size: 13px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .error-message {
      background: rgba(255, 51, 102, 0.1);
      border: 1px solid var(--neon-red);
      border-radius: 4px;
      padding: 12px 16px;
      color: var(--neon-red);
      font-size: 13px;
      margin-bottom: 16px;
    }

    a {
      color: #3b7eff;
      text-decoration: none;
    }

    a:hover {
      text-decoration: underline;
    }

    @media (max-width: 600px) {
      :host {
        padding: 16px;
      }
      .stats-grid {
        grid-template-columns: 1fr;
      }
    }
  `;

  @state() private walletAddress = '';
  @state() private inputAddress = '';
  @state() private loading = false;
  @state() private message = '';
  @state() private messageType: 'success' | 'error' | '' = '';
  @state() private hasPrivateKey = false;
  @state() private showPrivateKey = false;
  @state() private generatedKey = '';
  @state() private balances: Record<string, number> = {};
  @state() private loadingBalances = false;
  @state() private sendToken = 'ETH';
  @state() private sendTo = '';
  @state() private sendAmount = '';
  @state() private sending = false;

  connectedCallback() {
    super.connectedCallback();
    this.loadWallet().then(() => this.loadBalances());
  }

  private async loadWallet() {
    try {
      const res = await fetch('/api/wallet');
      if (res.ok) {
        const data = await res.json();
        this.walletAddress = data.address || '';
        this.hasPrivateKey = data.has_private_key || false;
      }
    } catch (error) {
      console.error('Failed to load wallet:', error);
    }
  }

  private async saveWallet() {
    const address = this.inputAddress.trim();

    // Basic validation
    if (!address) {
      this.showMessage('Please enter a wallet address', 'error');
      return;
    }

    if (!address.startsWith('0x') || address.length !== 42) {
      this.showMessage('Invalid address format. Must be 0x followed by 40 hex characters.', 'error');
      return;
    }

    this.loading = true;

    try {
      const res = await fetch('/api/wallet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      });

      if (res.ok) {
        this.walletAddress = address;
        this.inputAddress = '';
        this.showMessage('Wallet saved successfully!', 'success');
      } else {
        const data = await res.json();
        this.showMessage(data.error || 'Failed to save wallet', 'error');
      }
    } catch (error) {
      this.showMessage('Failed to save wallet', 'error');
    } finally {
      this.loading = false;
    }
  }

  private async removeWallet() {
    if (!confirm('Are you sure you want to remove the wallet? This will DELETE your private key!')) return;

    try {
      const res = await fetch('/api/wallet', { method: 'DELETE' });
      if (res.ok) {
        this.walletAddress = '';
        this.hasPrivateKey = false;
        this.generatedKey = '';
        this.showMessage('Wallet removed', 'success');
      }
    } catch (error) {
      this.showMessage('Failed to remove wallet', 'error');
    }
  }

  private async generateWallet() {
    if (this.walletAddress) {
      if (!confirm('A wallet already exists. Delete it first to generate a new one.')) return;
      await this.removeWallet();
    }

    this.loading = true;

    try {
      const res = await fetch('/api/wallet/generate', { method: 'POST' });
      const data = await res.json();

      if (data.success) {
        this.walletAddress = data.address;
        this.hasPrivateKey = true;
        this.generatedKey = data.private_key;
        this.showPrivateKey = true;
        this.showMessage('Wallet generated! SAVE YOUR PRIVATE KEY NOW!', 'success');
      } else {
        this.showMessage(data.error || 'Failed to generate wallet', 'error');
      }
    } catch (error) {
      this.showMessage('Failed to generate wallet', 'error');
    } finally {
      this.loading = false;
    }
  }

  private async exportPrivateKey() {
    try {
      const res = await fetch('/api/wallet/export');
      const data = await res.json();

      if (data.success && data.private_key) {
        this.generatedKey = data.private_key;
        this.showPrivateKey = true;
      } else {
        this.showMessage(data.error || 'Failed to export wallet', 'error');
      }
    } catch (error) {
      this.showMessage('Failed to export wallet', 'error');
    }
  }

  private copyPrivateKey() {
    navigator.clipboard.writeText(this.generatedKey);
    this.showMessage('Private key copied! Keep it safe!', 'success');
  }

  private hidePrivateKey() {
    this.showPrivateKey = false;
    this.generatedKey = '';
  }

  private async importWallet() {
    const privateKey = this.inputAddress.trim();

    if (!privateKey) {
      this.showMessage('Please enter a private key', 'error');
      return;
    }

    // Basic validation - private keys are 64 hex chars (or 66 with 0x prefix)
    const cleanKey = privateKey.startsWith('0x') ? privateKey.slice(2) : privateKey;
    if (cleanKey.length !== 64 || !/^[a-fA-F0-9]+$/.test(cleanKey)) {
      this.showMessage('Invalid private key format. Must be 64 hex characters.', 'error');
      return;
    }

    this.loading = true;

    try {
      const res = await fetch('/api/wallet/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ private_key: privateKey.startsWith('0x') ? privateKey : '0x' + privateKey })
      });

      const data = await res.json();

      if (data.success) {
        this.walletAddress = data.address;
        this.hasPrivateKey = true;
        this.inputAddress = '';
        this.showMessage('Wallet imported successfully!', 'success');
      } else {
        this.showMessage(data.error || 'Failed to import wallet', 'error');
      }
    } catch (error) {
      this.showMessage('Failed to import wallet', 'error');
    } finally {
      this.loading = false;
    }
  }

  private showMessage(text: string, type: 'success' | 'error') {
    this.message = text;
    this.messageType = type;
    setTimeout(() => {
      this.message = '';
      this.messageType = '';
    }, 5000);
  }

  private formatAddress(addr: string): string {
    if (!addr) return '';
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  }

  private async loadBalances() {
    if (!this.walletAddress) return;
    this.loadingBalances = true;
    try {
      const res = await fetch('/api/balances');
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.balances) {
          this.balances = data.balances;
        }
      }
    } catch (error) {
      console.error('Failed to load balances:', error);
    } finally {
      this.loadingBalances = false;
    }
  }

  private async sendTokens() {
    if (!this.sendTo || !this.sendAmount || !this.sendToken) {
      this.showMessage('Please fill in all send fields', 'error');
      return;
    }

    this.sending = true;
    try {
      const res = await fetch('/api/token/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_address: this.sendTo,
          amount: parseFloat(this.sendAmount),
          token: this.sendToken
        })
      });
      const data = await res.json();
      if (data.success) {
        this.showMessage(`Sent ${this.sendAmount} ${this.sendToken}! TX: ${data.tx_hash?.slice(0, 10)}...`, 'success');
        this.sendTo = '';
        this.sendAmount = '';
        this.loadBalances();
      } else {
        this.showMessage(data.error || 'Send failed', 'error');
      }
    } catch (error) {
      this.showMessage('Failed to send tokens', 'error');
    } finally {
      this.sending = false;
    }
  }

  private copyAddress() {
    navigator.clipboard.writeText(this.walletAddress);
    this.showMessage('Address copied!', 'success');
  }

  render() {
    return html`
      <div class="wallet-container">
        <div class="header">
          <h1 class="title">💎 Wallet</h1>
          <p class="subtitle">Manage GLTCH's BASE network wallet</p>
        </div>

        ${this.message ? html`
          <div class="${this.messageType === 'success' ? 'success-message' : 'error-message'}">
            ${this.messageType === 'success' ? '✓' : '✗'} ${this.message}
          </div>
        ` : ''}

        <div class="section">
          <div class="section-title">◆ Current Wallet</div>
          
          <div class="wallet-display">
            <div class="wallet-icon">◈</div>
            <div class="wallet-info">
              <div class="wallet-label">BASE Address</div>
              <div class="wallet-address ${!this.walletAddress ? 'empty' : ''}">
                ${this.walletAddress || 'No wallet configured'}
              </div>
            </div>
            <div class="network-badge">
              <span class="network-dot"></span>
              BASE
            </div>
          </div>

          ${this.walletAddress ? html`
            <div class="button-row">
              <button @click=${this.copyAddress}>copy address</button>
              <button @click=${() => window.open(`https://basescan.org/address/${this.walletAddress}`, '_blank')}>
                view on basescan ↗
              </button>
              <button class="danger" @click=${this.removeWallet}>remove</button>
            </div>
          ` : ''}
        </div>

        ${this.showPrivateKey && this.generatedKey ? html`
          <div class="section" style="border-color: var(--neon-red);">
            <div class="section-title" style="color: var(--neon-red);">⚠️ Private Key - SAVE THIS NOW!</div>
            <div class="info-text" style="margin-bottom: 12px; color: var(--neon-red);">
              This is your wallet's private key. Anyone with this key can access your funds.
              Save it somewhere secure. It will NOT be shown again!
            </div>
            <div style="background: var(--bg-primary); padding: 12px; border-radius: 4px; word-break: break-all; font-family: monospace; font-size: 11px; color: var(--text-primary);">
              ${this.generatedKey}
            </div>
            <div class="button-row">
              <button class="primary" @click=${this.copyPrivateKey}>copy private key</button>
              <button class="danger" @click=${this.hidePrivateKey}>I've saved it - hide</button>
            </div>
          </div>
        ` : ''}

        <div class="section">
          <div class="section-title">◆ ${this.walletAddress ? 'Wallet Options' : 'Create Wallet'}</div>
          
          ${!this.walletAddress ? html`
            <div style="text-align: center; padding: 20px 0;">
              <button class="primary" @click=${this.generateWallet} ?disabled=${this.loading} style="font-size: 14px; padding: 16px 32px;">
                ${this.loading ? 'generating...' : '🔑 Generate New BASE Wallet'}
              </button>
              <div class="info-text" style="margin-top: 12px;">
                Creates a new wallet with private key. GLTCH will own this wallet.
              </div>
            </div>
            
            <div style="text-align: center; color: var(--text-muted); margin: 20px 0;">— or import existing —</div>
          ` : ''}

          ${this.hasPrivateKey && this.walletAddress ? html`
            <div class="button-row" style="margin-bottom: 16px;">
              <button @click=${this.exportPrivateKey}>🔐 show private key</button>
            </div>
          ` : ''}
          
          <div class="form-group">
            <label class="form-label">${this.walletAddress ? 'Import Different Wallet' : 'Import Existing Wallet (with Private Key)'}</label>
            <input 
              type="password"
              placeholder="Private key (0x...)"
              .value=${this.inputAddress}
              @input=${(e: Event) => this.inputAddress = (e.target as HTMLInputElement).value}
            />
            <div class="info-text" style="margin-top: 8px; font-size: 11px;">
              Enter your private key to give GLTCH full control of the wallet.
            </div>
          </div>

          <div class="button-row">
            <button @click=${this.importWallet} ?disabled=${this.loading}>
              ${this.loading ? 'importing...' : '🔑 import with private key'}
            </button>
          </div>

          <div class="info-box">
            <div class="info-title">ℹ️ About BASE Wallets</div>
            <div class="info-text">
              <a href="https://base.org" target="_blank">BASE</a> is Coinbase's L2 network built on Ethereum. 
              GLTCH can receive tips, payments, or hold tokens on BASE. 
              <br><br>
              <strong>Generate</strong>: Creates a new wallet GLTCH fully controls.<br>
              <strong>Import</strong>: Import your private key so GLTCH can sign transactions.
            </div>
          </div>
        </div>

        ${this.walletAddress ? html`
          <div class="section">
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
              <span>◆ Token Balances</span>
              <button style="padding: 6px 12px; font-size: 10px;" @click=${this.loadBalances} ?disabled=${this.loadingBalances}>
                ${this.loadingBalances ? '...' : '↻ refresh'}
              </button>
            </div>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-value" style="color: #627eea;">${(this.balances['ETH'] || 0).toFixed(6)}</div>
                <div class="stat-label">ETH</div>
              </div>
              <div class="stat-card">
                <div class="stat-value" style="color: var(--neon-magenta);">${(this.balances['XRGE'] || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
                <div class="stat-label">XRGE</div>
              </div>
              <div class="stat-card">
                <div class="stat-value" style="color: #2775ca;">${(this.balances['USDC'] || 0).toFixed(2)}</div>
                <div class="stat-label">USDC</div>
              </div>
              <div class="stat-card">
                <div class="stat-value" style="color: var(--neon-green);">${(this.balances['KTA'] || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
                <div class="stat-label">KTA</div>
              </div>
            </div>
          </div>

          ${this.hasPrivateKey ? html`
            <div class="section">
              <div class="section-title">◆ Send Tokens</div>
              <div class="form-group">
                <label class="form-label">Token</label>
                <select 
                  style="width: 100%; padding: 12px; background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 4px;"
                  .value=${this.sendToken}
                  @change=${(e: Event) => this.sendToken = (e.target as HTMLSelectElement).value}
                >
                  <option value="ETH">ETH</option>
                  <option value="XRGE">XRGE</option>
                  <option value="USDC">USDC</option>
                  <option value="KTA">KTA</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Recipient Address</label>
                <input 
                  type="text"
                  placeholder="0x..."
                  .value=${this.sendTo}
                  @input=${(e: Event) => this.sendTo = (e.target as HTMLInputElement).value}
                />
              </div>
              <div class="form-group">
                <label class="form-label">Amount</label>
                <input 
                  type="number"
                  step="0.000001"
                  placeholder="0.0"
                  .value=${this.sendAmount}
                  @input=${(e: Event) => this.sendAmount = (e.target as HTMLInputElement).value}
                />
              </div>
              <div class="button-row">
                <button class="primary" @click=${this.sendTokens} ?disabled=${this.sending}>
                  ${this.sending ? 'sending...' : `⚡ send ${this.sendToken}`}
                </button>
              </div>
            </div>
          ` : ''}
        ` : ''}
      </div>
    `;
  }
}
