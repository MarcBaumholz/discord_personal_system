#!/usr/bin/env python3
"""
Erinnerungen Bot - DEMO VERSION
Shows functionality without requiring real Discord/Notion API keys
"""

import asyncio
from datetime import datetime, date, timedelta
import pytz
from typing import List, Dict, Any

# Mock services for demo
class MockNotionManager:
    """Mock Notion manager for demo purposes"""
    
    def __init__(self):
        # Sample birthday data
        self.sample_birthdays = [
            {
                'name': 'Marc',
                'birthday': date(1990, 5, 15),
                'relation': 'Friend',
                'page_id': 'mock-id-1'
            },
            {
                'name': 'Anna',
                'birthday': date(1985, 12, 3),
                'relation': 'Family', 
                'page_id': 'mock-id-2'
            },
            # Add today's date for demo
            {
                'name': 'Demo Person',
                'birthday': date(1995, datetime.now().month, datetime.now().day),
                'relation': 'Demo Friend',
                'page_id': 'mock-id-3'
            }
        ]
    
    async def get_all_birthdays(self) -> List[Dict[str, Any]]:
        """Return mock birthday data"""
        return self.sample_birthdays

class MockMuellkalenderManager:
    """Mock waste calendar manager for demo purposes"""
    
    def __init__(self):
        self.timezone = pytz.timezone('Europe/Berlin')
    
    async def check_tomorrows_collection(self) -> str:
        """Return mock waste collection info"""
        now = datetime.now(self.timezone)
        tomorrow = (now + timedelta(days=1)).date()
        
        # Always return demo waste collection
        message = f"🗑️ **MÜLL-ERINNERUNG** 🗑️\n\n"
        message += f"**Morgen ({tomorrow.strftime('%d.%m.%Y')}) wird Müll abgeholt!**\n\n"
        message += "**Bitte bereitstellen:**\n"
        message += "• 🍂 Biotonne (braune Tonne)\n"
        message += "• ♻️ Gelber Sack (gelbe Tonne)\n"
        message += f"\n📍 **Ort:** Schwaikheim, Baden-Württemberg"
        message += f"\n⏰ **Erinnerung:** Tonnen bis 06:00 Uhr bereitstellen"
        
        return message

class MockGeburtstageManager:
    """Mock birthday manager for demo purposes"""
    
    def __init__(self, notion_manager):
        self.notion_manager = notion_manager
        self.timezone = pytz.timezone('Europe/Berlin')
    
    async def check_todays_birthdays(self) -> List[str]:
        """Check for demo birthdays today"""
        now = datetime.now(self.timezone)
        today = now.date()
        
        all_birthdays = await self.notion_manager.get_all_birthdays()
        todays_birthdays = []
        
        for birthday_data in all_birthdays:
            if self._is_birthday_today(birthday_data['birthday'], today):
                message = self._format_birthday_message(birthday_data, today)
                todays_birthdays.append(message)
        
        return todays_birthdays
    
    def _is_birthday_today(self, birthday: date, today: date) -> bool:
        """Check if birthday matches today (ignoring year)"""
        return birthday.month == today.month and birthday.day == today.day
    
    def _format_birthday_message(self, birthday_data: dict, today: date) -> str:
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

async def demo_birthday_check():
    """Demo birthday functionality"""
    print("🎂 === GEBURTSTAGS-CHECK DEMO ===")
    print("Checking for birthdays today...\n")
    
    notion_manager = MockNotionManager()
    geburtstage_manager = MockGeburtstageManager(notion_manager)
    
    birthdays = await geburtstage_manager.check_todays_birthdays()
    
    if birthdays:
        for birthday in birthdays:
            print(birthday)
            print("-" * 50)
    else:
        print("Keine Geburtstage heute.")
    
    print()

async def demo_waste_check():
    """Demo waste collection functionality"""
    print("🗑️ === MÜLLKALENDER-CHECK DEMO ===")
    print("Checking waste collection for tomorrow...\n")
    
    muell_manager = MockMuellkalenderManager()
    waste_info = await muell_manager.check_tomorrows_collection()
    
    print(waste_info)
    print("-" * 50)
    print()

def show_info():
    """Show bot information"""
    print("=" * 60)
    print("🤖 ERINNERUNGEN BOT - DEMO VERSION")
    print("=" * 60)
    print()
    print("This demo shows how your bot will work when configured!")
    print()
    print("📋 FEATURES:")
    print("• 🎂 Birthday reminders from Notion database")
    print("• 🗑️ Waste collection reminders for Schwaikheim")
    print("• ⏰ Automatic scheduling (07:00 & 20:00 daily)")
    print("• 💬 Discord integration")
    print()
    print("🔧 TO USE WITH REAL DATA:")
    print("1. Get Discord Bot Token")
    print("2. Get Notion Integration Token") 
    print("3. Update .env file with real tokens")
    print("4. Run: python erinnerungen_bot.py")
    print()
    print("📊 DEMO OUTPUT:")
    print("=" * 60)
    print()

async def main():
    """Run the demo"""
    show_info()
    
    # Demo birthday check
    await demo_birthday_check()
    
    # Demo waste collection check
    await demo_waste_check()
    
    print("✅ Demo completed!")
    print()
    print("This is exactly how your bot will work with real API keys!")
    print("See GETTING_STARTED.md for setup instructions.")

if __name__ == "__main__":
    asyncio.run(main()) 