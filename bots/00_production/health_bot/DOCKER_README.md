# 🏥 Health Bot - Docker Setup

## 🚀 Quick Start

The Health Bot is now containerized and ready to run with Docker! It will automatically send daily health reports at **9:00 AM** with comprehensive analysis including Oura Ring data and Notion calories tracking.

### Prerequisites

- Docker and Docker Compose installed
- All environment variables configured in `/home/pi/Documents/discord/.env`

### 🐳 Docker Commands

Use the management script for easy operations:

```bash
# Build the Docker image
./health_bot_manager.sh build

# Start the Health Bot (runs at 9 AM daily)
./health_bot_manager.sh start

# Check container status
./health_bot_manager.sh status

# View logs
./health_bot_manager.sh logs

# Stop the container
./health_bot_manager.sh stop

# Restart the container
./health_bot_manager.sh restart

# Update and restart
./health_bot_manager.sh update
```

### 📋 Manual Docker Commands

If you prefer manual Docker commands:

```bash
# Build the image
docker build -t health-bot .

# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f health-bot

# Stop
docker-compose down
```

## ⏰ Scheduling

The Health Bot is configured to run daily health reports at **9:00 AM Europe/Berlin timezone**.

### What Happens at 9 AM:

1. **Fetches Yesterday's Data**:
   - Oura Ring: Sleep, readiness, activity, calories burned
   - Notion Database: Calories consumed from food tracking

2. **Analyzes Health Metrics**:
   - Overall health score (0-100)
   - Sleep quality analysis
   - Activity vs readiness balance
   - Calories balance (consumed vs burned)

3. **Sends Discord Report**:
   - Beautiful embed with color-coded status
   - Personalized insights and recommendations
   - Calorie analysis with surplus/deficit status
   - Yesterday's meal breakdown

## 🔧 Configuration

The container uses environment variables from the main `.env` file:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_token
HEALTH_CHANNEL_ID=your_channel_id

# Oura API
OURA_ACCESS_TOKEN=your_oura_token

# Notion API
NOTION_TOKEN=your_notion_token
FOODIATE_DB_ID=your_database_id

# Health Bot Settings (optional)
DAILY_SCHEDULE_TIME=09:00
TARGET_CALORIES=2200
TARGET_ACTIVE_CALORIES=450
TARGET_STEPS=8000
```

## 📊 Features

### ✅ **Working Features**:
- **Daily 9 AM Reports**: Automatic scheduling
- **Oura Ring Integration**: Sleep, readiness, activity data
- **Notion Calories Tracking**: Food consumption analysis
- **Calories Balance**: Consumed vs burned comparison
- **Smart Analysis**: Personalized health insights
- **Discord Integration**: Rich embeds with status indicators
- **Error Handling**: Robust failure recovery
- **Health Monitoring**: Container health checks

### 📈 **Report Example**:
```
📊 Daily Health Report - LIVE DATA
Status: 🟢 Excellent (Score: 86/100)

🔥 Calories (Real Data)
Total: 2,846
Active: 472

👟 Steps (Real Data): 10,771

😴 Sleep Score (Real Data): 87/100
🏃 Readiness Score (Real Data): 84/100

🍽️ Calories Analysis
🟡 Calories Balance
🍽️ Consumed: 1,002 kcal (1 meals)
🔥 Burned: 2,846 kcal
📉 Net: -1,844 kcal

💪 Calorie Deficit - Great for weight loss, ensure adequate nutrition
```

## 🛠️ Troubleshooting

### Container Won't Start:
```bash
# Check logs
./health_bot_manager.sh logs

# Check status
./health_bot_manager.sh status

# Rebuild and restart
./health_bot_manager.sh update
```

### No Reports at 9 AM:
1. Check container is running: `./health_bot_manager.sh status`
2. Verify timezone: Container uses Europe/Berlin
3. Check Discord channel permissions
4. Verify API tokens in logs

### API Connection Issues:
- Check Oura Ring API token
- Verify Notion database access
- Ensure Discord bot permissions

## 📁 File Structure

```
health_bot/
├── Dockerfile                 # Docker image definition
├── docker-compose.yml        # Container orchestration
├── health_bot_manager.sh     # Management script
├── start_health_bot.sh       # Startup script
├── .dockerignore             # Docker build exclusions
├── health_bot.py             # Main bot application
├── oura_client.py            # Oura Ring API client
├── notion_calories_client.py # Notion calories integration
├── health_analyzer.py        # Health analysis engine
├── config.py                 # Configuration management
└── requirements.txt          # Python dependencies
```

## 🔄 Updates

To update the Health Bot:

```bash
# Pull latest changes
git pull

# Update and restart container
./health_bot_manager.sh update
```

## 📝 Logs

Logs are stored in the `logs/` directory and can be viewed with:

```bash
# Real-time logs
./health_bot_manager.sh logs

# Or with docker-compose
docker-compose logs -f health-bot
```

## 🎯 Success Indicators

When everything is working correctly, you should see:

1. **Container Status**: `healthy` and `running`
2. **Daily Reports**: Posted at 9:00 AM in Discord
3. **Logs**: No error messages, successful API calls
4. **Data**: Real Oura Ring and Notion data in reports

---

**The Health Bot is now ready to provide daily health insights with comprehensive analysis! 🏥💪**
