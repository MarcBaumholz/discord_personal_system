import discord
from discord.ext import commands, tasks
import os
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Import our modules
from notion_manager import NotionManager
from openrouter_service import OpenRouterService
from routine_scheduler import RoutineScheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('routine_bot')

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ROUTINE_CHANNEL_ID = int(os.getenv("ROUTINE_CHANNEL_ID"))

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
routine_scheduler = None

# Track last command execution time
last_command_time = {}
command_cooldown = 5  # 5 seconds cooldown

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    global notion_manager, openrouter_service, routine_scheduler
    
    logger.info(f"Logged in as {bot.user}")
    logger.info(f"Using routine channel ID: {ROUTINE_CHANNEL_ID}")
    
    # Initialize services
    try:
        notion_manager = NotionManager()
        openrouter_service = OpenRouterService()
        routine_scheduler = RoutineScheduler(bot, notion_manager, openrouter_service, ROUTINE_CHANNEL_ID)
        
        # Start background tasks
        check_and_post_routines.start()
        
        # Send welcome message
        channel = bot.get_channel(ROUTINE_CHANNEL_ID)
        if channel:
            await channel.send("📅 Routine Bot is online! I'll help you keep track of your daily routines. Use 📢 emoji to see today's routines, :one: for morning routine, or :two: for evening routine.")
            
        logger.info("Routine Bot is ready!")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check for emoji triggers in the routine channel
    if message.channel.id == ROUTINE_CHANNEL_ID:
        user_id = message.author.id
        current_time = datetime.now().timestamp()
        
        # Create a trigger key based on the emoji and user
        trigger_key = None
        if "📢" in message.content or ":loudspeaker:" in message.content:
            trigger_key = f"{user_id}_loudspeaker"
        elif "1️⃣" in message.content or ":one:" in message.content:
            trigger_key = f"{user_id}_one"
        elif "2️⃣" in message.content or ":two:" in message.content:
            trigger_key = f"{user_id}_two"
            
        # Check if there's a cooldown active
        if trigger_key and trigger_key in last_command_time:
            time_diff = current_time - last_command_time[trigger_key]
            if time_diff < command_cooldown:
                logger.info(f"Command on cooldown for {trigger_key}, ignoring (waited only {time_diff:.1f}s)")
                return  # Still on cooldown, don't process
        
        # Process based on emoji triggers
        if "📢" in message.content or ":loudspeaker:" in message.content:
            try:
                last_command_time[trigger_key] = current_time
                await routine_scheduler.post_todays_routines(message.channel)
            except Exception as e:
                logger.error(f"Error posting routines via emoji: {e}")
                await message.channel.send("Sorry, there was an error getting your routines.")
        
        # Handle morning/evening routine emoji triggers
        elif ("1️⃣" in message.content or ":one:" in message.content or 
              "2️⃣" in message.content or ":two:" in message.content):
            try:
                last_command_time[trigger_key] = current_time
                await routine_scheduler.handle_emoji_trigger(message)
            except Exception as e:
                logger.error(f"Error handling emoji trigger: {e}")
    
    # Process commands
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reaction events"""
    # Ignore bot's own reactions
    if user == bot.user:
        return
        
    # Only process reactions in the designated channel
    if reaction.message.channel.id == ROUTINE_CHANNEL_ID:
        try:
            # Process the reaction with routine scheduler
            await routine_scheduler.process_emoji_reaction(reaction.message, reaction.emoji, user)
        except Exception as e:
            logger.error(f"Error processing reaction: {e}")

@tasks.loop(minutes=30)
async def check_and_post_routines():
    """Check and post routines periodically"""
    try:
        await routine_scheduler.check_and_post_routines()
    except Exception as e:
        logger.error(f"Error in routine check: {e}")

@check_and_post_routines.before_loop
async def before_routine_check():
    """Wait until the bot is ready before starting the task"""
    await bot.wait_until_ready()

@bot.command(name="routine")
async def routine_command(ctx, action="today"):
    """Handle routine commands"""
    if ctx.channel.id != ROUTINE_CHANNEL_ID:
        await ctx.send("Please use this command in the routine channel.")
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
        if action == "today":
            await routine_scheduler.post_todays_routines(ctx)
        elif action == "tomorrow":
            await routine_scheduler.post_tomorrows_routines(ctx)
        elif action == "morning":
            await routine_scheduler.post_morning_routine()
        elif action == "evening":
            await routine_scheduler.post_evening_routine()
        elif action == "help":
            await post_help(ctx)
        else:
            await ctx.send("Unknown command. Try `!routine help` for available commands.")
    except Exception as e:
        logger.error(f"Error handling routine command: {e}")
        await ctx.send("Sorry, there was an error processing your request.")

async def post_help(ctx):
    """Post help information"""
    help_text = """
📅 **Routine Bot Help**

**Commands:**
- `!routine today` - Show your routines for today
- `!routine tomorrow` - Show planned routines for tomorrow
- `!routine morning` - Show your morning routine with steps
- `!routine evening` - Show your evening routine with steps
- `!routine help` - Show this help message

**Emoji Triggers:**
- 📢 or `:loudspeaker:` - Quickly show today's routines
- :one: - Show your morning routine with steps
- :two: - Show your evening routine with steps

I'll also automatically post:
- Morning routine at 8:00 AM
- Evening routine at 10:00 PM

Your routine steps will have checkmarks that you can click to track your progress!
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN) 