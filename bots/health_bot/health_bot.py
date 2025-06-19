"""Main Health Bot with Discord integration and daily scheduling."""
import asyncio
import logging
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config
from oura_client import OuraClient, HealthData
from health_analyzer import HealthAnalyzer, HealthInsight

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthBot(commands.Bot):
    """Discord bot for daily health monitoring."""
    
    def __init__(self):
        """Initialize the health bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        self.config = Config()
        self.oura_client = OuraClient(self.config.OURA_ACCESS_TOKEN)
        self.health_analyzer = HealthAnalyzer()
        self.scheduler = AsyncIOScheduler()
        
    async def setup_hook(self) -> None:
        """Setup bot and scheduler."""
        logger.info("Setting up Health Bot...")
        
        # Validate configuration
        if not self.config.validate():
            logger.error("Invalid configuration. Please check your environment variables.")
            return
        
        # Setup daily scheduler
        hour, minute = map(int, self.config.DAILY_SCHEDULE_TIME.split(':'))
        self.scheduler.add_job(
            self.send_daily_health_report,
            CronTrigger(hour=hour, minute=minute),
            id='daily_health_report'
        )
        
        self.scheduler.start()
        logger.info(f"Daily health report scheduled for {self.config.DAILY_SCHEDULE_TIME}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Health channel ID: {self.config.HEALTH_CHANNEL_ID}')
    
    async def on_message(self, message):
        """Handle incoming messages."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
        
        # Only respond in the health channel
        if message.channel.id != self.config.HEALTH_CHANNEL_ID:
            return
        
        # Convert message to lowercase for easier matching
        content = message.content.lower().strip()
        
        # React to "health" keyword
        if "health" in content:
            await message.channel.send("🔄 Generating your health report...")
            await self.send_daily_health_report()
        
        # React to "status" keyword  
        elif "status" in content:
            await self.send_bot_status(message.channel)
        
        # Process commands as well
        await self.process_commands(message)
        
    async def send_daily_health_report(self):
        """Send daily health report to Discord channel."""
        try:
            logger.info("Generating daily health report...")
            
            # Get yesterday's data
            health_data = self.oura_client.get_yesterday_data()
            if not health_data:
                await self._send_error_message("Failed to fetch health data from Oura Ring")
                return
            
            # Analyze health data
            insight = self.health_analyzer.analyze(health_data)
            
            # Send Discord message
            await self._send_health_message(health_data, insight)
            
            logger.info("Daily health report sent successfully")
            
        except Exception as e:
            logger.error(f"Error in daily health report: {e}")
            await self._send_error_message(f"Error generating health report: {str(e)}")
    
    async def _send_health_message(self, health_data: HealthData, insight: HealthInsight):
        """Send formatted health message to Discord."""
        channel = self.get_channel(self.config.HEALTH_CHANNEL_ID)
        if not channel:
            logger.error(f"Could not find channel with ID: {self.config.HEALTH_CHANNEL_ID}")
            return
        
        # Create rich embed
        embed = discord.Embed(
            title="📊 Daily Health Report",
            description=f"**Status: {insight.status.value}** (Score: {insight.score}/100)",
            color=self._get_status_color(insight.status.value),
            timestamp=datetime.now()
        )
        
        # Add health data fields
        embed.add_field(
            name="🔥 Calories",
            value=f"**Total:** {health_data.total_calories}\n**Active:** {health_data.active_calories}",
            inline=True
        )
        
        embed.add_field(
            name="👟 Steps",
            value=f"{health_data.steps:,}",
            inline=True
        )
        
        embed.add_field(
            name="📅 Date",
            value=health_data.date,
            inline=True
        )
        
        # Add insight message
        embed.add_field(
            name="💭 Analysis",
            value=insight.message,
            inline=False
        )
        
        # Add tips
        if insight.tips:
            tips_text = "\n".join([f"• {tip}" for tip in insight.tips])
            embed.add_field(
                name="💡 Tips for Today",
                value=tips_text,
                inline=False
            )
        
        # Add targets for reference
        embed.add_field(
            name="🎯 Daily Targets",
            value=f"Calories: {self.config.TARGET_CALORIES} | Active: {self.config.TARGET_ACTIVE_CALORIES} | Steps: {self.config.TARGET_STEPS:,}",
            inline=False
        )
        
        embed.set_footer(text="Powered by Oura Ring")
        
        await channel.send(embed=embed)
    
    def _get_status_color(self, status: str) -> int:
        """Get Discord embed color based on status."""
        color_map = {
            "🟢 Excellent": 0x00FF00,  # Green
            "🟡 Good": 0xFFFF00,       # Yellow  
            "🟠 Average": 0xFF8C00,    # Orange
            "🔴 Needs Improvement": 0xFF0000  # Red
        }
        return color_map.get(status, 0x808080)  # Default gray
    
    async def _send_error_message(self, error: str):
        """Send error message to Discord channel."""
        try:
            channel = self.get_channel(self.config.HEALTH_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="⚠️ Health Bot Error",
                    description=error,
                    color=0xFF0000,
                    timestamp=datetime.now()
                )
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def send_bot_status(self, channel):
        """Send bot status to specified channel."""
        embed = discord.Embed(
            title="🤖 Health Bot Status",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="⏰ Schedule",
            value=f"Daily report at {self.config.DAILY_SCHEDULE_TIME}",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Targets",
            value=f"Calories: {self.config.TARGET_CALORIES}\nActive: {self.config.TARGET_ACTIVE_CALORIES}\nSteps: {self.config.TARGET_STEPS:,}",
            inline=True
        )
        
        embed.add_field(
            name="🔗 API Status",
            value="✅ Connected to Oura",
            inline=True
        )
        
        embed.add_field(
            name="💬 Usage",
            value="Type 'health' for report\nType 'status' for this info",
            inline=False
        )
        
        await channel.send(embed=embed)
    
    @commands.command(name='healthtest')
    async def test_command(self, ctx):
        """Test command to manually trigger health report."""
        if ctx.channel.id != self.config.HEALTH_CHANNEL_ID:
            await ctx.send("This command can only be used in the health channel.")
            return
        
        await ctx.send("🔄 Generating health report...")
        await self.send_daily_health_report()
    
    @commands.command(name='healthstatus')
    async def status_command(self, ctx):
        """Show bot status and configuration."""
        if ctx.channel.id != self.config.HEALTH_CHANNEL_ID:
            await ctx.send("This command can only be used in the health channel.")
            return
        
        embed = discord.Embed(
            title="🤖 Health Bot Status",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="⏰ Schedule",
            value=f"Daily report at {self.config.DAILY_SCHEDULE_TIME}",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Targets",
            value=f"Calories: {self.config.TARGET_CALORIES}\nActive: {self.config.TARGET_ACTIVE_CALORIES}\nSteps: {self.config.TARGET_STEPS:,}",
            inline=True
        )
        
        embed.add_field(
            name="🔗 API Status",
            value="✅ Connected to Oura",
            inline=True
        )
        
        await ctx.send(embed=embed)


async def main():
    """Main function to run the bot."""
    bot = HealthBot()
    
    try:
        await bot.start(bot.config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        if bot.scheduler.running:
            bot.scheduler.shutdown()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main()) 