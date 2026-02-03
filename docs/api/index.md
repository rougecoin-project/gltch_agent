# API Reference

Complete API documentation for GLTCH's REST and JSON-RPC interfaces.

## REST API (Gateway)

The Gateway exposes a REST API on port 18888 by default.

### Base URL

```
http://localhost:18888
```

---

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "running",
  "connections": 0,
  "sessions": 1,
  "agent": {
    "connected": true
  }
}
```

---

### Get Status

```http
GET /api/status
```

**Response:**
```json
{
  "status": "running",
  "connections": 2,
  "sessions": 3,
  "agent": {
    "connected": true,
    "mode": "cyberpunk",
    "mood": "focused",
    "level": 5
  }
}
```

---

### Send Chat Message

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Hello GLTCH!",
  "session_id": "optional-session-id",
  "channel": "api",
  "user": "optional-username"
}
```

**Response:**
```json
{
  "response": "Hey! What's up?",
  "mood": "focused",
  "session_id": "api"
}
```

---

### Get Settings

```http
GET /api/settings
```

**Response:**
```json
{
  "mode": "cyberpunk",
  "mood": "focused",
  "boost": false,
  "openai_mode": false,
  "network_active": false,
  "level": 5,
  "xp": 1250,
  "model": "deepseek-r1:8b"
}
```

---

### Update Settings

```http
POST /api/settings
Content-Type: application/json

{
  "mode": "operator",
  "mood": "calm"
}
```

**Response:**
```json
{
  "success": true
}
```

---

### Toggle Setting

```http
POST /api/toggle/:setting
Content-Type: application/json

{
  "state": true
}
```

**Available settings:**
- `boost` — Remote GPU mode
- `openai` — OpenAI cloud mode
- `network` — Network tools

**Response:**
```json
{
  "success": true
}
```

---

### Get API Keys

```http
GET /api/keys
```

**Response:**
```json
{
  "openai": { "set": true, "masked": "••••abcd" },
  "anthropic": { "set": false, "masked": "" },
  "gemini": { "set": false, "masked": "" }
}
```

---

### Set API Key

```http
POST /api/keys/:key
Content-Type: application/json

{
  "value": "sk-..."
}
```

**Response:**
```json
{
  "success": true
}
```

---

### Delete API Key

```http
DELETE /api/keys/:key
```

**Response:**
```json
{
  "success": true
}
```

---

### List Models

```http
GET /api/models
```

**Response:**
```json
{
  "models": ["deepseek-r1:8b", "phi3:3.8b", "llama3.2:latest"],
  "current": "deepseek-r1:8b",
  "boost": false
}
```

---

### Select Model

```http
POST /api/models/select
Content-Type: application/json

{
  "model": "phi3:3.8b",
  "boost": false
}
```

**Response:**
```json
{
  "success": true,
  "model": "phi3:3.8b"
}
```

---

### Get Sessions

```http
GET /api/sessions
```

**Response:**
```json
{
  "sessions": [
    { "id": "default", "messages": 15 },
    { "id": "discord-123", "messages": 8 }
  ]
}
```

---

## JSON-RPC API (Agent)

The Agent exposes a JSON-RPC 2.0 API on port 18890 by default.

### Base URL

```
http://localhost:18890
```

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": {},
  "id": 1
}
```

### Response Format

**Success:**
```json
{
  "jsonrpc": "2.0",
  "result": {},
  "id": 1
}
```

**Error:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request"
  },
  "id": 1
}
```

---

### ping

Health check.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "ping",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "ok",
    "agent": "GLTCH"
  },
  "id": 1
}
```

---

### chat

Send a chat message.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "chat",
  "params": {
    "message": "Hello!",
    "session_id": "default",
    "channel": "api",
    "user": "dreadx"
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "response": "Hey! What's up?",
    "mood": "focused",
    "session_id": "default"
  },
  "id": 1
}
```

---

### status

Get agent status.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "status",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "agent_name": "GLTCH",
    "operator": "dreadx",
    "mode": "cyberpunk",
    "mood": "focused",
    "level": 5,
    "xp": 1250,
    "rank": "FIREWALL BREAKER",
    "boost": false,
    "openai_mode": false,
    "network_active": false,
    "llm_connected": true
  },
  "id": 1
}
```

---

### set_mode

Change personality mode.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "set_mode",
  "params": {
    "mode": "operator"
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "mode": "operator"
  },
  "id": 1
}
```

---

### set_mood

Change current mood.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "set_mood",
  "params": {
    "mood": "calm"
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "mood": "calm"
  },
  "id": 1
}
```

---

### toggle_boost

Toggle remote GPU mode.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "toggle_boost",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "boost": true
  },
  "id": 1
}
```

---

### toggle_openai

Toggle OpenAI cloud mode.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "toggle_openai",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "openai_mode": true
  },
  "id": 1
}
```

---

### toggle_network

Toggle network tools.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "toggle_network",
  "params": {
    "state": true
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "network_active": true
  },
  "id": 1
}
```

---

### get_settings

Get all settings.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_settings",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "mode": "cyberpunk",
    "mood": "focused",
    "boost": false,
    "openai_mode": false,
    "network_active": false,
    "level": 5,
    "xp": 1250,
    "model": "deepseek-r1:8b"
  },
  "id": 1
}
```

---

### set_settings

Update settings.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "set_settings",
  "params": {
    "mode": "operator",
    "mood": "calm"
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true
  },
  "id": 1
}
```

---

### get_api_keys

Get API keys (masked).

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_api_keys",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "openai": { "set": true, "masked": "••••abcd" },
    "anthropic": { "set": false, "masked": "" }
  },
  "id": 1
}
```

---

### set_api_key

Set an API key.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "set_api_key",
  "params": {
    "key": "openai",
    "value": "sk-..."
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true
  },
  "id": 1
}
```

---

### delete_api_key

Delete an API key.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "delete_api_key",
  "params": {
    "key": "openai"
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true
  },
  "id": 1
}
```

---

### list_models

List available models.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "list_models",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "models": ["deepseek-r1:8b", "phi3:3.8b"],
    "current": "deepseek-r1:8b",
    "boost": false
  },
  "id": 1
}
```

---

### set_model

Select a model.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "set_model",
  "params": {
    "model": "phi3:3.8b",
    "boost": false
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "model": "phi3:3.8b"
  },
  "id": 1
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| -32700 | Parse error |
| -32600 | Invalid Request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |

## Rate Limiting

The API currently has no rate limiting. For production deployments, consider adding rate limiting at the reverse proxy level (nginx, Caddy, etc.).

## Authentication

The API currently has no authentication. For production deployments, consider:

1. Running behind a reverse proxy with auth
2. Using Tailscale for private network access
3. Implementing JWT tokens (coming soon)
