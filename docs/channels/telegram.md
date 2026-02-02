# Telegram

Set up GLTCH as a Telegram bot.

## Prerequisites

- A Telegram account
- The Telegram app

## Setup

### 1. Create a Bot with BotFather

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow the prompts:
   - Choose a name (e.g., "GLTCH")
   - Choose a username (must end in `bot`, e.g., `my_gltch_bot`)
4. Copy the **HTTP API token**

### 2. Configure GLTCH

Add your token to `.env`:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

Or use the CLI:

```bash
gltch channels login telegram
```

### 3. Start the Gateway

```bash
gltch gateway start
```

### 4. Start Chatting

Find your bot on Telegram and send a message!

## Usage

### In Direct Messages

All messages get a response.

### In Groups

Add the bot to a group. It responds when:
- Mentioned with `@your_bot_username`
- Replying to a bot message

## Configuration Options

Restrict access to specific users:

```json
{
  "channels": {
    "telegram": {
      "allowedUsers": ["username1", "username2"]
    }
  }
}
```

## Bot Commands

You can configure bot commands in BotFather:

1. Send `/setcommands` to @BotFather
2. Select your bot
3. Send:
```
help - Show available commands
status - Check agent status
mode - Change personality mode
```

## Troubleshooting

### Bot doesn't respond

1. Make sure the gateway is running
2. Check the token is correct
3. Verify with: `gltch channels status`

### "Unauthorized" error

The bot token may be invalid. Generate a new one with @BotFather.

### Messages not received in groups

Make sure the bot is mentioned or you're replying to a bot message.
