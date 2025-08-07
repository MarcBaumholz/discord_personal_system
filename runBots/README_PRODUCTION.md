# Production Bot Management Scripts

Simple and efficient scripts to manage all Discord bots in the `00_production` folder.

## 📁 Files

- **`start_production_bots.py`** - Start all production bots automatically
- **`stop_all_bots.py`** - Emergency stop script for all bot processes  
- **`run_all_bots.py`** - Advanced bot manager with monitoring (existing)

## 🚀 Quick Start

### Start All Production Bots
```bash
cd /home/pi/Documents/discord/runBots
python3 start_production_bots.py
```

### Stop All Bots (Emergency)
```bash
python3 stop_all_bots.py
```

## ✨ Features

### `start_production_bots.py`
- **🔍 Auto-discovery**: Automatically finds all bot files in production folders
- **📊 Real-time monitoring**: Shows status, PID, and uptime for each bot
- **🔄 Background monitoring**: Detects when bots stop and reports it
- **⚡ Graceful shutdown**: Ctrl+C stops all bots cleanly
- **📋 Detailed logging**: Logs to file and console
- **🎯 Simple**: Just run and forget

### Discovery Logic
The script automatically finds bot files using these patterns:
- `{folder_name}_bot.py` (e.g., `calories_bot.py`)
- `{folder_name}.py` (e.g., `health_bot.py`) 
- `bot.py` (generic bot file)

### Status Display
```
🤖 PRODUCTION BOTS STATUS
================================================================================
Bot Name                  Status     PID      Uptime         
--------------------------------------------------------------------------------
Calories Bot              🟢 RUNNING 123456   2h 15m         
Health Bot                🟢 RUNNING 123457   2h 15m         
Decision Bot              🔴 STOPPED N/A      N/A            
...
```

### Environment Setup
Each bot runs with:
- **Working directory**: Set to the bot's folder
- **PYTHONPATH**: Includes the bot's directory
- **PYTHONUNBUFFERED**: Ensures real-time output

## 🛑 Emergency Stop

The `stop_all_bots.py` script:
1. Finds all Python processes with "bot" in the name
2. Sends SIGTERM for graceful shutdown (3 second wait)
3. Sends SIGKILL for any remaining processes
4. Reports all stopped processes

## 📊 Monitoring

The production bot starter includes:
- **Real-time status**: Updated every 30 seconds
- **Failure detection**: Automatically detects when bots crash
- **Uptime tracking**: Shows how long each bot has been running
- **Status reports**: Full status printed every 5 minutes

## 🔧 Usage Examples

### Start and monitor all bots:
```bash
python3 start_production_bots.py
# Press Ctrl+C when you want to stop all bots
```

### View logs:
```bash
tail -f /home/pi/Documents/discord/runBots/logs/production_bots.log
```

### Force stop everything:
```bash
python3 stop_all_bots.py --force  # Kills ALL Python processes (careful!)
```

## 📂 Production Folder Structure

The script expects this structure:
```
discord/bots/00_production/
├── Calories_bot/
│   └── calories_bot.py
├── health_bot/
│   └── health_bot.py
├── decision_bot/
│   └── decision_bot.py
├── money_bot-1/
│   └── bot.py
└── ...
```

## 🎯 Advantages Over Complex Scripts

1. **Simple**: No complex configuration needed
2. **Auto-discovery**: Finds bots automatically  
3. **Focused**: Only handles production bots
4. **Reliable**: Less code = fewer bugs
5. **Clear output**: Easy to see what's happening
6. **Fast startup**: Minimal delay between bot starts

## ⚠️ Notes

- Each bot must be in its own subfolder under `00_production/`
- Bot files should follow the naming conventions above
- Make sure all bot dependencies are installed
- The script creates logs in `/home/pi/Documents/discord/runBots/logs/`

## 🔄 Integration

This script works alongside the existing bot infrastructure and can replace more complex bot management when you just need to "start everything quickly."
