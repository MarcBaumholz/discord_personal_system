# Allgemeine Wohl Bot

Discord bot that tracks household activities and good deeds for the "Allgemeine Wohl" (common good) system.

## Features

- 🏠 Automatically tracks household activities from Discord messages
- 🤖 Uses AI (OpenRouter) to analyze and categorize activities
- 📊 Maintains activity statistics and ground truth database
- 💾 Saves entries to Notion databases
- ✅ Provides visual feedback with reactions and responses

## Setup

1. **Environment Variables**: Ensure these are set in the main discord `.env` file:
   ```bash
   DISCORD_TOKEN=your_discord_token
   NOTION_TOKEN=your_notion_token
   OPENROUTER_API_KEY=your_openrouter_api_key
   ALLGEMEINE_WOHL_CHANNEL_ID=your_channel_id
   ALLGEMEINE_WOHL_DATABASE_ID=your_database_id
   GROUND_TRUTH_DATABASE_ID=your_ground_truth_database_id
   ```

2. **Build and run with Docker**:
   ```bash
   chmod +x setup.sh restart_bot.sh
   ./setup.sh build
   ./setup.sh start
   ```

## Docker Commands

```bash
./setup.sh build     # Build the Docker image
./setup.sh start     # Start the bot
./setup.sh stop      # Stop the bot
./setup.sh restart   # Restart the bot
./setup.sh logs      # View real-time logs
./setup.sh status    # Show current status
./setup.sh cleanup   # Stop and remove everything
./setup.sh backup    # Backup bot state file
./restart_bot.sh     # Quick restart
```

## Bot Functionality

The bot monitors the configured Discord channel and:
- Analyzes messages for household activities
- Categorizes activities using AI
- Maintains a ground truth database of activities
- Tracks activity statistics in bot state
- Saves entries to Notion databases
- Provides feedback and confirmations

## State Management

The bot maintains state in `bot_state.json` which includes:
- Top activities list
- Activity statistics
- Configuration data

Use `./setup.sh backup` to create timestamped backups of the state file.

## Notion Database Structure

The bot works with two Notion databases:
1. **Allgemeine Wohl Database**: Main activity tracking
2. **Ground Truth Database**: Reference activities and categories

## Logging

Logs are stored in the `logs/` directory and can be viewed with:
```bash
./setup.sh logs
```

## Health Monitoring

The container includes health checks to ensure the bot is running properly. Check status with:
```bash
./setup.sh status
```

## ✅ Current Status (September 2025)

**🟢 BOT IS LIVE AND OPERATIONAL**

The Allgemeine Wohl Bot is currently running in a Docker container and fully functional.

### Bot Status
- **Container**: `allgemeinewohl_allgemeine-wohl-bot` - Running (Healthy)
- **Uptime**: 38+ hours
- **Health Check**: ✅ Healthy
- **Last Restart**: September 8, 2025

### Recent Updates
- ✅ **Stable Operation**: Bot running continuously without issues
- ✅ **Docker Health Checks**: Automated monitoring and restart capability
- ✅ **Notion Integration**: Active database connectivity
- ✅ **AI Analysis**: OpenRouter integration working properly
- ✅ **Activity Tracking**: Successfully processing household activities

### Tested Functionality
- ✅ Household activity analysis and categorization
- ✅ Ground truth database maintenance
- ✅ Notion database integration
- ✅ Discord message processing
- ✅ AI-powered activity recognition
