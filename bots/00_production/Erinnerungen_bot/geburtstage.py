"""
Geburtstage Manager for Erinnerungen Bot
Handles birthday checking and notification formatting
"""

import logging
from typing import List, Optional
from datetime import datetime, date
import pytz
from notion_manager import NotionManager

logger = logging.getLogger('erinnerungen_bot.geburtstage')

class GeburtstageManager:
    """Manages birthday checks and notifications"""
    
    def __init__(self, notion_manager: NotionManager):
        """Initialize with Notion manager"""
        self.notion_manager = notion_manager
        self.timezone = pytz.timezone('Europe/Berlin')
        logger.info("Geburtstage Manager initialized")
    
    async def check_todays_birthdays(self) -> List[str]:
        """
        Check for birthdays today and return formatted messages
        
        Returns:
            List of formatted birthday messages
        """
        try:
            # Get current date in Berlin timezone
            now = datetime.now(self.timezone)
            today = now.date()
            
            logger.info(f"Checking birthdays for {today}")
            
            # Fetch all birthdays from Notion
            all_birthdays = await self.notion_manager.get_all_birthdays()
            
            # Find today's birthdays
            todays_birthdays = []
            for birthday_data in all_birthdays:
                if self._is_birthday_today(birthday_data['birthday'], today):
                    message = self._format_birthday_message(birthday_data, today)
                    todays_birthdays.append(message)
                    logger.info(f"Birthday today: {birthday_data['name']}")
            
            if not todays_birthdays:
                logger.info("No birthdays today")
            
            return todays_birthdays
            
        except Exception as e:
            logger.error(f"Error checking birthdays: {e}")
            raise
    
    def _is_birthday_today(self, birthday: date, today: date) -> bool:
        """Check if birthday matches today (ignoring year)"""
        return birthday.month == today.month and birthday.day == today.day
    
    def _format_birthday_message(self, birthday_data: dict, today: date) -> str:
        """
        Format a birthday message
        
        Args:
            birthday_data: Dictionary with name, birthday, relation, page_id
            today: Current date
            
        Returns:
            Formatted birthday message
        """
        name = birthday_data['name']
        birthday = birthday_data['birthday']
        relation = birthday_data.get('relation', '')
        
        # Calculate age
        age = today.year - birthday.year
        
        # Create base message
        message = f"🎉 **HAPPY BIRTHDAY!** 🎉\n\n"
        message += f"**{name}** hat heute Geburtstag!\n"
        message += f"🎂 **{age} Jahre alt** 🎂\n"
        
        # Add relation if available
        if relation:
            message += f"👥 **Beziehung:** {relation}\n"
        
        # Add birthday emoji based on age ranges
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
    
    async def get_upcoming_birthdays(self, days_ahead: int = 7) -> List[dict]:
        """
        Get birthdays in the next specified days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming birthday data
        """
        try:
            now = datetime.now(self.timezone)
            today = now.date()
            
            # Fetch all birthdays
            all_birthdays = await self.notion_manager.get_all_birthdays()
            
            upcoming = []
            for birthday_data in all_birthdays:
                days_until = self._days_until_next_birthday(birthday_data['birthday'], today)
                if 0 < days_until <= days_ahead:
                    birthday_data['days_until'] = days_until
                    upcoming.append(birthday_data)
            
            # Sort by days until birthday
            upcoming.sort(key=lambda x: x['days_until'])
            
            return upcoming
            
        except Exception as e:
            logger.error(f"Error getting upcoming birthdays: {e}")
            raise
    
    def _days_until_next_birthday(self, birthday: date, today: date) -> int:
        """
        Calculate days until next birthday
        
        Args:
            birthday: The person's birthday
            today: Current date
            
        Returns:
            Number of days until next birthday (0 if today)
        """
        # Create this year's birthday
        this_year_birthday = birthday.replace(year=today.year)
        
        if this_year_birthday < today:
            # Birthday already passed this year, use next year
            next_birthday = birthday.replace(year=today.year + 1)
        elif this_year_birthday == today:
            # Birthday is today
            return 0
        else:
            # Birthday is still coming this year
            next_birthday = this_year_birthday
        
        return (next_birthday - today).days
    
    def format_upcoming_birthdays_summary(self, upcoming_birthdays: List[dict]) -> str:
        """
        Format a summary of upcoming birthdays
        
        Args:
            upcoming_birthdays: List of upcoming birthday data
            
        Returns:
            Formatted summary message
        """
        if not upcoming_birthdays:
            return "Keine Geburtstage in den nächsten Tagen."
        
        message = "📅 **KOMMENDE GEBURTSTAGE** 📅\n\n"
        
        for birthday_data in upcoming_birthdays:
            name = birthday_data['name']
            days_until = birthday_data['days_until']
            birthday = birthday_data['birthday']
            relation = birthday_data.get('relation', '')
            
            if days_until == 1:
                day_text = "morgen"
            else:
                day_text = f"in {days_until} Tagen"
            
            message += f"🎂 **{name}** - {day_text}\n"
            if relation:
                message += f"   👥 {relation}\n"
            message += f"   📅 {birthday.strftime('%d.%m.%Y')}\n\n"
        
        return message 