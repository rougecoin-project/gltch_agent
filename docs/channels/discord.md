# Discord

Set up GLTCH as a Discord bot.

## Prerequisites

- A Discord account
- A server where you have admin permissions

## Setup

### 1. Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it "GLTCH" (or your preference)
4. Click "Create"

### 2. Create a Bot

1. Go to the "Bot" section
2. Click "Add Bot"
3. Copy the **Bot Token** (keep this secret!)

### 3. Enable Intents

Under "Privileged Gateway Intents", enable:
- **MESSAGE CONTENT INTENT** (required for reading messages)

### 4. Configure GLTCH

Add your token to `.env`:

```bash
DISCORD_BOT_TOKEN=your-bot-token-here
```

Or use the CLI:

```bash
gltch channels login discord
```

### 5. Invite the Bot

1. Go to "OAuth2" > "URL Generator"
2. Select scopes:
   - `bot`
3. Select permissions:
   - Read Messages/View Channels
   - Send Messages
   - Read Message History
4. Copy the generated URL
5. Open it and select your server

### 6. Start the Gateway

```bash
gltch gateway start
```

## Usage

### In Direct Messages

Just message the bot directly. All messages will get a response.

### In Servers

The bot responds when:
- Mentioned with `@GLTCH`
- Message starts with `!gltch` (configurable)

Example:
```
@GLTCH scan my network
```

## Configuration Options

In your config:

```json
{
  "channels": {
    "discord": {
      "prefix": "!gltch",
      "mentionRequired": false
    }
  }
}
```

## Troubleshooting

### Bot doesn't respond

1. Check the bot has MESSAGE CONTENT INTENT enabled
2. Verify the bot has permissions in the channel
3. Check gateway logs: `gltch gateway logs`

### "Missing Access" error

The bot needs to be invited with the correct permissions. Re-generate the invite URL with required permissions.
