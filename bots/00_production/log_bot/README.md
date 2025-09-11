# Discord Log Bot

A centralized logging bot that collects logs from all active Discord channels and forwards them to a designated logs channel with clear headers and separation.

## Features

- **Centralized Logging**: Collects logs from all monitored channels
- **Bot Identification**: Each log includes clear bot identification headers
- **Message Formatting**: Properly formatted logs with timestamps and separators
- **Docker Support**: Easy deployment via Docker Compose
- **Health Monitoring**: Built-in health checks and status commands

## Configuration

The bot monitors the following channels (configured via environment variables):

- Calories Bot: `CALORIES_CHANNEL_ID`
- Money Bot: `FINANCE_CHANNEL_ID`
- Todo Bot: `TODOLISTE_CHANNEL_ID`
- Health Bot: `HEALTH_CHANNEL_ID`
- Learning Bot: `LEARNING_CHANNEL_ID`
- RSS Bot: `RSS_CHANNEL_ID`
- YouTube Bot: `YOUTUBE_CHANNEL_ID`
- Meal Plan Bot: `MEAL_PLAN_CHANNEL_ID`
- Routine Bot: `ROUTINE_CHANNEL_ID`
- Weekly Planning Bot: `WEEKLY_PLANNING_CHANNEL_ID`
- Decision Bot: `DECISION_CHANNEL_ID`
- Erinnerungen Bot: `ERINNERUNGEN_CHANNEL_ID`
- Preisvergleich Bot: `DB_CHANNEL_ID`
- Allgemeine Wohl Bot: `GENERAL_CHANNEL_ID`
- Tagebuch Bot: `TAGEBUCH_CHANNEL_ID`

## Log Format

Each log message includes:

```
🤖 BOT_NAME | HH:MM:SS
──────────────────────────────────────────────────
👤 Username | 📺 #channel-name
Message content here
📎 Attachments: filename1, filename2 (if any)
📋 Embeds: 2 embed(s) (if any)
──────────────────────────────────────────────────
```

## Commands

- `!log_status` - Show bot status and monitored channels
- `!log_test` - Send a test message to verify functionality

## Deployment

### Docker Compose

```bash
cd /home/pi/Documents/discord/bots/00_production/log_bot
docker-compose up -d
```

### Manual Run

```bash
cd /home/pi/Documents/discord/bots/00_production/log_bot
python log_bot.py
```

## Testing

Run the test script to verify configuration:

```bash
python test_log_bot.py
```

## Environment Variables

Required environment variables:

- `DISCORD_TOKEN` - Discord bot token
- `LOGS_CHANNEL_ID` - Target channel for logs (default: 1415623068965142580)
- All channel IDs for monitored bots (see Configuration section)

## Logs

The bot creates logs in the `./logs/` directory with rotation support.
