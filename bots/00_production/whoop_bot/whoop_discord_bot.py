#!/usr/bin/env python3
"""
WHOOP Discord Bot - Sends daily WHOOP data to Discord channel
"""

import os
import sys
import asyncio
import discord
from datetime import datetime, timedelta, time
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth
from src.client import WhoopClient
from src.token_manager import TokenManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whoop_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
WHOOP_CHANNEL_ID = 1415625361106014348  # Your specified channel ID

class WhoopDiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize WHOOP API
        self.whoop_config = WhoopConfig.from_env()
        self.whoop_oauth = WhoopOAuth(self.whoop_config)
        self.token_manager = TokenManager()
        self.whoop_client = WhoopClient(self.whoop_config, self.whoop_oauth, self.token_manager)
        
        # Check if we have valid tokens
        if not self.whoop_client.is_authenticated():
            logger.error("No valid WHOOP tokens found. Please authenticate first.")
            sys.exit(1)
    
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Start the daily task
        self.daily_whoop_data.start()
        logger.info("Daily WHOOP data task started")
    
    def format_duration(self, seconds):
        """Format seconds into hours and minutes"""
        if not seconds:
            return "N/A"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
    def get_score_emoji(self, score):
        """Get emoji based on score value"""
        if not score:
            return "❓"
        if isinstance(score, dict):
            score_val = score.get('score', 0)
        else:
            score_val = score
        
        if score_val >= 80:
            return "🟢"
        elif score_val >= 60:
            return "🟡"
        else:
            return "🔴"
    
    async def get_yesterday_data(self):
        """Get WHOOP data from yesterday"""
        try:
            # Use UTC for date comparison since WHOOP timestamps are in UTC
            yesterday_utc = datetime.utcnow() - timedelta(days=1)
            yesterday_str = yesterday_utc.strftime('%Y-%m-%d')
            
            logger.info(f"Fetching WHOOP data for {yesterday_str} (UTC)")
            
            # Get profile
            profile = self.whoop_client.get_user_profile()
            
            # Get cycles (last 10 days to find yesterday's)
            cycles = self.whoop_client.get_cycles(limit=10)
            yesterday_cycle = None
            logger.info(f"Checking {len(cycles.records)} cycles for date {yesterday_utc.date()}")
            for cycle_data in cycles.records:
                cycle = self.whoop_client.get_cycle(cycle_data['id'])
                logger.info(f"Cycle date: {cycle.start.date()}, matches: {cycle.start.date() == yesterday_utc.date()}")
                if cycle.start.date() == yesterday_utc.date():
                    yesterday_cycle = cycle
                    logger.info(f"Found yesterday's cycle: {cycle.id}")
                    break
            
            # Get sleep data (last 10 days to find yesterday's)
            sleep_data = self.whoop_client.get_sleep_data(limit=10)
            yesterday_sleep = None
            logger.info(f"Checking {len(sleep_data.records)} sleep records for date {yesterday_utc.date()}")
            for sleep_record in sleep_data.records:
                sleep = self.whoop_client.get_sleep(sleep_record['id'])
                logger.info(f"Sleep date: {sleep.start.date()}, matches: {sleep.start.date() == yesterday_utc.date()}")
                if sleep.start.date() == yesterday_utc.date():
                    yesterday_sleep = sleep
                    logger.info(f"Found yesterday's sleep: {sleep.id}")
                    break
            
            # Get recovery data (last 10 days to find yesterday's)
            recovery_data = self.whoop_client.get_recovery_data(limit=10)
            yesterday_recovery = None
            logger.info(f"Checking {len(recovery_data.records)} recovery records for date {yesterday_utc.date()}")
            for recovery_record in recovery_data.records:
                # Recovery records don't have direct 'id' field, they have cycle_id
                # We need to get the cycle first to get the start date
                try:
                    cycle = self.whoop_client.get_cycle(recovery_record['cycle_id'])
                    logger.info(f"Recovery cycle date: {cycle.start.date()}, matches: {cycle.start.date() == yesterday_utc.date()}")
                    if cycle.start.date() == yesterday_utc.date():
                        yesterday_recovery = recovery_record
                        logger.info(f"Found yesterday's recovery for cycle: {cycle.id}")
                        break
                except Exception as e:
                    logger.warning(f"Error getting cycle for recovery: {e}")
                    continue
            
            # Get workouts from yesterday
            workouts = self.whoop_client.get_workouts(limit=10)
            yesterday_workouts = []
            logger.info(f"Checking {len(workouts.records)} workouts for date {yesterday_utc.date()}")
            for workout_record in workouts.records:
                workout = self.whoop_client.get_workout(workout_record['id'])
                logger.info(f"Workout date: {workout.start.date()}, matches: {workout.start.date() == yesterday_utc.date()}")
                if workout.start.date() == yesterday_utc.date():
                    yesterday_workouts.append(workout)
                    logger.info(f"Found yesterday's workout: {workout.sport_name}")
            
            return {
                'profile': profile,
                'cycle': yesterday_cycle,
                'sleep': yesterday_sleep,
                'recovery': yesterday_recovery,
                'workouts': yesterday_workouts,
                'date': yesterday_str
            }
            
        except Exception as e:
            logger.error(f"Error fetching WHOOP data: {e}")
            return None
    
    def create_whoop_embed(self, data):
        """Create a Discord embed with WHOOP data"""
        if not data:
            embed = discord.Embed(
                title="🏃‍♂️ WHOOP Daily Report - Error",
                description="Failed to fetch WHOOP data",
                color=0xff0000
            )
            return embed
        
        yesterday = data['date']
        profile = data['profile']
        cycle = data['cycle']
        sleep = data['sleep']
        recovery = data['recovery']
        workouts = data['workouts']
        
        # Create main embed
        embed = discord.Embed(
            title=f"🏃‍♂️ WHOOP Daily Report - {yesterday}",
            description=f"**{profile.first_name} {profile.last_name or ''}**'s WHOOP data from yesterday",
            color=0x00ff00
        )
        
        # Add profile info
        embed.add_field(
            name="👤 Profile",
            value=f"**User ID:** {profile.user_id}\n**Email:** {profile.email}",
            inline=False
        )
        
        # Add cycle data
        if cycle and cycle.score:
            strain = cycle.score.strain if cycle.score.strain else "N/A"
            avg_hr = cycle.score.average_heart_rate if cycle.score.average_heart_rate else "N/A"
            max_hr = cycle.score.max_heart_rate if cycle.score.max_heart_rate else "N/A"
            energy = cycle.score.kilojoules if cycle.score.kilojoules else "N/A"
            
            embed.add_field(
                name="📈 Daily Cycle",
                value=f"**Strain:** {self.get_score_emoji(strain)} {strain}\n"
                      f"**Avg HR:** {avg_hr} bpm\n"
                      f"**Max HR:** {max_hr} bpm\n"
                      f"**Energy:** {energy:.0f} kJ" if isinstance(energy, (int, float)) else f"**Energy:** {energy}",
                inline=True
            )
        else:
            embed.add_field(
                name="📈 Daily Cycle",
                value="No cycle data available",
                inline=True
            )
        
        # Add sleep data
        if sleep:
            sleep_score = "N/A"
            if sleep.score:
                if isinstance(sleep.score, dict):
                    sleep_score = sleep.score.get('score', 'N/A')
                else:
                    sleep_score = sleep.score
            
            # Calculate sleep stages
            total_sleep = 0
            light_sleep = 0
            deep_sleep = 0
            rem_sleep = 0
            
            if sleep.stage_summary:
                light_sleep = sleep.stage_summary.light_sleep_time_seconds or 0
                deep_sleep = sleep.stage_summary.slow_wave_sleep_time_seconds or 0
                rem_sleep = sleep.stage_summary.rem_sleep_time_seconds or 0
                total_sleep = light_sleep + deep_sleep + rem_sleep
            
            embed.add_field(
                name="😴 Sleep Analysis",
                value=f"**Score:** {self.get_score_emoji(sleep_score)} {sleep_score}\n"
                      f"**Total:** {self.format_duration(total_sleep)}\n"
                      f"**Light:** {self.format_duration(light_sleep)}\n"
                      f"**Deep:** {self.format_duration(deep_sleep)}\n"
                      f"**REM:** {self.format_duration(rem_sleep)}\n"
                      f"**Resp Rate:** {sleep.respiratory_rate:.1f}" if sleep.respiratory_rate else f"**Resp Rate:** N/A",
                inline=True
            )
        else:
            embed.add_field(
                name="😴 Sleep Analysis",
                value="No sleep data available",
                inline=True
            )
        
        # Add recovery data
        if recovery:
            # Handle recovery data structure (it's a dict, not an object)
            if isinstance(recovery, dict):
                score_data = recovery.get('score', {})
                recovery_score = score_data.get('recovery_score') if score_data else "N/A"
                resting_hr = score_data.get('resting_heart_rate') if score_data else "N/A"
                hrv = f"{score_data.get('hrv_rmssd_milli', 0):.1f} ms" if score_data and score_data.get('hrv_rmssd_milli') else "N/A"
                spo2 = f"{score_data.get('spo2_percentage', 0):.1f}%" if score_data and score_data.get('spo2_percentage') else "N/A"
                skin_temp = f"{score_data.get('skin_temp_celsius', 0):.1f}°C" if score_data and score_data.get('skin_temp_celsius') else "N/A"
            else:
                recovery_score = recovery.score or "N/A"
                resting_hr = recovery.resting_heart_rate or "N/A"
                hrv = f"{recovery.hrv_rmssd_milli_seconds:.1f} ms" if recovery.hrv_rmssd_milli_seconds else "N/A"
                spo2 = f"{recovery.spo2_percentage:.1f}%" if recovery.spo2_percentage else "N/A"
                skin_temp = f"{recovery.skin_temp_celsius:.1f}°C" if recovery.skin_temp_celsius else "N/A"
            
            embed.add_field(
                name="💪 Recovery Metrics",
                value=f"**Score:** {self.get_score_emoji(recovery_score)} {recovery_score}\n"
                      f"**Resting HR:** {resting_hr} bpm\n"
                      f"**HRV:** {hrv}\n"
                      f"**SpO2:** {spo2}\n"
                      f"**Skin Temp:** {skin_temp}",
                inline=True
            )
        else:
            embed.add_field(
                name="💪 Recovery Metrics",
                value="No recovery data available",
                inline=True
            )
        
        # Add workouts
        if workouts:
            workout_text = ""
            for i, workout in enumerate(workouts[:3]):  # Show max 3 workouts
                strain = workout.score.strain if workout.score and workout.score.strain else "N/A"
                avg_hr = workout.score.average_heart_rate if workout.score and workout.score.average_heart_rate else "N/A"
                max_hr = workout.score.max_heart_rate if workout.score and workout.score.max_heart_rate else "N/A"
                energy = workout.score.kilojoules if workout.score and workout.score.kilojoules else "N/A"
                
                workout_text += f"**{workout.sport_name.title()}**\n"
                workout_text += f"Strain: {self.get_score_emoji(strain)} {strain} | "
                workout_text += f"HR: {avg_hr}-{max_hr} bpm\n"
                if isinstance(energy, (int, float)):
                    workout_text += f"Energy: {energy:.0f} kJ\n"
                else:
                    workout_text += f"Energy: {energy}\n"
                workout_text += "\n"
            
            if len(workouts) > 3:
                workout_text += f"... and {len(workouts) - 3} more workouts"
            
            embed.add_field(
                name="🏃 Workouts",
                value=workout_text or "No workout data",
                inline=False
            )
        else:
            embed.add_field(
                name="🏃 Workouts",
                value="No workouts recorded",
                inline=False
            )
        
        # Add footer
        embed.set_footer(text=f"WHOOP API v2 • Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return embed
    
    @tasks.loop(time=datetime.time(hour=0, minute=0))  # Run at midnight (12:00 AM)
    async def daily_whoop_data(self):
        """Send daily WHOOP data to the channel at midnight"""
        try:
            channel = self.get_channel(WHOOP_CHANNEL_ID)
            if not channel:
                logger.error(f"Channel {WHOOP_CHANNEL_ID} not found")
                return
            
            logger.info("🕛 Midnight WHOOP data task triggered - Fetching yesterday's data...")
            data = await self.get_yesterday_data()
            
            if data:
                embed = self.create_whoop_embed(data)
                await channel.send(embed=embed)
                logger.info(f"✅ Sent daily WHOOP data to channel {WHOOP_CHANNEL_ID}")
            else:
                await channel.send("❌ Failed to fetch WHOOP data for yesterday")
                logger.error("Failed to fetch WHOOP data")
                
        except Exception as e:
            logger.error(f"Error in daily_whoop_data task: {e}")
    
    @daily_whoop_data.before_loop
    async def before_daily_whoop_data(self):
        """Wait until bot is ready before starting the task"""
        await self.wait_until_ready()
        logger.info("⏰ Daily WHOOP data task scheduled for 12:00 AM (midnight)")
    
    @commands.command(name='whoop')
    async def whoop_command(self, ctx):
        """Manual command to get WHOOP data"""
        try:
            data = await self.get_yesterday_data()
            embed = self.create_whoop_embed(data)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error fetching WHOOP data: {e}")
            logger.error(f"Error in whoop command: {e}")
    
    @commands.command(name='whoop_now')
    async def whoop_now_command(self, ctx):
        """Get current WHOOP data (not just yesterday)"""
        try:
            # Get recent data
            profile = self.whoop_client.get_user_profile()
            cycles = self.whoop_client.get_cycles(limit=1)
            sleep_data = self.whoop_client.get_sleep_data(limit=1)
            recovery_data = self.whoop_client.get_recovery_data(limit=1)
            workouts = self.whoop_client.get_workouts(limit=5)
            
            # Create data structure
            data = {
                'profile': profile,
                'cycle': self.whoop_client.get_cycle(cycles.records[0]['id']) if cycles.records else None,
                'sleep': self.whoop_client.get_sleep(sleep_data.records[0]['id']) if sleep_data.records else None,
                'recovery': self.whoop_client.get_recovery(recovery_data.records[0]['id']) if recovery_data.records else None,
                'workouts': [self.whoop_client.get_workout(w['id']) for w in workouts.records[:3]],
                'date': 'Latest'
            }
            
            embed = self.create_whoop_embed(data)
            embed.title = "🏃‍♂️ WHOOP Current Data"
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error fetching current WHOOP data: {e}")
            logger.error(f"Error in whoop_now command: {e}")
    
    @commands.command(name='whoop_schedule')
    async def whoop_schedule_command(self, ctx):
        """Show WHOOP bot schedule information"""
        try:
            # Calculate next run time
            now = datetime.now()
            next_run = datetime.combine(now.date() + timedelta(days=1), time(0, 0))
            time_until = next_run - now
            
            hours, remainder = divmod(time_until.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            embed = discord.Embed(
                title="⏰ WHOOP Bot Schedule",
                description="Daily WHOOP data delivery schedule",
                color=0x00ff00
            )
            
            embed.add_field(
                name="🕛 Next Delivery",
                value=f"**Time:** {next_run.strftime('%Y-%m-%d at %H:%M:%S')}\n"
                      f"**In:** {hours}h {minutes}m {seconds}s",
                inline=False
            )
            
            embed.add_field(
                name="📅 Schedule",
                value="**Frequency:** Daily at 12:00 AM (midnight)\n"
                      "**Data:** Previous day's WHOOP metrics\n"
                      "**Channel:** <#1415625361106014348>",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Commands",
                value="`!whoop` - Get yesterday's data\n"
                      "`!whoop_now` - Get current data\n"
                      "`!whoop_schedule` - Show this info",
                inline=False
            )
            
            embed.set_footer(text="WHOOP Discord Bot • Automated Daily Reports")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error getting schedule info: {e}")
            logger.error(f"Error in whoop_schedule command: {e}")
    
    @commands.command(name='whoop_test_schedule')
    async def whoop_test_schedule_command(self, ctx):
        """Test the scheduled task (admin only)"""
        try:
            # Check if user has admin permissions
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ This command requires administrator permissions")
                return
            
            await ctx.send("🔄 Testing scheduled WHOOP data task...")
            
            # Trigger the scheduled task manually
            await self.daily_whoop_data()
            
            await ctx.send("✅ Scheduled task test completed!")
            
        except Exception as e:
            await ctx.send(f"❌ Error testing scheduled task: {e}")
            logger.error(f"Error in whoop_test_schedule command: {e}")

async def main():
    """Main function to run the bot"""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not found in environment variables")
        sys.exit(1)
    
    bot = WhoopDiscordBot()
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
