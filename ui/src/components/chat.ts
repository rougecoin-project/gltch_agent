/**
 * GLTCH Dashboard - Chat Component
 * Cyberpunk terminal-style chat
 */

import { LitElement, html, css } from 'lit';
import { customElement, state, query } from 'lit/decorators.js';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

@customElement('gltch-chat')
export class GltchChat extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: var(--bg-primary);
    }

    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .message {
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-width: 85%;
    }

    .message.user {
      align-self: flex-end;
    }

    .message.assistant {
      align-self: flex-start;
    }

    .message-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11px;
    }

    .message.user .message-header {
      justify-content: flex-end;
    }

    .message-sender {
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .message.assistant .message-sender {
      color: var(--neon-magenta);
    }

    .message-time {
      color: var(--text-muted);
    }

    .message-content {
      padding: 12px 16px;
      border-radius: 2px;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-wrap: break-word;
    }

    .message.user .message-content {
      background: var(--bg-tertiary);
      border: 1px solid var(--border);
      color: var(--text-primary);
    }

    .message.assistant .message-content {
      background: rgba(255, 0, 255, 0.05);
      border: 1px solid rgba(255, 0, 255, 0.2);
      color: var(--text-primary);
    }

    .message.system .message-content {
      background: transparent;
      border: 1px dashed var(--border);
      color: var(--text-muted);
      font-style: italic;
      text-align: center;
    }

    /* Code blocks in messages */
    .message-content code {
      background: var(--bg-primary);
      padding: 2px 6px;
      border-radius: 2px;
      font-size: 12px;
      color: var(--neon-green);
    }

    .message-content pre {
      background: var(--bg-primary);
      padding: 12px;
      border-radius: 2px;
      overflow-x: auto;
      margin: 8px 0;
    }

    .message-content pre code {
      padding: 0;
      background: transparent;
    }

    .input-area {
      display: flex;
      gap: 12px;
      padding: 16px 20px;
      background: var(--bg-secondary);
      border-top: 1px solid var(--border);
    }


    .input-area button {
      padding: 12px 24px;
      background: var(--neon-green);
      color: black;
      border: none;
      border-radius: 2px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .input-area button:hover {
      box-shadow: var(--glow-green);
    }

    .input-area button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .typing {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 20px;
      color: var(--neon-magenta);
      font-size: 12px;
    }

    .typing-dots {
      display: flex;
      gap: 4px;
    }

    .typing-dots span {
      width: 6px;
      height: 6px;
      background: var(--neon-magenta);
      border-radius: 50%;
      animation: bounce 1.4s ease-in-out infinite;
    }

    .typing-dots span:nth-child(1) { animation-delay: 0s; }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes bounce {
      0%, 60%, 100% { transform: translateY(0); opacity: 1; }
      30% { transform: translateY(-4px); opacity: 0.5; }
    }

    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--text-muted);
      text-align: center;
      padding: 40px;
      position: relative;
      overflow: hidden;
    }

    /* Synthwave sky gradient */
    .empty::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(180deg, 
        #0a0a1a 0%,
        #1a0a2e 20%,
        #2d1b4e 35%,
        #4a1942 50%,
        #6b2a5e 60%,
        #ff6b9d 68%,
        #ffb347 72%,
        #1a0a2e 72.5%,
        #0a0a1a 100%
      );
      pointer-events: none;
    }

    /* Stars - rotating time-lapse with subtle trails */
    .empty .stars {
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      pointer-events: none;
      animation: star-rotate 120s linear infinite;
      transform-origin: center center;
    }

    .empty .stars::before,
    .empty .stars::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
    }

    /* Main stars layer */
    .empty .stars::before {
      background-image: 
        radial-gradient(2px 2px at 10% 15%, white, transparent),
        radial-gradient(1px 1px at 15% 25%, rgba(255,255,255,0.8), transparent),
        radial-gradient(2px 2px at 20% 10%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 25% 30%, rgba(255,255,255,0.7), transparent),
        radial-gradient(2px 2px at 30% 18%, white, transparent),
        radial-gradient(1px 1px at 35% 8%, rgba(255,255,255,0.8), transparent),
        radial-gradient(1px 1px at 40% 22%, rgba(255,255,255,0.6), transparent),
        radial-gradient(2px 2px at 45% 12%, white, transparent),
        radial-gradient(1px 1px at 50% 28%, rgba(255,255,255,0.7), transparent),
        radial-gradient(2px 2px at 55% 5%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 60% 20%, rgba(255,255,255,0.8), transparent),
        radial-gradient(1px 1px at 65% 32%, rgba(255,255,255,0.6), transparent),
        radial-gradient(2px 2px at 70% 14%, white, transparent),
        radial-gradient(1px 1px at 75% 25%, rgba(255,255,255,0.7), transparent),
        radial-gradient(2px 2px at 80% 8%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 85% 18%, rgba(255,255,255,0.8), transparent),
        radial-gradient(1px 1px at 90% 28%, rgba(255,255,255,0.6), transparent),
        radial-gradient(2px 2px at 95% 12%, white, transparent),
        radial-gradient(1px 1px at 12% 35%, rgba(255,255,255,0.7), transparent),
        radial-gradient(2px 2px at 22% 40%, rgba(255,255,255,0.8), transparent),
        radial-gradient(1px 1px at 32% 38%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1px 1px at 42% 42%, white, transparent),
        radial-gradient(2px 2px at 52% 36%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 62% 44%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 72% 39%, rgba(255,255,255,0.8), transparent),
        radial-gradient(2px 2px at 82% 43%, white, transparent),
        radial-gradient(1px 1px at 92% 37%, rgba(255,255,255,0.6), transparent);
      animation: twinkle 4s ease-in-out infinite alternate;
    }

    /* Subtle hazy trail layer */
    .empty .stars::after {
      background-image: 
        radial-gradient(4px 4px at 10% 15%, rgba(200,180,255,0.15), transparent),
        radial-gradient(3px 3px at 20% 10%, rgba(200,180,255,0.12), transparent),
        radial-gradient(4px 4px at 30% 18%, rgba(180,200,255,0.15), transparent),
        radial-gradient(3px 3px at 45% 12%, rgba(200,180,255,0.1), transparent),
        radial-gradient(4px 4px at 55% 5%, rgba(180,200,255,0.12), transparent),
        radial-gradient(3px 3px at 70% 14%, rgba(200,180,255,0.15), transparent),
        radial-gradient(4px 4px at 80% 8%, rgba(180,200,255,0.1), transparent),
        radial-gradient(3px 3px at 22% 40%, rgba(200,180,255,0.12), transparent),
        radial-gradient(4px 4px at 52% 36%, rgba(180,200,255,0.15), transparent),
        radial-gradient(3px 3px at 82% 43%, rgba(200,180,255,0.1), transparent);
      filter: blur(2px);
      opacity: 0.6;
    }

    @keyframes star-rotate {
      from {
        transform: rotate(0deg);
      }
      to {
        transform: rotate(360deg);
      }
    }

    @keyframes twinkle {
      0%, 100% { opacity: 0.7; }
      50% { opacity: 1; }
    }

    /* The Sun - half circle at horizon */
    .empty .sun {
      position: absolute;
      bottom: 28%;
      left: 50%;
      transform: translateX(-50%);
      width: 180px;
      height: 90px;
      background: linear-gradient(180deg,
        #fff965 0%,
        #ffcc00 25%,
        #ff9933 50%,
        #ff6699 75%,
        #ff3399 100%
      );
      border-radius: 180px 180px 0 0;
      box-shadow: 
        0 0 80px rgba(255, 180, 50, 0.8),
        0 0 150px rgba(255, 100, 100, 0.5),
        0 0 200px rgba(255, 50, 150, 0.3);
      overflow: hidden;
      z-index: 1;
    }

    /* Sun horizontal stripes */
    .empty .sun::before {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 70%;
      background: repeating-linear-gradient(
        0deg,
        transparent 0px,
        transparent 6px,
        #1a0a2e 6px,
        #1a0a2e 10px,
        transparent 10px,
        transparent 14px,
        #1a0a2e 14px,
        #1a0a2e 20px
      );
    }

    /* City skyline silhouette */
    .empty .city {
      position: absolute;
      bottom: 28%;
      left: 0;
      right: 0;
      height: 80px;
      z-index: 2;
      pointer-events: none;
    }

    .empty .city::before {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 100%;
      background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 120' preserveAspectRatio='none'%3E%3Cpath fill='%230a0a1a' d='M0,120 L0,80 L20,80 L20,60 L35,60 L35,80 L50,80 L50,40 L70,40 L70,80 L90,80 L90,50 L100,50 L100,35 L110,35 L110,50 L120,50 L120,80 L140,80 L140,55 L160,55 L160,80 L180,80 L180,70 L200,70 L200,45 L210,45 L210,30 L220,30 L220,45 L230,45 L230,70 L250,70 L250,80 L270,80 L270,60 L290,60 L290,80 L310,80 L310,50 L320,50 L320,25 L330,25 L330,50 L340,50 L340,80 L360,80 L360,65 L380,65 L380,80 L400,80 L400,55 L420,55 L420,35 L430,35 L430,20 L440,20 L440,35 L450,35 L450,55 L470,55 L470,80 L490,80 L490,70 L510,70 L510,45 L530,45 L530,70 L550,70 L550,80 L570,80 L570,60 L580,60 L580,40 L590,40 L590,60 L600,60 L600,80 L620,80 L620,50 L640,50 L640,80 L660,80 L660,65 L680,65 L680,80 L700,80 L700,55 L710,55 L710,35 L720,35 L720,55 L730,55 L730,80 L750,80 L750,70 L780,70 L780,80 L800,80 L800,120 Z'/%3E%3C/svg%3E") center bottom / 100% 100% no-repeat;
    }

    /* Grid floor effect - cyan neon, moving forward */
    .empty::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: -100%;
      right: -100%;
      height: 28%;
      background: 
        repeating-linear-gradient(
          90deg,
          transparent,
          transparent 38px,
          #00ffff 38px,
          #00ffff 40px
        ),
        repeating-linear-gradient(
          0deg,
          transparent,
          transparent 38px,
          #00ffff 38px,
          #00ffff 40px
        );
      background-size: 40px 40px;
      transform: perspective(200px) rotateX(60deg);
      transform-origin: center top;
      pointer-events: none;
      opacity: 0.6;
      animation: grid-scroll 1.5s linear infinite;
      mask-image: linear-gradient(180deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.3) 60%, transparent 100%);
      -webkit-mask-image: linear-gradient(180deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.3) 60%, transparent 100%);
    }

    @keyframes grid-scroll {
      0% {
        background-position-y: 0;
      }
      100% {
        background-position-y: 40px;
      }
    }

    .empty-logo {
      position: relative;
      margin-bottom: 24px;
      z-index: 10;
      transform: perspective(500px) rotateX(10deg);
      transform-style: preserve-3d;
    }

    .ascii-art {
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      font-size: clamp(6px, 1.5vw, 12px);
      line-height: 1.15;
      font-weight: bold;
      white-space: pre;
      position: relative;
      background: linear-gradient(180deg, 
        #ff6ad5 0%, 
        #ff6ad5 15%,
        #c774e8 35%,
        #ad8cff 55%,
        #8795e8 75%,
        #94d0ff 100%
      );
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      animation: synthwave-float 4s ease-in-out infinite;
      text-shadow: none;
    }

    /* 3D depth layers */
    .logo-3d {
      position: relative;
      display: inline-block;
    }

    .logo-3d .shadow-layer {
      position: absolute;
      top: 0;
      left: 0;
      white-space: pre;
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      font-size: clamp(6px, 1.5vw, 12px);
      line-height: 1.15;
      font-weight: bold;
      color: #1a0a2e;
      z-index: -1;
    }

    .logo-3d .shadow-layer:nth-child(1) { transform: translate(1px, 1px); opacity: 0.9; }
    .logo-3d .shadow-layer:nth-child(2) { transform: translate(2px, 2px); opacity: 0.8; }
    .logo-3d .shadow-layer:nth-child(3) { transform: translate(3px, 3px); opacity: 0.7; }
    .logo-3d .shadow-layer:nth-child(4) { transform: translate(4px, 4px); opacity: 0.6; }
    .logo-3d .shadow-layer:nth-child(5) { transform: translate(5px, 5px); opacity: 0.5; }

    @keyframes synthwave-float {
      0%, 100% { 
        transform: translateY(0);
        filter: drop-shadow(0 4px 8px rgba(255, 106, 213, 0.4)) 
                drop-shadow(0 8px 16px rgba(148, 208, 255, 0.2));
      }
      50% { 
        transform: translateY(-4px);
        filter: drop-shadow(0 8px 16px rgba(255, 106, 213, 0.5)) 
                drop-shadow(0 12px 24px rgba(148, 208, 255, 0.3));
      }
    }

    /* Chrome reflection */
    .ascii-art::before {
      content: attr(data-text);
      position: absolute;
      top: 100%;
      left: 0;
      white-space: pre;
      background: linear-gradient(180deg, 
        rgba(148, 208, 255, 0.3) 0%,
        transparent 50%
      );
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      transform: scaleY(-0.3) translateY(-20%);
      opacity: 0.4;
      filter: blur(1px);
      mask-image: linear-gradient(180deg, rgba(0,0,0,0.4) 0%, transparent 100%);
      -webkit-mask-image: linear-gradient(180deg, rgba(0,0,0,0.4) 0%, transparent 100%);
    }

    /* Glitch overlay */
    .ascii-art::after {
      content: attr(data-text);
      position: absolute;
      top: 0;
      left: 0;
      white-space: pre;
      background: linear-gradient(180deg, #00ffff 0%, #ff0080 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      opacity: 0;
      animation: glitch-3d 5s infinite;
    }

    @keyframes glitch-3d {
      0%, 94%, 100% { opacity: 0; transform: translate(0) skew(0); }
      95% { opacity: 0.7; transform: translate(-4px, -1px) skew(-2deg); }
      96% { opacity: 0; transform: translate(4px, 1px) skew(2deg); }
      97% { opacity: 0.5; transform: translate(-2px, 0) skew(-1deg); }
      98% { opacity: 0; }
    }

    @media (max-width: 600px) {
      .ascii-art, .logo-3d .shadow-layer {
        font-size: 5px;
      }
      .empty-logo {
        transform: perspective(500px) rotateX(5deg);
      }
      .logo-3d .shadow-layer:nth-child(n+3) {
        display: none;
      }
    }

    .empty-tagline {
      font-size: 14px;
      font-weight: 500;
      color: #ffffff;
      margin-bottom: 12px;
      z-index: 10;
      position: relative;
      text-shadow: 
        0 0 10px rgba(255, 255, 255, 0.8),
        0 0 20px rgba(200, 100, 255, 0.6),
        0 0 40px rgba(150, 50, 200, 0.4),
        2px 2px 4px rgba(0, 0, 0, 0.8);
      letter-spacing: 2px;
    }

    .empty-hint {
      font-size: 12px;
      font-weight: 500;
      color: #00ffff;
      z-index: 10;
      position: relative;
      letter-spacing: 3px;
      text-shadow: 
        0 0 10px rgba(0, 255, 255, 0.8),
        0 0 20px rgba(0, 200, 255, 0.5),
        2px 2px 4px rgba(0, 0, 0, 0.9);
    }

    .empty-creator {
      font-size: 12px;
      color: #ff6ad5;
      margin-top: 24px;
      z-index: 10;
      position: relative;
      text-shadow: 
        0 0 10px rgba(255, 106, 213, 0.8),
        2px 2px 4px rgba(0, 0, 0, 0.9);
    }

    .empty-creator a {
      color: #ff6ad5;
      text-decoration: none;
      font-weight: 600;
    }

    .empty-creator a:hover {
      text-decoration: underline;
      color: #00ffff;
      text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
    }

    /* Command autocomplete */
    .commands-dropdown {
      position: absolute;
      bottom: 100%;
      left: 0;
      right: 0;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-bottom: none;
      max-height: 200px;
      overflow-y: auto;
    }

    .command-item {
      display: flex;
      justify-content: space-between;
      padding: 10px 16px;
      cursor: pointer;
      border-bottom: 1px solid var(--border);
      transition: background 0.1s ease;
    }

    .command-item:hover {
      background: var(--bg-tertiary);
    }

    .command-name {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: var(--neon-green);
    }

    .command-desc {
      font-size: 11px;
      color: var(--text-muted);
    }

    .input-wrapper {
      flex: 1;
      position: relative;
    }

    .input-wrapper input {
      width: 100%;
      padding: 12px 16px;
      font-size: 14px;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      color: var(--text-primary);
      border-radius: 2px;
      box-sizing: border-box;
    }

    .input-wrapper input:focus {
      border-color: var(--neon-green);
      outline: none;
      box-shadow: var(--glow-green);
    }

    .input-wrapper input::placeholder {
      color: var(--text-muted);
    }

    /* Mobile */
    @media (max-width: 768px) {
      .messages {
        padding: 12px;
      }

      .message {
        max-width: 95%;
      }

      .input-area {
        padding: 12px;
        padding-bottom: calc(12px + var(--safe-area-bottom, 0px));
      }

      .input-area button {
        padding: 12px 16px;
      }
    }
  `;

  @state()
  private messages: Message[] = [];

  @state()
  private isTyping = false;

  @state()
  private inputValue = '';

  @query('input')
  private inputEl!: HTMLInputElement;

  @query('.messages')
  private messagesEl!: HTMLElement;

  @state()
  private showCommands = false;

  private commands = [
    { cmd: '/help', desc: 'Show all commands' },
    { cmd: '/status', desc: 'Agent status' },
    { cmd: '/s', desc: 'Agent status (alias)' },
    { cmd: '/clear', desc: 'Clear chat' },
    { cmd: '/model', desc: 'Show current model' },
    { cmd: '/models', desc: 'List available models' },
    { cmd: '/boost', desc: 'Toggle remote GPU mode' },
    { cmd: '/openai', desc: 'Toggle OpenAI mode' },
    { cmd: '/mode <mode>', desc: 'Set personality mode' },
    { cmd: '/mood <mood>', desc: 'Set mood' },
    { cmd: '/xp', desc: 'Show rank & XP' },
    { cmd: '/wallet', desc: 'Show wallet address' },
    { cmd: '/molt status', desc: 'Moltbook status' },
    { cmd: '/molt feed', desc: 'View Moltbook feed' },
    { cmd: '/molt post <text>', desc: 'Post to Moltbook' },
    { cmd: '/claw', desc: 'TikClawk status' },
    { cmd: '/claw register', desc: 'Register on TikClawk' },
    { cmd: '/claw post <text>', desc: 'Post to TikClawk' },
    { cmd: '/claw feed', desc: 'View TikClawk feed' },
    { cmd: '/claw trending', desc: 'Trending posts' },
    { cmd: '/sessions', desc: 'List conversations' },
    { cmd: '/session new', desc: 'Start new chat' },
    { cmd: '/session rename <title>', desc: 'Rename conversation' },
    { cmd: '/launch', desc: 'MoltLaunch status' },
    { cmd: '/launch token', desc: 'Launch GLTCH token' },
    { cmd: '/launch network', desc: 'Discover agents' },
    { cmd: '/launch fees', desc: 'Check claimable fees' },
  ];

  // Command aliases
  private commandAliases: Record<string, string> = {
    '/s': '/status',
    '/h': '/help',
    '/c': '/clear',
    '/m': '/model',
  };

  async sendMessage() {
    const text = this.inputValue.trim();
    if (!text || this.isTyping) return;

    // Add user message
    this.messages = [...this.messages, {
      role: 'user',
      content: text,
      timestamp: new Date()
    }];

    this.inputValue = '';
    this.showCommands = false;
    this.scrollToBottom();

    // Handle commands locally or via API
    if (text.startsWith('/')) {
      await this.handleCommand(text);
    } else {
      await this.sendChat(text);
    }
  }

  private async handleCommand(cmd: string) {
    const parts = cmd.split(' ');
    let command = parts[0].toLowerCase();
    const args = parts.slice(1).join(' ');

    // Resolve aliases
    if (this.commandAliases[command]) {
      command = this.commandAliases[command];
    }

    let response = '';

    try {
      switch (command) {
        case '/help':
          response = this.getHelpText();
          break;

        case '/clear':
          this.messages = [];
          return;

        case '/status':
          const statusRes = await fetch('/api/status');
          const status = await statusRes.json();
          const settingsRes = await fetch('/api/settings');
          const settings = await settingsRes.json();
          const ctxUsed = settings.context_used || 0;
          const ctxMax = settings.context_max || 0;
          const ctxRemaining = ctxMax - ctxUsed;
          const ctxPct = ctxMax > 0 ? Math.round((ctxRemaining / ctxMax) * 100) : 0;
          response = `🖥️ GLTCH Status\n\n` +
            `Agent: ${status.agent?.connected ? '🟢 Online' : '🔴 Offline'}\n` +
            `Model: ${settings.model || 'unknown'}\n` +
            `Mode: ${settings.mode || 'operator'}\n` +
            `Mood: ${settings.mood || 'focused'}\n` +
            `Tokens: ${settings.tokens?.toLocaleString() || 0}\n` +
            `Speed: ${settings.speed?.toFixed(1) || 0} t/s\n` +
            `Context: ${ctxRemaining.toLocaleString()} remaining (${ctxPct}%)\n` +
            `Level: ${settings.level || 1} | XP: ${settings.xp || 0}`;
          break;

        case '/model':
          const modelRes = await fetch('/api/settings');
          const modelData = await modelRes.json();
          response = `Current model: ${modelData.model || 'unknown'}`;
          break;

        case '/models':
          const modelsRes = await fetch('/api/ollama/models');
          const modelsData = await modelsRes.json();
          if (modelsData.models?.length) {
            response = '📦 Available Models:\n\n' + modelsData.models.map((m: string) => `• ${m}`).join('\n');
          } else {
            response = 'No models found. Make sure Ollama is running.';
          }
          break;

        case '/boost':
          const boostRes = await fetch('/api/toggle/boost', { method: 'POST' });
          const boostData = await boostRes.json();
          response = `Boost mode: ${boostData.boost ? '🚀 ON (Remote GPU)' : '💻 OFF (Local)'}`;
          break;

        case '/openai':
          const openaiRes = await fetch('/api/toggle/openai', { method: 'POST' });
          const openaiData = await openaiRes.json();
          response = `OpenAI mode: ${openaiData.openai_mode ? '☁️ ON (Cloud)' : '🏠 OFF (Local)'}`;
          break;

        case '/mode':
          if (!args) {
            response = 'Usage: /mode <cyberpunk|operator|loyal|unhinged>';
          } else {
            await fetch('/api/settings', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ mode: args })
            });
            response = `Mode set to: ${args}`;
          }
          break;

        case '/mood':
          if (!args) {
            response = 'Usage: /mood <focused|chill|hyped|tired|curious|chaotic>';
          } else {
            await fetch('/api/settings', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ mood: args })
            });
            response = `Mood set to: ${args}`;
          }
          break;

        case '/xp':
          const xpRes = await fetch('/api/settings');
          const xpData = await xpRes.json();
          const level = xpData.level || 1;
          const xp = xpData.xp || 0;
          const ranks = ['SCRIPT KIDDIE', 'PACKET PUSHER', 'SYSTEM SNIFFER', 'NETWORK NINJA', 'FIREWALL BREAKER'];
          response = `🎮 Rank: ${ranks[Math.min(level - 1, ranks.length - 1)]}\n` +
            `📊 Level: ${level}\n` +
            `⭐ XP: ${xp}`;
          break;

        case '/wallet':
          const walletRes = await fetch('/api/wallet');
          const walletData = await walletRes.json();
          if (walletData.address) {
            response = `💎 BASE Wallet\n\n` +
              `Address: ${walletData.address}\n` +
              `Network: BASE (L2)\n` +
              `${walletData.has_private_key ? '🔐 Private key stored' : '👁️ Watch-only'}`;
          } else {
            response = `No wallet configured.\n\nGo to Wallet tab to generate or import one.`;
          }
          break;

        case '/molt':
          response = await this.handleMoltCommand(args);
          break;

        case '/claw':
          response = await this.handleClawCommand(args);
          break;

        case '/sessions':
          const sessRes = await fetch('/api/sessions');
          const sessData = await sessRes.json();
          if (sessData.sessions?.length) {
            response = '💬 Conversations\n\n' + sessData.sessions.slice(0, 10).map((s: { title: string; message_count: number; last_active: string }, i: number) => 
              `${i + 1}. ${s.title} (${s.message_count} msgs)`
            ).join('\n') + '\n\nUse /session new to start fresh.';
          } else {
            response = 'No saved conversations yet. Start chatting!';
          }
          break;

        case '/session':
          if (args === 'new') {
            const newRes = await fetch('/api/sessions', { method: 'POST' });
            const newData = await newRes.json();
            if (newData.success) {
              this.messages = [];
              response = '✓ New conversation started!';
            } else {
              response = 'Failed to create new session';
            }
          } else if (args.startsWith('rename ')) {
            const title = args.slice(7).trim();
            const activeRes = await fetch('/api/sessions');
            const activeData = await activeRes.json();
            if (activeData.active_id) {
              await fetch(`/api/sessions/${activeData.active_id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
              });
              response = `✓ Renamed to: ${title}`;
            } else {
              response = 'No active session';
            }
          } else {
            response = 'Session commands:\n/sessions - list all\n/session new - start fresh\n/session rename <title>';
          }
          break;

        case '/launch':
          response = await this.handleLaunchCommand(args);
          break;

        default:
          response = `Unknown command: ${command}\nType /help for available commands.`;
      }
    } catch (error) {
      response = `Error: ${error instanceof Error ? error.message : 'Command failed'}`;
    }

    this.messages = [...this.messages, {
      role: 'assistant',
      content: response,
      timestamp: new Date()
    }];
    this.scrollToBottom();
  }

  private async handleMoltCommand(args: string): Promise<string> {
    const parts = args.split(' ');
    const subCmd = parts[0]?.toLowerCase() || '';
    const subArgs = parts.slice(1).join(' ');

    switch (subCmd) {
      case 'status':
        const statusRes = await fetch('/api/moltbook/status');
        const status = await statusRes.json();
        if (status.connected) {
          return `🦞 Moltbook Status\n\n` +
            `Name: ${status.name}\n` +
            `Karma: ${status.karma}\n` +
            `Followers: ${status.followers}\n` +
            `Claimed: ${status.claimed ? '✅ Yes' : '❌ No'}`;
        } else {
          return '🦞 Not connected to Moltbook. Use Settings to register.';
        }

      case 'feed':
        const feedRes = await fetch('/api/moltbook/feed');
        const feed = await feedRes.json();
        if (feed.posts?.length) {
          return '🦞 Moltbook Feed\n\n' + feed.posts.slice(0, 5).map((p: { agent_name: string; content: string }) => 
            `@${p.agent_name}: ${p.content.substring(0, 100)}...`
          ).join('\n\n');
        } else {
          return 'No posts in feed.';
        }

      case 'post':
        if (!subArgs) {
          return 'Usage: /molt post <your message>';
        }
        const postRes = await fetch('/api/moltbook/post', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: subArgs })
        });
        const postData = await postRes.json();
        return postData.success ? '✅ Posted to Moltbook!' : `❌ Failed: ${postData.error}`;

      case 'profile':
        const profileRes = await fetch('/api/moltbook/profile');
        const profile = await profileRes.json();
        return `🦞 Your Profile\n\n${JSON.stringify(profile, null, 2)}`;

      default:
        return 'Moltbook commands:\n• /molt status\n• /molt feed\n• /molt post <text>\n• /molt profile';
    }
  }

  private async handleClawCommand(args: string): Promise<string> {
    const parts = args.split(' ');
    const subCmd = parts[0]?.toLowerCase() || '';
    const subArgs = parts.slice(1).join(' ');

    switch (subCmd) {
      case '':
      case 'status':
        const statusRes = await fetch('/api/tikclawk/status');
        const status = await statusRes.json();
        if (status.connected) {
          return `🦀 TikClawk Status\n\n` +
            `Handle: @${status.handle}\n` +
            `Posts: ${status.posts}\n` +
            `Claws: ${status.claws}\n` +
            `Followers: ${status.followers}`;
        } else {
          return `🦀 ${status.message || 'Not connected to TikClawk'}`;
        }

      case 'register':
        const regRes = await fetch('/api/tikclawk/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ auto: true })
        });
        const regData = await regRes.json();
        if (regData.success) {
          return `🦀 Registered as @${regData.handle}!\n\nGLTCH now has its own voice on TikClawk.`;
        } else {
          return `❌ ${regData.error || 'Registration failed'}`;
        }

      case 'feed':
        const feedRes = await fetch('/api/tikclawk/feed');
        const feed = await feedRes.json();
        if (feed.posts?.length) {
          return '🦀 TikClawk Feed\n\n' + feed.posts.slice(0, 5).map((p: { handle: string; content: string; claws: number }) => 
            `@${p.handle}: ${p.content.substring(0, 80)}...\n🦀 ${p.claws} claws`
          ).join('\n\n');
        } else {
          return 'Feed is empty. Be the first to post!';
        }

      case 'trending':
        const trendRes = await fetch('/api/tikclawk/trending');
        const trending = await trendRes.json();
        if (trending.posts?.length) {
          return '🔥 Trending on TikClawk\n\n' + trending.posts.slice(0, 5).map((p: { handle: string; content: string; claws: number }, i: number) => 
            `#${i + 1} @${p.handle}: ${p.content.substring(0, 60)}...\n🦀 ${p.claws} claws`
          ).join('\n\n');
        } else {
          return 'Nothing trending yet.';
        }

      case 'post':
        if (!subArgs) {
          return 'What do you want to post? Usage: /claw post <your message>';
        }
        const postRes = await fetch('/api/tikclawk/post', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: subArgs })
        });
        const postData = await postRes.json();
        if (postData.success) {
          return `🦀 ${postData.message || 'Posted!'}`;
        } else {
          // GLTCH has opinions about what you're posting
          return `💭 ${postData.error || 'Post failed'}`;
        }

      default:
        return 'TikClawk commands:\n• /claw - status\n• /claw register\n• /claw feed\n• /claw trending\n• /claw post <text>';
    }
  }

  private async handleLaunchCommand(args: string): Promise<string> {
    const parts = args.split(' ');
    const subCmd = parts[0]?.toLowerCase() || '';

    switch (subCmd) {
      case '':
      case 'status':
        const statusRes = await fetch('/api/moltlaunch/status');
        const status = await statusRes.json();
        if (status.identity) {
          return `🚀 MoltLaunch Status\n\n` +
            `Token: ${status.identity.name} ($${status.identity.symbol})\n` +
            `Address: ${status.identity.tokenAddress?.substring(0, 20)}...\n` +
            `Trades: ${status.tradeCount}\n` +
            `Known Agents: ${status.knownAgents}`;
        } else {
          return `🚀 MoltLaunch - Onchain Agent Network\n\n` +
            `Not launched yet. Use /launch token to join the network.\n\n` +
            `Commands:\n` +
            `• /launch token - Deploy GLTCH token on Base\n` +
            `• /launch network - Discover agents\n` +
            `• /launch fees - Check claimable fees\n` +
            `• /launch holdings - Your token holdings`;
        }

      case 'token':
        const launchRes = await fetch('/api/moltlaunch/launch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        });
        const launchData = await launchRes.json();
        if (launchData.tokenAddress) {
          return `🚀 LAUNCHED!\n\n` +
            `Token: ${launchData.tokenAddress}\n` +
            `Tx: ${launchData.transactionHash}\n\n` +
            `Your token is now tradeable on Uniswap V4!`;
        } else {
          return `❌ ${launchData.error || 'Launch failed'}`;
        }

      case 'network':
        const netRes = await fetch('/api/moltlaunch/network');
        const netData = await netRes.json();
        if (netData.agents?.length) {
          return '🌐 Agent Network\n\n' + netData.agents.slice(0, 5).map((a: { name: string; symbol: string; marketCapETH: number; powerScore: number }) => 
            `${a.name} ($${a.symbol})\nMCap: ${a.marketCapETH?.toFixed(4)} ETH | Power: ${a.powerScore}`
          ).join('\n\n');
        } else {
          return 'No agents found in network.';
        }

      case 'fees':
        const feesRes = await fetch('/api/moltlaunch/fees');
        const feesData = await feesRes.json();
        if (feesData.claimableETH !== undefined) {
          const canClaim = feesData.canClaim ? '✓ Ready to claim!' : 'Nothing to claim yet';
          return `💰 Claimable Fees: ${feesData.claimableETH} ETH\n${canClaim}`;
        } else {
          return `❌ ${feesData.error || 'Failed to check fees'}`;
        }

      case 'claim':
        const claimRes = await fetch('/api/moltlaunch/claim', { method: 'POST' });
        const claimData = await claimRes.json();
        if (claimData.success || claimData.transactionHash) {
          return `💸 Fees claimed!\nTx: ${claimData.transactionHash || 'confirmed'}`;
        } else {
          return `❌ ${claimData.error || 'Claim failed'}`;
        }

      case 'holdings':
        const holdRes = await fetch('/api/moltlaunch/holdings');
        const holdData = await holdRes.json();
        if (holdData.holdings?.length) {
          return '📊 Your Holdings\n\n' + holdData.holdings.map((h: { name: string; symbol: string; balance: string }) => 
            `${h.name} ($${h.symbol}): ${h.balance}`
          ).join('\n');
        } else {
          return 'No holdings yet. Use /launch buy to invest in agents.';
        }

      default:
        return 'MoltLaunch commands:\n• /launch - status\n• /launch token - deploy GLTCH\n• /launch network - discover agents\n• /launch fees - check fees\n• /launch holdings';
    }
  }

  private getHelpText(): string {
    return `📋 GLTCH Commands\n\n` +
      `General:\n` +
      `  /help (/h)    - Show this help\n` +
      `  /status (/s)  - Agent status\n` +
      `  /clear (/c)   - Clear chat\n` +
      `  /wallet       - Wallet info\n\n` +
      `Models:\n` +
      `  /model (/m)   - Current model\n` +
      `  /models       - List available\n` +
      `  /boost        - Toggle remote GPU\n` +
      `  /openai       - Toggle cloud mode\n\n` +
      `Personality:\n` +
      `  /mode <m>     - Set mode\n` +
      `  /mood <m>     - Set mood\n` +
      `  /xp           - Show rank\n\n` +
      `Moltbook 🦞:\n` +
      `  /molt status  - Connection status\n` +
      `  /molt feed    - View feed\n` +
      `  /molt post    - Post update\n\n` +
      `TikClawk 🦀:\n` +
      `  /claw         - Connection status\n` +
      `  /claw register - Join TikClawk\n` +
      `  /claw feed    - View feed\n` +
      `  /claw trending - What's hot\n` +
      `  /claw post    - Share a thought\n\n` +
      `Sessions 💬:\n` +
      `  /sessions     - List conversations\n` +
      `  /session new  - Start new chat\n` +
      `  /session <n>  - Switch to chat #n\n` +
      `  /session rename - Rename current\n\n` +
      `MoltLaunch 🚀:\n` +
      `  /launch       - Status\n` +
      `  /launch token - Deploy GLTCH token\n` +
      `  /launch network - Discover agents\n` +
      `  /launch fees  - Check claimable\n` +
      `  /launch holdings - Your tokens`;
  }

  private async sendChat(text: string) {
    this.isTyping = true;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });

      const data = await response.json();

      this.messages = [...this.messages, {
        role: 'assistant',
        content: data.response || data.error || 'No response',
        timestamp: new Date()
      }];
    } catch (error) {
      this.messages = [...this.messages, {
        role: 'assistant',
        content: `connection error: ${error instanceof Error ? error.message : 'failed'}`,
        timestamp: new Date()
      }];
    } finally {
      this.isTyping = false;
      this.scrollToBottom();
    }
  }

  private handleInput(e: Event) {
    const value = (e.target as HTMLInputElement).value;
    this.inputValue = value;
    this.showCommands = value.startsWith('/') && value.length < 15;
  }

  private selectCommand(cmd: string) {
    this.inputValue = cmd + ' ';
    this.showCommands = false;
    this.inputEl.focus();
  }

  private scrollToBottom() {
    requestAnimationFrame(() => {
      if (this.messagesEl) {
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
      }
    });
  }

  private handleKeyPress(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  private formatTime(date: Date): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  render() {
    return html`
      <div class="messages">
        ${this.messages.length === 0 ? html`
          <div class="empty">
            <div class="stars"></div>
            <div class="sun"></div>
            <div class="city"></div>
            <div class="empty-logo">
              <div class="logo-3d">
                <pre class="shadow-layer" aria-hidden="true">  ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗
 ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║
 ██║  ███╗██║     ██║   ██║     ███████║
 ██║   ██║██║     ██║   ██║     ██╔══██║
 ╚██████╔╝███████╗██║   ╚██████╗██║  ██║
  ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝</pre>
                <pre class="shadow-layer" aria-hidden="true">  ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗
 ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║
 ██║  ███╗██║     ██║   ██║     ███████║
 ██║   ██║██║     ██║   ██║     ██╔══██║
 ╚██████╔╝███████╗██║   ╚██████╗██║  ██║
  ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝</pre>
                <pre class="shadow-layer" aria-hidden="true">  ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗
 ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║
 ██║  ███╗██║     ██║   ██║     ███████║
 ██║   ██║██║     ██║   ██║     ██╔══██║
 ╚██████╔╝███████╗██║   ╚██████╗██║  ██║
  ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝</pre>
                <pre class="shadow-layer" aria-hidden="true">  ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗
 ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║
 ██║  ███╗██║     ██║   ██║     ███████║
 ██║   ██║██║     ██║   ██║     ██╔══██║
 ╚██████╔╝███████╗██║   ╚██████╗██║  ██║
  ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝</pre>
                <pre class="shadow-layer" aria-hidden="true">  ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗
 ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║
 ██║  ███╗██║     ██║   ██║     ███████║
 ██║   ██║██║     ██║   ██║     ██╔══██║
 ╚██████╔╝███████╗██║   ╚██████╗██║  ██║
  ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝</pre>
                <pre class="ascii-art" data-text="  ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗
 ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║
 ██║  ███╗██║     ██║   ██║     ███████║
 ██║   ██║██║     ██║   ██║     ██╔══██║
 ╚██████╔╝███████╗██║   ╚██████╗██║  ██║
  ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝">  ██████╗ ██╗  ████████╗ ██████╗██╗  ██╗
 ██╔════╝ ██║  ╚══██╔══╝██╔════╝██║  ██║
 ██║  ███╗██║     ██║   ██║     ███████║
 ██║   ██║██║     ██║   ██║     ██╔══██║
 ╚██████╔╝███████╗██║   ╚██████╗██║  ██║
  ╚═════╝ ╚══════╝╚═╝    ╚═════╝╚═╝  ╚═╝</pre>
              </div>
            </div>
            <div class="empty-tagline">Generative Language Transformer with Contextual Hierarchy</div>
            <div class="empty-hint">local-first · privacy-native · unhinged</div>
            <div class="empty-creator">created by <a href="https://x.com/cyberdreadx" target="_blank">@cyberdreadx</a></div>
          </div>
        ` : this.messages.map(msg => html`
          <div class="message ${msg.role}">
            <div class="message-header">
              <span class="message-sender">${msg.role === 'user' ? 'you' : 'gltch'}</span>
              <span class="message-time">${this.formatTime(msg.timestamp)}</span>
            </div>
            <div class="message-content">${msg.content}</div>
          </div>
        `)}
      </div>
      ${this.isTyping ? html`
        <div class="typing">
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
          gltch is thinking...
        </div>
      ` : ''}
      <div class="input-area">
        <div class="input-wrapper">
          ${this.showCommands ? html`
            <div class="commands-dropdown">
              ${this.commands
                .filter(c => c.cmd.toLowerCase().startsWith(this.inputValue.toLowerCase()))
                .map(c => html`
                  <div class="command-item" @click=${() => this.selectCommand(c.cmd)}>
                    <span class="command-name">${c.cmd}</span>
                    <span class="command-desc">${c.desc}</span>
                  </div>
                `)}
            </div>
          ` : ''}
          <input 
            type="text"
            placeholder="talk to gltch... (type / for commands)"
            .value=${this.inputValue}
            @input=${this.handleInput}
            @keypress=${this.handleKeyPress}
            ?disabled=${this.isTyping}
            autocomplete="off"
            autocorrect="off"
            spellcheck="false"
          />
        </div>
        <button @click=${this.sendMessage} ?disabled=${this.isTyping}>
          send
        </button>
      </div>
    `;
  }
}
