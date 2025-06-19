"""
Notion Manager for Tagebuch Bot
Handles all interactions with the Notion database for journal entries.
"""

import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from notion_client import Client
from notion_client.errors import APIResponseError, HTTPResponseError, RequestTimeoutError
import pytz

logger = logging.getLogger('tagebuch_bot.notion_manager')

class NotionManager:
    """Manages interaction with Notion API for journal entries"""
    
    def __init__(self):
        """Initialize Notion client and configuration"""
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("TAGEBUCH_DATABASE_ID")
        self.timezone = pytz.timezone("Europe/Berlin")
        
        if not self.token or not self.database_id:
            raise ValueError("NOTION_TOKEN and TAGEBUCH_DATABASE_ID are required")
        
        logger.info("Notion Manager initialized")
        
        # Create Notion client
        self.notion = Client(auth=self.token)
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test connection to Notion database"""
        try:
            # Try to retrieve database info
            database = self.notion.databases.retrieve(database_id=self.database_id)
            logger.info(f"✅ Connected to Notion database: {database.get('title', [{}])[0].get('plain_text', 'Tagebuch')}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Notion database: {e}")
            raise
    
    async def create_journal_entry(self, title: str, text: str):
        """Create a new journal entry in Notion"""
        try:
            date = datetime.now(self.timezone)
            date_str = date.strftime("%Y-%m-%d")
            
            properties = {
                "Titel": {
                    "title": [{"text": {"content": title}}]
                },
                "Datum": {
                    "date": {"start": date_str}
                },
                "Text": {
                    "rich_text": [{"text": {"content": text}}]
                }
            }
            
            response = await asyncio.to_thread(
                self.notion.pages.create,
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"✅ Created journal entry: '{title}'")
            return {"success": True, "page_id": response["id"], "title": title}
            
        except Exception as e:
            logger.error(f"❌ Error creating journal entry: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_recent_entries(self, limit: int = 5) -> list:
        """
        Get recent journal entries from the database
        
        Args:
            limit: Maximum number of entries to retrieve
            
        Returns:
            list: List of recent journal entries
        """
        try:
            response = await asyncio.to_thread(
                self.notion.databases.query,
                database_id=self.database_id,
                sorts=[
                    {
                        "property": "Datum",
                        "direction": "descending"
                    }
                ],
                page_size=limit
            )
            
            entries = []
            for page in response.get("results", []):
                entry = self._parse_journal_entry(page)
                if entry:
                    entries.append(entry)
            
            logger.info(f"Retrieved {len(entries)} recent journal entries")
            return entries
            
        except Exception as e:
            logger.error(f"Error retrieving recent entries: {e}")
            return []
    
    def _parse_journal_entry(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a Notion page into a journal entry object"""
        try:
            properties = page.get("properties", {})
            
            # Extract title
            title_prop = properties.get("Titel", {})
            title = ""
            if title_prop.get("title"):
                title = "".join([text.get("plain_text", "") for text in title_prop.get("title", [])])
            
            # Extract date
            date_prop = properties.get("Datum", {})
            date_str = ""
            if date_prop.get("date") and date_prop.get("date", {}).get("start"):
                date_str = date_prop.get("date", {}).get("start")
            
            # Extract text
            text_prop = properties.get("Text", {})
            text = ""
            if text_prop.get("rich_text"):
                text = "".join([text.get("plain_text", "") for text in text_prop.get("rich_text", [])])
            
            return {
                "id": page.get("id"),
                "title": title,
                "date": date_str,
                "text": text[:100] + "..." if len(text) > 100 else text,  # Truncate for display
                "url": page.get("url", "")
            }
            
        except Exception as e:
            logger.error(f"Error parsing journal entry: {e}")
            return None
    
    async def check_entry_exists_today(self) -> bool:
        """
        Check if a journal entry already exists for today
        
        Returns:
            bool: True if entry exists for today
        """
        try:
            today = datetime.now(self.timezone).strftime("%Y-%m-%d")
            
            response = await asyncio.to_thread(
                self.notion.databases.query,
                database_id=self.database_id,
                filter={
                    "property": "Datum",
                    "date": {
                        "equals": today
                    }
                }
            )
            
            exists = len(response.get("results", [])) > 0
            logger.info(f"Journal entry for {today}: {'exists' if exists else 'not found'}")
            return exists
            
        except Exception as e:
            logger.error(f"Error checking if entry exists for today: {e}")
            return False
    
    async def get_journal_stats(self) -> Dict[str, Any]:
        """
        Get statistics about journal entries
        
        Returns:
            dict: Statistics about journal entries
        """
        try:
            # Get all entries (limited to 100 for performance)
            response = await asyncio.to_thread(
                self.notion.databases.query,
                database_id=self.database_id,
                page_size=100
            )
            
            entries = response.get("results", [])
            total_entries = len(entries)
            
            # Calculate stats
            current_month = datetime.now(self.timezone).strftime("%Y-%m")
            monthly_entries = 0
            
            for page in entries:
                date_prop = page.get("properties", {}).get("Datum", {})
                if date_prop.get("date") and date_prop.get("date", {}).get("start"):
                    entry_date = date_prop.get("date", {}).get("start")
                    if entry_date.startswith(current_month):
                        monthly_entries += 1
            
            return {
                "total_entries": total_entries,
                "monthly_entries": monthly_entries,
                "current_month": current_month
            }
            
        except Exception as e:
            logger.error(f"Error getting journal stats: {e}")
            return {
                "total_entries": 0,
                "monthly_entries": 0,
                "current_month": datetime.now(self.timezone).strftime("%Y-%m")
            } 