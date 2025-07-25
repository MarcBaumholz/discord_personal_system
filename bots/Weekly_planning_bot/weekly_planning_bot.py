import discord
from discord.ext import commands, tasks
import os
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import json

# Import our modules
from notion_manager import NotionManager
from openrouter_service import OpenRouterService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('weekly_planning_bot')

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEEKLY_PLANNING_CHANNEL_ID = int(os.getenv("WEEKLY_PLANNING_CHANNEL_ID"))

# Set timezone to Europe/Berlin
TIMEZONE = pytz.timezone('Europe/Berlin')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Enable reaction events

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Service instances
notion_manager = None
openrouter_service = None

# Track last command execution time
last_command_time = {}
command_cooldown = 5  # 5 seconds cooldown

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    global notion_manager, openrouter_service
    
    logger.info(f"Logged in as {bot.user}")
    logger.info(f"Using weekly planning channel ID: {WEEKLY_PLANNING_CHANNEL_ID}")
    
    # Initialize services
    try:
        notion_manager = NotionManager()
        openrouter_service = OpenRouterService()
        
        # Start background tasks
        weekly_plan_reminder.start()
        
        # Send startup message
        channel = bot.get_channel(WEEKLY_PLANNING_CHANNEL_ID)
        if channel:
            await channel.send("🟢 **Bot is running!** Ready to help with your weekly planning. Type `!plan` to get started.")
            
        logger.info("Weekly Planning Bot is ready!")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

