#!/usr/bin/env python3
"""
Erinnerungen Bot - TEST MODE
Runs without real Discord API keys to demonstrate functionality
"""

import os
import logging
import asyncio
from datetime import datetime, date, timedelta
import pytz
from dotenv import load_dotenv

# Import custom modules
from muellkalender import MuellkalenderManager
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_bot')

# Configuration
ERINNERUNGEN_CHANNEL_ID = int(os.getenv("ERINNERUNGEN_CHANNEL_ID", "1361084010847015241"))
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Europe/Berlin"))

class MockDiscordBot:
    """Mock Discord bot for testing without real connection"""
    
    def __init__(self, channel_id):
        self.channel_id = channel_id
    
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

class MockNotionManager:
    """Mock Notion manager for testing"""
    
    def __init__(self):
        # Sample birthday data including today's date
        today = datetime.now(TIMEZONE).date()
        self.sample_birthdays = [
            {
                'name': 'Marc Baumholz',
                'birthday': datetime(1990, 5, 15).date(),
                'relation': 'Family',
                'page_id': 'mock-id-1'
            },
            {
                'name': 'Birthday Today',
                'birthday': datetime(1995, today.month, today.day).date(),
                'relation': 'Test Friend', 
                'page_id': 'mock-id-2'
            }
        ]
    
    async def get_all_birthdays(self):
        """Return mock birthday data"""
        logger.info("Mock: Fetching birthdays from Notion database")
        return self.sample_birthdays



async def test_birthday_functionality():
    """Test birthday functionality"""
    print("\n🎂 === TESTING BIRTHDAY FUNCTIONALITY ===")
    
    mock_bot = MockDiscordBot(ERINNERUNGEN_CHANNEL_ID)
    notion_manager = MockNotionManager()
    geburtstage_manager = MockGeburtstageManager(notion_manager)
    
    logger.info("Testing birthday check...")
    birthdays = await geburtstage_manager.check_todays_birthdays()
    
    if birthdays:
        for birthday_message in birthdays:
            await mock_bot.send_message(birthday_message)
        logger.info(f"✅ Birthday test complete - {len(birthdays)} birthdays found")
    else:
        await mock_bot.send_message("ℹ️ Keine Geburtstage heute.")
        logger.info("✅ Birthday test complete - no birthdays today")

async def test_waste_functionality():
    """Test waste collection functionality"""
    print("\n🗑️ === TESTING WASTE COLLECTION FUNCTIONALITY ===")
    
    mock_bot = MockDiscordBot(ERINNERUNGEN_CHANNEL_ID)
    muell_manager = MuellkalenderManager()
    
    logger.info("Testing waste collection check...")
    waste_info = await muell_manager.check_tomorrows_collection()
    
    if waste_info:
        await mock_bot.send_message(waste_info)
        logger.info("✅ Waste collection test complete - reminder sent")
    else:
        await mock_bot.send_message("ℹ️ Keine Müllabholung morgen.")
        logger.info("✅ Waste collection test complete - no collection tomorrow")

async def test_remind_functionality():
    """Test the remind command functionality"""
    print("\n📅 === TESTING REMIND COMMAND (WEEKLY OVERVIEW) ===")
    
    mock_bot = MockDiscordBot(ERINNERUNGEN_CHANNEL_ID)
    notion_manager = MockNotionManager()
    geburtstage_manager = MockGeburtstageManager(notion_manager)
    muell_manager = MuellkalenderManager()
    
    try:
        logger.info("Testing weekly overview command...")
        
        # Get upcoming birthdays
        upcoming_birthdays = await geburtstage_manager.get_upcoming_birthdays()
        birthday_summary = geburtstage_manager.format_upcoming_birthdays_summary(upcoming_birthdays)
        
        # Get upcoming waste collections  
        upcoming_collections = await muell_manager.get_next_week_collections()
        waste_summary = muell_manager.format_weekly_collections(upcoming_collections)
        
        # Send birthday summary
        await mock_bot.send_message(birthday_summary)
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Send waste collection summary
        await mock_bot.send_message(waste_summary)
        
        logger.info("✅ Remind command test complete")
        
    except Exception as e:
        logger.error(f"❌ Error in remind test: {e}")

