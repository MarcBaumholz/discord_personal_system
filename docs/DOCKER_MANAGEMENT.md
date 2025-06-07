# Discord Bots Docker Management Guide

## ✅ Current Status

Your Discord bots are now successfully running in Docker! All hardcoded IDs and API keys have been moved to the `.env` file for better security and management.

## 🚀 Quick Commands

### Starting the Bots
```bash
cd /home/pi/Documents/discord
docker compose up -d
```

### Stopping the Bots
```bash
docker compose down
```

### Viewing Logs
```bash
# View all logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View last 50 lines
docker compose logs --tail=50
```

### Checking Status
```bash
# Check if container is running
docker compose ps

# Check container health
docker ps
```

### Restarting After Changes
```bash
# Rebuild and restart (after code changes)
docker compose down
docker compose up --build -d
```

## 📋 What Was Fixed

### 1. Environment Variables Migration
All hardcoded values have been moved to `.env`:

**Channel IDs:**
- `HAUSHALTSPLAN_CHANNEL_ID=1361083769427202291`
- `ERINNERUNGEN_CHANNEL_ID=1361083869729919046`
- `TODOLISTE_CHANNEL_ID=1361083732638957669`
- `EINKAUFSLISTE_CHANNEL_ID=1361083312109522956`
- `WISHLIST_CHANNEL_ID=1361083698560368953`
- `FINANCE_CHANNEL_ID=1361083750000000000`
- `ROUTINE_CHANNEL_ID=1366687489720451114`
- `WEEKLY_PLANNING_CHANNEL_ID=1368180016785002536`

**API Keys:**
- `NOTION_TOKEN=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`
- `OPENROUTER_API_KEY=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`
- `TODOIST_API_KEY=b420f2b62422561cfd1aaa5cf3fc025818376d8c`

**Database IDs:**
- `WEEKLY_PLANNING_DATABASE_ID=1e8d42a1faf5801cb087ef00741d7785`
- `NOTION_INTERESTS_DATABASE_ID=1e8d42a1faf5801797f1e32471a5a152`
- `ROUTINE_DATABASE_ID=1e4d42a1faf5808ca3d5edbc77dd402e`
- `PREISVERGLEICH_DATABASE_ID=1e5d42a1faf580fe9450efa4d13cc4a2`

### 2. Updated Bot Files
The following bots were updated to use environment variables:

- ✅ **Daily Todo Bot** - Channel ID moved to env
- ✅ **Meal Plan Bot** - API keys and channel ID moved to env
- ✅ **Plan Bot** - Channel ID moved to env
- ✅ **Todo Bot** - Channel IDs moved to env
- ✅ **Routine Bot** - Database ID and API key fallbacks removed
- ✅ **Weekly Planning Bot** - Database ID and API key fallbacks removed
- ✅ **Wishlist Bot** - Channel ID fallback removed
- ✅ **Preisvergleich Bot** - Database ID environment variable fixed

### 3. Docker Configuration
- Updated `docker-compose.yml` with all environment variables
- All secrets are now properly passed from `.env` to container
- Container runs with non-root user for security
- Health checks implemented
- Auto-restart on failure configured

## 🔧 Troubleshooting

### Container Won't Start
```bash
# Check build logs
docker compose build

# Check container logs
docker compose logs discord-bots

# Check if .env file exists and has correct values
cat .env
```

### Bot Connection Issues
```bash
# Check if Discord token is valid
docker compose logs discord-bots | grep -i "discord"

# Verify environment variables are loaded
docker compose exec discord-bots env | grep -E "(DISCORD|NOTION|OPENROUTER)"
```

### After Code Changes
```bash
# Always rebuild after changing bot code
docker compose down
docker compose up --build -d
```

## 📁 File Structure
```
discord/
├── .env                    # All secrets and configuration
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Container image definition
├── requirements.txt       # Python dependencies
├── run_all_bots.py        # Main bot launcher
├── bots/                  # Individual bot directories
│   ├── daily_todo_bot/
│   ├── meal_plan_bot/
│   ├── plan_bot/
│   ├── routine_bot/
│   ├── todo_bot/
│   ├── Weekly_planning_bot/
│   ├── Wishlist_bot/
│   └── preisvergleich_bot/
├── logs/                  # Container logs (mounted)
└── data/                  # Persistent data (mounted)
```

## 🔒 Security Notes

1. **Never commit `.env` file** - It contains sensitive API keys
2. **Backup your `.env` file** - Store it securely outside the repository
3. **Rotate API keys regularly** - Update them in `.env` and restart container
4. **Container runs as non-root** - Better security isolation

## 🔄 Maintenance

### Daily Operations
- Check logs: `docker compose logs --tail=100`
- Check status: `docker compose ps`

### Weekly Operations
- Update dependencies: `docker compose build --no-cache`
- Check disk usage: `docker system df`

### Monthly Operations
- Clean unused images: `docker system prune`
- Backup `.env` file
- Review and rotate API keys if needed

## 🆘 Emergency Commands

### Stop Everything Immediately
```bash
docker compose kill
```

### Complete Reset
```bash
# Stop everything
docker compose down

# Remove container and images
docker compose down --rmi all

# Rebuild from scratch
docker compose up --build -d
```

### Access Container Shell (for debugging)
```bash
docker compose exec discord-bots bash
```

## ✅ Success Indicators

Your setup is working correctly if:
1. `docker compose ps` shows container as "Up" and "healthy"
2. `docker compose logs` shows "All 6 bots are now running!"
3. No error messages in the logs
4. Bots respond to commands in Discord channels

## 📞 Next Steps

1. Test each bot in their respective Discord channels
2. Monitor logs for any runtime errors
3. Set up log rotation if needed
4. Consider setting up monitoring/alerting for production use

Your Discord bots are now properly containerized and ready for production use! 🎉 