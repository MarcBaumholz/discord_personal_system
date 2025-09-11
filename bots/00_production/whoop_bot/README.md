# WHOOP Discord Bot

A Discord bot that automatically sends daily WHOOP health and fitness data to a specified Discord channel.

## Features

- **Daily WHOOP Data Reports**: Automatically sends yesterday's WHOOP data every 24 hours
- **Comprehensive Health Metrics**: Includes cycles, sleep, recovery, and workout data
- **Beautiful Discord Embeds**: Rich, color-coded displays with emojis and formatting
- **Token Persistence**: Saves WHOOP API tokens to avoid re-authentication
- **Manual Commands**: `!whoop` and `!whoop_now` commands for on-demand data

## Data Included

### 📈 Daily Cycles
- Strain score with color coding (🟢 High, 🟡 Medium, 🔴 Low)
- Average and maximum heart rate
- Energy expenditure in kilojoules

### 😴 Sleep Analysis
- Sleep performance score
- Total sleep duration
- Sleep stage breakdown (Light, Deep, REM)
- Respiratory rate

### 💪 Recovery Metrics
- Recovery score
- Resting heart rate
- Heart rate variability (HRV)
- Blood oxygen saturation (SpO2)
- Skin temperature

### 🏃 Workout Activities
- Sport type and duration
- Strain score and heart rate zones
- Energy expenditure
- Distance (when available)

## Configuration

The bot requires the following environment variables in `.env`:

```env
# WHOOP API Configuration
WHOOP_CLIENT_ID=your_client_id
WHOOP_CLIENT_SECRET=your_client_secret
WHOOP_REDIRECT_URI=http://localhost:8080/callback

# Discord Configuration
DISCORD_TOKEN=your_discord_token

# Channel ID (hardcoded in bot)
WHOOP_CHANNEL_ID=1415625361106014348
```

## Usage

### Running the Bot
```bash
python bot.py
```

### Manual Commands
- `!whoop` - Get yesterday's WHOOP data
- `!whoop_now` - Get current/latest WHOOP data

### Testing
```bash
# Test WHOOP API connection
python test_whoop_bot.py

# Test Discord connection
python test_discord_connection.py

# Send test data to Discord
python send_test_data.py
```

## File Structure

```
whoop_bot/
├── bot.py                    # Main bot runner
├── whoop_discord_bot.py      # Discord bot implementation
├── src/                      # WHOOP API client library
│   ├── config.py
│   ├── oauth.py
│   ├── client.py
│   ├── models.py
│   ├── token_manager.py
│   └── rate_limiter.py
├── test_whoop_bot.py         # WHOOP API tests
├── test_discord_connection.py # Discord connection tests
├── send_test_data.py         # Manual data sending
├── debug_api.py              # API response debugging
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── whoop_tokens.json         # Saved WHOOP tokens
└── README.md                 # This file
```

## Docker Deployment

### Quick Start
```bash
# Start the bot
./start_whoop_bot.sh

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down

# Update the bot
docker-compose down && docker-compose build && docker-compose up -d
```

### Docker Commands
```bash
# Build image
docker-compose build

# Start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart container
docker-compose restart

# Check status
docker-compose ps
```

### Scheduled Delivery
- **Daily at 12:00 AM (midnight)**: Automatically sends yesterday's WHOOP data
- **Manual commands**: `!whoop`, `!whoop_now`, `!whoop_schedule`
- **Admin test**: `!whoop_test_schedule` (triggers scheduled task manually)

## Integration with Multibot

The bot is designed to work with the existing multibot system. To add it to the multibot runner, add this line to `start_multibot.py`:

```python
("whoop", "bots/00_production/whoop_bot/bot.py"),
```

## Authentication

The bot uses OAuth 2.0 for WHOOP API authentication. Tokens are automatically saved and refreshed, so manual re-authentication is rarely needed.

## Error Handling

- Automatic retry on API failures
- Graceful handling of missing data
- Comprehensive logging
- Discord error reporting

## Rate Limiting

Respects WHOOP API rate limits:
- 100 requests per minute
- 10,000 requests per day

## Logging

All bot activity is logged to `whoop_bot.log` with timestamps and detailed error information.
