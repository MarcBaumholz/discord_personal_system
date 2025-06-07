import os
import logging
from datetime import datetime, timedelta
import pytz
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('routine_bot.notion_manager')

class NotionManager:
    """Manages interaction with Notion API to fetch and update routine data"""
    
    def __init__(self):
        """Initialize Notion client and configuration"""
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("ROUTINE_DATABASE_ID") 
        self.timezone = pytz.timezone('Europe/Berlin')
        
        logger.info("Initializing Notion Manager")
        
        # Create Notion client
        self.notion = Client(auth=self.token)
        
        # If database ID is not provided, try to find it
        if not self.database_id:
            logger.warning("No database ID provided, attempting to find it")
            self.database_id = self.find_routine_database()
            if self.database_id:
                logger.info(f"Found routine database: {self.database_id}")
            else:
                logger.error("Could not find routine database")
    
    def find_routine_database(self):
        """Find the routine database by searching for a database named 'Routines' or 'My Routines'"""
        try:
            response = self.notion.search(filter={"property": "object", "value": "database"})
            
            for result in response.get('results', []):
                title = self._get_title_from_result(result)
                if title and ('routines' in title.lower() or 'my routines' in title.lower()):
                    return result['id']
            
            return None
        except Exception as e:
            logger.error(f"Error finding routine database: {e}")
            return None
    
    def _get_title_from_result(self, result):
        """Extract title from Notion API result"""
        try:
            title_object = result.get('title', [])
            if title_object:
                title_text = ''.join([text.get('plain_text', '') for text in title_object])
                return title_text
            else:
                return None
        except Exception:
            return None
    
    def get_routines_for_day(self, date=None):
        """
        Get routines for a specific day
        
        Args:
            date: Date to get routines for (defaults to today)
            
        Returns:
            list: Routines for the specified day
        """
        if date is None:
            date = datetime.now(self.timezone).date()
        
        try:
            # Get the day of week (1=Monday, 7=Sunday)
            day_of_week = date.isoweekday()
            day_names = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_name = day_names[day_of_week]
            
            # Query for routines with the matching frequency or day
            filter_conditions = {
                "or": [
                    {
                        "property": "Frequency",
                        "select": {
                            "equals": "Daily"
                        }
                    },
                    {
                        "property": "Frequency",
                        "select": {
                            "equals": day_name
                        }
                    },
                    {
                        "property": "Frequency",
                        "select": {
                            "equals": "Weekdays"
                        }
                    },
                    {
                        "property": "Frequency",
                        "select": {
                            "equals": "Weekends"
                        }
                    }
                ]
            }
            
            # Refine filters for weekdays/weekends
            if day_of_week <= 5:  # Monday-Friday
                filter_conditions["or"].append({
                    "property": "Frequency",
                    "select": {
                        "equals": "Weekdays"
                    }
                })
            else:  # Saturday-Sunday
                filter_conditions["or"].append({
                    "property": "Frequency",
                    "select": {
                        "equals": "Weekends"
                    }
                })
            
            # Query the database
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter=filter_conditions,
                sorts=[
                    {
                        "property": "Time of Day",
                        "direction": "ascending"
                    }
                ]
            )
            
            # Process and return the routines
            routines = []
            for page in response.get('results', []):
                routine = self._parse_routine_page(page)
                if routine:
                    routines.append(routine)
            
            logger.info(f"Found {len(routines)} routines for {date}")
            return routines
            
        except Exception as e:
            logger.error(f"Error getting routines for {date}: {e}")
            return []
    
    def _parse_routine_page(self, page):
        """Parse a Notion page into a routine object"""
        try:
            properties = page.get('properties', {})
            
            # Extract routine name
            name = self._extract_text_property(properties.get('Routine Name', {}))
            
            # Extract time of day
            time_of_day = self._extract_select_property(properties.get('Time of Day', {}))
            
            # Extract frequency
            frequency = self._extract_select_property(properties.get('Frequency', {}))
            
            # Extract duration
            duration = self._extract_number_property(properties.get('Duration', {}))
            
            # Extract status
            status = self._extract_select_property(properties.get('Status', {}))
            
            # Extract notes/description
            notes = self._extract_rich_text_property(properties.get('Notes', {}))
            
            # Return the parsed routine
            return {
                'id': page.get('id'),
                'name': name,
                'time_of_day': time_of_day,
                'frequency': frequency,
                'duration': duration,
                'status': status,
                'notes': notes
            }
        except Exception as e:
            logger.error(f"Error parsing routine page: {e}")
            return None
    
    def _extract_text_property(self, property_obj):
        """Extract text value from a Notion property"""
        try:
            if property_obj.get('type') == 'title':
                title = property_obj.get('title', [])
                return ''.join([text.get('plain_text', '') for text in title])
            return None
        except Exception:
            return None
    
    def _extract_select_property(self, property_obj):
        """Extract select value from a Notion property"""
        try:
            if property_obj.get('type') == 'select' and property_obj.get('select'):
                return property_obj.get('select', {}).get('name')
            return None
        except Exception:
            return None
    
    def _extract_number_property(self, property_obj):
        """Extract number value from a Notion property"""
        try:
            if property_obj.get('type') == 'number':
                return property_obj.get('number')
            return None
        except Exception:
            return None
    
    def _extract_rich_text_property(self, property_obj):
        """Extract rich text value from a Notion property"""
        try:
            if property_obj.get('type') == 'rich_text':
                rich_text = property_obj.get('rich_text', [])
                return ''.join([text.get('plain_text', '') for text in rich_text])
            return None
        except Exception:
            return None
    
    def get_routine_steps(self, routine_id):
        """Get detailed steps from a routine's Notes field
        
        Args:
            routine_id: ID of the routine page
            
        Returns:
            list: List of routine steps
        """
        try:
            # Retrieve the page with Notes property
            page = self.notion.pages.retrieve(page_id=routine_id)
            properties = page.get('properties', {})
            
            # Extract Notes field (assumes a field called 'Notes' exists)
            notes = self._extract_rich_text_property(properties.get('Notes', {}))
            
            if not notes:
                logger.warning(f"No notes found for routine {routine_id}")
                return []
            
            # Parse steps (assuming format with line breaks, numbers, or bullet points)
            steps = []
            
            # Split by line breaks and process each line
            for line in notes.split('\n'):
                # Remove leading numbers, dashes, asterisks, etc.
                cleaned_line = line.strip()
                if cleaned_line:
                    # Remove bullet points or numbers at the beginning (1., -, *, etc.)
                    import re
                    cleaned_line = re.sub(r'^[\d\.\-\*\•\⁃\◦\○\▪\■\□\▫\❏\❑\❒\➤\➣\➢\➡\→\►\➔\✓\✔\✗\✘\☐\☑\☒]+\s*', '', cleaned_line)
                    
                    if cleaned_line:  # Only add non-empty lines
                        steps.append(cleaned_line.strip())
            
            logger.info(f"Found {len(steps)} steps for routine {routine_id}")
            return steps
            
        except Exception as e:
            logger.error(f"Error getting routine steps: {e}")
            return []
    
    def update_routine_status(self, routine_id, status):
        """Update the status of a routine"""
        try:
            self.notion.pages.update(
                page_id=routine_id,
                properties={
                    "Status": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            logger.info(f"Updated routine {routine_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating routine status: {e}")
            return False
    
    def get_routines_by_time(self, time_of_day=None, date=None):
        """
        Get routines for a specific time of day
        
        Args:
            time_of_day: Time of day filter (Morning, Afternoon, Evening)
            date: Date to get routines for
            
        Returns:
            list: Filtered routines
        """
        routines = self.get_routines_for_day(date)
        
        if time_of_day:
            return [r for r in routines if r.get('time_of_day') == time_of_day]
        
        return routines
    
    def get_routines_by_name_contains(self, keyword, date=None):
        """
        Get routines where the name contains a specific keyword
        
        Args:
            keyword: Keyword to search for in routine names (case insensitive)
            date: Date to get routines for
            
        Returns:
            list: Filtered routines
        """
        routines = self.get_routines_for_day(date)
        
        if keyword:
            keyword = keyword.lower()
            return [r for r in routines if keyword in r.get('name', '').lower()]
        
        return [] 