#!/usr/bin/env python3
"""
Centralized Log Bot for Discord
Collects logs from all active channels and forwards them to a centralized logs channel
"""

import discord
from discord.ext import commands
import os
import asyncio
import json
import subprocess
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv
from api_monitor import APICallMonitor

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID") or "1415623068965142580")

# Channel mappings for different bots
CHANNEL_MAPPINGS = {
    "calories": "CALORIES_CHANNEL_ID",
    "money": "FINANCE_CHANNEL_ID", 
    "todo": "TODOLISTE_CHANNEL_ID",
    "health": "HEALTH_CHANNEL_ID",
    "learning": "LEARNING_CHANNEL_ID",
    "rss": "RSS_CHANNEL_ID",
    "youtube": "YOUTUBE_CHANNEL_ID",
    "meal_plan": "MEAL_PLAN_CHANNEL_ID",
    "routine": "ROUTINE_CHANNEL_ID",
    "weekly": "WEEKLY_PLANNING_CHANNEL_ID",
    "decision": "DECISION_CHANNEL_ID",
    "erinnerungen": "ERINNERUNGEN_CHANNEL_ID",
    "preisvergleich": "DB_CHANNEL_ID",
    "allgemeine": "GENERAL_CHANNEL_ID",
    "tagebuch": "TAGEBUCH_CHANNEL_ID"
}

