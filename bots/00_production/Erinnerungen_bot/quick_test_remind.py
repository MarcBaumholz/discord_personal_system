#!/usr/bin/env python3
"""Quick test for remind functionality"""

import asyncio
from test_bot import MockNotionManager, MockGeburtstageManager, MuellkalenderManager, MockDiscordBot, ERINNERUNGEN_CHANNEL_ID

async def test_full_remind():
    """Test complete remind functionality"""
    print("🧪 TESTING FULL REMIND COMMAND")
    print("=" * 40)
    
    # Setup managers
    mock_bot = MockDiscordBot(ERINNERUNGEN_CHANNEL_ID)
    notion_manager = MockNotionManager()
    geburtstage_manager = MockGeburtstageManager(notion_manager)
    muell_manager = MuellkalenderManager()
    
    # Get upcoming birthdays
    print("\n📅 Getting upcoming birthdays...")
    upcoming_birthdays = await geburtstage_manager.get_upcoming_birthdays()
    birthday_summary = geburtstage_manager.format_upcoming_birthdays_summary(upcoming_birthdays)
    
    # Get upcoming waste collections
    print("🗑️ Getting upcoming waste collections...")
    upcoming_collections = await muell_manager.get_next_week_collections()
    waste_summary = muell_manager.format_weekly_collections(upcoming_collections)
    
    # Display results
    print("\n" + "="*60)
    print("📢 REMIND COMMAND OUTPUT:")
    print("="*60)
    
    await mock_bot.send_message(birthday_summary)
    await asyncio.sleep(0.5)
    await mock_bot.send_message(waste_summary)
    
    print("✅ Remind command test complete!")

if __name__ == "__main__":
    asyncio.run(test_full_remind()) 