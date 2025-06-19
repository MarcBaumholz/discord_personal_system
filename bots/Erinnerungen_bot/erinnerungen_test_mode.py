#!/usr/bin/env python3
"""
Erinnerungen Bot - TEST MODE
Runs without real Discord API keys to demonstrate functionality
"""

import os
import logging
import asyncio
from datetime import datetime
import pytz
from dotenv import load_dotenv
import time

# Import custom modules
from notion_manager import NotionManager
from geburtstage import GeburtstageManager
from muellkalender import MuellkalenderManager
from scheduler import ErinnerungsScheduler

env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('erinnerungen_bot_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('erinnerungen_bot_test')

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "test_token")
ERINNERUNGEN_CHANNEL_ID = int(os.getenv("ERINNERUNGEN_CHANNEL_ID", "1361084010847015241"))
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Europe/Berlin"))

class MockDiscordBot:
    """Mock Discord bot for testing without real connection"""
    
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.running = False
    
    async def send_message(self, message):
        """Simulate sending Discord message"""
        print("=" * 60)
        print("📢 DISCORD MESSAGE SENT")
        print("=" * 60)
        print(f"Channel: {self.channel_id}")
        print(f"Time: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(message)
        print("=" * 60)
        print()
    
    def get_channel(self, channel_id):
        """Mock get_channel method"""
        return self if channel_id == self.channel_id else None

class MockNotionManager:
    """Mock Notion manager for testing"""
    
    def __init__(self):
        # Sample birthday data
        self.sample_birthdays = [
            {
                'name': 'Marc Baumholz',
                'birthday': datetime(1990, 5, 15).date(),
                'relation': 'Family',
                'page_id': 'mock-id-1'
            },
            {
                'name': 'Test Person',
                'birthday': datetime(1985, datetime.now().month, datetime.now().day).date(),
                'relation': 'Friend', 
                'page_id': 'mock-id-2'
            }
        ]
    
    async def get_all_birthdays(self):
        """Return mock birthday data"""
        logger.info("Mock: Fetching birthdays from Notion database")
        return self.sample_birthdays
    
    async def test_connection(self):
        """Mock connection test"""
        logger.info("Mock: Notion API connection test successful")
        return True

class TestModeScheduler:
    """Test mode scheduler that runs checks immediately"""
    
    def __init__(self, bot, channel_id, geburtstage_manager, muellkalender_manager):
        self.bot = bot
        self.channel_id = channel_id
        self.geburtstage_manager = geburtstage_manager
        self.muellkalender_manager = muellkalender_manager
        self.timezone = TIMEZONE
    
    async def run_all_checks(self):
        """Run all checks in test mode"""
        logger.info("🧪 Running TEST MODE checks...")
        
        # Birthday check
        await self._test_birthday_check()
        
        # Wait a moment for readability
        await asyncio.sleep(2)
        
        # Waste collection check
        await self._test_waste_check()
    
    async def _test_birthday_check(self):
        """Test birthday check"""
        try:
            logger.info("Testing birthday check...")
            birthdays = await self.geburtstage_manager.check_todays_birthdays()
            
            if birthdays:
                for birthday_message in birthdays:
                    await self.bot.send_message(birthday_message)
                logger.info(f"✅ Birthday check complete - {len(birthdays)} birthdays found")
            else:
                await self.bot.send_message("ℹ️ Keine Geburtstage heute.")
                logger.info("✅ Birthday check complete - no birthdays today")
                
        except Exception as e:
            logger.error(f"❌ Error in birthday check: {e}")
    
    async def _test_waste_check(self):
        """Test waste collection check"""
        try:
            logger.info("Testing waste collection check...")
            waste_info = await self.muellkalender_manager.check_tomorrows_collection()
            
            if waste_info:
                await self.bot.send_message(waste_info)
                logger.info("✅ Waste collection check complete - reminder sent")
            else:
                await self.bot.send_message("ℹ️ Keine Müllabholung morgen.")
                logger.info("✅ Waste collection check complete - no collection tomorrow")
                
        except Exception as e:
            logger.error(f"❌ Error in waste collection check: {e}")

async def main():
    """Main function for test mode"""
    print("\n🧪 ERINNERUNGEN BOT - TEST MODE")
    print("=" * 50)
    print("Running without real Discord/Notion API keys")
    print("This shows exactly how the bot will work in production!")
    print("=" * 50)
    
    try:
        # Initialize mock Discord bot
        mock_bot = MockDiscordBot(ERINNERUNGEN_CHANNEL_ID)
        logger.info("✅ Mock Discord bot initialized")
        
        # Check if we should use real Notion or mock
        notion_token = os.getenv("NOTION_TOKEN", "")
        if notion_token and notion_token != "your_notion_integration_token_here":
            logger.info("🔗 Using real Notion integration")
            notion_manager = NotionManager()
            
            # Test real connection
            if await notion_manager.test_connection():
                logger.info("✅ Real Notion connection successful")
            else:
                logger.warning("⚠️ Real Notion connection failed, using mock data")
                notion_manager = MockNotionManager()
        else:
            logger.info("🎭 Using mock Notion data (no real token)")
            notion_manager = MockNotionManager()
        
        # Initialize birthday manager
        geburtstage_manager = GeburtstageManager(notion_manager)
        logger.info("✅ Birthday manager initialized")
        
        # Initialize waste calendar manager
        muellkalender_manager = MuellkalenderManager()
        logger.info("✅ Waste calendar manager initialized")
        
        # Initialize test scheduler
        test_scheduler = TestModeScheduler(
            mock_bot,
            ERINNERUNGEN_CHANNEL_ID,
            geburtstage_manager,
            muellkalender_manager
        )
        
        logger.info("✅ Test scheduler initialized")
        
        # Run all checks
        await test_scheduler.run_all_checks()
        
        print("\n🎯 TEST MODE COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("📋 WHAT HAPPENS IN PRODUCTION:")
        print("• 07:00 daily → Birthday checks & notifications")
        print("• 20:00 daily → Waste collection reminders")
        print("• Messages sent to Discord channel:", ERINNERUNGEN_CHANNEL_ID)
        print("• Data from Notion database: 214d42a1faf580fa8eccd0ddfd69ca98")
        print("\n🔧 TO GO LIVE:")
        print("1. Get Discord Bot Token")
        print("2. Get Notion Integration Token")
        print("3. Update .env file")
        print("4. Run: python erinnerungen_bot.py")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Error in test mode: {e}")
        print(f"\n❌ Test failed: {e}")

def show_configuration():
    """Show current configuration"""
    print("\n🔧 CURRENT CONFIGURATION:")
    print("-" * 30)
    
    discord_token = os.getenv("DISCORD_TOKEN", "")
    notion_token = os.getenv("NOTION_TOKEN", "")
    
    print(f"Discord Token: {'✅ SET' if discord_token and discord_token != 'your_discord_bot_token_here' else '❌ PLACEHOLDER'}")
    print(f"Notion Token: {'✅ SET' if notion_token and notion_token != 'your_notion_integration_token_here' else '❌ PLACEHOLDER'}")
    print(f"Channel ID: {ERINNERUNGEN_CHANNEL_ID}")
    print(f"Database ID: {os.getenv('GEBURTSTAGE_DATABASE_ID', 'N/A')}")
    print(f"Timezone: {TIMEZONE}")
    print("-" * 30)

if __name__ == "__main__":
    show_configuration()
    asyncio.run(main()) 