# Telegram Integration

Connect GLTCH to Telegram to chat from your phone or any device.

## Setup

### 1. Create a Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Follow the prompts to name your bot
4. Copy the **bot token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Configure GLTCH

Set the bot token in your environment:

```bash
export TELEGRAM_BOT_TOKEN=your-bot-token-here
```

Or add it via the Web UI:
1. Open http://localhost:3000
2. Go to **Settings > API Keys**
3. Click **Add Key** next to Telegram
4. Paste your bot token

### 3. Start the Gateway

```bash
cd gateway
npm run dev
```

The gateway will automatically connect to Telegram when a token is configured.

## Usage

1. Open Telegram
2. Search for your bot by name
3. Start a conversation with `/start`
4. Chat normally!

## Commands

All GLTCH commands work in Telegram:

```
/help    - Show commands
/status  - Agent status
/mode    - Change personality
/clear   - Clear history
```

## Features

### Private Chats
- Full GLTCH access
- Persistent session per user

### Group Chats
- Mention the bot: `@YourBot hello`
- Or reply to bot messages
- Separate session per group

### Media Support
- Text messages ✅
- Images (coming soon)
- Voice (coming soon)

## Configuration Options

```bash
# Bot token (required)
TELEGRAM_BOT_TOKEN=your-token

# Optional: Restrict to specific users
TELEGRAM_ALLOWED_USERS=user_id_1,user_id_2

# Optional: Restrict to specific groups
TELEGRAM_ALLOWED_GROUPS=group_id_1,group_id_2
```

## Security

### Restrict Access

By default, anyone can message your bot. To restrict:

1. Get your Telegram user ID (message @userinfobot)
2. Set allowed users:
   ```bash
   export TELEGRAM_ALLOWED_USERS=123456789
   ```

### Webhook Mode (Advanced)

For production, use webhooks instead of polling:

```bash
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your-secret
```

## Troubleshooting

### Bot Not Responding

1. Check gateway logs for connection errors
2. Verify bot token is correct
3. Ensure gateway is running with `--host 0.0.0.0` if accessing remotely

### Messages Not Sending

1. Check if user/group is in allowed list (if configured)
2. Verify network connectivity
3. Check Telegram API status

### Duplicate Messages

This usually indicates the gateway restarted. Sessions are preserved, but in-flight messages may be duplicated.
