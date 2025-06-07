import os
import discord
import asyncio
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_discord')

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
if CHANNEL_ID:
    CHANNEL_ID = int(CHANNEL_ID)

# Set up Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f"Logged in as {client.user}")
    
    if not CHANNEL_ID:
        logger.error("DISCORD_CHANNEL_ID not set in environment variables")
        await client.close()
        return
    
    logger.info(f"Using channel ID: {CHANNEL_ID}")
    
    # Get the channel and send a test message
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🔍 Test message from Preisvergleich Bot!")
        logger.info("Test message sent successfully!")
    else:
        logger.error(f"Could not find channel with ID {CHANNEL_ID}")
    
    # Close the client after sending the message
    await client.close()

# Run the test
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set in environment variables")
        exit(1)
        
    client.run(DISCORD_TOKEN) 