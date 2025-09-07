# {BOT_NAME} Discord Bot

A Discord bot that [describe what your bot does].

## Features

- 🤖 [Feature 1]
- 📊 [Feature 2]
- 💾 [Feature 3]
- ✅ [Feature 4]

## Quick Setup

1. **Clone/Copy this template**
2. **Replace all `{BOT_NAME}` placeholders** in the files with your actual bot name
3. **Configure environment variables** in the main discord `.env` file:
   ```bash
   DISCORD_TOKEN=your_discord_token
   # Add any additional environment variables your bot needs
   ```
4. **Customize the bot.py** with your specific logic
5. **Update requirements.txt** with any additional dependencies
6. **Build and run**:
   ```bash
   chmod +x setup.sh restart_bot.sh
   ./setup.sh build
   ./setup.sh start
   ```

## Files to Customize

### Essential Files (Replace {BOT_NAME}):
- `docker-compose.yml.template` → `docker-compose.yml`
- `setup.sh` (replace all {BOT_NAME} placeholders)
- `restart_bot.sh` (replace all {BOT_NAME} placeholders)
- `README.md` (this file)

### Bot Logic:
- `bot.py` - Main bot code (add your custom functionality here)
- `requirements.txt` - Add your dependencies

## Environment Variables

Add these to your main discord `.env` file (`../../../.env`):

```bash
# Required
DISCORD_TOKEN=your_discord_bot_token

# Add any additional variables your bot needs:
# API_KEY=your_api_key
# DATABASE_URL=your_database_url
# NOTION_TOKEN=your_notion_token
# OPENROUTER_API_KEY=your_openrouter_api_key
```

## Usage

### Setup Commands:
```bash
./setup.sh build     # Build the Docker image
./setup.sh start     # Start the bot
./setup.sh stop      # Stop the bot
./setup.sh restart   # Restart the bot
./setup.sh logs      # View real-time logs
./setup.sh status    # Show current status
./setup.sh cleanup   # Stop and remove everything
```

### Quick Restart:
```bash
./restart_bot.sh
```

## Bot Commands

- `!status` - Check if the bot is running
- `!help` - Show available commands
- [Add your custom commands here]

## Development

1. **Test locally** first by running `python bot.py` directly
2. **Check logs** with `./setup.sh logs`
3. **Update code** and restart with `./restart_bot.sh`
4. **Monitor health** with `docker ps` to see if container is healthy

## Project Structure

```
your_bot/
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── bot.py                  # Main bot code
├── requirements.txt        # Python dependencies
├── setup.sh               # Setup and management script
├── restart_bot.sh         # Quick restart script
├── .dockerignore          # Docker ignore rules
├── README.md              # This file
├── logs/                  # Bot logs (created automatically)
└── data/                  # Persistent data (created automatically)
```

## Based on Money Bot Template

This template is based on the successful Money Bot implementation that includes:
- ✅ Docker containerization
- ✅ Health checks
- ✅ Persistent logging
- ✅ Auto-restart on failure
- ✅ Security (non-root user)
- ✅ Environment variable management
- ✅ Easy setup and management scripts

## Troubleshooting

### Bot won't start:
1. Check if Discord token is correct in `.env`
2. Check logs: `./setup.sh logs`
3. Ensure all {BOT_NAME} placeholders are replaced

### Container not healthy:
1. Check bot logs for errors
2. Verify all required environment variables are set
3. Test bot code locally first

### Permission errors:
```bash
chmod +x setup.sh restart_bot.sh
```

## Next Steps

1. Customize `bot.py` with your specific bot logic
2. Add any required dependencies to `requirements.txt`
3. Update this README with your bot's specific features
4. Test thoroughly before deploying to production
