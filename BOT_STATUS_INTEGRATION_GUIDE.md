# Bot Status Integration Guide

## 🎯 Overview
This guide shows how to add startup status messages to existing Discord bots using the `BotStatusManager` utility.

## 📋 Integration Steps

### Step 1: Import the Status Manager
Add this import to your bot file:

```python
# Import bot status manager  
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from bot_status_utils import BotStatusManager
```

### Step 2: Initialize in Bot Constructor
Add this to your bot's `__init__` method:

```python
def __init__(self):
    # ... existing initialization ...
    
    # Initialize status manager
    self.status_manager = BotStatusManager(self, "Your Bot Name")
```

### Step 3: Send Startup Message in on_ready
Modify your `on_ready` method:

```python
async def on_ready(self):
    """Called when the bot is ready."""
    logger.info(f'{self.user} has connected to Discord!')
    
    # Send startup message
    await self.status_manager.send_startup_message()
    
    # ... rest of your on_ready code ...
```

## 🤖 Complete Example

Here's a complete example for a simple bot:

```python
import discord
from discord.ext import commands
import logging
import sys
import os

# Import bot status manager
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from bot_status_utils import BotStatusManager

logger = logging.getLogger(__name__)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize status manager
        self.status_manager = BotStatusManager(self, "My Bot")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'{self.user} has connected to Discord!')
        
        # Send startup message
        await self.status_manager.send_startup_message()

# Run the bot
if __name__ == "__main__":
    bot = MyBot()
    bot.run(os.getenv('DISCORD_TOKEN'))
```

## 🔧 Environment Variables

The status manager uses these environment variables (automatically set by the bot runner):

- `BOT_STARTUP_MESSAGE`: Set to "true" to enable startup messages
- `BOT_NAME`: Name of the bot (set automatically)
- `BOT_LOCATION`: Location where bot is running (set automatically)

## 📍 Channel Configuration

The status manager automatically finds the right channel using these environment variables:

- `CALORIES_CHANNEL_ID` for Calories Bot
- `HEALTH_CHANNEL_ID` for Health Bot  
- `ERINNERUNGEN_CHANNEL_ID` for Erinnerungen Bot
- `TODOLISTE_CHANNEL_ID` for Todo Bots
- ... (see `bot_status_utils.py` for complete list)

If no specific channel is found, it falls back to the first available channel ID.

## 📊 Status Message Features

The startup message includes:
- ✅ Bot name and status
- 📍 Runtime location (Docker Container)
- 🕒 Startup timestamp
- 💾 Process information (PID, user)

## 🚫 Optional Shutdown Messages

You can also send shutdown messages by calling:

```python
await self.status_manager.send_shutdown_message()
```

## 🔧 Additional Status Updates

Send custom status updates:

```python
await self.status_manager.send_status_update("Custom message", "info")
# status_type can be: "info", "success", "warning", "error"
```

## 🎯 Bot Integration Checklist

For each bot, ensure:
- [ ] Status manager imported
- [ ] Status manager initialized in `__init__`
- [ ] Startup message called in `on_ready`
- [ ] Appropriate channel ID environment variable set
- [ ] Bot tested with `BOT_STARTUP_MESSAGE=true`

## 📝 Integration Status

### Production Bots (00_production/)
- [x] Health Bot - Integrated ✅
- [ ] Calories Bot 
- [ ] Decision Bot
- [ ] Erinnerungen Bot
- [ ] Tagebuch Bot
- [ ] Preisvergleich Bot
- [ ] Meal Plan Bot
- [ ] Weekly Todo Bot

### Other Bots
- [ ] DB Bot (00_improve/)
- [ ] Learning Bot
- [ ] Personal RSS Bot  
- [ ] Weekly Planning Bot

## 🚀 Testing

To test status messages locally:
```bash
export BOT_STARTUP_MESSAGE=true
export BOT_NAME="Test Bot"
export BOT_LOCATION="Local Development"
python your_bot.py
``` 