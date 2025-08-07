"""
Bot Status Utilities
Common utilities for Discord bots to send status and startup messages
"""

import os
import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class BotStatusManager:
    """Manages bot status messages and announcements"""
    
    def __init__(self, bot: commands.Bot, bot_name: str = None):
        self.bot = bot
        self.bot_name = bot_name or os.getenv('BOT_NAME', 'Unknown Bot')
        self.bot_location = os.getenv('BOT_LOCATION', 'Local Environment')
        self.startup_message_enabled = os.getenv('BOT_STARTUP_MESSAGE', 'false').lower() == 'true'
        self.status_channel_id = self._get_status_channel_id()
        self.start_time = datetime.now()
    
    def _get_status_channel_id(self) -> Optional[int]:
        """Get the appropriate status channel ID based on bot type"""
        # Try to get specific channel for this bot first
        bot_channel_mapping = {
            'Calories Bot': 'CALORIES_CHANNEL_ID',
            'Health Bot': 'HEALTH_CHANNEL_ID', 
            'Decision Bot': 'DECISION_CHANNEL_ID',
            'DB Bot': 'DB_CHANNEL_ID',
            'Erinnerungen Bot': 'ERINNERUNGEN_CHANNEL_ID',
            'Learning Bot': 'LEARNING_CHANNEL_ID',
            'Personal RSS Bot': 'RSS_CHANNEL_ID',
            'Tagebuch Bot': 'TAGEBUCH_CHANNEL_ID',
            'Weekly Planning Bot': 'WEEKLY_PLANNING_CHANNEL_ID',
            'Preisvergleich Bot': 'PREISVERGLEICH_CHANNEL_ID',
            'Meal Plan Bot': 'MEAL_PLAN_CHANNEL_ID',
            'Weekly Todo Bot': 'TODOLISTE_CHANNEL_ID'
        }
        
        # Get specific channel for this bot
        env_var = bot_channel_mapping.get(self.bot_name)
        if env_var:
            channel_id = os.getenv(env_var)
            if channel_id:
                try:
                    return int(channel_id)
                except ValueError:
                    pass
        
        # Fallback to general status channel
        general_channel = os.getenv('GENERAL_CHANNEL_ID')
        if general_channel:
            try:
                return int(general_channel)
            except ValueError:
                pass
        
        # Final fallback - use the first available channel ID from environment
        for env_var in bot_channel_mapping.values():
            channel_id = os.getenv(env_var)
            if channel_id:
                try:
                    return int(channel_id)
                except ValueError:
                    continue
        
        return None
    
    async def send_startup_message(self):
        """Send a startup message when the bot comes online"""
        if not self.startup_message_enabled:
            return
        
        if not self.status_channel_id:
            logger.warning(f"No status channel configured for {self.bot_name}")
            return
        
        try:
            # Wait for bot to be ready
            await self.bot.wait_until_ready()
            
            channel = self.bot.get_channel(self.status_channel_id)
            if not channel:
                logger.error(f"Could not find channel with ID {self.status_channel_id}")
                return
            
            # Create startup embed
            embed = discord.Embed(
                title="🤖 Bot Status",
                description=f"**{self.bot_name}** is now running!",
                color=0x00ff00,  # Green color
                timestamp=self.start_time
            )
            
            embed.add_field(
                name="📍 Location",
                value=self.bot_location,
                inline=True
            )
            
            embed.add_field(
                name="🕒 Started",
                value=f"<t:{int(self.start_time.timestamp())}:R>",
                inline=True
            )
            
            embed.add_field(
                name="💾 Process Info",
                value=f"PID: {os.getpid()}\nUser: {os.getenv('USER', 'docker')}",
                inline=True
            )
            
            embed.set_footer(text=f"{self.bot_name} • Docker Deployment")
            
            await channel.send(embed=embed)
            logger.info(f"✅ Startup message sent for {self.bot_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send startup message for {self.bot_name}: {e}")
    
    async def send_shutdown_message(self):
        """Send a shutdown message when the bot goes offline"""
        if not self.startup_message_enabled or not self.status_channel_id:
            return
        
        try:
            channel = self.bot.get_channel(self.status_channel_id)
            if not channel:
                return
            
            uptime = datetime.now() - self.start_time
            
            embed = discord.Embed(
                title="🔴 Bot Status",
                description=f"**{self.bot_name}** is shutting down",
                color=0xff0000,  # Red color
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="⏱️ Uptime",
                value=str(uptime).split('.')[0],  # Remove microseconds
                inline=True
            )
            
            embed.add_field(
                name="📍 Location",
                value=self.bot_location,
                inline=True
            )
            
            embed.set_footer(text=f"{self.bot_name} • Docker Deployment")
            
            await channel.send(embed=embed)
            logger.info(f"✅ Shutdown message sent for {self.bot_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send shutdown message for {self.bot_name}: {e}")
    
    async def send_status_update(self, message: str, status_type: str = "info"):
        """Send a general status update"""
        if not self.status_channel_id:
            return
        
        try:
            channel = self.bot.get_channel(self.status_channel_id)
            if not channel:
                return
            
            color_map = {
                "info": 0x0099ff,     # Blue
                "success": 0x00ff00,  # Green  
                "warning": 0xffaa00,  # Orange
                "error": 0xff0000     # Red
            }
            
            embed = discord.Embed(
                title=f"📊 {self.bot_name} Status",
                description=message,
                color=color_map.get(status_type, 0x0099ff),
                timestamp=datetime.now()
            )
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"❌ Failed to send status update for {self.bot_name}: {e}")

# Convenience function for easy integration
def add_status_to_bot(bot: commands.Bot, bot_name: str = None) -> BotStatusManager:
    """
    Add status management to a Discord bot
    
    Usage:
    status_manager = add_status_to_bot(bot, "My Bot Name")
    
    Then in your bot's on_ready event:
    await status_manager.send_startup_message()
    """
    return BotStatusManager(bot, bot_name)

# Decorator for automatic startup message
def with_startup_message(bot_name: str = None):
    """
    Decorator to automatically add startup messages to a bot
    
    Usage:
    @with_startup_message("My Bot")
    class MyBot(commands.Bot):
        async def on_ready(self):
            await self.status_manager.send_startup_message()
    """
    def decorator(bot_class):
        original_init = bot_class.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.status_manager = BotStatusManager(self, bot_name)
        
        bot_class.__init__ = new_init
        return bot_class
    
    return decorator 