async def post_sample_plan(channel):
    """Post a sample weekly plan for demonstration"""
    try:
        # Create a sample weekly plan
        sample_plan = await openrouter_service.generate_sample_weekly_plan()
        
        # Send the sample plan
        await channel.send("Here's a sample of how your weekly plan will look:")
        await channel.send(sample_plan)
        
        # Add reactions for interaction
        message = await channel.send("React with 📊 to view detailed statistics, 🔄 to regenerate the plan, or 👨‍👧‍👦 for family planning.")
        await message.add_reaction("📊")
        await message.add_reaction("🔄")
        await message.add_reaction("👨‍👧‍👦")
    except Exception as e:
        logger.error(f"Error posting sample plan: {e}")
        await channel.send("Sorry, there was an error generating the sample plan.")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if the message is in the weekly planning channel
    if message.channel.id == WEEKLY_PLANNING_CHANNEL_ID:
        user_id = message.author.id
        current_time = datetime.now().timestamp()
        
        # Create a key for command cooldown
        command_key = f"{user_id}_plan"
        
        # Check for plan command via text
        if "!plan" in message.content.lower():
            # Check cooldown
            if command_key in last_command_time:
                time_diff = current_time - last_command_time[command_key]
                if time_diff < command_cooldown:
                    logger.info(f"Command on cooldown for {command_key}, ignoring (waited only {time_diff:.1f}s)")
                    return  # Still on cooldown
            
            # Update command time
            last_command_time[command_key] = current_time
            
            # Get weekly plan from Notion and OpenRouter
            try:
                plan = await get_weekly_plan(message.channel)
                if plan:
                    await message.channel.send(plan)
                else:
                    await message.channel.send("Sorry, I couldn't retrieve your weekly plan. Try again later.")
            except Exception as e:
                logger.error(f"Error processing plan command: {e}")
                await message.channel.send("Sorry, there was an error getting your weekly plan.")
        
        # Check for family emoji trigger
        elif "👨‍👧‍👦" in message.content or ":family_adult_child_child:" in message.content:
            # Check cooldown
            family_key = f"{user_id}_family"
            if family_key in last_command_time:
                time_diff = current_time - last_command_time[family_key]
                if time_diff < command_cooldown:
                    logger.info(f"Command on cooldown for {family_key}, ignoring (waited only {time_diff:.1f}s)")
                    return  # Still on cooldown
            
            # Update command time
            last_command_time[family_key] = current_time
            
            # Generate family plan
            try:
                family_plan = await generate_family_plan(message.channel)
                if family_plan:
                    await message.channel.send("📋 **Family Weekly Plan**")
                    await message.channel.send(family_plan)
                else:
                    await message.channel.send("Sorry, I couldn't generate your family plan. Try again later.")
            except Exception as e:
                logger.error(f"Error processing family plan command: {e}")
                await message.channel.send("Sorry, there was an error generating your family plan.")
    
    # Process commands
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reaction events"""
    # Ignore bot's own reactions
    if user == bot.user:
        return
        
    # Only process reactions in the designated channel
    if reaction.message.channel.id == WEEKLY_PLANNING_CHANNEL_ID:
        try:
            if str(reaction.emoji) == "📊":
                # Generate detailed statistics
                stats = await openrouter_service.generate_weekly_stats()
                await reaction.message.channel.send(f"**Weekly Statistics for {user.display_name}**\n\n{stats}")
            elif str(reaction.emoji) == "🔄":
                # Regenerate the plan
                new_plan = await get_weekly_plan(reaction.message.channel)
                if new_plan:
                    await reaction.message.channel.send(f"**Updated Weekly Plan for {user.display_name}**\n\n{new_plan}")
                else:
                    await reaction.message.channel.send("Sorry, I couldn't regenerate your weekly plan.")
            elif str(reaction.emoji) == "👨‍👧‍👦":
                # Generate family plan
                family_plan = await generate_family_plan(reaction.message.channel)
                if family_plan:
                    await reaction.message.channel.send(f"**Family Weekly Plan for {user.display_name}**\n\n{family_plan}")
                else:
                    await reaction.message.channel.send("Sorry, I couldn't generate your family plan.")
        except Exception as e:
            logger.error(f"Error processing reaction: {e}")

async def get_weekly_plan(channel):
    """Get weekly plan from Notion and format with OpenRouter"""
    try:
        # Get weekly planning data from Notion
        weekly_data = await notion_manager.get_latest_weekly_plan()
        
        # Use OpenRouter to format the weekly plan in a visually appealing way
        formatted_plan = await openrouter_service.format_weekly_plan(weekly_data)
        
        return formatted_plan
    except Exception as e:
        logger.error(f"Error getting weekly plan: {e}")
        return None

async def generate_family_plan(channel):
    """Generate a family weekly plan with OpenRouter"""
    try:
        # Generate family plan data using OpenRouter
        family_plan = await openrouter_service.generate_family_plan()
        return family_plan
    except Exception as e:
        logger.error(f"Error generating family plan: {e}")
        return None

@tasks.loop(hours=24)
async def weekly_plan_reminder():
    """Send weekly planning reminder on Sundays"""
    try:
        # Get the current day of the week (0 = Monday, 6 = Sunday)
        current_day = datetime.now(TIMEZONE).weekday()
        
        # Send reminder on Sunday
        if current_day == 6:
            channel = bot.get_channel(WEEKLY_PLANNING_CHANNEL_ID)
            if channel:
                await channel.send("🔔 **Weekly Planning Reminder**\n\nIt's Sunday - time to plan your upcoming week! Use `!plan` to see your current plan, react with 🔄 to generate a new one, or use 👨‍👧‍👦 for family planning.")
    except Exception as e:
        logger.error(f"Error in weekly plan reminder: {e}")

@weekly_plan_reminder.before_loop
async def before_reminder():
    """Wait until the bot is ready before starting the task"""
    await bot.wait_until_ready()

@bot.command(name="plan")
async def plan_command(ctx, action="current"):
    """Handle plan commands"""
    if ctx.channel.id != WEEKLY_PLANNING_CHANNEL_ID:
        await ctx.send("Please use this command in the weekly planning channel.")
        return
    
    # Check for command cooldown
    user_id = ctx.author.id
    current_time = datetime.now().timestamp()
    command_key = f"{user_id}_{action}"
    
    if command_key in last_command_time:
        time_diff = current_time - last_command_time[command_key]
        if time_diff < command_cooldown:
            logger.info(f"Command on cooldown for {command_key}, ignoring (waited only {time_diff:.1f}s)")
            return  # Still on cooldown, don't process
    
    # Update command time
    last_command_time[command_key] = current_time
    
    try:
        if action == "current":
            plan = await get_weekly_plan(ctx.channel)
            if plan:
                await ctx.send(plan)
            else:
                await ctx.send("Sorry, I couldn't retrieve your weekly plan.")
        elif action == "new":
            # Force regeneration of the plan
            plan = await get_weekly_plan(ctx.channel)
            if plan:
                await ctx.send("**New Weekly Plan**\n\n" + plan)
            else:
                await ctx.send("Sorry, I couldn't generate a new weekly plan.")
        elif action == "family":
            # Generate family plan
            family_plan = await generate_family_plan(ctx.channel)
            if family_plan:
                await ctx.send("**Family Weekly Plan**\n\n" + family_plan)
            else:
                await ctx.send("Sorry, I couldn't generate a family plan.")
        elif action == "help":
            await post_help(ctx)
        else:
            await ctx.send("Unknown command. Try `!plan help` for available commands.")
    except Exception as e:
        logger.error(f"Error handling plan command: {e}")
        await ctx.send("Sorry, there was an error processing your request.")

async def post_help(ctx):
    """Post help information"""
    help_text = """
📆 **Weekly Planning Bot Help**

**Commands:**
- `!plan` - Show your current weekly plan
- `!plan new` - Generate a new weekly plan
- `!plan family` - Generate a family weekly plan
- `!plan help` - Show this help message

**Emoji Triggers:**
- 📊 - Show detailed statistics for your week
- 🔄 - Regenerate your weekly plan
- 👨‍👧‍👦 - Generate a family weekly plan

**Family Planning Features:**
The family plan includes:
- Who is present each day of the week
- Meal planning for each person
- Grocery shopping assignments
- Evening and weekend planning
- Important events for each family member
- Trash schedule (who is responsible for taking out trash)

I'll also remind you every Sunday to plan your upcoming week!
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN) 