# Docker container mappings for log monitoring
DOCKER_CONTAINERS = {
    "money-bot": ["money"],
    "calories-bot": ["calories"],
    "allgemeine-wohl-bot": ["allgemeine"],
    "preisvergleich-bot": ["preisvergleich"],
    "erinnerungen-bot": ["erinnerungen"],
    "discord-todo-bot": ["todo"],
    "tagebuch-bot": ["tagebuch"],
    "health-bot": ["health"],
    # Add more containers as needed
}

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DockerLogMonitor:
    """Monitors Docker container logs for errors and important events"""
    
    def __init__(self, logs_channel):
        self.logs_channel = logs_channel
        self.container_positions = {}  # Track last read position for each container
        self.error_keywords = [
            "error", "exception", "traceback", "failed", "crash", "timeout",
            "connection refused", "permission denied", "not found", "invalid",
            "❌", "⚠️", "critical", "fatal", "abort"
        ]
    
    def get_container_logs(self, container_name: str, lines: int = 50) -> list:
        """Get recent logs from a Docker container"""
        try:
            result = subprocess.run([
                "docker", "logs", "--tail", str(lines), container_name
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                logger.error(f"Failed to get logs from {container_name}: {result.stderr}")
                return []
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting logs from {container_name}")
            return []
        except Exception as e:
            logger.error(f"Error getting logs from {container_name}: {e}")
            return []
    
    def is_error_line(self, line: str) -> bool:
        """Check if a log line contains error indicators"""
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in self.error_keywords)
    
    def format_docker_log(self, container_name: str, log_lines: list, is_error: bool = False) -> str:
        """Format Docker log lines for Discord"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Choose emoji and color based on content
        if is_error:
            header_emoji = "🚨"
            bot_name = f"ERROR-{container_name.upper()}"
        else:
            header_emoji = "📋"
            bot_name = f"LOG-{container_name.upper()}"
        
        header = f"{header_emoji} **{bot_name}** | {timestamp}"
        separator = "─" * 50
        
        # Join log lines and truncate if too long
        content = "\n".join(log_lines)
        if len(content) > 1500:  # Leave room for header
            content = content[:1500] + "\n... (truncated)"
        
        formatted_log = f"""
{header}
{separator}
📦 **Container:** {container_name}
{content}
{separator}
"""
        return formatted_log.strip()
    
    async def monitor_container_logs(self, container_name: str):
        """Monitor a specific container for new log entries"""
        logger.info(f"🔍 Starting log monitoring for container: {container_name}")
        
        while True:
            try:
                # Get recent logs
                log_lines = self.get_container_logs(container_name, lines=20)
                
                if not log_lines:
                    await asyncio.sleep(30)  # Wait 30 seconds if no logs
                    continue
                
                # Check for errors
                error_lines = [line for line in log_lines if self.is_error_line(line)]
                
                if error_lines:
                    # Send error logs immediately
                    formatted_log = self.format_docker_log(container_name, error_lines, is_error=True)
                    await self.send_log_to_channel(formatted_log)
                    logger.info(f"🚨 Sent error logs from {container_name}")
                
                # Send regular logs less frequently (every 5 minutes)
                elif len(log_lines) > 10:  # Only if there are substantial logs
                    formatted_log = self.format_docker_log(container_name, log_lines[-10:], is_error=False)
                    await self.send_log_to_channel(formatted_log)
                    logger.info(f"📋 Sent regular logs from {container_name}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring {container_name}: {e}")
                await asyncio.sleep(60)
    
    async def send_log_to_channel(self, formatted_log: str):
        """Send formatted log to the logs channel"""
        if self.logs_channel:
            try:
                await self.logs_channel.send(formatted_log)
            except Exception as e:
                logger.error(f"Error sending Docker log to channel: {e}")

class LogCollector:
    """Handles log collection and formatting"""
    
    def __init__(self):
        self.logs_channel = None
        self.channel_mappings = {}
        self.docker_monitor = None
        self.setup_channel_mappings()
    
    def setup_channel_mappings(self):
        """Setup channel ID mappings from environment variables"""
        for bot_name, env_var in CHANNEL_MAPPINGS.items():
            channel_id = os.getenv(env_var)
            if channel_id:
                self.channel_mappings[int(channel_id)] = bot_name
                logger.info(f"Mapped {bot_name} to channel {channel_id}")
    
    def get_bot_name_from_channel(self, channel_id: int) -> str:
        """Get bot name from channel ID"""
        return self.channel_mappings.get(channel_id, "unknown")
    
    def format_log_message(self, message: discord.Message, bot_name: str) -> str:
        """Format log message with bot header and separation"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Create header with bot identification
        header = f"🤖 **{bot_name.upper()} BOT** | {timestamp}"
        separator = "─" * 50
        
        # Format the message content
        content = message.content if message.content else "[No text content]"
        
        # Add author info
        author_info = f"👤 **{message.author.display_name}**"
        
        # Add channel info
        channel_info = f"📺 **#{message.channel.name}**"
        
        # Format attachments if any
        attachments_info = ""
        if message.attachments:
            attachment_names = [att.filename for att in message.attachments]
            attachments_info = f"\n📎 **Attachments:** {', '.join(attachment_names)}"
        
        # Format embeds if any
        embeds_info = ""
        if message.embeds:
            embeds_info = f"\n📋 **Embeds:** {len(message.embeds)} embed(s)"
        
        # Combine all parts
        formatted_log = f"""
{header}
{separator}
{author_info} | {channel_info}
{content}{attachments_info}{embeds_info}
{separator}
"""
        return formatted_log.strip()
    
    async def send_log_to_channel(self, formatted_log: str):
        """Send formatted log to the logs channel"""
        if self.logs_channel:
            try:
                # Split long messages if needed (Discord has 2000 char limit)
                if len(formatted_log) > 1900:
                    # Split by lines and send in chunks
                    lines = formatted_log.split('\n')
                    current_chunk = ""
                    
                    for line in lines:
                        if len(current_chunk + line + '\n') > 1900:
                            if current_chunk:
                                await self.logs_channel.send(current_chunk)
                            current_chunk = line + '\n'
                        else:
                            current_chunk += line + '\n'
                    
                    if current_chunk:
                        await self.logs_channel.send(current_chunk)
                else:
                    await self.logs_channel.send(formatted_log)
                    
            except Exception as e:
                logger.error(f"Error sending log to channel: {e}")

# Initialize log collector and API monitor
log_collector = LogCollector()
api_monitor = APICallMonitor()

@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f'🤖 Log Bot has connected to Discord!')
    logger.info(f'📊 Monitoring {len(log_collector.channel_mappings)} channels')
    logger.info(f'📝 Logs will be sent to channel ID: {LOGS_CHANNEL_ID}')
    
    # Get the logs channel
    log_collector.logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    
    if log_collector.logs_channel:
        logger.info(f'✅ Connected to logs channel: #{log_collector.logs_channel.name}')
        
        # Initialize Docker log monitoring
        log_collector.docker_monitor = DockerLogMonitor(log_collector.logs_channel)
        
        # Start Docker log monitoring tasks
        for container_name in DOCKER_CONTAINERS.keys():
            asyncio.create_task(log_collector.docker_monitor.monitor_container_logs(container_name))
            logger.info(f'🔍 Started Docker log monitoring for: {container_name}')
        
        # Start daily API call reporting
        asyncio.create_task(daily_api_report())
        logger.info('📊 Started daily API call reporting')
        
        # Send startup message
        startup_message = f"""
🤖 **LOG BOT STARTED** | {datetime.now().strftime("%H:%M:%S")}
──────────────────────────────────────────────────
📊 **Monitoring {len(log_collector.channel_mappings)} channels:**
{chr(10).join([f"• {bot_name}: #{bot.get_channel(ch_id).name if bot.get_channel(ch_id) else 'Unknown'}" for ch_id, bot_name in log_collector.channel_mappings.items()])}

🐳 **Docker Container Monitoring:**
{chr(10).join([f"• {container}: {', '.join(bots)}" for container, bots in DOCKER_CONTAINERS.items()])}

📝 **All bot logs and Docker container logs will be forwarded here with clear headers and separation.**
🚨 **Errors will be highlighted and sent immediately!**
──────────────────────────────────────────────────
"""
        await log_collector.logs_channel.send(startup_message)
    else:
        logger.error(f'❌ Could not find logs channel with ID {LOGS_CHANNEL_ID}')

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Check if message is from a monitored channel
    if message.channel.id in log_collector.channel_mappings:
        bot_name = log_collector.get_bot_name_from_channel(message.channel.id)
        
        # Format and send the log
        formatted_log = log_collector.format_log_message(message, bot_name)
        await log_collector.send_log_to_channel(formatted_log)
        
        logger.info(f"📝 Logged message from {bot_name} bot in #{message.channel.name}")

