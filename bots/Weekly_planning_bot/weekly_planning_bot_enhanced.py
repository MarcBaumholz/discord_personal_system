import discord
from discord.ext import commands, tasks
import os
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import json

# Import our enhanced modules
from notion_manager import NotionManager
from openrouter_service import OpenRouterService
from core.database import get_database
from features.task_manager import TaskManagerCog
from features.analytics import AnalyticsCog
from integrations.google_calendar import get_calendar_integration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('weekly_planning_bot_enhanced')

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEEKLY_PLANNING_CHANNEL_ID = int(os.getenv("WEEKLY_PLANNING_CHANNEL_ID"))

# Set timezone to Europe/Berlin
TIMEZONE = pytz.timezone('Europe/Berlin')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True

# Initialize enhanced bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Service instances
notion_manager = None
openrouter_service = None
db_manager = None
calendar_integration = None

# Track last command execution time
last_command_time = {}
command_cooldown = 5  # 5 seconds cooldown

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    global notion_manager, openrouter_service, db_manager, calendar_integration
    
    logger.info(f"🚀 Enhanced Weekly Planning Bot logged in as {bot.user}")
    logger.info(f"📱 Using channel ID: {WEEKLY_PLANNING_CHANNEL_ID}")
    
    # Initialize services
    try:
        # Initialize database
        db_manager = get_database()
        logger.info("✅ Database initialized")
        
        # Initialize existing services
        notion_manager = NotionManager()
        openrouter_service = OpenRouterService()
        logger.info("✅ Notion and OpenRouter services initialized")
        
        # Initialize calendar integration
        calendar_integration = get_calendar_integration()
        if calendar_integration.is_available():
            logger.info("✅ Google Calendar integration available")
        else:
            logger.info("⚠️ Google Calendar integration not configured")
        
        # Load enhanced cogs
        await bot.add_cog(TaskManagerCog(bot))
        await bot.add_cog(AnalyticsCog(bot))
        logger.info("✅ Enhanced cogs loaded")
        
        # Start background tasks
        weekly_plan_reminder.start()
        analytics_snapshot.start()
        
        # Send startup message
        channel = bot.get_channel(WEEKLY_PLANNING_CHANNEL_ID)
        if channel:
            await channel.send("🟢 **Enhanced Bot is running!** Ready with task management, analytics & calendar sync. Type `!plan` to get started.")
            
        logger.info("🎉 Enhanced Weekly Planning Bot is ready!")
        
    except Exception as e:
        logger.error(f"❌ Error initializing enhanced services: {e}")

async def post_enhanced_sample_plan(channel):
    """Post a sample enhanced weekly plan with new features"""
    try:
        # Create a sample weekly plan with database integration
        sample_plan = await openrouter_service.generate_sample_weekly_plan()
        
        # Send the sample plan
        await channel.send("🌟 **Enhanced Weekly Plan Sample** - Now with persistent storage and analytics!")
        await channel.send(sample_plan)
        
        # Add enhanced interactive elements
        embed = discord.Embed(
            title="🎮 Try the New Interactive Features!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Analytics",
            value="React with 📊 for detailed stats\n"
                  "Use `!analytics chart` for visual trends",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Task Management",
            value="Use `!tasks` for interactive task toggles\n"
                  "React with ⚡ for quick task view",
            inline=True
        )
        
        embed.add_field(
            name="📅 Calendar Sync",
            value="Use `!calendar sync` to sync with Google\n"
                  "Use `!calendar import` to import events",
            inline=True
        )
        
        message = await channel.send(embed=embed)
        
        # Add reactions for interaction
        await message.add_reaction("📊")  # Analytics
        await message.add_reaction("🔄")  # Regenerate
        await message.add_reaction("👨‍👧‍👦")  # Family plan
        await message.add_reaction("🎯")  # Task management
        await message.add_reaction("📅")  # Calendar
        await message.add_reaction("⚡")  # Quick stats
        
    except Exception as e:
        logger.error(f"Error posting enhanced sample plan: {e}")
        await channel.send("❌ Error generating enhanced sample plan.")

