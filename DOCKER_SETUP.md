# Discord Bots Docker Setup Guide

This guide will help you run your Discord bots in Docker containers for easy management, automatic restarts, and isolation.

## 🚀 Quick Start

If you just want to get started quickly:

```bash
cd /home/pi/Documents/discord
docker compose up -d
```

## 📋 Prerequisites

- ✅ Docker is installed (done!)
- ✅ Docker Compose is available 
- ✅ Discord bot tokens and API keys configured in `.env`

## 🏗️ Project Structure

```
discord/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Container orchestration
├── .dockerignore           # Files to exclude from build
├── .env                    # Environment variables (your secrets)
├── requirements.txt        # Python dependencies
├── run_all_bots.py        # Main bot launcher
├── bots/                  # Individual bot directories
│   ├── todo_bot/
│   ├── daily_todo_bot/
│   ├── meal_plan_bot/
│   ├── Weekly_planning_bot/
│   ├── routine_bot/
│   ├── Wishlist_bot/
│   ├── plan_bot/
│   ├── finance_bot/
│   └── preisvergleich_bot/
└── logs/                  # Container logs (created automatically)
```

## 🔧 Setup Instructions

### 1. Environment Variables

Make sure your `.env` file contains all necessary tokens:

```bash
# Check if .env exists and has the required variables
cat .env
```

Required variables:
- `DISCORD_TOKEN` - Your Discord bot token
- `NOTION_TOKEN` - Notion API token
- `OPENROUTER_API_KEY` - OpenRouter API key
- Other bot-specific variables

### 2. Build and Run

```bash
# Navigate to the discord directory
cd /home/pi/Documents/discord

# Build and start the containers
docker compose up -d
```

The `-d` flag runs containers in detached mode (background).

## 🎮 Container Management Commands

### Starting Bots
```bash
# Start all bots
docker compose up -d

# Start and see logs in real-time
docker compose up

# Start specific service
docker compose up discord-bots
```

### Stopping Bots
```bash
# Stop all containers
docker compose down

# Stop but keep containers (can restart quickly)
docker compose stop

# Force stop everything
docker compose kill
```

### Viewing Logs
```bash
# View all logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View logs for last 100 lines
docker compose logs --tail=100

# View logs for specific service
docker compose logs discord-bots
```

### Container Status
```bash
# Check if containers are running
docker compose ps

# View container health
docker ps

# Get detailed container info
docker inspect discord-bots
```

## 🔄 Auto-Restart Features

The setup includes automatic restart capabilities:

- **Restart Policy**: `unless-stopped` - containers restart automatically unless explicitly stopped
- **Health Checks**: Built-in health monitoring every 60 seconds
- **Crash Recovery**: If a bot crashes, Docker will restart the entire container

### Manual Restart
```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart discord-bots

# Rebuild and restart (after code changes)
docker compose up --build -d
```

## 📊 Monitoring & Debugging

### Health Checks
The container includes health checks that verify bots are running:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' discord-bots

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' discord-bots
```

### Accessing Container Shell
```bash
# Open a shell in the running container
docker exec -it discord-bots /bin/bash

# Run a command in the container
docker exec discord-bots python -c "print('Hello from container')"
```

### Resource Usage
```bash
# Monitor resource usage
docker stats discord-bots

# Check container processes
docker exec discord-bots ps aux
```

## 🔧 Updating Bot Code

When you make changes to your bot code:

```bash
# Method 1: Rebuild and restart
docker compose down
docker compose up --build -d

# Method 2: Build new image and restart
docker compose build
docker compose up -d
```

## 📁 Data Persistence

The setup includes persistent volumes for:

- `./logs:/app/logs` - Bot logs
- `./data:/app/data` - Bot data storage
- `./completed_todos.json:/app/completed_todos.json` - Todo data

Data persists even when containers are recreated.

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check build logs
docker compose build

# Check container logs
docker compose logs discord-bots

# Check system resources
docker system df
free -h
```

### Bot Connection Issues
```bash
# Verify environment variables
docker exec discord-bots env | grep DISCORD

# Test network connectivity
docker exec discord-bots ping -c 3 discord.com

# Check DNS resolution
docker exec discord-bots nslookup discord.com
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R pi:pi /home/pi/Documents/discord

# Check Docker permissions
groups $USER
```

### Clean Up Docker Resources
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove all unused resources
docker system prune

# Nuclear option - remove everything
docker system prune -a --volumes
```

## 🔒 Security Considerations

- ✅ Bots run as non-root user inside container
- ✅ Environment variables used for secrets
- ✅ No unnecessary ports exposed
- ✅ Minimal base image used
- ✅ Regular security updates via image rebuilds

## ⚡ Performance Tips

### Resource Limits
Add resource limits to `docker-compose.yml`:

```yaml
services:
  discord-bots:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Log Management
Logs are automatically rotated (max 10MB, 3 files) to prevent disk space issues.

## 🎯 Advanced Usage

### Running Individual Bots
To run specific bots instead of all:

1. Modify `run_all_bots.py` to comment out unwanted bots
2. Rebuild: `docker compose up --build -d`

### Multiple Bot Instances
Create separate docker-compose files for different bot groups:

```bash
# Copy and modify for different setups
cp docker-compose.yml docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

### Custom Scripts
Add scripts to the container:

```bash
# Copy script to container
docker cp myscript.py discord-bots:/app/

# Run custom script
docker exec discord-bots python myscript.py
```

## 🆘 Emergency Procedures

### Complete Reset
```bash
# Stop everything
docker compose down

# Remove container and images
docker compose down --rmi all

# Rebuild from scratch
docker compose up --build -d
```

### Backup Data
```bash
# Backup persistent data
tar -czf discord-bots-backup-$(date +%Y%m%d).tar.gz \
  logs/ data/ completed_todos.json .env
```

### Restore from Backup
```bash
# Stop containers
docker-compose down

# Restore data
tar -xzf discord-bots-backup-YYYYMMDD.tar.gz

# Restart
docker-compose up -d
```

## 📞 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `docker exec discord-bots env`
3. Check container health: `docker inspect discord-bots`
4. Review this guide for troubleshooting steps

## 🎉 Success!

Your Discord bots are now running in Docker with:
- ✅ Automatic restarts on crashes
- ✅ Health monitoring
- ✅ Centralized logging
- ✅ Easy start/stop management
- ✅ Isolated environment
- ✅ Persistent data storage

Enjoy your containerized Discord bots! 🤖🐳 