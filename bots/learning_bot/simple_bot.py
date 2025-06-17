import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data_loader import get_random_learning

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

scheduler = AsyncIOScheduler()

async def send_learning(channel):
    """Send a random learning to the specified channel."""
    try:
        title, content, actions = get_random_learning()
        
        # Format the message
        msg = f"🧠 **Daily Learning: {title}**\n\n"
        
        # Add content (limit to 1500 chars to avoid Discord limits)
        if content:
            content_preview = content[:1500] + "..." if len(content) > 1500 else content
            msg += f"{content_preview}\n\n"
        
        # Add action steps if available
        if actions:
            actions_preview = actions[:500] + "..." if len(actions) > 500 else actions
            msg += f"🎯 **Action Steps:**\n{actions_preview}"
        
        await channel.send(msg)
        logger.info(f"Sent learning: {title}")
        
    except Exception as e:
        logger.error(f"Error sending learning: {e}")
        await channel.send("❌ Sorry, I encountered an error while preparing your learning.")

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('------')
    
    # Schedule daily learning
    channel_id = os.getenv('DAILY_LEARNING_CHANNEL_ID')
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            scheduler.add_job(
                lambda: bot.loop.create_task(send_learning(channel)), 
                'cron', 
                hour=8, 
                minute=0
            )
            scheduler.start()
            logger.info(f"Scheduled daily learning for channel {channel.name} at 8:00 AM")
        else:
            logger.error(f"Could not find channel with ID {channel_id}")
    else:
        logger.error("DISCORD_CHANNEL_ID not set in environment variables")

@bot.event
async def on_message(message):
    """Handle incoming messages."""
    if message.author == bot.user:
        return
    
    # Check for 'learn' trigger in the specified channel
    channel_id = os.getenv('DAILY_LEARNING_CHANNEL_ID')
    if channel_id and message.channel.id == int(channel_id) and 'learn' in message.content.lower():
        await send_learning(message.channel)
    
    await bot.process_commands(message)

@bot.command(name='ping')
async def ping(ctx):
    """Simple command to check if the bot is responsive."""
    await ctx.send('Pong! 🏓')

@bot.command(name='test_learning')
async def test_learning(ctx):
    """Test command to send a learning immediately."""
    await send_learning(ctx.channel)

@bot.command(name='info')
async def info_command(ctx):
    """Display available commands and their usage."""
    help_text = """
🤖 **Learning Bot Commands:**
`!ping` - Check if the bot is responsive
`!test_learning` - Get a random learning immediately
`!info` - Display this help message

📚 **Auto Features:**
- Daily learning at 8:00 AM
- Type 'learn' in the channel to get a random learning
"""
    await ctx.send(help_text)

def main():
    """Main function to run the bot."""
    if not DISCORD_TOKEN:
        logger.error("No Discord token found. Please set DISCORD_TOKEN in .env file")
        return

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main() 