/**
 * GLTCH Dashboard - Chat Component
 */

import { LitElement, html, css } from 'lit';
import { customElement, state, query } from 'lit/decorators.js';

interface Message {
  role: 'user' | 'assistant';
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

    .header {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 12px 16px;
      background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0a 100%);
      border-bottom: 1px solid var(--border);
    }

    .header h1 {
      font-size: 18px;
      color: #ff00ff;
      text-shadow: 0 0 10px #ff00ff44;
    }

    .header .emoji {
      margin: 0 8px;
    }

    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      -webkit-overflow-scrolling: touch;
    }

    .message {
      margin-bottom: 16px;
      max-width: 85%;
    }

    .message.user {
      margin-left: auto;
    }

    .message-header {
      font-size: 11px;
      color: var(--text-muted);
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .message.user .message-header {
      justify-content: flex-end;
    }

    .message-content {
      padding: 12px 16px;
      border-radius: 16px;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-size: 14px;
      line-height: 1.5;
    }

    .message.user .message-content {
      background: linear-gradient(135deg, #00aaff 0%, #0088cc 100%);
      color: white;
      border-bottom-right-radius: 4px;
    }

    .message.assistant .message-content {
      background: linear-gradient(135deg, #2a1a3a 0%, #1a1a2e 100%);
      border: 1px solid #ff00ff33;
      border-bottom-left-radius: 4px;
      box-shadow: 0 0 15px #ff00ff11;
    }

    .input-area {
      display: flex;
      gap: 10px;
      padding: 12px 16px;
      padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
      background: var(--bg-secondary);
      border-top: 1px solid var(--border);
    }

    .input-area input {
      flex: 1;
      padding: 14px 16px;
      font-size: 16px; /* Prevents iOS zoom */
      border-radius: 24px;
      min-height: 48px;
    }

    .input-area button {
      padding: 14px 20px;
      min-height: 48px;
      min-width: 48px;
      background: linear-gradient(135deg, #ff00ff 0%, #cc00cc 100%);
      color: white;
      border: none;
      border-radius: 24px;
      font-weight: bold;
      font-size: 16px;
      box-shadow: 0 0 15px #ff00ff44;
    }

    .input-area button:hover {
      opacity: 0.9;
    }

    .input-area button:active {
      transform: scale(0.95);
    }

    .input-area button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .typing {
      color: #ff00ff;
      font-style: italic;
      padding: 8px 20px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .typing-dots {
      display: flex;
      gap: 4px;
    }

    .typing-dots span {
      width: 6px;
      height: 6px;
      background: #ff00ff;
      border-radius: 50%;
      animation: bounce 1.4s ease-in-out infinite;
    }

    .typing-dots span:nth-child(1) { animation-delay: 0s; }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes bounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-6px); }
    }

    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--text-muted);
      padding: 20px;
      text-align: center;
    }

    .empty .logo {
      font-size: 48px;
      margin-bottom: 16px;
      text-shadow: 0 0 30px #ff00ff66;
    }

    .empty h2 {
      color: #ff00ff;
      margin-bottom: 8px;
      font-size: 24px;
      text-shadow: 0 0 15px #ff00ff44;
    }

    .empty p {
      max-width: 280px;
      line-height: 1.6;
    }

    /* Mobile responsive */
    @media (max-width: 480px) {
      .message {
        max-width: 90%;
      }

      .input-area {
        padding: 10px 12px;
        padding-bottom: calc(10px + env(safe-area-inset-bottom, 0px));
      }

      .input-area input {
        padding: 12px 14px;
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
    this.isTyping = true;
    this.scrollToBottom();

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
        content: `Error: ${error instanceof Error ? error.message : 'Connection failed'}`,
        timestamp: new Date()
      }];
    } finally {
      this.isTyping = false;
      this.scrollToBottom();
    }
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

  render() {
    return html`
      <div class="header">
        <span class="emoji">💜</span>
        <h1>GLTCH</h1>
        <span class="emoji">✨</span>
      </div>
      <div class="messages">
        ${this.messages.length === 0 ? html`
          <div class="empty">
            <div class="logo">💜</div>
            <h2>GLTCH</h2>
            <p>your cyber operator is ready~</p>
            <p style="margin-top: 12px; font-size: 12px;">local-first • privacy-native • unhinged</p>
          </div>
        ` : this.messages.map(msg => html`
          <div class="message ${msg.role}">
            <div class="message-header">
              ${msg.role === 'user' ? '👤 you' : '💜 GLTCH'} • 
              ${msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
          GLTCH is thinking~
        </div>
      ` : ''}
      <div class="input-area">
        <input 
          type="text"
          placeholder="talk to GLTCH~"
          .value=${this.inputValue}
          @input=${(e: Event) => this.inputValue = (e.target as HTMLInputElement).value}
          @keypress=${this.handleKeyPress}
          ?disabled=${this.isTyping}
          autocomplete="off"
          autocorrect="off"
          spellcheck="false"
        />
        <button @click=${this.sendMessage} ?disabled=${this.isTyping}>
          ⚡
        </button>
      </div>
    `;
  }
}