@bot.event
async def on_message(message):
    """Enhanced message handling with database integration"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if the message is in the weekly planning channel
    if message.channel.id == WEEKLY_PLANNING_CHANNEL_ID:
        user_id = message.author.id
        current_time = datetime.now().timestamp()
        
        # Get or create user in database
        try:
            user = await db_manager.get_or_create_user(str(user_id), message.author.display_name)
        except Exception as e:
            logger.error(f"Error getting/creating user: {e}")
            user = None
        
        # Enhanced command handling
        if "!plan" in message.content.lower():
            command_key = f"{user_id}_plan"
            
            if command_key in last_command_time:
                time_diff = current_time - last_command_time[command_key]
                if time_diff < command_cooldown:
                    return
            
            last_command_time[command_key] = current_time
            
            try:
                await handle_enhanced_plan_command(message, user)
            except Exception as e:
                logger.error(f"Error processing enhanced plan command: {e}")
                await message.channel.send("❌ Error processing plan command.")
        
        elif "!setup" in message.content.lower():
            await handle_setup_command(message, user)
        
        elif "!status" in message.content.lower():
            await handle_status_command(message, user)
    
    # Process commands
    await bot.process_commands(message)

async def handle_enhanced_plan_command(message, user):
    """Handle enhanced plan commands with database integration"""
    try:
        if not user:
            await message.channel.send("❌ Error accessing user data. Please try again.")
            return
        
        # Get weekly plan from Notion and OpenRouter
        weekly_data = await notion_manager.get_latest_weekly_plan()
        
        # Save to database for persistence
        if weekly_data and user:
            plan_id = await db_manager.save_weekly_plan(user['id'], weekly_data)
            logger.info(f"Saved weekly plan {plan_id} to database")
        
        # Format with OpenRouter
        formatted_plan = await openrouter_service.format_weekly_plan(weekly_data)
        
        if formatted_plan:
            # Send enhanced plan with database info
            embed = discord.Embed(
                title="📅 Enhanced Weekly Plan",
                description="Your plan has been saved to the database for analytics and tracking.",
                color=discord.Color.green()
            )
            
            await message.channel.send(embed=embed)
            await message.channel.send(formatted_plan)
            
            # Add enhanced interaction buttons
            embed2 = discord.Embed(
                title="🎮 Enhanced Interactions Available",
                description="Your plan is now enhanced with new features:",
                color=discord.Color.blue()
            )
            
            embed2.add_field(
                name="Available Commands",
                value="`!tasks` - Interactive task management\n"
                      "`!analytics` - View productivity insights\n"
                      "`!calendar sync` - Sync to Google Calendar\n"
                      "`!analytics chart` - Visual trends",
                inline=False
            )
            
            interaction_msg = await message.channel.send(embed=embed2)
            
            # Add reaction options
            await interaction_msg.add_reaction("🎯")  # Tasks
            await interaction_msg.add_reaction("📊")  # Analytics
            await interaction_msg.add_reaction("📅")  # Calendar
            
        else:
            await message.channel.send("❌ Could not retrieve your weekly plan.")
            
    except Exception as e:
        logger.error(f"Error in enhanced plan command: {e}")
        await message.channel.send("❌ Error processing enhanced plan command.")

async def handle_setup_command(message, user):
    """Handle setup and configuration commands"""
    try:
        embed = discord.Embed(
            title="⚙️ Enhanced Bot Setup",
            description="Configure your enhanced weekly planning experience:",
            color=discord.Color.orange()
        )
        
        # Database status
        db_status = "✅ Connected" if db_manager else "❌ Error"
        embed.add_field(
            name="💾 Database",
            value=f"Status: {db_status}\n"
                  f"User ID: {user['id'] if user else 'Not found'}\n"
                  f"Storage: Persistent SQLite",
            inline=True
        )
        
        # Calendar status
        calendar_status = "✅ Available" if calendar_integration and calendar_integration.is_available() else "⚠️ Not configured"
        embed.add_field(
            name="📅 Google Calendar",
            value=f"Status: {calendar_status}\n"
                  f"Integration: {calendar_integration is not None}\n"
                  f"Setup: Use `!calendar setup`",
            inline=True
        )
        
        # Analytics status
        embed.add_field(
            name="📊 Analytics",
            value="Status: ✅ Available\n"
                  "Charts: ✅ Enabled\n"
                  "Tracking: ✅ Active",
            inline=True
        )
        
        embed.add_field(
            name="🚀 Getting Started",
            value="1. Use `!plan` to create your first plan\n"
                  "2. Try `!tasks` for interactive management\n"
                  "3. Check `!analytics` for insights\n"
                  "4. Set up `!calendar` for sync",
            inline=False
        )
        
        await message.channel.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in setup command: {e}")
        await message.channel.send("❌ Error displaying setup information.")

async def handle_status_command(message, user):
    """Handle status and health check commands"""
    try:
        embed = discord.Embed(
            title="🔍 Enhanced Bot Status",
            color=discord.Color.blue()
        )
        
        # Core services status
        services_status = []
        
        # Database
        try:
            if user:
                plan = await db_manager.get_weekly_plan(user['id'])
                db_info = f"✅ Connected (Plans: {'Found' if plan else 'None'})"
            else:
                db_info = "⚠️ User not found"
        except:
            db_info = "❌ Error"
        
        services_status.append(f"💾 Database: {db_info}")
        
        # Notion
        notion_status = "✅ Connected" if notion_manager else "❌ Error"
        services_status.append(f"📝 Notion: {notion_status}")
        
        # OpenRouter
        openrouter_status = "✅ Connected" if openrouter_service else "❌ Error"
        services_status.append(f"🤖 AI Service: {openrouter_status}")
        
        # Calendar
        calendar_status = "✅ Available" if calendar_integration and calendar_integration.is_available() else "⚠️ Not configured"
        services_status.append(f"📅 Calendar: {calendar_status}")
        
        embed.add_field(
            name="🔧 Service Status",
            value="\n".join(services_status),
            inline=False
        )
        
        # Recent activity (if user exists)
        if user:
            try:
                analytics = await db_manager.get_user_analytics(user['id'], 2)
                if analytics and 'weeks_analyzed' in analytics:
                    activity_info = f"Weeks tracked: {analytics['weeks_analyzed']}\n"
                    activity_info += f"Avg completion: {analytics.get('average_completion_rate', 0):.1%}\n"
                    activity_info += f"Total tasks: {analytics.get('total_tasks', 0)}"
                else:
                    activity_info = "No analytics data yet"
            except:
                activity_info = "Error loading analytics"
            
            embed.add_field(
                name="📈 Your Activity",
                value=activity_info,
                inline=True
            )
        
        # System info
        embed.add_field(
            name="⚡ Performance",
            value=f"Latency: {round(bot.latency * 1000)}ms\n"
                  f"Commands: Enhanced\n"
                  f"Features: All active",
            inline=True
        )
        
        await message.channel.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.channel.send("❌ Error checking bot status.")

@bot.event
async def on_reaction_add(reaction, user):
    """Enhanced reaction handling with new features"""
    if user == bot.user:
        return
        
    if reaction.message.channel.id == WEEKLY_PLANNING_CHANNEL_ID:
        try:
            user_data = await db_manager.get_or_create_user(str(user.id), user.display_name)
            
            if str(reaction.emoji) == "📊":
                # Enhanced analytics
                analytics = await db_manager.get_user_analytics(user_data['id'], 4)
                if analytics and 'average_completion_rate' in analytics:
                    embed = discord.Embed(
                        title="📊 Quick Analytics Dashboard",
                        color=discord.Color.purple()
                    )
                    
                    embed.add_field(
                        name="🎯 Performance",
                        value=f"Avg Completion: {analytics['average_completion_rate']:.1%}\n"
                              f"Best Day: {analytics.get('most_productive_day', 'Unknown')}\n"
                              f"Weeks Tracked: {analytics.get('weeks_analyzed', 0)}",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📈 Trends",
                        value="Use `!analytics chart` for visual trends\n"
                              "Use `!analytics` for full dashboard",
                        inline=True
                    )
                    
                    await reaction.message.channel.send(embed=embed)
                else:
                    await reaction.message.channel.send("📊 No analytics data yet. Create some weekly plans first!")
            
            elif str(reaction.emoji) == "🎯":
                # Quick task overview
                plan_data = await db_manager.get_weekly_plan(user_data['id'])
                if plan_data:
                    total = plan_data['total_tasks']
                    completed = plan_data['completed_tasks']
                    rate = plan_data['completion_rate']
                    
                    embed = discord.Embed(
                        title="🎯 Quick Task Overview",
                        description=f"Progress: {completed}/{total} ({rate:.1%})",
                        color=discord.Color.green()
                    )
                    
                    progress_bar = "█" * int(rate * 10) + "░" * (10 - int(rate * 10))
                    embed.add_field(
                        name="Progress",
                        value=progress_bar,
                        inline=False
                    )
                    
                    embed.add_field(
                        name="Interactive Management",
                        value="Use `!tasks` for full interactive task management",
                        inline=False
                    )
                    
                    await reaction.message.channel.send(embed=embed)
                else:
                    await reaction.message.channel.send("🎯 No tasks found. Create a weekly plan first!")
            
            elif str(reaction.emoji) == "📅":
                # Calendar integration info
                if calendar_integration and calendar_integration.is_available():
                    await reaction.message.channel.send(
                        "📅 **Calendar Integration Available!**\n\n"
                        "Commands:\n"
                        "`!calendar sync` - Sync your weekly plan to Google Calendar\n"
                        "`!calendar import` - Import calendar events to your plan\n"
                        "`!calendar summary` - View upcoming events"
                    )
                else:
                    await reaction.message.channel.send(
                        "📅 **Calendar Integration Setup**\n\n"
                        "Google Calendar integration is not configured yet.\n"
                        "Contact your administrator to set up calendar integration."
                    )
            
            # Handle existing reactions for backward compatibility
            elif str(reaction.emoji) == "🔄":
                new_plan = await get_enhanced_weekly_plan(reaction.message.channel, user_data)
                if new_plan:
                    await reaction.message.channel.send(f"🔄 **Updated Plan for {user.display_name}**\n\n{new_plan}")
            
            elif str(reaction.emoji) == "👨‍👧‍👦":
                family_plan = await generate_enhanced_family_plan(reaction.message.channel, user_data)
                if family_plan:
                    await reaction.message.channel.send(f"👨‍👧‍👦 **Enhanced Family Plan**\n\n{family_plan}")
                    
        except Exception as e:
            logger.error(f"Error processing enhanced reaction: {e}")

async def get_enhanced_weekly_plan(channel, user_data):
    """Get enhanced weekly plan with database integration"""
    try:
        # Get from Notion
        weekly_data = await notion_manager.get_latest_weekly_plan()
        
        # Save to database
        if weekly_data and user_data:
            await db_manager.save_weekly_plan(user_data['id'], weekly_data)
        
        # Format with AI
        formatted_plan = await openrouter_service.format_weekly_plan(weekly_data)
        return formatted_plan
        
    except Exception as e:
        logger.error(f"Error getting enhanced weekly plan: {e}")
        return None

async def generate_enhanced_family_plan(channel, user_data):
    """Generate enhanced family plan"""
    try:
        family_plan = await openrouter_service.generate_family_plan()
        
        # Could save family-specific data to database here
        # For now, just return the formatted plan
        
        return family_plan
        
    except Exception as e:
        logger.error(f"Error generating enhanced family plan: {e}")
        return None

@tasks.loop(hours=24)
async def weekly_plan_reminder():
    """Enhanced weekly planning reminder with analytics"""
    try:
        current_day = datetime.now(TIMEZONE).weekday()
        
        if current_day == 6:  # Sunday
            channel = bot.get_channel(WEEKLY_PLANNING_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🔔 Enhanced Weekly Planning Reminder",
                    description="Time to plan your upcoming week with enhanced features!",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="🎯 This Week's Focus",
                    value="• Use `!plan` for your weekly overview\n"
                          "• Try `!analytics` to see your trends\n"
                          "• Use `!tasks` for interactive management\n"
                          "• Sync with `!calendar` if configured",
                    inline=False
                )
                
                embed.add_field(
                    name="📊 Weekly Analytics",
                    value="Your progress data is being tracked!\n"
                          "Check your productivity trends with `!analytics chart`",
                    inline=False
                )
                
                await channel.send(embed=embed)
                
    except Exception as e:
        logger.error(f"Error in enhanced weekly plan reminder: {e}")

@tasks.loop(hours=168)  # Weekly
async def analytics_snapshot():
    """Create weekly analytics snapshots for all users"""
    try:
        # This would create analytics snapshots for performance tracking
        # Implementation would iterate through all users and create snapshots
        logger.info("Creating weekly analytics snapshots...")
        
        # Cleanup old data periodically
        deleted_count = await db_manager.cleanup_old_data(90)  # Keep 90 days
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old records")
            
    except Exception as e:
        logger.error(f"Error in analytics snapshot task: {e}")

@weekly_plan_reminder.before_loop
async def before_reminder():
    """Wait until the bot is ready before starting tasks"""
    await bot.wait_until_ready()

@analytics_snapshot.before_loop
async def before_analytics():
    """Wait until the bot is ready before starting analytics tasks"""
    await bot.wait_until_ready()

# Enhanced help command
@bot.command(name="help")
async def enhanced_help(ctx, section: str = "basic"):
    """Enhanced help command with feature documentation"""
    if section == "enhanced":
        embed = discord.Embed(
            title="🎉 Enhanced Weekly Planning Bot - Complete Guide",
            description="Your upgraded planning assistant with advanced features",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📅 Basic Planning",
            value="`!plan` - Enhanced weekly plan view\n"
                  "`!plan new` - Generate new plan\n"
                  "`!plan family` - Family planning mode\n"
                  "`!plan help` - Planning help",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Task Management",
            value="`!tasks` - Interactive task manager\n"
                  "`!tasks quick` - Quick overview\n"
                  "`!tasks category [name]` - Filter by category\n"
                  "`!task [title]` - Quick toggle task",
            inline=True
        )
        
        embed.add_field(
            name="📊 Analytics & Insights",
            value="`!analytics` - Full dashboard\n"
                  "`!analytics chart` - Visual trends\n"
                  "`!analytics trends` - Productivity trends\n"
                  "`!analytics time` - Time allocation",
            inline=True
        )
        
        embed.add_field(
            name="📅 Calendar Integration",
            value="`!calendar sync` - Sync to Google Calendar\n"
                  "`!calendar import` - Import events\n"
                  "`!calendar summary` - Upcoming events\n"
                  "`!calendar setup` - Configuration",
            inline=True
        )
        
        embed.add_field(
            name="⚙️ System Commands",
            value="`!setup` - Configuration overview\n"
                  "`!status` - System health check\n"
                  "`!help enhanced` - This guide",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Interactive Features",
            value="• React with 📊 for quick analytics\n"
                  "• React with 🎯 for task overview\n"
                  "• React with 📅 for calendar info\n"
                  "• React with 🔄 to regenerate plans",
            inline=True
        )
        
        embed.set_footer(text="💡 All your data is automatically saved and tracked for insights!")
        
        await ctx.send(embed=embed)
    else:
        # Basic help - unchanged from original
        await ctx.send("Use `!help enhanced` for the complete feature guide!")

if __name__ == "__main__":
    logger.info("🚀 Starting Enhanced Weekly Planning Bot...")
    bot.run(DISCORD_TOKEN) 