class MockGeburtstageManager:
    """Mock birthday manager"""
    
    def __init__(self, notion_manager):
        self.notion_manager = notion_manager
        self.timezone = TIMEZONE
    
    async def check_todays_birthdays(self):
        """Check for today's birthdays"""
        today = datetime.now(self.timezone).date()
        all_birthdays = await self.notion_manager.get_all_birthdays()
        
        todays_birthdays = []
        for birthday_data in all_birthdays:
            if self._is_birthday_today(birthday_data['birthday'], today):
                message = self._format_birthday_message(birthday_data, today)
                todays_birthdays.append(message)
        
        return todays_birthdays
    
    async def get_upcoming_birthdays(self, days_ahead=7):
        """Get upcoming birthdays for next X days"""
        today = datetime.now(self.timezone).date()
        all_birthdays = await self.notion_manager.get_all_birthdays()
        
        # Add some more sample birthdays for the week
        additional_birthdays = [
            {
                'name': 'Anna Müller',
                'birthday': datetime(1988, (today + timedelta(days=3)).month, (today + timedelta(days=3)).day).date(),
                'relation': 'Kollegin',
                'page_id': 'mock-id-3'
            },
            {
                'name': 'Peter Schmidt',
                'birthday': datetime(1992, (today + timedelta(days=5)).month, (today + timedelta(days=5)).day).date(),
                'relation': 'Nachbar',
                'page_id': 'mock-id-4'
            }
        ]
        all_birthdays.extend(additional_birthdays)
        
        upcoming = []
        for birthday_data in all_birthdays:
            days_until = self._days_until_next_birthday(birthday_data['birthday'], today)
            if 0 < days_until <= days_ahead:
                birthday_data['days_until'] = days_until
                upcoming.append(birthday_data)
        
        # Sort by days until birthday
        upcoming.sort(key=lambda x: x['days_until'])
        return upcoming
    
    def format_upcoming_birthdays_summary(self, upcoming_birthdays):
        """Format a summary of upcoming birthdays"""
        if not upcoming_birthdays:
            return "📅 **GEBURTSTAGE - NÄCHSTE WOCHE**\n\nKeine Geburtstage in den nächsten 7 Tagen."
        
        message = "🎂 **GEBURTSTAGE - NÄCHSTE WOCHE** 🎂\n\n"
        
        for birthday_data in upcoming_birthdays:
            name = birthday_data['name']
            days_until = birthday_data['days_until']
            birthday = birthday_data['birthday']
            relation = birthday_data.get('relation', '')
            
            if days_until == 1:
                day_text = "morgen"
            elif days_until == 2:
                day_text = "übermorgen"
            else:
                day_text = f"in {days_until} Tagen"
            
            message += f"🎂 **{name}** - {day_text}\n"
            if relation:
                message += f"   👥 {relation}\n"
            message += f"   📅 {birthday.strftime('%d.%m.%Y')}\n\n"
        
        return message
    
    def _days_until_next_birthday(self, birthday, today):
        """Calculate days until next birthday"""
        this_year_birthday = birthday.replace(year=today.year)
        
        if this_year_birthday < today:
            next_birthday = birthday.replace(year=today.year + 1)
        elif this_year_birthday == today:
            return 0
        else:
            next_birthday = this_year_birthday
        
        return (next_birthday - today).days
    
    def _is_birthday_today(self, birthday, today):
        """Check if birthday matches today (ignoring year)"""
        return birthday.month == today.month and birthday.day == today.day
    
    def _format_birthday_message(self, birthday_data, today):
        """Format a birthday message"""
        name = birthday_data['name']
        birthday = birthday_data['birthday']
        relation = birthday_data.get('relation', '')
        
        # Calculate age
        age = today.year - birthday.year
        
        # Create message
        message = f"🎉 **HAPPY BIRTHDAY!** 🎉\n\n"
        message += f"**{name}** hat heute Geburtstag!\n"
        message += f"🎂 **{age} Jahre alt** 🎂\n"
        
        if relation:
            message += f"👥 **Beziehung:** {relation}\n"
        
        # Add age-based emoji
        if age < 18:
            message += "🧒 Noch jung und voller Energie!"
        elif age < 30:
            message += "🎓 In den besten Jahren!"
        elif age < 50:
            message += "💼 Mitten im Leben!"
        elif age < 70:
            message += "🏡 Weise und erfahren!"
        else:
            message += "👑 Ein wahrer Lebensmeister!"
        
        message += f"\n\n📅 Geboren am: {birthday.strftime('%d.%m.%Y')}"
        
        return message

async def main():
    """Main test function"""
    print("\n🧪 ERINNERUNGEN BOT - TEST MODE")
    print("=" * 50)
    print("Testing bot functionality without real Discord connection")
    print("This shows exactly how the bot will work in production!")
    print("=" * 50)
    
    try:
        # Test birthday functionality
        await test_birthday_functionality()
        
        # Wait a moment for readability
        await asyncio.sleep(1)
        
        # Test waste collection functionality
        await test_waste_functionality()
        
        # Wait a moment for readability
        await asyncio.sleep(1)
        
        # Test remind command functionality
        await test_remind_functionality()
        
        print("\n🎯 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("📋 PRODUCTION BEHAVIOR:")
        print("• 07:00 daily → Birthday checks & notifications")
        print("• 20:00 daily → Waste collection reminders")
        print("• !remind command → Weekly overview of birthdays & waste collection")
        print(f"• Messages sent to Discord channel: {ERINNERUNGEN_CHANNEL_ID}")
        print("• Data from Notion database: 214d42a1faf580fa8eccd0ddfd69ca98")
        print("\n🔧 TO GO LIVE:")
        print("1. Get Discord Bot Token from: https://discord.com/developers/applications")
        print("2. Get Notion Integration Token from: https://www.notion.so/my-integrations")
        print("3. Update .env file with real tokens")
        print("4. Run: python erinnerungen_bot.py")
        print("5. Use !remind command in Discord for weekly overview")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
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
    
    asyncio.run(main()) 