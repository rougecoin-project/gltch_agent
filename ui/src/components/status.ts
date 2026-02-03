/**
 * GLTCH Dashboard - Status Component
 * Physics-based network + agent stats
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface NetworkNode {
  id: string;
  label: string;
  type: 'agent' | 'model' | 'tool' | 'channel' | 'social';
  status: 'online' | 'offline' | 'busy' | 'error';
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

@customElement('gltch-status')
export class GltchStatus extends LitElement {
  static styles = css`
    :host {
      display: flex;
      height: 100%;
      background: var(--bg-primary);
    }

    .network-view {
      flex: 1;
      position: relative;
      overflow: hidden;
    }

    .network-canvas {
      width: 100%;
      height: 100%;
      cursor: grab;
    }

    .network-canvas:active {
      cursor: grabbing;
    }

    .hint {
      position: absolute;
      bottom: 16px;
      left: 16px;
      font-size: 10px;
      color: var(--text-muted);
      background: rgba(18, 18, 24, 0.9);
      padding: 6px 10px;
      border-radius: 4px;
      border: 1px solid var(--border);
    }

    /* Stats panel */
    .stats-panel {
      width: 260px;
      background: var(--bg-secondary);
      border-left: 1px solid var(--border);
      padding: 20px;
      overflow-y: auto;
    }

    .stats-title {
      font-size: 12px;
      color: var(--neon-magenta);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border);
    }

    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
    }

    .stat-label {
      font-size: 11px;
      color: var(--text-muted);
    }

    .stat-value {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .stat-value.green { color: var(--neon-green); }
    .stat-value.red { color: var(--neon-red); }
    .stat-value.magenta { color: var(--neon-magenta); }

    .xp-bar {
      margin-top: 16px;
    }

    .xp-label {
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }

    .xp-track {
      height: 6px;
      background: var(--bg-primary);
      border-radius: 3px;
      overflow: hidden;
    }

    .xp-fill {
      height: 100%;
      background: var(--neon-magenta);
      box-shadow: var(--glow-magenta);
      transition: width 0.3s ease;
    }

    .tools-list {
      margin-top: 20px;
    }

    .tools-title {
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 10px;
    }

    .tool-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
    }

    .tool-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--neon-green);
      box-shadow: 0 0 6px var(--neon-green);
    }

    .tool-dot.offline {
      background: var(--text-muted);
      box-shadow: none;
    }

    .tool-name {
      font-size: 11px;
      color: var(--text-secondary);
    }

    .legend {
      margin-top: 20px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      font-size: 10px;
      color: var(--text-muted);
    }

    .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }

    .legend-dot.agent { background: #ff00ff; }
    .legend-dot.model { background: #00d4ff; }
    .legend-dot.tool { background: #ffd700; }
    .legend-dot.channel { background: #00ff66; }
    .legend-dot.social { background: #ff6b35; }

    @media (max-width: 768px) {
      .stats-panel { display: none; }
    }
  `;

  @state() private nodes: NetworkNode[] = [];
  
  @state() private stats = {
    level: 1,
    xp: 0,
    xpNext: 100,
    rank: 'SCRIPT KIDDIE',
    tokens: 0,
    sessions: 0,
    uptime: '--'
  };

  private canvas!: HTMLCanvasElement;
  private ctx!: CanvasRenderingContext2D;
  private animationId = 0;
  private draggingNode: NetworkNode | null = null;
  private mouseX = 0;
  private mouseY = 0;
  private startTime = Date.now();
  private width = 0;
  private height = 0;

  private readonly SPRING_LENGTH = 100;
  private readonly SPRING_STRENGTH = 0.025;
  private readonly REPULSION = 6000;
  private readonly DAMPING = 0.88;
  private readonly CENTER_GRAVITY = 0.004;

  connectedCallback() {
    super.connectedCallback();
    this.initNodes();
    this.loadStatus();
    setInterval(() => this.loadStatus(), 5000);
    setInterval(() => this.updateUptime(), 1000);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    cancelAnimationFrame(this.animationId);
  }

  firstUpdated() {
    this.canvas = this.shadowRoot!.querySelector('canvas')!;
    this.ctx = this.canvas.getContext('2d')!;
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.runAnimation();
  }

  private initNodes() {
    const cx = 300, cy = 250;
    this.nodes = [
      { id: 'gltch', label: 'GLTCH', type: 'agent', status: 'offline', x: cx, y: cy, vx: 0, vy: 0, radius: 40 },
      { id: 'ollama', label: 'Ollama', type: 'model', status: 'offline', x: cx - 120, y: cy - 80, vx: 0, vy: 0, radius: 28 },
      { id: 'lmstudio', label: 'LM Studio', type: 'model', status: 'offline', x: cx + 120, y: cy - 80, vx: 0, vy: 0, radius: 28 },
      { id: 'opencode', label: 'OpenCode', type: 'tool', status: 'offline', x: cx - 140, y: cy + 40, vx: 0, vy: 0, radius: 24 },
      { id: 'moltbook', label: 'Moltbook', type: 'social', status: 'offline', x: cx + 140, y: cy + 40, vx: 0, vy: 0, radius: 24 },
      { id: 'telegram', label: 'Telegram', type: 'channel', status: 'offline', x: cx + 80, y: cy + 110, vx: 0, vy: 0, radius: 22 },
      { id: 'discord', label: 'Discord', type: 'channel', status: 'offline', x: cx, y: cy + 130, vx: 0, vy: 0, radius: 22 },
      { id: 'webchat', label: 'WebChat', type: 'channel', status: 'online', x: cx - 80, y: cy + 110, vx: 0, vy: 0, radius: 22 },
    ];
  }

  private resize() {
    const container = this.canvas?.parentElement;
    if (!container) return;
    
    const rect = container.getBoundingClientRect();
    this.width = rect.width;
    this.height = rect.height;
    this.canvas.width = this.width * window.devicePixelRatio;
    this.canvas.height = this.height * window.devicePixelRatio;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    
    const cx = this.width / 2, cy = this.height / 2;
    const agent = this.nodes.find(n => n.type === 'agent');
    if (agent) {
      const dx = cx - agent.x, dy = cy - agent.y;
      this.nodes.forEach(n => { n.x += dx; n.y += dy; });
    }
  }

  private runAnimation() {
    this.physics();
    this.draw();
    this.animationId = requestAnimationFrame(() => this.runAnimation());
  }

  private physics() {
    const nodes = this.nodes;
    const agent = nodes.find(n => n.type === 'agent')!;
    const cx = this.width / 2, cy = this.height / 2;

    for (const node of nodes) {
      if (node === this.draggingNode) continue;

      if (node !== agent) {
        const dx = agent.x - node.x;
        const dy = agent.y - node.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - this.SPRING_LENGTH) * this.SPRING_STRENGTH;
        node.vx += (dx / dist) * force;
        node.vy += (dy / dist) * force;
      }

      for (const other of nodes) {
        if (other === node) continue;
        const dx = node.x - other.x;
        const dy = node.y - other.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const minDist = node.radius + other.radius + 15;
        if (dist < minDist * 3) {
          const force = this.REPULSION / (dist * dist);
          node.vx += (dx / dist) * force;
          node.vy += (dy / dist) * force;
        }
      }

      node.vx += (cx - node.x) * this.CENTER_GRAVITY;
      node.vy += (cy - node.y) * this.CENTER_GRAVITY;

      node.vx *= this.DAMPING;
      node.vy *= this.DAMPING;
      node.x += node.vx;
      node.y += node.vy;

      node.x = Math.max(node.radius, Math.min(this.width - node.radius, node.x));
      node.y = Math.max(node.radius, Math.min(this.height - node.radius, node.y));
    }
  }

  private draw() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    const agent = this.nodes.find(n => n.type === 'agent')!;

    for (const node of this.nodes) {
      if (node === agent) continue;
      
      ctx.beginPath();
      ctx.moveTo(agent.x, agent.y);
      ctx.lineTo(node.x, node.y);
      
      if (node.status === 'online') {
        ctx.strokeStyle = this.getNodeColor(node.type);
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.shadowColor = this.getNodeColor(node.type);
        ctx.shadowBlur = 6;
      } else {
        ctx.strokeStyle = 'rgba(255,255,255,0.12)';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 4]);
        ctx.shadowBlur = 0;
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    for (const node of this.nodes) {
      this.drawNode(node);
    }
  }

  private drawNode(node: NetworkNode) {
    const ctx = this.ctx;
    const color = this.getNodeColor(node.type);
    const isOnline = node.status === 'online';
    const isAgent = node.type === 'agent';

    if (isOnline || isAgent) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius + 6, 0, Math.PI * 2);
      const gradient = ctx.createRadialGradient(node.x, node.y, node.radius, node.x, node.y, node.radius + 15);
      gradient.addColorStop(0, color + '30');
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    ctx.beginPath();
    ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
    
    if (isOnline || isAgent) {
      ctx.fillStyle = color + '18';
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;
    } else {
      ctx.fillStyle = 'rgba(35,35,45,0.9)';
      ctx.strokeStyle = 'rgba(255,255,255,0.18)';
      ctx.lineWidth = 1;
      ctx.shadowBlur = 0;
    }
    ctx.fill();
    ctx.stroke();
    ctx.shadowBlur = 0;

    ctx.font = `${isAgent ? 24 : 16}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(this.getNodeIcon(node), node.x, node.y);

    ctx.font = `${isAgent ? 11 : 9}px "JetBrains Mono", monospace`;
    ctx.fillStyle = isOnline || isAgent ? color : 'rgba(255,255,255,0.4)';
    ctx.fillText(node.label.toUpperCase(), node.x, node.y + node.radius + 12);

    const dotX = node.x + node.radius * 0.65;
    const dotY = node.y - node.radius * 0.65;
    ctx.beginPath();
    ctx.arc(dotX, dotY, 5, 0, Math.PI * 2);
    ctx.fillStyle = node.status === 'online' ? '#00ff66' : '#555';
    ctx.fill();
    ctx.strokeStyle = '#0a0a0f';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  private getNodeColor(type: string): string {
    return { agent: '#ff00ff', model: '#00d4ff', tool: '#ffd700', channel: '#00ff66', social: '#ff6b35' }[type] || '#fff';
  }

  private getNodeIcon(node: NetworkNode): string {
    return { gltch: '💜', ollama: '🦙', lmstudio: '🧠', opencode: '⚡', moltbook: '🦞', telegram: '📱', discord: '💬', webchat: '🌐' }[node.id] || '○';
  }

  private handleMouseDown(e: MouseEvent) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    for (const node of [...this.nodes].reverse()) {
      const dx = x - node.x, dy = y - node.y;
      if (dx * dx + dy * dy < node.radius * node.radius) {
        this.draggingNode = node;
        this.mouseX = x;
        this.mouseY = y;
        break;
      }
    }
  }

  private handleMouseMove(e: MouseEvent) {
    if (!this.draggingNode) return;
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    this.draggingNode.x += x - this.mouseX;
    this.draggingNode.y += y - this.mouseY;
    this.draggingNode.vx = 0;
    this.draggingNode.vy = 0;
    this.mouseX = x;
    this.mouseY = y;
  }

  private handleMouseUp() {
    this.draggingNode = null;
  }

  private async loadStatus() {
    try {
      const statusRes = await fetch('/api/status');
      if (statusRes.ok) {
        const status = await statusRes.json();
        this.stats = { ...this.stats, sessions: status.sessions || 0 };
        this.updateNode('gltch', status.agent?.connected ? 'online' : 'offline');
      }

      const settingsRes = await fetch('/api/settings');
      if (settingsRes.ok) {
        const s = await settingsRes.json();
        this.stats = { ...this.stats, level: s.level || 1, xp: s.xp || 0, rank: this.getRankName(s.level || 1) };
      }

      const ollamaRes = await fetch('/api/ollama/status');
      if (ollamaRes.ok) {
        const o = await ollamaRes.json();
        if (o.connected) {
          this.updateNode(o.boost ? 'lmstudio' : 'ollama', 'online');
          this.updateNode(o.boost ? 'ollama' : 'lmstudio', 'offline');
        }
      }

      const moltRes = await fetch('/api/moltbook/status');
      if (moltRes.ok) {
        const m = await moltRes.json();
        this.updateNode('moltbook', m.connected ? 'online' : 'offline');
      }
    } catch { this.updateNode('gltch', 'offline'); }
  }

  private updateNode(id: string, status: NetworkNode['status']) {
    const node = this.nodes.find(n => n.id === id);
    if (node) node.status = status;
  }

  private updateUptime() {
    const s = Math.floor((Date.now() - this.startTime) / 1000);
    this.stats = { ...this.stats, uptime: `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m` };
  }

  private getRankName(level: number): string {
    const ranks = ['SCRIPT KIDDIE', 'PACKET PUSHER', 'SYSTEM SNIFFER', 'NETWORK NINJA', 'FIREWALL BREAKER', 'ROOTKIT RIDER', 'GHOST IN SHELL', 'ZERO DAY HUNTER', 'CYBER PHANTOM', 'DIGITAL DEITY'];
    return ranks[Math.min(level - 1, ranks.length - 1)];
  }

  render() {
    return html`
      <div class="network-view">
        <canvas 
          class="network-canvas"
          @mousedown=${this.handleMouseDown}
          @mousemove=${this.handleMouseMove}
          @mouseup=${this.handleMouseUp}
          @mouseleave=${this.handleMouseUp}
        ></canvas>
        <div class="hint">drag nodes to rearrange</div>
      </div>

      <div class="stats-panel">
        <div class="stats-title">◆ agent status</div>
        
        <div class="stat-item">
          <span class="stat-label">rank</span>
          <span class="stat-value magenta">${this.stats.rank}</span>
        </div>
        
        <div class="stat-item">
          <span class="stat-label">level</span>
          <span class="stat-value">LVL ${this.stats.level}</span>
        </div>
        
        <div class="stat-item">
          <span class="stat-label">sessions</span>
          <span class="stat-value">${this.stats.sessions}</span>
        </div>
        
        <div class="stat-item">
          <span class="stat-label">uptime</span>
          <span class="stat-value">${this.stats.uptime}</span>
        </div>

        <div class="xp-bar">
          <div class="xp-label">
            <span>XP</span>
            <span>${this.stats.xp} / ${this.stats.xpNext}</span>
          </div>
          <div class="xp-track">
            <div class="xp-fill" style="width: ${(this.stats.xp / this.stats.xpNext) * 100}%"></div>
          </div>
        </div>

        <div class="tools-list">
          <div class="tools-title">◆ connections</div>
          ${this.nodes.filter(n => n.type !== 'agent').map(node => html`
            <div class="tool-item">
              <div class="tool-dot ${node.status === 'online' ? '' : 'offline'}"></div>
              <span class="tool-name">${node.label}</span>
            </div>
          `)}
        </div>

        <div class="legend">
          <div class="legend-item"><div class="legend-dot agent"></div><span>agent</span></div>
          <div class="legend-item"><div class="legend-dot model"></div><span>models</span></div>
          <div class="legend-item"><div class="legend-dot tool"></div><span>tools</span></div>
          <div class="legend-item"><div class="legend-dot channel"></div><span>channels</span></div>
          <div class="legend-item"><div class="legend-dot social"></div><span>social</span></div>
        </div>
      </div>
    `;
  }
}
