# WebChat

Browser-based chat interface, built into the gateway.

## Overview

WebChat is the easiest way to interact with GLTCH - no additional setup required. Just start the gateway and open your browser.

## Usage

### 1. Start the Gateway

```bash
gltch gateway start
```

### 2. Open the Dashboard

Navigate to: http://localhost:18888

The dashboard includes:
- **Chat**: Real-time conversation with GLTCH
- **Status**: System and agent status
- **Settings**: Configure mode, mood, and options

## WebSocket Connection

For custom integrations, connect directly via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:18889?channel=webchat');

ws.onopen = () => {
  console.log('Connected to GLTCH');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Send a message
ws.send(JSON.stringify({
  type: 'chat',
  text: 'Hello GLTCH!'
}));
```

## Message Format

### Sending

```json
{
  "type": "chat",
  "text": "Your message here"
}
```

### Receiving

```json
{
  "type": "response",
  "response": "Agent response",
  "mood": "focused",
  "xp_gained": 5
}
```

### Typing Indicator

```json
{
  "type": "typing",
  "typing": true
}
```

## Configuration

WebChat is enabled by default. To disable:

```json
{
  "channels": {
    "webchat": {
      "enabled": false
    }
  }
}
```

## Customization

The dashboard UI is built with Lit and can be customized:

1. Edit files in `ui/src/components/`
2. Rebuild: `cd ui && npm run build`
3. The gateway serves the built files

## Remote Access

By default, the gateway binds to `127.0.0.1` (localhost only).

For remote access:

```bash
gltch gateway start --host 0.0.0.0
```

**Warning**: This exposes the gateway to your network. Use with caution.
