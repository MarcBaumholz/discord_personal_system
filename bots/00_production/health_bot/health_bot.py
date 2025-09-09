"""Main Health Bot with Discord integration and daily scheduling."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config
from oura_client import OuraClient, HealthData
from health_analyzer import HealthAnalyzer, HealthInsight

# Import bot status manager
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from bot_status_utils import BotStatusManager

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
        
        # Cooldown tracking to prevent duplicate reports
        self.last_report_time = None
        self.report_cooldown_minutes = 15  # Minimum 15 minutes between reports
        
        # Initialize status manager
        self.status_manager = BotStatusManager(self, "Health Bot")
        
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
            lambda: self.send_daily_health_report(force=True),
            CronTrigger(hour=hour, minute=minute),
            id='daily_health_report'
        )
        
        self.scheduler.start()
        logger.info(f"Daily health report scheduled for {self.config.DAILY_SCHEDULE_TIME}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Health channel ID: {self.config.HEALTH_CHANNEL_ID}')
        
        # Send custom health bot startup message
        await self.send_health_bot_startup_message()
    
    async def send_health_bot_startup_message(self):
        """Send a custom startup message explaining what the health bot does."""
        logger.info("🏥 Sending custom Health Bot startup message...")
        try:
            channel = self.get_channel(self.config.HEALTH_CHANNEL_ID)
            if not channel:
                logger.error(f"Could not find health channel with ID {self.config.HEALTH_CHANNEL_ID}")
                return
            
            # Create health bot specific startup embed
            embed = discord.Embed(
                title="🏥 Health Bot ist online!",
                description="**Dein persönlicher Gesundheitsassistent ist bereit!**",
                color=0x00ff88,  # Health green color
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🔄 Automatische Berichte",
                value=f"Täglich um **{self.config.DAILY_SCHEDULE_TIME}** Uhr",
                inline=True
            )
            
            embed.add_field(
                name="📊 Überwachte Daten",
                value="• Kalorien (Gesamt & Aktiv)\n• Schritte\n• Oura Ring Daten",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Deine Ziele",
                value=f"• Kalorien: {self.config.TARGET_CALORIES:,}\n• Aktiv: {self.config.TARGET_ACTIVE_CALORIES:,}\n• Schritte: {self.config.TARGET_STEPS:,}",
                inline=True
            )
            
            embed.add_field(
                name="💬 Befehle",
                value="• `health` - Sofortiger Bericht\n• `status` - Bot Status\n• `!healthtest` - Manueller Test",
                inline=False
            )
            
            embed.add_field(
                name="🤖 Bot Status",
                value="✅ Verbunden mit Discord\n✅ Oura API konfiguriert\n✅ Scheduler aktiv",
                inline=False
            )
            
            embed.set_footer(text="Health Bot • Dein täglicher Gesundheitsbegleiter")
            
            await channel.send(embed=embed)
            logger.info("✅ Health Bot startup message sent successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to send health bot startup message: {e}")
    
    async def on_command_error(self, ctx, error):
        """Handle command errors gracefully."""
        if isinstance(error, commands.CommandNotFound):
            # Don't show "command not found" errors to users
            logger.warning(f"Unknown command attempted: {ctx.message.content}")
            # Instead, check if it's a health-related message and respond appropriately
            content = ctx.message.content.lower().strip()
            if any(keyword in content for keyword in ["health", "status", "report"]):
                await ctx.send("🔄 Generating your health report...")
                await self.send_daily_health_report()
            return
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ This command can only be used in the health channel.")
            return
        else:
            logger.error(f"Command error: {error}")
            await self._send_user_friendly_error(ctx.channel, "Sorry, something went wrong with that command. Please try again or type 'health' for a health report.")
    
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
        if "health" in content and not content.startswith("!"):
            try:
                await message.channel.send("🔄 Generating your health report...")
                await self.send_daily_health_report()
            except Exception as e:
                logger.error(f"Error processing health keyword: {e}")
                await self._send_user_friendly_error(message.channel, "Sorry, I had trouble generating your health report. Please try again in a few minutes.")
        
        # React to "status" keyword  
        elif "status" in content and not content.startswith("!"):
            try:
                await self.send_bot_status(message.channel)
            except Exception as e:
                logger.error(f"Error processing status keyword: {e}")
                await self._send_user_friendly_error(message.channel, "Sorry, I had trouble showing the bot status. Please try again.")
        
        # Process commands as well
        await self.process_commands(message)
        
    async def send_daily_health_report(self, force=False):
        """Send daily health report to Discord channel."""
        try:
            # Check cooldown to prevent duplicate reports (unless forced)
            if not force and self.last_report_time:
                time_since_last = datetime.now() - self.last_report_time
                if time_since_last.total_seconds() < (self.report_cooldown_minutes * 60):
                    remaining_minutes = self.report_cooldown_minutes - (time_since_last.total_seconds() / 60)
                    logger.info(f"Report cooldown active. {remaining_minutes:.1f} minutes remaining.")
                    
                    # Send cooldown message only if manually triggered
                    if not force:
                        channel = self.get_channel(self.config.HEALTH_CHANNEL_ID)
                        if channel:
                            await channel.send(f"⏰ Health report cooldown active. Please wait {remaining_minutes:.1f} more minutes.")
                    return
            
            logger.info("Generating daily health report...")
            
            # Validate API connection first
            if not await self._validate_api_connection():
                await self._send_user_friendly_error(
                    self.get_channel(self.config.HEALTH_CHANNEL_ID),
                    "🔌 Cannot connect to Oura Ring API. Please check your internet connection and try again later."
                )
                return
            
            # Get yesterday's data
            health_data = self.oura_client.get_yesterday_data()
            if not health_data:
                await self._send_user_friendly_error(
                    self.get_channel(self.config.HEALTH_CHANNEL_ID),
                    "📡 No health data available from your Oura Ring yet. Data typically syncs with a 1-2 day delay. Please try again tomorrow."
                )
                return
            
            # Validate data quality
            if not self._validate_data_quality(health_data):
                await self._send_user_friendly_error(
                    self.get_channel(self.config.HEALTH_CHANNEL_ID),
                    "⚠️ Health data appears incomplete. Your Oura Ring may still be syncing. Please try again later."
                )
                return
            
            # Analyze health data
            insight = self.health_analyzer.analyze(health_data)
            
            # Send Discord message
            await self._send_health_message(health_data, insight)
            
            # Update last report time
            self.last_report_time = datetime.now()
            
            logger.info("Daily health report sent successfully")
            
        except Exception as e:
            logger.error(f"Error in daily health report: {e}")
            await self._send_user_friendly_error(
                self.get_channel(self.config.HEALTH_CHANNEL_ID),
                "🚨 Sorry, I encountered an issue generating your health report. This usually resolves itself - please try again in a few minutes."
            )
    
    async def _validate_api_connection(self) -> bool:
        """Validate API connection before attempting data retrieval."""
        try:
            # Try a simple API call to check connectivity
            test_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            response = self.oura_client.session.get(
                f"{self.oura_client.BASE_URL}/daily_sleep",
                params={"start_date": test_date, "end_date": test_date},
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"API connection validation failed: {e}")
            return False
    
    def _validate_data_quality(self, health_data: HealthData) -> bool:
        """Validate that health data contains real, meaningful information."""
        # Check if we have at least some meaningful data
        has_sleep_data = health_data.sleep_score is not None and health_data.sleep_score > 0
        has_readiness_data = health_data.readiness_score is not None and health_data.readiness_score > 0
        has_activity_data = (health_data.total_calories > 0 or health_data.steps > 0)
        
        # We need at least sleep OR readiness data for a meaningful report
        return has_sleep_data or has_readiness_data or has_activity_data
    
    async def _send_health_message(self, health_data: HealthData, insight: HealthInsight):
        """Send formatted health message to Discord."""
        channel = self.get_channel(self.config.HEALTH_CHANNEL_ID)
        if not channel:
            logger.error(f"Could not find channel with ID: {self.config.HEALTH_CHANNEL_ID}")
            return
        
        # Create rich embed with data source indicators
        embed = discord.Embed(
            title="📊 Daily Health Report - LIVE DATA",
            description=f"**Status: {insight.status.value}** (Score: {insight.score}/100)",
            color=self._get_status_color(insight.status.value),
            timestamp=datetime.now()
        )
        
        # Add health data fields with availability indicators
        if health_data.total_calories > 0 or health_data.steps > 0:
            embed.add_field(
                name="🔥 Calories (Real Data)",
                value=f"**Total:** {health_data.total_calories:,}\n**Active:** {health_data.active_calories:,}",
                inline=True
            )
            
            embed.add_field(
                name="👟 Steps (Real Data)",
                value=f"{health_data.steps:,}",
                inline=True
            )
        else:
            embed.add_field(
                name="⏳ Activity Data",
                value="Not yet available\n(5-day sync delay)",
                inline=True
            )
        
        # Add sleep data if available
        if health_data.sleep_score:
            embed.add_field(
                name="😴 Sleep Score (Real Data)",
                value=f"{health_data.sleep_score}/100",
                inline=True
            )
        
        # Add readiness data if available
        if health_data.readiness_score:
            embed.add_field(
                name="🏃 Readiness Score (Real Data)",
                value=f"{health_data.readiness_score}/100",
                inline=True
            )
        
        embed.add_field(
            name="📅 Data Date",
            value=f"{health_data.date}\n*(Most recent available)*",
            inline=True
        )
        
        # Add insight message
        embed.add_field(
            name="💭 Analysis",
            value=insight.message,
            inline=False
        )
        
        # Add individual insights (2 specific recommendations)
        if hasattr(insight, 'individual_insights') and insight.individual_insights:
            insights_text = "\n".join([f"• {insight}" for insight in insight.individual_insights])
            embed.add_field(
                name="🎯 Personal Insights for Today",
                value=insights_text,
                inline=False
            )
        
        # Add calories analysis if available
        if hasattr(insight, 'calories_analysis') and insight.calories_analysis:
            calories_data = insight.calories_analysis
            self._add_calories_analysis_to_embed(embed, calories_data)
        
        # Add tips
        if insight.tips:
            tips_text = "\n".join([f"• {tip}" for tip in insight.tips])
            embed.add_field(
                name="💡 Tips for Today",
                value=tips_text,
                inline=False
            )
        
        # Add data source information
        data_sources = []
        if health_data.sleep_score: data_sources.append("Sleep")
        if health_data.readiness_score: data_sources.append("Readiness")
        if health_data.total_calories > 0: data_sources.append("Activity")
        if health_data.spo2_average: data_sources.append("SpO2")
        
        embed.add_field(
            name="📊 Data Sources",
            value=f"✅ {', '.join(data_sources) if data_sources else 'Limited data available'}",
            inline=False
        )
        
        embed.set_footer(text="✅ Powered by Oura Ring - All data is LIVE and real-time synced")
        
        await channel.send(embed=embed)
    
    def _add_calories_analysis_to_embed(self, embed: discord.Embed, calories_data: dict):
        """Add calories analysis to the Discord embed."""
        try:
            consumed = calories_data.get("consumed_calories", 0)
            burned = calories_data.get("burned_calories", 0)
            net = calories_data.get("net_calories", 0)
            balance_status = calories_data.get("balance_status", "unknown")
            food_count = calories_data.get("food_count", 0)
            
            # Determine emoji and color based on balance
            if balance_status == "calorie_surplus":
                emoji = "📈"
                color_emoji = "🔴"
            elif balance_status == "calorie_deficit":
                emoji = "📉"
                color_emoji = "🟡"
            elif balance_status == "calorie_balanced":
                emoji = "⚖️"
                color_emoji = "🟢"
            else:
                emoji = "❓"
                color_emoji = "⚪"
            
            # Create calories summary
            calories_text = f"{color_emoji} **Calories Balance**\n"
            calories_text += f"🍽️ **Consumed:** {consumed:,} kcal ({food_count} meals)\n"
            calories_text += f"🔥 **Burned:** {burned:,} kcal\n"
            calories_text += f"{emoji} **Net:** {net:+,} kcal"
            
            # Add status message
            if balance_status == "calorie_surplus":
                calories_text += "\n\n⚠️ **Calorie Surplus** - Consider reducing intake or increasing activity"
            elif balance_status == "calorie_deficit":
                calories_text += "\n\n💪 **Calorie Deficit** - Great for weight loss, ensure adequate nutrition"
            elif balance_status == "calorie_balanced":
                calories_text += "\n\n✅ **Well Balanced** - Perfect calorie balance for maintenance"
            elif balance_status == "no_food_data":
                calories_text += "\n\n📝 **No Food Data** - Track your meals to see calorie balance"
            
            embed.add_field(
                name="🍽️ Calories Analysis",
                value=calories_text,
                inline=False
            )
            
            # Add food entries if available
            food_entries = calories_data.get("food_entries", [])
            if food_entries and len(food_entries) > 0:
                # Show top 5 food entries
                top_foods = food_entries[:5]
                food_text = "\n".join([
                    f"• {entry['food_name']} ({entry['calories']} kcal)"
                    for entry in top_foods
                ])
                
                if len(food_entries) > 5:
                    food_text += f"\n• ... and {len(food_entries) - 5} more meals"
                
                embed.add_field(
                    name="🍽️ Yesterday's Meals",
                    value=food_text,
                    inline=False
                )
                
        except Exception as e:
            logger.error(f"Error adding calories analysis to embed: {e}")
    
    def _get_status_color(self, status: str) -> int:
        """Get Discord embed color based on status."""
        color_map = {
            "🟢 Excellent": 0x00FF00,  # Green
            "🟡 Good": 0xFFFF00,       # Yellow  
            "🟠 Average": 0xFF8C00,    # Orange
            "🔴 Needs Improvement": 0xFF0000  # Red
        }
        return color_map.get(status, 0x808080)  # Default gray
    
    async def _send_user_friendly_error(self, channel, message: str):
        """Send user-friendly error message to Discord channel."""
        try:
            if channel:
                embed = discord.Embed(
                    title="🤖 Health Bot Notice",
                    description=message,
                    color=0xFFA500,  # Orange for notices
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="💡 Need Help?",
                    value="• Type **'health'** to try generating a report\n• Type **'status'** to check bot status\n• Use **!healthforce** to force a new report",
                    inline=False
                )
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send user-friendly error message: {e}")
    
    async def send_bot_status(self, channel):
        """Send bot status to specified channel."""
        try:
            # Test API connection
            api_status = "✅ Connected" if await self._validate_api_connection() else "❌ Connection Issues"
            
            embed = discord.Embed(
                title="🤖 Health Bot Status",
                color=0x00FF00 if "✅" in api_status else 0xFF0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="⏰ Schedule",
                value=f"Daily report at {self.config.DAILY_SCHEDULE_TIME}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Targets",
                value=f"Calories: {self.config.TARGET_CALORIES:,}\nActive: {self.config.TARGET_ACTIVE_CALORIES:,}\nSteps: {self.config.TARGET_STEPS:,}",
                inline=True
            )
            
            embed.add_field(
                name="🔗 API Status",
                value=api_status,
                inline=True
            )
            
            # Add cooldown info
            cooldown_status = "Ready"
            if self.last_report_time:
                time_since_last = datetime.now() - self.last_report_time
                if time_since_last.total_seconds() < (self.report_cooldown_minutes * 60):
                    remaining_minutes = self.report_cooldown_minutes - (time_since_last.total_seconds() / 60)
                    cooldown_status = f"Cooldown: {remaining_minutes:.1f}m remaining"
            
            embed.add_field(
                name="⏱️ Report Status",
                value=cooldown_status,
                inline=True
            )
            
            embed.add_field(
                name="💬 Usage",
                value="• Type **'health'** for instant report\n• Type **'status'** for this info\n• **!healthtest** (respects cooldown)\n• **!healthforce** (ignores cooldown)",
                inline=False
            )
            
            embed.set_footer(text="🔄 Status checked in real-time")
            
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending bot status: {e}")
            await self._send_user_friendly_error(channel, "Sorry, I had trouble checking the bot status.")
    
    @commands.command(name='healthtest')
    async def test_command(self, ctx):
        """Test command to manually trigger health report (respects cooldown)."""
        try:
            if ctx.channel.id != self.config.HEALTH_CHANNEL_ID:
                await ctx.send("❌ This command can only be used in the health channel.")
                return
            
            await ctx.send("🔄 Generating health report...")
            await self.send_daily_health_report()
        except Exception as e:
            logger.error(f"Error in healthtest command: {e}")
            await self._send_user_friendly_error(ctx.channel, "Sorry, the healthtest command encountered an issue.")
    
    @commands.command(name='healthforce')
    async def force_command(self, ctx):
        """Force health report (ignores cooldown - for testing)."""
        try:
            if ctx.channel.id != self.config.HEALTH_CHANNEL_ID:
                await ctx.send("❌ This command can only be used in the health channel.")
                return
            
            await ctx.send("🔄 Forcing health report generation (ignoring cooldown)...")
            await self.send_daily_health_report(force=True)
        except Exception as e:
            logger.error(f"Error in healthforce command: {e}")
            await self._send_user_friendly_error(ctx.channel, "Sorry, the healthforce command encountered an issue.")
    
    @commands.command(name='healthstatus')
    async def status_command(self, ctx):
        """Show bot status and configuration."""
        try:
            if ctx.channel.id != self.config.HEALTH_CHANNEL_ID:
                await ctx.send("❌ This command can only be used in the health channel.")
                return
            
            await self.send_bot_status(ctx.channel)
        except Exception as e:
            logger.error(f"Error in healthstatus command: {e}")
            await self._send_user_friendly_error(ctx.channel, "Sorry, I had trouble checking the status.")


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