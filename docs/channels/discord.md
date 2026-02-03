# Discord Integration

Add GLTCH to your Discord server for AI assistance in channels or DMs.

## Setup

### 1. Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**
3. Name it (e.g., "GLTCH")
4. Go to **Bot** section
5. Click **Add Bot**
6. Copy the **bot token**

### 2. Configure Bot Permissions

Under **OAuth2 > URL Generator**:

1. Select scopes:
   - `bot`
   - `applications.commands`

2. Select bot permissions:
   - Send Messages
   - Read Message History
   - Use Slash Commands
   - Embed Links
   - Attach Files

3. Copy the generated URL and open it to invite the bot

### 3. Configure GLTCH

Set the bot token:

```bash
export DISCORD_BOT_TOKEN=your-bot-token-here
```

Or via Web UI:
1. Open http://localhost:3000
2. Go to **Settings > API Keys**
3. Click **Add Key** next to Discord
4. Paste your bot token

### 4. Enable Intents

In Discord Developer Portal:
1. Go to **Bot** section
2. Enable **Message Content Intent**
3. Save changes

### 5. Start the Gateway

```bash
cd gateway
npm run dev
```

## Usage

### Mention the Bot
```
@GLTCH what's the weather like?
```

### DM the Bot
Send a direct message to the bot for private conversations.

### Slash Commands
```
/gltch ask What is the meaning of life?
/gltch status
/gltch mode cyberpunk
```

## Features

### Per-Server Sessions
Each server has its own conversation context.

### Per-User DMs
Private conversations are separate from server chats.

### Rich Embeds
GLTCH responses use Discord embeds for better formatting.

### Typing Indicator
Shows "GLTCH is typing..." while generating responses.

## Configuration

```bash
# Bot token (required)
DISCORD_BOT_TOKEN=your-token

# Optional: Command prefix (default: /)
DISCORD_PREFIX=/

# Optional: Restrict to specific servers
DISCORD_ALLOWED_GUILDS=guild_id_1,guild_id_2

# Optional: Restrict to specific channels
DISCORD_ALLOWED_CHANNELS=channel_id_1,channel_id_2

# Optional: Admin user IDs (can use all commands)
DISCORD_ADMINS=user_id_1,user_id_2
```

## Slash Commands

Register slash commands:

```bash
cd gateway
npm run register-commands
```

Available commands:
| Command | Description |
|---------|-------------|
| `/gltch ask <message>` | Ask GLTCH something |
| `/gltch status` | Show agent status |
| `/gltch mode <mode>` | Change personality |
| `/gltch mood <mood>` | Change mood |
| `/gltch clear` | Clear conversation |

## Security

### Server Restrictions

Limit which servers can use the bot:

```bash
export DISCORD_ALLOWED_GUILDS=123456789,987654321
```

### Channel Restrictions

Limit which channels the bot responds in:

```bash
export DISCORD_ALLOWED_CHANNELS=123456789
```

### Admin Users

Give specific users full access:

```bash
export DISCORD_ADMINS=your_user_id
```

## Troubleshooting

### Bot Offline

1. Check gateway logs
2. Verify bot token is correct
3. Ensure Message Content Intent is enabled

### Bot Not Responding to Messages

1. Check if bot has permissions in the channel
2. Verify the channel is allowed (if restrictions are set)
3. Make sure you're mentioning the bot or using slash commands

### Slash Commands Not Showing

1. Run `npm run register-commands`
2. Wait a few minutes (Discord caches commands)
3. Try refreshing Discord (Ctrl+R)

### Rate Limited

Discord has rate limits. If you see 429 errors:
1. Reduce message frequency
2. Implement message queuing in your adapter
