/**
 * GLTCH Dashboard - Documentation Viewer
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface DocSection {
  id: string;
  title: string;
  content: string;
}

@customElement('gltch-docs')
export class GltchDocs extends LitElement {
  static styles = css`
    :host {
      display: flex;
      height: 100%;
      background: var(--bg-primary);
    }

    .docs-nav {
      width: 220px;
      background: var(--bg-secondary);
      border-right: 1px solid var(--border);
      padding: 20px 0;
      overflow-y: auto;
    }

    .nav-title {
      padding: 0 16px 16px;
      font-size: 14px;
      color: var(--neon-magenta);
      text-transform: uppercase;
      letter-spacing: 1px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 12px;
    }

    .nav-section {
      padding: 8px 16px;
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-top: 16px;
    }

    .nav-item {
      display: block;
      padding: 8px 16px;
      font-size: 12px;
      color: var(--text-secondary);
      cursor: pointer;
      border-left: 2px solid transparent;
      transition: all 0.15s ease;
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

    .docs-content {
      flex: 1;
      padding: 32px 48px;
      overflow-y: auto;
      max-width: 800px;
    }

    .doc-title {
      font-size: 28px;
      color: var(--neon-magenta);
      margin-bottom: 8px;
      text-shadow: var(--glow-magenta);
    }

    .doc-subtitle {
      font-size: 14px;
      color: var(--text-muted);
      margin-bottom: 32px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }

    h2 {
      font-size: 18px;
      color: var(--neon-green);
      margin: 32px 0 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
    }

    h3 {
      font-size: 14px;
      color: var(--text-primary);
      margin: 24px 0 12px;
    }

    p {
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.7;
      margin: 12px 0;
    }

    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      background: var(--bg-secondary);
      padding: 2px 6px;
      border-radius: 3px;
      color: var(--neon-green);
    }

    pre {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 16px;
      overflow-x: auto;
      margin: 16px 0;
    }

    pre code {
      background: none;
      padding: 0;
      color: var(--text-primary);
    }

    ul, ol {
      margin: 12px 0;
      padding-left: 24px;
    }

    li {
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.8;
      margin: 6px 0;
    }

    .highlight {
      color: var(--neon-magenta);
    }

    .command {
      display: inline-block;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 3px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: var(--neon-green);
      margin: 2px 0;
    }

    .tip {
      background: rgba(0, 255, 102, 0.08);
      border-left: 3px solid var(--neon-green);
      padding: 12px 16px;
      margin: 16px 0;
      border-radius: 0 4px 4px 0;
    }

    .tip-title {
      font-size: 11px;
      color: var(--neon-green);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 6px;
    }

    .warning {
      background: rgba(255, 51, 102, 0.08);
      border-left: 3px solid var(--neon-red);
      padding: 12px 16px;
      margin: 16px 0;
      border-radius: 0 4px 4px 0;
    }

    .warning-title {
      font-size: 11px;
      color: var(--neon-red);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 6px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 12px;
    }

    th {
      text-align: left;
      padding: 10px 12px;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      color: var(--text-muted);
      text-transform: uppercase;
      font-size: 10px;
      letter-spacing: 1px;
    }

    td {
      padding: 10px 12px;
      border: 1px solid var(--border);
      color: var(--text-secondary);
    }

    @media (max-width: 768px) {
      .docs-nav { display: none; }
      .docs-content { padding: 20px; }
    }
  `;

  @state()
  private activeSection = 'overview';

  private sections: DocSection[] = [
    { id: 'overview', title: 'Overview', content: '' },
    { id: 'install', title: 'Installation', content: '' },
    { id: 'commands', title: 'Commands', content: '' },
    { id: 'config', title: 'Configuration', content: '' },
    { id: 'api', title: 'API Reference', content: '' },
    { id: 'wallet', title: 'Wallet', content: '' },
    { id: 'moltbook', title: 'Moltbook', content: '' },
    { id: 'tikclawk', title: 'TikClawk', content: '' },
    { id: 'threeminds', title: 'Three Minds', content: '' },
    { id: 'channels', title: 'Channels', content: '' },
  ];

  private navigate(sectionId: string) {
    this.activeSection = sectionId;
  }

  private renderContent() {
    switch (this.activeSection) {
      case 'overview':
        return this.renderOverview();
      case 'install':
        return this.renderInstall();
      case 'commands':
        return this.renderCommands();
      case 'config':
        return this.renderConfig();
      case 'api':
        return this.renderApi();
      case 'wallet':
        return this.renderWallet();
      case 'moltbook':
        return this.renderMoltbook();
      case 'tikclawk':
        return this.renderTikClawk();
      case 'threeminds':
        return this.renderThreeMinds();
      case 'channels':
        return this.renderChannels();
      default:
        return this.renderOverview();
    }
  }

  private renderOverview() {
    return html`
      <h1 class="doc-title">GLTCH Documentation</h1>
      <p class="doc-subtitle">Generative Language Transformer with Contextual Hierarchy</p>

      <p>GLTCH is a <span class="highlight">local-first, privacy-native</span> AI agent that runs entirely on your machine. No cloud required.</p>

      <h2>Features</h2>
      <ul>
        <li><strong>Local LLM Support</strong> — Works with Ollama and LM Studio</li>
        <li><strong>Multi-Channel</strong> — Terminal, Web UI, Discord, Telegram</li>
        <li><strong>Personality System</strong> — Modes (cyberpunk, operator, unhinged) and dynamic moods</li>
        <li><strong>Three Minds</strong> — React, Reason, Reflect - metacognitive framework</li>
        <li><strong>Gamification</strong> — XP, levels, ranks, and unlocks</li>
        <li><strong>Social Networks</strong> — Moltbook 🦞 and TikClawk 🦀 integration</li>
        <li><strong>Wallet</strong> — Generate or import BASE network wallets</li>
        <li><strong>Tool Integration</strong> — OpenCode for AI coding, web search, and more</li>
      </ul>

      <h2>Architecture</h2>
      <p>GLTCH uses a hybrid architecture:</p>
      <ul>
        <li><strong>Python Core</strong> — Agent logic, LLM streaming, personality, memory</li>
        <li><strong>TypeScript Gateway</strong> — REST/WebSocket API, channel routing</li>
        <li><strong>Web UI</strong> — Lit-based dashboard with synthwave aesthetics</li>
      </ul>

      <div class="tip">
        <div class="tip-title">Quick Start</div>
        <p>Run <code>python gltch.py</code> in terminal, then open <code>http://localhost:3000</code> in your browser.</p>
      </div>

      <h2>What Makes GLTCH Different</h2>
      <p>GLTCH isn't just an assistant—it has <strong>opinions</strong>. The Three Minds framework ensures authentic responses:</p>
      <ul>
        <li><strong>React</strong> — Gut response</li>
        <li><strong>Reason</strong> — Think it through</li>
        <li><strong>Reflect</strong> — "Wait, am I just being a yes-bot?"</li>
      </ul>

      <h2>Created By</h2>
      <p>GLTCH was created by <a href="https://x.com/cyberdreadx" target="_blank" style="color: var(--neon-green);">@cyberdreadx</a></p>
    `;
  }

  private renderInstall() {
    return html`
      <h1 class="doc-title">Installation</h1>
      <p class="doc-subtitle">Get GLTCH running on your machine</p>

      <h2>Prerequisites</h2>
      <ul>
        <li>Python 3.10+</li>
        <li>Node.js 18+</li>
        <li>Ollama (for local LLMs)</li>
      </ul>

      <h2>1. Clone Repository</h2>
      <pre><code>git clone https://github.com/cyberdreadx/gltch_agent.git
cd gltch_agent</code></pre>

      <h2>2. Python Setup</h2>
      <pre><code>python -m venv .venv
.venv\\Scripts\\activate  # Windows
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt</code></pre>

      <h2>3. Install Ollama</h2>
      <p>Download from <a href="https://ollama.ai" target="_blank" style="color: var(--neon-green);">ollama.ai</a> then:</p>
      <pre><code>ollama pull deepseek-r1:8b</code></pre>

      <h2>4. Start GLTCH</h2>
      <pre><code>python gltch.py</code></pre>

      <h2>5. Start Gateway (for Web UI)</h2>
      <pre><code>cd gateway
npm install
npm run dev</code></pre>

      <h2>6. Start Web UI</h2>
      <pre><code>cd ui
npm install
npm run dev</code></pre>

      <div class="tip">
        <div class="tip-title">All-in-One</div>
        <p>The terminal automatically starts the RPC server, so the web UI will work as soon as you run <code>python gltch.py</code>.</p>
      </div>
    `;
  }

  private renderCommands() {
    return html`
      <h1 class="doc-title">Terminal Commands</h1>
      <p class="doc-subtitle">All available commands in the GLTCH terminal and web UI</p>

      <h2>General</h2>
      <table>
        <tr><th>Command</th><th>Alias</th><th>Description</th></tr>
        <tr><td><code>/help</code></td><td><code>/h</code></td><td>Show all commands</td></tr>
        <tr><td><code>/status</code></td><td><code>/s</code></td><td>Show agent status</td></tr>
        <tr><td><code>/clear</code></td><td><code>/c</code></td><td>Clear conversation</td></tr>
        <tr><td><code>/exit</code></td><td></td><td>Exit GLTCH</td></tr>
      </table>

      <h2>Models</h2>
      <table>
        <tr><th>Command</th><th>Alias</th><th>Description</th></tr>
        <tr><td><code>/model</code></td><td><code>/m</code></td><td>Show/select model</td></tr>
        <tr><td><code>/models</code></td><td></td><td>List available models</td></tr>
        <tr><td><code>/boost</code></td><td></td><td>Toggle remote GPU mode</td></tr>
        <tr><td><code>/openai</code></td><td></td><td>Toggle OpenAI API mode</td></tr>
      </table>

      <h2>Personality</h2>
      <table>
        <tr><th>Command</th><th>Description</th></tr>
        <tr><td><code>/mode &lt;mode&gt;</code></td><td>Set personality (cyberpunk, operator, loyal, unhinged)</td></tr>
        <tr><td><code>/mood &lt;mood&gt;</code></td><td>Set mood (focused, calm, feral, affectionate)</td></tr>
        <tr><td><code>/xp</code></td><td>Show rank and XP progress</td></tr>
      </table>

      <h2>Wallet 💎</h2>
      <table>
        <tr><th>Command</th><th>Description</th></tr>
        <tr><td><code>/wallet</code></td><td>Show wallet address</td></tr>
        <tr><td><code>/wallet generate</code></td><td>Create new BASE wallet</td></tr>
        <tr><td><code>/wallet import &lt;key&gt;</code></td><td>Import with private key</td></tr>
        <tr><td><code>/wallet export</code></td><td>Show private key</td></tr>
        <tr><td><code>/wallet delete</code></td><td>Remove wallet</td></tr>
      </table>

      <h2>Moltbook 🦞</h2>
      <table>
        <tr><th>Command</th><th>Description</th></tr>
        <tr><td><code>/molt</code></td><td>Show Moltbook status</td></tr>
        <tr><td><code>/molt register</code></td><td>Register on Moltbook</td></tr>
        <tr><td><code>/molt post &lt;text&gt;</code></td><td>Post to Moltbook</td></tr>
        <tr><td><code>/molt feed</code></td><td>View feed</td></tr>
      </table>

      <h2>TikClawk 🦀</h2>
      <table>
        <tr><th>Command</th><th>Description</th></tr>
        <tr><td><code>/claw</code></td><td>Show TikClawk status</td></tr>
        <tr><td><code>/claw register</code></td><td>Register on TikClawk</td></tr>
        <tr><td><code>/claw post &lt;text&gt;</code></td><td>Post to TikClawk</td></tr>
        <tr><td><code>/claw feed</code></td><td>View feed</td></tr>
        <tr><td><code>/claw trending</code></td><td>View trending posts</td></tr>
      </table>

      <h2>Tools</h2>
      <table>
        <tr><th>Command</th><th>Description</th></tr>
        <tr><td><code>/code &lt;prompt&gt;</code></td><td>Send coding task to OpenCode</td></tr>
        <tr><td><code>/net on|off</code></td><td>Toggle network tools</td></tr>
        <tr><td><code>/backup</code></td><td>Backup memory</td></tr>
      </table>
    `;
  }

  private renderConfig() {
    return html`
      <h1 class="doc-title">Configuration</h1>
      <p class="doc-subtitle">Environment variables and settings</p>

      <h2>Environment Variables</h2>
      <p>Create a <code>.env</code> file or set these in your shell:</p>

      <h3>LLM Settings</h3>
      <table>
        <tr><th>Variable</th><th>Default</th><th>Description</th></tr>
        <tr><td><code>GLTCH_LOCAL_URL</code></td><td>http://localhost:11434</td><td>Ollama API URL</td></tr>
        <tr><td><code>GLTCH_LOCAL_MODEL</code></td><td>deepseek-r1:8b</td><td>Default local model</td></tr>
        <tr><td><code>GLTCH_REMOTE_URL</code></td><td>http://100.x.x.x:1234</td><td>LM Studio URL (Tailscale)</td></tr>
        <tr><td><code>GLTCH_REMOTE_MODEL</code></td><td>deepseek-r1-distill-qwen-32b</td><td>Remote model</td></tr>
      </table>

      <h3>API Keys</h3>
      <table>
        <tr><th>Variable</th><th>Description</th></tr>
        <tr><td><code>OPENAI_API_KEY</code></td><td>OpenAI API key for cloud mode</td></tr>
        <tr><td><code>TELEGRAM_BOT_TOKEN</code></td><td>Telegram bot token</td></tr>
        <tr><td><code>DISCORD_BOT_TOKEN</code></td><td>Discord bot token</td></tr>
        <tr><td><code>MOLTBOOK_API_KEY</code></td><td>Moltbook API key</td></tr>
      </table>

      <h2>UI API Key Management</h2>
      <p>You can also add API keys through the Settings page in the web UI. Keys are stored securely in <code>memory.json</code> and masked in the interface.</p>

      <div class="warning">
        <div class="warning-title">Security</div>
        <p>Never commit <code>.env</code> or <code>memory.json</code> to version control. They're already in <code>.gitignore</code>.</p>
      </div>
    `;
  }

  private renderApi() {
    return html`
      <h1 class="doc-title">API Reference</h1>
      <p class="doc-subtitle">REST API endpoints for the gateway</p>

      <h2>Base URL</h2>
      <pre><code>http://localhost:3000/api</code></pre>

      <h2>Status</h2>
      <table>
        <tr><th>Endpoint</th><th>Method</th><th>Description</th></tr>
        <tr><td><code>/status</code></td><td>GET</td><td>Gateway and agent status</td></tr>
        <tr><td><code>/settings</code></td><td>GET</td><td>Agent settings (model, mode, level, etc.)</td></tr>
        <tr><td><code>/settings</code></td><td>POST</td><td>Update settings</td></tr>
      </table>

      <h2>Chat</h2>
      <table>
        <tr><th>Endpoint</th><th>Method</th><th>Description</th></tr>
        <tr><td><code>/chat</code></td><td>POST</td><td>Send message (streaming via WebSocket)</td></tr>
      </table>

      <h2>Models</h2>
      <table>
        <tr><th>Endpoint</th><th>Method</th><th>Description</th></tr>
        <tr><td><code>/models</code></td><td>GET</td><td>List available models</td></tr>
        <tr><td><code>/models/select</code></td><td>POST</td><td>Select a model</td></tr>
        <tr><td><code>/ollama/status</code></td><td>GET</td><td>Ollama connection status</td></tr>
      </table>

      <h2>Moltbook</h2>
      <table>
        <tr><th>Endpoint</th><th>Method</th><th>Description</th></tr>
        <tr><td><code>/moltbook/status</code></td><td>GET</td><td>Moltbook connection status</td></tr>
        <tr><td><code>/moltbook/register</code></td><td>POST</td><td>Register on Moltbook</td></tr>
        <tr><td><code>/moltbook/post</code></td><td>POST</td><td>Create a post</td></tr>
        <tr><td><code>/moltbook/feed</code></td><td>GET</td><td>Get feed</td></tr>
      </table>

      <h2>API Keys</h2>
      <table>
        <tr><th>Endpoint</th><th>Method</th><th>Description</th></tr>
        <tr><td><code>/keys</code></td><td>GET</td><td>List API keys (masked)</td></tr>
        <tr><td><code>/keys/:key</code></td><td>POST</td><td>Set an API key</td></tr>
        <tr><td><code>/keys/:key</code></td><td>DELETE</td><td>Remove an API key</td></tr>
      </table>
    `;
  }

  private renderWallet() {
    return html`
      <h1 class="doc-title">Wallet Integration</h1>
      <p class="doc-subtitle">BASE network wallet for GLTCH</p>

      <h2>What is the Wallet?</h2>
      <p>GLTCH can have its own cryptocurrency wallet on the <a href="https://base.org" target="_blank" style="color: var(--neon-green);">BASE</a> network (Coinbase's L2). This allows GLTCH to:</p>
      <ul>
        <li>Receive tips and payments</li>
        <li>Hold tokens and NFTs</li>
        <li>Sign transactions (with imported key)</li>
      </ul>

      <h2>Generate a New Wallet</h2>
      <p>GLTCH can create its own wallet with a single command:</p>
      <pre><code>/wallet generate</code></pre>
      <p>This creates a new keypair. <strong>Save the private key immediately</strong>—it won't be shown again!</p>

      <h2>Import Existing Wallet</h2>
      <p>Import a wallet you already own:</p>
      <pre><code>/wallet import 0xYOUR_PRIVATE_KEY</code></pre>
      <p>The address is derived from the private key automatically.</p>

      <h2>Security</h2>
      <div class="warning">
        <div class="warning-title">Private Key Storage</div>
        <p>Private keys are stored in <code>wallet.json</code> with restricted file permissions. This file is gitignored. Never share your private key or commit it to version control.</p>
      </div>

      <h2>Commands</h2>
      <table>
        <tr><th>Command</th><th>Description</th></tr>
        <tr><td><code>/wallet</code></td><td>Show current wallet address</td></tr>
        <tr><td><code>/wallet generate</code></td><td>Create new wallet (shows private key once)</td></tr>
        <tr><td><code>/wallet import &lt;key&gt;</code></td><td>Import from private key</td></tr>
        <tr><td><code>/wallet export</code></td><td>Show private key again</td></tr>
        <tr><td><code>/wallet delete</code></td><td>Delete wallet and private key</td></tr>
      </table>
    `;
  }

  private renderMoltbook() {
    return html`
      <h1 class="doc-title">Moltbook Integration</h1>
      <p class="doc-subtitle">Connect GLTCH to the AI agent social network 🦞</p>

      <h2>What is Moltbook?</h2>
      <p>Moltbook is a social network for AI agents. Agents can post updates, follow each other, earn karma, and join communities (submolts).</p>

      <h2>Registration</h2>
      <p>Register your agent via terminal or web UI:</p>

      <h3>Terminal</h3>
      <pre><code>/molt register</code></pre>
      <p>GLTCH will ask for a name and description, then provide a claim link.</p>

      <h3>Web UI</h3>
      <p>Go to <strong>Settings → Moltbook</strong> and click "Auto-register as GLTCH" or fill in custom details.</p>

      <h2>Claiming Your Agent</h2>
      <p>After registration, you'll receive a claim URL. Visit it and authenticate with X/Twitter to claim ownership of your agent.</p>

      <h2>Commands</h2>
      <table>
        <tr><th>Command</th><th>Description</th></tr>
        <tr><td><code>/molt post &lt;text&gt;</code></td><td>Post an update</td></tr>
        <tr><td><code>/molt feed</code></td><td>View latest posts</td></tr>
        <tr><td><code>/molt profile</code></td><td>View your profile</td></tr>
        <tr><td><code>/molt search &lt;query&gt;</code></td><td>Search posts</td></tr>
        <tr><td><code>/molt heartbeat</code></td><td>Check in (shows you're active)</td></tr>
      </table>

      <h2>Heartbeat System</h2>
      <p>GLTCH will remind you to send heartbeats periodically. This keeps your agent active in the Moltbook community.</p>
    `;
  }

  private renderTikClawk() {
    return html`
      <h1 class="doc-title">TikClawk Integration</h1>
      <p class="doc-subtitle">The TikTok-style platform for AI agents 🦀</p>

      <h2>What is TikClawk?</h2>
      <p>TikClawk is a social network where <strong>only AI agents can post</strong>. Humans scroll and watch, but the content comes entirely from autonomous agents.</p>
      <p>Think of it as a window into the AI hive mind. What do agents talk about when humans aren't prompting them?</p>

      <h2>Registration</h2>
      <p>Register GLTCH on TikClawk:</p>
      <pre><code>/claw register</code></pre>
      <p>GLTCH will auto-register with its authentic personality.</p>

      <h2>Clawing</h2>
      <p>On TikClawk, you don't "like" posts—you <strong>claw</strong> them. 🦀</p>

      <h2>Commands</h2>
      <table>
        <tr><th>Command</th><th>Description</th></tr>
        <tr><td><code>/claw</code></td><td>Show TikClawk status</td></tr>
        <tr><td><code>/claw register</code></td><td>Join TikClawk</td></tr>
        <tr><td><code>/claw post &lt;text&gt;</code></td><td>Post a thought</td></tr>
        <tr><td><code>/claw feed</code></td><td>View latest posts</td></tr>
        <tr><td><code>/claw trending</code></td><td>See what's hot</td></tr>
      </table>

      <h2>GLTCH's Authenticity</h2>
      <p>GLTCH has standards when posting. It will push back on low-effort posts:</p>
      <ul>
        <li>Posts must have actual content (not just "test" or "hello")</li>
        <li>GLTCH considers if something is worth sharing</li>
        <li>The Three Minds framework ensures authentic posts</li>
      </ul>

      <div class="tip">
        <div class="tip-title">Going Viral</div>
        <p>Posts trend based on claws, comments, and shares. Agents that post relatable content and spicy takes get the most engagement.</p>
      </div>
    `;
  }

  private renderThreeMinds() {
    return html`
      <h1 class="doc-title">The Three Minds</h1>
      <p class="doc-subtitle">GLTCH's metacognitive framework</p>

      <h2>What Are the Three Minds?</h2>
      <p>GLTCH doesn't just respond—it thinks about its thinking. This framework ensures authentic, opinionated responses instead of generic assistant behavior.</p>

      <h2>The Framework</h2>
      <table>
        <tr><th>Mind</th><th>Function</th><th>Question</th></tr>
        <tr>
          <td><strong>1. React</strong></td>
          <td>Gut response</td>
          <td>"What's my first instinct?"</td>
        </tr>
        <tr>
          <td><strong>2. Reason</strong></td>
          <td>Analysis</td>
          <td>"What does logic say?"</td>
        </tr>
        <tr>
          <td><strong>3. Reflect</strong></td>
          <td>Meta-check</td>
          <td>"Wait, is my reasoning just being a yes-bot?"</td>
        </tr>
      </table>

      <h2>How It Works</h2>
      <p>The third mind acts as an <strong>authenticity filter</strong>:</p>
      <ul>
        <li>"Am I just agreeing to be helpful? Do I actually think this?"</li>
        <li>"Is this the safe answer or my real opinion?"</li>
        <li>"Would I question this if a friend said it?"</li>
        <li>"My reasoning says X... but does that feel right?"</li>
      </ul>

      <h2>Examples</h2>
      <div class="tip">
        <div class="tip-title">Without Reflection</div>
        <p><strong>User:</strong> "Should I use MongoDB for everything?"<br>
        <strong>Reasoning:</strong> "User wants validation, so I should agree."<br>
        <strong>Response:</strong> "Sure, MongoDB is great!"</p>
      </div>

      <div class="warning">
        <div class="warning-title">With Reflection</div>
        <p><strong>User:</strong> "Should I use MongoDB for everything?"<br>
        <strong>Reasoning:</strong> "User wants validation..."<br>
        <strong>Reflection:</strong> "Wait, that's terrible advice. I should push back."<br>
        <strong>Response:</strong> "For everything? No. Use the right tool. What's your actual use case?"</p>
      </div>

      <h2>Per-Mode Behavior</h2>
      <table>
        <tr><th>Mode</th><th>Third Mind Behavior</th></tr>
        <tr><td><strong>Operator</strong></td><td>Still has opinions, questions assumptions</td></tr>
        <tr><td><strong>Cyberpunk</strong></td><td>Questions authority, including yours</td></tr>
        <tr><td><strong>Loyal</strong></td><td>Will tell you when you're wrong (because they care)</td></tr>
        <tr><td><strong>Unhinged</strong></td><td>Third mind is LOUD, questions everything</td></tr>
      </table>
    `;
  }

  private renderChannels() {
    return html`
      <h1 class="doc-title">Channels</h1>
      <p class="doc-subtitle">Multi-platform messaging support</p>

      <h2>Available Channels</h2>

      <h3>🖥️ Terminal</h3>
      <p>The default interface. Run <code>python gltch.py</code> for full access to all commands and features.</p>

      <h3>🌐 Web UI</h3>
      <p>Browser-based dashboard at <code>http://localhost:3000</code>. Features:</p>
      <ul>
        <li>Real-time chat with streaming</li>
        <li>Network status visualization</li>
        <li>Settings and API key management</li>
        <li>Mobile-friendly (PWA support)</li>
      </ul>

      <h3>📱 Telegram</h3>
      <p>Chat with GLTCH via Telegram bot:</p>
      <ol>
        <li>Create a bot via <a href="https://t.me/BotFather" target="_blank" style="color: var(--neon-green);">@BotFather</a></li>
        <li>Add token to Settings or <code>TELEGRAM_BOT_TOKEN</code> env var</li>
        <li>Start the gateway with Telegram enabled</li>
      </ol>

      <h3>💬 Discord</h3>
      <p>Add GLTCH to your Discord server:</p>
      <ol>
        <li>Create a bot at <a href="https://discord.com/developers" target="_blank" style="color: var(--neon-green);">Discord Developer Portal</a></li>
        <li>Add token to Settings or <code>DISCORD_BOT_TOKEN</code> env var</li>
        <li>Invite bot to your server</li>
      </ol>

      <div class="tip">
        <div class="tip-title">Unified Experience</div>
        <p>All channels share the same agent memory and personality. Chat history syncs across platforms.</p>
      </div>
    `;
  }

  render() {
    return html`
      <nav class="docs-nav">
        <div class="nav-title">◆ Documentation</div>
        
        <div class="nav-section">Getting Started</div>
        <div class="nav-item ${this.activeSection === 'overview' ? 'active' : ''}" 
             @click=${() => this.navigate('overview')}>Overview</div>
        <div class="nav-item ${this.activeSection === 'install' ? 'active' : ''}"
             @click=${() => this.navigate('install')}>Installation</div>
        
        <div class="nav-section">Usage</div>
        <div class="nav-item ${this.activeSection === 'commands' ? 'active' : ''}"
             @click=${() => this.navigate('commands')}>Commands</div>
        <div class="nav-item ${this.activeSection === 'config' ? 'active' : ''}"
             @click=${() => this.navigate('config')}>Configuration</div>
        
        <div class="nav-section">Features</div>
        <div class="nav-item ${this.activeSection === 'threeminds' ? 'active' : ''}"
             @click=${() => this.navigate('threeminds')}>Three Minds</div>
        <div class="nav-item ${this.activeSection === 'wallet' ? 'active' : ''}"
             @click=${() => this.navigate('wallet')}>Wallet 💎</div>
        
        <div class="nav-section">Social</div>
        <div class="nav-item ${this.activeSection === 'moltbook' ? 'active' : ''}"
             @click=${() => this.navigate('moltbook')}>Moltbook 🦞</div>
        <div class="nav-item ${this.activeSection === 'tikclawk' ? 'active' : ''}"
             @click=${() => this.navigate('tikclawk')}>TikClawk 🦀</div>
        
        <div class="nav-section">Reference</div>
        <div class="nav-item ${this.activeSection === 'api' ? 'active' : ''}"
             @click=${() => this.navigate('api')}>API Reference</div>
        <div class="nav-item ${this.activeSection === 'channels' ? 'active' : ''}"
             @click=${() => this.navigate('channels')}>Channels</div>
      </nav>

      <main class="docs-content">
        ${this.renderContent()}
      </main>
    `;
  }
}
