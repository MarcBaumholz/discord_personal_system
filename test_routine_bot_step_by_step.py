import discord
from discord.ext import commands
import os
import asyncio
import sys
import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('routine_bot_test')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Channel ID for the routine channel
ROUTINE_CHANNEL_ID = 1366687489720451114

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Test results
test_results = {
    "initialization": {"status": "pending", "message": ""},
    "help_command": {"status": "pending", "message": ""},
    "today_command": {"status": "pending", "message": ""},
    "tomorrow_command": {"status": "pending", "message": ""},
    "emoji_trigger": {"status": "pending", "message": ""}
}

@bot.event
async def on_ready():
    """Called when the bot is ready to start testing"""
    logger.info(f"Logged in as {bot.user}")
    
    try:
        channel = bot.get_channel(ROUTINE_CHANNEL_ID)
        
        if not channel:
            logger.error(f"Could not find channel with ID: {ROUTINE_CHANNEL_ID}")
            test_results["initialization"]["status"] = "failed"
            test_results["initialization"]["message"] = f"Channel not found: {ROUTINE_CHANNEL_ID}"
            await bot.close()
            return
            
        logger.info(f"Found channel: {channel.name}")
        test_results["initialization"]["status"] = "success"
        test_results["initialization"]["message"] = f"Connected to channel: {channel.name}"
        
        # Run the tests
        await run_tests(channel)
        
        # Output test results
        logger.info("\n=== TEST RESULTS ===")
        for test, result in test_results.items():
            logger.info(f"{test}: {result['status']}")
            if result['message']:
                logger.info(f"  Message: {result['message']}")
        
        # Keep the bot running for a bit
        logger.info("All tests completed. Check Discord for responses.")
        await asyncio.sleep(10)
        await bot.close()
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        await bot.close()

async def run_tests(channel):
    """Run each test in sequence"""
    logger.info("Starting routine bot tests...")
    
    # Test 1: Help command
    await test_help_command(channel)
    await asyncio.sleep(3)
    
    # Test 2: Today's routines
    await test_today_command(channel)
    await asyncio.sleep(5)  # Give more time as this might call the LLM API
    
    # Test 3: Tomorrow's routines
    await test_tomorrow_command(channel)
    await asyncio.sleep(5)  # Give more time for API response
    
    # Test 4: Emoji trigger
    await test_emoji_trigger(channel)
    await asyncio.sleep(5)  # Give more time for API response

async def test_help_command(channel):
    """Test the help command"""
    logger.info("\n=== TEST 1: Help Command ===")
    try:
        await channel.send("!routine help")
        logger.info("Sent: !routine help")
        test_results["help_command"]["status"] = "success"
        test_results["help_command"]["message"] = "Command sent successfully"
    except Exception as e:
        logger.error(f"Error sending help command: {e}")
        test_results["help_command"]["status"] = "failed"
        test_results["help_command"]["message"] = str(e)

async def test_today_command(channel):
    """Test the today command"""
    logger.info("\n=== TEST 2: Today's Routines ===")
    try:
        await channel.send("!routine today")
        logger.info("Sent: !routine today")
        test_results["today_command"]["status"] = "success"
        test_results["today_command"]["message"] = "Command sent successfully"
    except Exception as e:
        logger.error(f"Error sending today command: {e}")
        test_results["today_command"]["status"] = "failed"
        test_results["today_command"]["message"] = str(e)

async def test_tomorrow_command(channel):
    """Test the tomorrow command"""
    logger.info("\n=== TEST 3: Tomorrow's Routines ===")
    try:
        await channel.send("!routine tomorrow")
        logger.info("Sent: !routine tomorrow")
        test_results["tomorrow_command"]["status"] = "success"
        test_results["tomorrow_command"]["message"] = "Command sent successfully"
    except Exception as e:
        logger.error(f"Error sending tomorrow command: {e}")
        test_results["tomorrow_command"]["status"] = "failed"
        test_results["tomorrow_command"]["message"] = str(e)

async def test_emoji_trigger(channel):
    """Test the emoji trigger"""
    logger.info("\n=== TEST 4: Emoji Trigger ===")
    try:
        await channel.send("📢")
        logger.info("Sent: 📢 emoji")
        test_results["emoji_trigger"]["status"] = "success"
        test_results["emoji_trigger"]["message"] = "Emoji sent successfully"
    except Exception as e:
        logger.error(f"Error sending emoji: {e}")
        test_results["emoji_trigger"]["status"] = "failed"
        test_results["emoji_trigger"]["message"] = str(e)

if __name__ == "__main__":
    logger.info("Starting step-by-step routine bot test...")
    bot.run(TOKEN) 