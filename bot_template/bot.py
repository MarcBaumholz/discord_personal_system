import discord
import os
import logging
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN not found in environment variables")
    exit(1)

# Set up bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Called when the bot has successfully connected to Discord."""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set bot status
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="for commands | !help"
        )
    )

@bot.event
async def on_message(message):
    """Handle incoming messages."""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Log message for debugging (be careful with sensitive data)
    logger.info(f"Message from {message.author}: {message.content[:50]}...")
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='status')
async def status_command(ctx):
    """Check bot status."""
    embed = discord.Embed(
        title="🤖 Bot Status",
        description="Bot is running and operational!",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Latency", 
        value=f"{round(bot.latency * 1000)}ms", 
        inline=True
    )
    embed.add_field(
        name="Guilds", 
        value=len(bot.guilds), 
        inline=True
    )
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands."""
    embed = discord.Embed(
        title="📋 Available Commands",
        description="Here are the commands you can use:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="!status", 
        value="Check bot status", 
        inline=False
    )
    embed.add_field(
        name="!help", 
        value="Show this help message", 
        inline=False
    )
    # Add more commands here as you develop your bot
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help` to see available commands.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send("❌ An error occurred while processing the command.")

# Add your custom bot logic here
# Example:
# @bot.event
# async def on_message(message):
#     # Your custom message handling logic
#     pass

if __name__ == "__main__":
    logger.info("Starting bot...")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1)
