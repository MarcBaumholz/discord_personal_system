"""
Notion Manager for Erinnerungen Bot
Handles all interactions with Notion API for birthday data
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from notion_client import Client
from dotenv import load_dotenv
import pytz

env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

logger = logging.getLogger('erinnerungen_bot.notion_manager')

class NotionManager:
    """Manages interaction with Notion API for birthday data"""
    
    def __init__(self):
        """Initialize Notion client and configuration"""
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("GEBURTSTAGE_DATABASE_ID")
        self.timezone = pytz.timezone('Europe/Berlin')
        
        if not self.token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        
        if not self.database_id:
            raise ValueError("GEBURTSTAGE_DATABASE_ID environment variable is required")
        
        logger.info("Initializing Notion Manager")
        
        # Create Notion client
        self.notion = Client(auth=self.token)
        
        # Clean database ID if it's in URL format
        self.database_id = self._clean_database_id(self.database_id)
        
        logger.info(f"Notion Manager initialized with database ID: {self.database_id}")
    
    def _clean_database_id(self, database_id: str) -> str:
        """Clean database ID from URL format to pure ID"""
        # Remove URL parts if present
        if 'notion.so' in database_id:
            # Extract ID from URL like: https://www.notion.so/marcbaumholz/214d42a1faf580fa8eccd0ddfd69ca98
            parts = database_id.split('/')
            database_id = parts[-1]
        
        # Remove any query parameters
        if '?' in database_id:
            database_id = database_id.split('?')[0]
        
        # Remove dashes if present
        database_id = database_id.replace('-', '')
        
        return database_id
    
    async def get_all_birthdays(self) -> List[Dict[str, Any]]:
        """Fetch all birthday entries from Notion database"""
        try:
            logger.info("Fetching all birthdays from Notion database")
            
            # Query the database
            response = self.notion.databases.query(
                database_id=self.database_id
            )
            
            birthdays = []
            for page in response.get('results', []):
                birthday_data = self._parse_birthday_page(page)
                if birthday_data:
                    birthdays.append(birthday_data)
            
            logger.info(f"Found {len(birthdays)} birthday entries")
            return birthdays
            
        except Exception as e:
            logger.error(f"Error fetching birthdays from Notion: {e}")
            raise
    
    def _parse_birthday_page(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a birthday page from Notion API response"""
        try:
            properties = page.get('properties', {})
            
            # Extract name (assuming it's the title property)
            name = self._extract_title(properties)
            if not name:
                logger.warning(f"No name found for page {page.get('id')}")
                return None
            
            # Extract birthday date
            birthday_date = self._extract_date(properties)
            if not birthday_date:
                logger.warning(f"No birthday date found for {name}")
                return None
            
            # Extract optional relation/notes
            relation = self._extract_relation(properties)
            
            return {
                'name': name,
                'birthday': birthday_date,
                'relation': relation,
                'page_id': page.get('id')
            }
            
        except Exception as e:
            logger.error(f"Error parsing birthday page: {e}")
            return None
    
    def _extract_title(self, properties: Dict[str, Any]) -> Optional[str]:
        """Extract name/title from Notion properties"""
        # Common title property names
        title_keys = ['Name', 'Person', 'Title', '']
        
        for key, prop in properties.items():
            if prop.get('type') == 'title':
                title_content = prop.get('title', [])
                if title_content and len(title_content) > 0:
                    return title_content[0].get('text', {}).get('content', '')
        
        return None
    
    def _extract_date(self, properties: Dict[str, Any]) -> Optional[date]:
        """Extract birthday date from Notion properties"""
        # Common date property names
        date_keys = ['Geburtstag', 'Birthday', 'Datum', 'Date']
        
        for key, prop in properties.items():
            if prop.get('type') == 'date':
                date_data = prop.get('date')
                if date_data:
                    date_string = date_data.get('start')
                    if date_string:
                        try:
                            # Parse date string (format: YYYY-MM-DD)
                            return datetime.strptime(date_string, '%Y-%m-%d').date()
                        except ValueError as e:
                            logger.warning(f"Invalid date format: {date_string}")
                            continue
        
        return None
    
    def _extract_relation(self, properties: Dict[str, Any]) -> Optional[str]:
        """Extract relation/relationship from Notion properties"""
        relation_keys = ['Beziehung', 'Relation', 'Relationship', 'Type']
        
        for key, prop in properties.items():
            if prop.get('type') == 'select':
                select_data = prop.get('select')
                if select_data:
                    return select_data.get('name', '')
            elif prop.get('type') == 'rich_text':
                rich_text = prop.get('rich_text', [])
                if rich_text and len(rich_text) > 0:
                    return rich_text[0].get('text', {}).get('content', '')
        
        return None
    
    async def test_connection(self) -> bool:
        """Test the Notion API connection"""
        try:
            logger.info("Testing Notion API connection")
            response = self.notion.databases.retrieve(database_id=self.database_id)
            logger.info("Notion API connection successful")
            return True
        except Exception as e:
            logger.error(f"Notion API connection failed: {e}")
            return False 