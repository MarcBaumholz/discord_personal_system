# 🤖 Discord Bots Collection

A comprehensive collection of specialized Discord bots for productivity, planning, and automation. All bots are containerized with Docker for easy deployment and management.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🚀 Features

### 📊 **Real-time Dashboard**
- **Web Dashboard** - Monitor all bots in real-time via web interface
- **Status Monitoring** - See which bots are running, stopped, or failed
- **Health Metrics** - Track uptime, process IDs, and system health
- **Mobile Responsive** - Access from any device with responsive design

### 📅 **Planning & Organization**
- **Weekly Planning Bot** - AI-powered weekly schedule planning with Notion integration
- **Daily Todo Bot** - Daily task management and reminders
- **Routine Bot** - Habit tracking and routine management
- **Plan Bot** - General planning and project management

### 🛒 **Lifestyle & Shopping**
- **Meal Plan Bot** - Meal planning with Todoist integration
- **Wishlist Bot** - Product tracking and wishlist management
- **Preisvergleich Bot** - Price comparison and deal alerts

### 💰 **Finance**
- **Finance Bot** - Budget tracking and financial management
- **Todo Bot** - Task management with shopping list integration

## 🏗️ Architecture

- **Containerized**: All bots run in Docker for isolation and easy deployment
- **Environment-based**: All secrets and configuration via environment variables
- **Multi-service**: Each bot operates independently
- **Auto-restart**: Built-in health checks and restart policies
- **Scalable**: Easy to add new bots or modify existing ones

## 📦 Quick Start

### Prerequisites
- Docker & Docker Compose
- Discord Bot Token
- API keys for integrated services (Notion, OpenRouter, etc.)

### 1. Clone Repository
```bash
git clone https://github.com/MarcBaumholz/discord-bots-collection.git
cd discord-bots-collection
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your actual values
nano .env
```

### 3. Deploy with Docker
```bash
# Build and start all bots
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Access dashboard
open http://localhost:8080
```

### 4. Monitor Your Bots
- **Web Dashboard**: Open `http://localhost:8080` in your browser
- **Real-time Status**: See which bots are running, their uptime, and health
- **Mobile Access**: Dashboard works on phones and tablets

## ⚙️ Configuration

### Required Environment Variables

```bash
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token

# Channel IDs (Get from Discord Developer Mode)
HAUSHALTSPLAN_CHANNEL_ID=123456789
ERINNERUNGEN_CHANNEL_ID=123456789
TODOLISTE_CHANNEL_ID=123456789
# ... (see .env.example for complete list)

# API Keys
NOTION_TOKEN=your_notion_token
OPENROUTER_API_KEY=your_openrouter_key
TODOIST_API_KEY=your_todoist_key

# Database IDs
WEEKLY_PLANNING_DATABASE_ID=your_notion_db_id
# ... (see .env.example for complete list)
```

### Discord Setup
1. Create a Discord Application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a Bot and get the token
3. Invite bot to your server with appropriate permissions
4. Enable Developer Mode in Discord to get Channel IDs

## 🤖 Bot Details

### Weekly Planning Bot
- **Features**: AI-powered weekly planning, Notion integration
- **Commands**: `/plan_week`, `/add_task`, `/view_schedule`
- **Integration**: Notion databases, OpenRouter AI

### Daily Todo Bot
- **Features**: Daily task tracking, completion status
- **Commands**: `!todo [task]`, `!complete [id]`, `!list`
- **Storage**: Local JSON storage

### Routine Bot
- **Features**: Habit tracking, routine scheduling
- **Commands**: `/add_routine`, `/check_routine`, `/stats`
- **Integration**: Notion tracking, AI insights

### Meal Plan Bot
- **Features**: Weekly meal planning, grocery integration
- **Commands**: `/plan_meals`, `/grocery_list`, `/recipes`
- **Integration**: Todoist for shopping lists

### Preisvergleich Bot
- **Features**: Price tracking, deal alerts
- **Commands**: `/track_price`, `/price_alert`, `/deals`
- **Integration**: Web scraping, Notion database

### Wishlist Bot
- **Features**: Product wishlist, price monitoring
- **Commands**: `/add_wish`, `/check_prices`, `/wishlist`
- **Integration**: Notion database, price APIs

## 🐳 Docker Management

### Essential Commands
```bash
# Start all bots and dashboard
docker compose up -d

# Stop all bots and dashboard
docker compose down

# Restart after code changes
docker compose up --build -d

# View logs
docker compose logs [bot-name]

# Check status
docker compose ps

# Access dashboard
curl http://localhost:8080/api/status  # API status
open http://localhost:8080             # Web dashboard
```

### Health Monitoring
- Built-in health checks for all containers
- Automatic restart on failure
- Log aggregation and monitoring

## 📊 Dashboard Usage

### Access the Dashboard
Once your container is running, you can access the real-time dashboard at:
- **Local**: `http://localhost:8080`
- **Remote**: `http://your-server-ip:8080`

### Dashboard Features
- **Real-time Updates**: Status updates every 5 seconds automatically
- **Bot Status Cards**: Visual indicators for each bot (green=running, red=failed, yellow=stopped)
- **System Overview**: Total bots, running count, failed count, system uptime
- **Mobile Support**: Responsive design works on phones, tablets, and desktops
- **Process Information**: PID, uptime, and working directory for each bot

### Understanding Bot Status
- 🟢 **Running**: Bot is active and functioning normally
- 🟡 **Stopped**: Bot was running but has stopped (may restart automatically)
- 🔴 **Failed**: Bot failed to start or crashed
- ⚪ **Unknown**: Status cannot be determined

## 🔧 Development

### Adding a New Bot
1. Create bot directory in `bots/`
2. Implement bot with environment variable configuration
3. Add to `run_all_bots.py`
4. Update `docker-compose.yml` with new environment variables
5. Test locally and deploy

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run specific bot
python bots/daily_todo_bot/daily_todo_bot.py

# Run with dashboard
python start_services.py
```

## 📊 Monitoring & Logs

### Log Management
```bash
# View all logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View specific bot logs
docker compose logs discord-bots
```

### Performance Monitoring
- Container health status
- Resource usage tracking
- Error rate monitoring

## 🔒 Security

- **No hardcoded secrets** - All sensitive data in environment variables
- **Container isolation** - Each service runs in isolated environment
- **Non-root execution** - Containers run with limited privileges
- **Environment separation** - Clear separation between dev/prod configs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-bot`)
3. Commit your changes (`git commit -am 'Add new bot'`)
4. Push to branch (`git push origin feature/new-bot`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Marc Baumholz**
- GitHub: [@MarcBaumholz](https://github.com/MarcBaumholz)
- Website: [marcbaumholz.de](https://marcbaumholz.de)
- LinkedIn: [Marc Baumholz](https://linkedin.com/in/marcbaumholz)

## 🙏 Acknowledgments

- Discord.py community for excellent documentation
- Docker team for containerization platform
- Open source contributors to integrated APIs

---

⭐ **Star this repository if you find it useful!** # discord_personal_system
