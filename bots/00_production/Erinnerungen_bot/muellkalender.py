"""
Müllkalender Manager for Erinnerungen Bot
Handles waste collection calendar for Schwaikheim, Baden-Württemberg
"""

import logging
import csv
import os
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
import pytz

logger = logging.getLogger('erinnerungen_bot.muellkalender')

class MuellkalenderManager:
    """Manages waste collection calendar checks for Schwaikheim"""
    
    def __init__(self):
        """Initialize waste calendar manager"""
        self.timezone = pytz.timezone('Europe/Berlin')
        
        # Waste type mapping from CSV to internal format
        self.csv_to_internal = {
            'Papiertonne': 'papier',
            'Biotonne': 'bio', 
            'Restmülltonne (2-wöchentl.)': 'restmuell',
            'Gelbe Tonne': 'gelb'
        }
        
        # Waste type display information
        self.waste_types = {
            'restmuell': {'name': 'Restmüll', 'emoji': '🗑️', 'color': 'schwarz'},
            'bio': {'name': 'Biotonne', 'emoji': '🍂', 'color': 'braun'},
            'gelb': {'name': 'Gelber Sack', 'emoji': '♻️', 'color': 'gelb'},
            'papier': {'name': 'Papiertonne', 'emoji': '📰', 'color': 'blau'}
        }
        
        # Path to CSV file
        self.csv_file_path = os.path.join(os.path.dirname(__file__), 'Entleerungstermine_Juni_bis_Dez_2025.csv')
        
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
            
            # Get waste collection schedule from CSV
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
        Get waste collection schedule for Schwaikheim from CSV file
        
        Returns:
            List of waste collection events
        """
        try:
            collections = []
            
            # Check if CSV file exists
            if not os.path.exists(self.csv_file_path):
                logger.error(f"CSV file not found: {self.csv_file_path}")
                return []
            
            # Read CSV file
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        # Parse date from CSV (format: YYYY-MM-DD)
                        date_str = row['Datum'].strip()
                        collection_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        
                        # Map CSV waste type to internal type
                        csv_waste_type = row['Tonne'].strip()
                        internal_type = self.csv_to_internal.get(csv_waste_type)
                        
                        if internal_type:
                            collections.append({
                                'date': collection_date,
                                'type': internal_type,
                                'csv_name': csv_waste_type
                            })
                            logger.debug(f"Added collection: {collection_date} - {internal_type}")
                        else:
                            logger.warning(f"Unknown waste type in CSV: {csv_waste_type}")
                            
                    except ValueError as e:
                        logger.error(f"Error parsing CSV row {row}: {e}")
                        continue
            
            logger.info(f"Loaded {len(collections)} waste collection dates from CSV")
            return collections
            
        except Exception as e:
            logger.error(f"Error reading waste schedule from CSV: {e}")
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
        Get waste collections for the next 7 days from CSV data
        
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
                            'days_ahead': days_ahead,
                            'csv_name': collection.get('csv_name', '')
                        })
            
            logger.info(f"Found {len(week_collections)} collections in next 7 days")
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
            return "🗑️ **MÜLL - NÄCHSTE WOCHE** 🗑️\n\nKeine Müllabholung in den nächsten 7 Tagen."
        
        message = "🗑️ **MÜLL - NÄCHSTE WOCHE** 🗑️\n\n"
        
        # Group by date
        collections_by_date = {}
        for collection in collections:
            date_obj = collection['date']
            if date_obj not in collections_by_date:
                collections_by_date[date_obj] = []
            collections_by_date[date_obj].append(collection)
        
        # Sort by date
        sorted_dates = sorted(collections_by_date.keys())
        
        for date_obj in sorted_dates:
            date_collections = collections_by_date[date_obj]
            day_name = date_obj.strftime('%A')
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
                
            message += f"📅 **{german_day}, {date_obj.strftime('%d.%m.%Y')}** ({day_text})\n"
            
            for collection in date_collections:
                waste_type = collection['type']
                if waste_type in self.waste_types:
                    type_info = self.waste_types[waste_type]
                    message += f"   {type_info['emoji']} {type_info['name']} ({type_info['color']}e Tonne)\n"
            
            message += "\n"
        
        message += f"📍 **Ort:** Schwaikheim, Baden-Württemberg\n"
        message += f"⏰ **Erinnerung:** Tonnen bis 06:00 Uhr bereitstellen"
        
        return message 