@bot.command(name="log_status")
async def log_status(ctx):
    """Show log bot status"""
    if ctx.channel.id != LOGS_CHANNEL_ID:
        return
    
    embed = discord.Embed(
        title="🤖 Log Bot Status",
        description="Centralized logging system for all Discord bots",
        color=0x00ff00
    )
    
    # Show monitored channels
    monitored_channels = []
    for ch_id, bot_name in log_collector.channel_mappings.items():
        channel = bot.get_channel(ch_id)
        if channel:
            monitored_channels.append(f"• **{bot_name}**: #{channel.name}")
        else:
            monitored_channels.append(f"• **{bot_name}**: ❌ Channel not found")
    
    embed.add_field(
        name="📊 Monitored Channels",
        value="\n".join(monitored_channels) if monitored_channels else "No channels configured",
        inline=False
    )
    
    embed.add_field(
        name="📝 Log Channel",
        value=f"#{log_collector.logs_channel.name if log_collector.logs_channel else 'Not found'}",
        inline=True
    )
    
    embed.add_field(
        name="🔄 Status",
        value="✅ Active" if log_collector.logs_channel else "❌ Inactive",
        inline=True
    )
    
    embed.set_footer(text=f"Bot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await ctx.send(embed=embed)

@bot.command(name="log_test")
async def log_test(ctx):
    """Test the log bot functionality"""
    if ctx.channel.id != LOGS_CHANNEL_ID:
        return
    
    test_message = f"""
🧪 **LOG BOT TEST** | {datetime.now().strftime("%H:%M:%S")}
──────────────────────────────────────────────────
👤 **Test User** | 📺 **#{ctx.channel.name}**
This is a test message to verify the log bot is working correctly.
The bot should be able to format and display messages with proper headers and separation.
──────────────────────────────────────────────────
"""
    
    await ctx.send(test_message)
    logger.info("🧪 Log test message sent")

@bot.command(name="docker_logs")
async def docker_logs(ctx, container_name: str = None, lines: int = 20):
    """Get recent Docker container logs"""
    if ctx.channel.id != LOGS_CHANNEL_ID:
        return
    
    if not container_name:
        # List available containers
        available_containers = list(DOCKER_CONTAINERS.keys())
        embed = discord.Embed(
            title="🐳 Available Docker Containers",
            description="Use `!docker_logs <container_name> [lines]` to get logs",
            color=0x00aaff
        )
        embed.add_field(
            name="Containers",
            value="\n".join([f"• `{container}`" for container in available_containers]),
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    if container_name not in DOCKER_CONTAINERS:
        await ctx.send(f"❌ Container '{container_name}' not found. Use `!docker_logs` to see available containers.")
        return
    
    # Get logs from container
    if log_collector.docker_monitor:
        log_lines = log_collector.docker_monitor.get_container_logs(container_name, lines)
        
        if log_lines:
            # Check if there are errors
            error_lines = [line for line in log_lines if log_collector.docker_monitor.is_error_line(line)]
            is_error = len(error_lines) > 0
            
            formatted_log = log_collector.docker_monitor.format_docker_log(container_name, log_lines, is_error)
            await ctx.send(formatted_log)
        else:
            await ctx.send(f"❌ No logs found for container '{container_name}'")
    else:
        await ctx.send("❌ Docker monitoring not initialized")

@bot.command(name="docker_status")
async def docker_status(ctx):
    """Check status of all Docker containers"""
    if ctx.channel.id != LOGS_CHANNEL_ID:
        return
    
    try:
        # Get running containers
        result = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            container_info = result.stdout.strip()
            
            embed = discord.Embed(
                title="🐳 Docker Container Status",
                description="Current status of all containers",
                color=0x00ff00
            )
            
            # Format container info
            lines = container_info.split('\n')[1:]  # Skip header
            status_text = ""
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        name = parts[0]
                        status = parts[1]
                        ports = parts[2] if len(parts) > 2 else "No ports"
                        
                        # Add emoji based on status
                        if "Up" in status:
                            status_emoji = "✅"
                        elif "Exited" in status:
                            status_emoji = "❌"
                        else:
                            status_emoji = "⚠️"
                        
                        status_text += f"{status_emoji} **{name}**: {status}\n"
            
            if status_text:
                embed.add_field(name="Container Status", value=status_text, inline=False)
            else:
                embed.add_field(name="Container Status", value="No containers found", inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Failed to get Docker status: {result.stderr}")
            
    except Exception as e:
        await ctx.send(f"❌ Error checking Docker status: {e}")

async def daily_api_report():
    """Send daily API call report at midnight"""
    while True:
        try:
            # Calculate time until next midnight
            now = datetime.now()
            next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (next_midnight - now).total_seconds()
            
            logger.info(f"⏰ Next API report scheduled for {next_midnight.strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(sleep_seconds)
            
            # Send daily report
            await send_daily_api_report()
            
        except Exception as e:
            logger.error(f"Error in daily API report: {e}")
            await asyncio.sleep(3600)  # Wait 1 hour on error

async def send_daily_api_report():
    """Send daily API call statistics to logs channel"""
    if not log_collector.logs_channel:
        return
    
    try:
        yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        stats = api_monitor.get_daily_stats(yesterday)
        
        # Create report embed
        embed = discord.Embed(
            title="📊 Daily OpenRouter API Report",
            description=f"**{yesterday}** - API Usage Summary",
            color=0x00aaff
        )
        
        # Total calls
        total_calls = stats.get("total_calls", 0)
        successful_calls = stats.get("successful_calls", 0)
        failed_calls = stats.get("failed_calls", 0)
        
        embed.add_field(
            name="📈 Total API Calls",
            value=f"**{total_calls}** calls\n✅ {successful_calls} successful\n❌ {failed_calls} failed",
            inline=True
        )
        
        # Success rate
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        embed.add_field(
            name="📊 Success Rate",
            value=f"**{success_rate:.1f}%**",
            inline=True
        )
        
        # Calls by bot
        by_bot = stats.get("by_bot", {})
        if by_bot:
            bot_summary = "\n".join([f"• **{bot}**: {calls} calls" for bot, calls in sorted(by_bot.items(), key=lambda x: x[1], reverse=True)])
            embed.add_field(
                name="🤖 Calls by Bot",
                value=bot_summary[:1024],  # Discord field limit
                inline=False
            )
        
        # Calls by model
        by_model = stats.get("by_model", {})
        if by_model:
            model_summary = "\n".join([f"• **{model}**: {calls} calls" for model, calls in sorted(by_model.items(), key=lambda x: x[1], reverse=True)])
            embed.add_field(
                name="🧠 Calls by Model",
                value=model_summary[:1024],  # Discord field limit
                inline=False
            )
        
        embed.set_footer(text=f"Report generated at {datetime.now().strftime('%H:%M:%S')}")
        
        await log_collector.logs_channel.send(embed=embed)
        logger.info(f"📊 Sent daily API report for {yesterday}: {total_calls} total calls")
        
    except Exception as e:
        logger.error(f"Error sending daily API report: {e}")

@bot.command(name="api_stats")
async def api_stats(ctx, target_date: str = None):
    """Get API call statistics"""
    if ctx.channel.id != LOGS_CHANNEL_ID:
        return
    
    try:
        if target_date:
            # Validate date format
            try:
                datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                await ctx.send("❌ Invalid date format. Use YYYY-MM-DD")
                return
        else:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        stats = api_monitor.get_daily_stats(target_date)
        
        embed = discord.Embed(
            title="📊 OpenRouter API Statistics",
            description=f"**{target_date}** - API Usage",
            color=0x00aaff
        )
        
        total_calls = stats.get("total_calls", 0)
        successful_calls = stats.get("successful_calls", 0)
        failed_calls = stats.get("failed_calls", 0)
        
        if total_calls == 0:
            embed.add_field(
                name="📈 No API Calls",
                value=f"No OpenRouter API calls recorded for {target_date}",
                inline=False
            )
        else:
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
            
            embed.add_field(
                name="📈 Total API Calls",
                value=f"**{total_calls}** calls\n✅ {successful_calls} successful\n❌ {failed_calls} failed",
                inline=True
            )
            
            embed.add_field(
                name="📊 Success Rate",
                value=f"**{success_rate:.1f}%**",
                inline=True
            )
            
            # Calls by bot
            by_bot = stats.get("by_bot", {})
            if by_bot:
                bot_summary = "\n".join([f"• **{bot}**: {calls} calls" for bot, calls in sorted(by_bot.items(), key=lambda x: x[1], reverse=True)])
                embed.add_field(
                    name="🤖 Calls by Bot",
                    value=bot_summary[:1024],
                    inline=False
                )
            
            # Calls by model
            by_model = stats.get("by_model", {})
            if by_model:
                model_summary = "\n".join([f"• **{model}**: {calls} calls" for model, calls in sorted(by_model.items(), key=lambda x: x[1], reverse=True)])
                embed.add_field(
                    name="🧠 Calls by Model",
                    value=model_summary[:1024],
                    inline=False
                )
        
        embed.set_footer(text=f"Requested at {datetime.now().strftime('%H:%M:%S')}")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting API statistics: {e}")

@bot.command(name="api_total")
async def api_total(ctx):
    """Get total API call statistics across all time"""
    if ctx.channel.id != LOGS_CHANNEL_ID:
        return
    
    try:
        total_stats = api_monitor.get_total_stats()
        
        embed = discord.Embed(
            title="📊 Total OpenRouter API Statistics",
            description="All-time API usage across all bots",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📈 Total Calls",
            value=f"**{total_stats.get('total_calls', 0)}** calls",
            inline=True
        )
        
        embed.add_field(
            name="📅 Days Tracked",
            value=f"**{total_stats.get('days_tracked', 0)}** days",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Last Reset",
            value=f"**{total_stats.get('last_reset', 'Unknown')}**",
            inline=True
        )
        
        # Calculate average calls per day
        days_tracked = total_stats.get('days_tracked', 1)
        total_calls = total_stats.get('total_calls', 0)
        avg_calls = total_calls / days_tracked if days_tracked > 0 else 0
        
        embed.add_field(
            name="📊 Average per Day",
            value=f"**{avg_calls:.1f}** calls/day",
            inline=True
        )
        
        embed.set_footer(text=f"Statistics as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting total API statistics: {e}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("❌ Error: DISCORD_TOKEN not found in environment variables")
        exit(1)
    
    logger.info("🚀 Starting Log Bot...")
    bot.run(DISCORD_TOKEN)
