"""
Müllkalender Manager for Erinnerungen Bot
Handles waste collection calendar for Schwaikheim, Baden-Württemberg
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
import pytz

logger = logging.getLogger('erinnerungen_bot.muellkalender')

class MuellkalenderManager:
    """Manages waste collection calendar checks for Schwaikheim"""
    
    def __init__(self):
        """Initialize waste calendar manager"""
        self.timezone = pytz.timezone('Europe/Berlin')
        
        # Waste type mapping
        self.waste_types = {
            'restmuell': {'name': 'Restmüll', 'emoji': '🗑️', 'color': 'schwarz'},
            'bio': {'name': 'Biotonne', 'emoji': '🍂', 'color': 'braun'},
            'gelb': {'name': 'Gelber Sack', 'emoji': '♻️', 'color': 'gelb'},
            'papier': {'name': 'Papiertonne', 'emoji': '📰', 'color': 'blau'}
        }
        
        logger.info("Müllkalender Manager initialized for Schwaikheim")
    
    async def check_tomorrows_collection(self) -> Optional[str]:
        """
        Check if there's waste collection tomorrow
        
        Returns:
            Formatted message if waste collection tomorrow, None otherwise
        """
        try:
            now = datetime.now(self.timezone)
            tomorrow = (now + timedelta(days=1)).date()
            
            logger.info(f"Checking waste collection for tomorrow: {tomorrow}")
            
            # Get waste collection schedule
            collections = await self._get_waste_schedule()
            
            # Find collections for tomorrow
            tomorrow_collections = []
            for collection in collections:
                if collection['date'] == tomorrow:
                    tomorrow_collections.append(collection)
            
            if not tomorrow_collections:
                logger.info("No waste collection tomorrow")
                return None
            
            # Format message
            message = self._format_collection_reminder(tomorrow_collections, tomorrow)
            logger.info(f"Waste collection tomorrow: {len(tomorrow_collections)} types")
            
            return message
            
        except Exception as e:
            logger.error(f"Error checking waste collection: {e}")
            raise
    
    async def _get_waste_schedule(self) -> List[Dict]:
        """
        Get waste collection schedule for Schwaikheim
        Basic pattern-based schedule implementation
        
        Returns:
            List of waste collection events
        """
        try:
            now = datetime.now(self.timezone)
            collections = []
            
            # Generate realistic collection schedule for next 30 days
            for days_ahead in range(1, 31):
                future_date = (now + timedelta(days=days_ahead)).date()
                day_of_week = future_date.weekday()  # 0=Monday, 6=Sunday
                week_number = future_date.isocalendar()[1]
                
                # Realistic schedule for Schwaikheim area
                # Restmüll: every 2 weeks on Tuesday
                if day_of_week == 1 and week_number % 2 == 0:  # Tuesday, even weeks
                    collections.append({
                        'date': future_date,
                        'type': 'restmuell'
                    })
                
                # Biotonne: every Wednesday
                if day_of_week == 2:  # Wednesday  
                    collections.append({
                        'date': future_date,
                        'type': 'bio'
                    })
                
                # Gelber Sack: every 2 weeks on Friday
                if day_of_week == 4 and week_number % 2 == 1:  # Friday, odd weeks
                    collections.append({
                        'date': future_date,
                        'type': 'gelb'
                    })
                
                # Papier: once per month on first Monday
                if day_of_week == 0 and 1 <= future_date.day <= 7:  # First Monday of month
                    collections.append({
                        'date': future_date,
                        'type': 'papier'
                    })
            
            return collections
            
        except Exception as e:
            logger.error(f"Error getting waste schedule: {e}")
            return []
    
    def _format_collection_reminder(self, collections: List[Dict], date: date) -> str:
        """
        Format waste collection reminder message
        
        Args:
            collections: List of waste collections for the date
            date: Collection date
            
        Returns:
            Formatted reminder message
        """
        message = f"🗑️ **MÜLL-ERINNERUNG** 🗑️\n\n"
        message += f"**Morgen ({date.strftime('%d.%m.%Y')}) wird Müll abgeholt!**\n\n"
        
        # Add waste types
        waste_info = []
        for collection in collections:
            waste_type = collection['type']
            if waste_type in self.waste_types:
                type_info = self.waste_types[waste_type]
                waste_info.append(f"{type_info['emoji']} {type_info['name']} ({type_info['color']}e Tonne)")
        
        if waste_info:
            message += "**Bitte bereitstellen:**\n"
            for info in waste_info:
                message += f"• {info}\n"
        
        message += f"\n📍 **Ort:** Schwaikheim, Baden-Württemberg"
        message += f"\n⏰ **Erinnerung:** Tonnen bis 06:00 Uhr bereitstellen"
        
        return message
    
    async def get_next_week_collections(self) -> List[Dict]:
        """
        Get waste collections for the next 7 days
        
        Returns:
            List of waste collection events with dates
        """
        try:
            now = datetime.now(self.timezone)
            collections = await self._get_waste_schedule()
            
            # Filter for next 7 days
            week_collections = []
            for days_ahead in range(1, 8):  # Next 7 days
                target_date = (now + timedelta(days=days_ahead)).date()
                
                for collection in collections:
                    if collection['date'] == target_date:
                        week_collections.append({
                            'date': target_date,
                            'type': collection['type'],
                            'days_ahead': days_ahead
                        })
            
            return week_collections
            
        except Exception as e:
            logger.error(f"Error getting weekly collections: {e}")
            return []
    
    def format_weekly_collections(self, collections: List[Dict]) -> str:
        """
        Format weekly waste collection overview
        
        Args:
            collections: List of waste collections
            
        Returns:
            Formatted weekly overview message
        """
        if not collections:
            return "🗑️ **MÜLL - NÄCHSTE WOCHE**\n\nKeine Müllabholung in den nächsten 7 Tagen."
        
        message = "🗑️ **MÜLL - NÄCHSTE WOCHE** 🗑️\n\n"
        
        # Group by date
        collections_by_date = {}
        for collection in collections:
            date_str = collection['date']
            if date_str not in collections_by_date:
                collections_by_date[date_str] = []
            collections_by_date[date_str].append(collection)
        
        # Sort by date
        sorted_dates = sorted(collections_by_date.keys())
        
        for date in sorted_dates:
            date_collections = collections_by_date[date]
            day_name = date.strftime('%A')
            german_days = {
                'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
                'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag', 'Sunday': 'Sonntag'
            }
            german_day = german_days.get(day_name, day_name)
            
            days_ahead = date_collections[0]['days_ahead']
            if days_ahead == 1:
                day_text = "morgen"
            elif days_ahead == 2:
                day_text = "übermorgen"
            else:
                day_text = f"in {days_ahead} Tagen"
                
            message += f"📅 **{german_day}, {date.strftime('%d.%m.%Y')}** ({day_text})\n"
            
            for collection in date_collections:
                waste_type = collection['type']
                if waste_type in self.waste_types:
                    type_info = self.waste_types[waste_type]
                    message += f"   {type_info['emoji']} {type_info['name']} ({type_info['color']}e Tonne)\n"
            
            message += "\n"
        
        message += f"📍 **Ort:** Schwaikheim, Baden-Württemberg\n"
        message += f"⏰ **Erinnerung:** Tonnen bis 06:00 Uhr bereitstellen"
        
        return message 