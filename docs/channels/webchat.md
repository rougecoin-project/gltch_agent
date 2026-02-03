# WebChat

The built-in web interface for chatting with GLTCH from any browser.

## Quick Start

1. Start the full stack:
   ```bash
   # Terminal 1: Agent
   python gltch.py --rpc http

   # Terminal 2: Gateway
   cd gateway && npm run dev

   # Terminal 3: UI
   cd ui && npm run dev
   ```

2. Open http://localhost:3000

## Features

### Chat Interface
- Real-time streaming responses
- Markdown rendering
- Code syntax highlighting
- Typing indicators

### Settings Panel
- Toggle boost mode (remote GPU)
- Toggle OpenAI mode (cloud)
- Change personality mode
- Change mood
- Manage API keys

### Status View
- Network visualization
- Connected services status
- Agent statistics (level, XP, rank)

### Mobile Support
- Responsive design
- PWA support (Add to Home Screen)
- Touch-optimized controls

## Mobile Access

### Local Network

Access from any device on your network:

1. Start gateway with host binding:
   ```bash
   cd gateway
   npm run dev -- --host 0.0.0.0
   ```

2. Find your machine's IP:
   ```bash
   # Linux/macOS
   ip addr | grep inet
   
   # Windows
   ipconfig
   ```

3. Open `http://<your-ip>:3000` on your phone

### Tailscale (Recommended)

For secure remote access:

1. Install Tailscale on your server and phone
2. Run `tailscale up` on both
3. Access via Tailscale IP: `http://100.x.x.x:3000`

### iOS PWA

For app-like experience on iOS:

1. Open the web UI in Safari
2. Tap the Share button
3. Select "Add to Home Screen"
4. Name it "GLTCH"
5. Tap Add

The icon will appear on your home screen and open in full-screen mode.

## Configuration

### UI Port

```bash
# Default port is 3000
cd ui
PORT=8080 npm run dev
```

### API Proxy

The UI proxies API calls to the gateway. Configure in `ui/vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:18888',
      '/health': 'http://localhost:18888'
    }
  }
});
```

## Customization

### Theme

The UI uses CSS variables for theming. Edit `ui/src/styles/global.css`:

```css
:root {
  --bg-primary: #0a0a0a;
  --neon-green: #00ff66;
  --neon-red: #ff3366;
  --neon-magenta: #ff00ff;
  /* ... */
}
```

### Components

All UI components are in `ui/src/components/`:

- `app.ts` — Main layout
- `sidebar.ts` — Navigation
- `header.ts` — Status bar
- `chat.ts` — Chat interface
- `settings.ts` — Settings panel
- `status.ts` — Network view
- `ticker.ts` — Activity feed

## Building for Production

```bash
cd ui
npm run build
```

Output will be in `ui/dist/`. Serve with any static file server:

```bash
npx serve dist
```

Or integrate with the gateway to serve the UI directly.

## Troubleshooting

### Blank Page

1. Check browser console for errors
2. Verify gateway is running
3. Check network tab for failed API calls

### API Errors

1. Ensure agent is running in RPC mode
2. Check gateway logs
3. Verify proxy configuration in vite.config.ts

### Slow Responses

1. Check LLM model performance
2. Consider using boost mode for faster inference
3. Check network latency if using remote LLM
