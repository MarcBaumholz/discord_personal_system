import os
import logging
import asyncio
from datetime import datetime
import pytz
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('wishlist_bot.notion_manager')

class NotionManager:
    """Manages interaction with Notion API to fetch interests data"""
    
    def __init__(self):
        """Initialize Notion client and configuration"""
        self.token = os.getenv("NOTION_TOKEN")
        self.interests_database_id = os.getenv("NOTION_INTERESTS_DATABASE_ID")
        self.timezone = pytz.timezone('Europe/Berlin')
        
        logger.info("Initializing Notion Manager")
        
        # Create Notion client
        self.notion = Client(auth=self.token)
        
        # Cache for interests
        self.interests_cache = None
        self.interests_cache_time = None
        self.cache_expiry_hours = 24  # Refresh cache every 24 hours
    
    async def get_interests(self):
        """
        Get interests from Notion database
        
        Returns:
            list: List of interests
        """
        # Check if cache is valid
        current_time = datetime.now(self.timezone)
        if (self.interests_cache is not None and self.interests_cache_time is not None and
            (current_time - self.interests_cache_time).total_seconds() < self.cache_expiry_hours * 3600):
            logger.info("Using cached interests")
            return self.interests_cache
        
        try:
            logger.info("Fetching interests from Notion")
            
            # Query the database
            response = await asyncio.to_thread(
                self.notion.databases.query,
                database_id=self.interests_database_id
            )
            
            # Extract interests from response
            interests = []
            
            for page in response.get('results', []):
                properties = page.get('properties', {})
                
                # Extract interest name
                interest_name = self._extract_text_property(properties.get('Name', {}))
                
                if interest_name:
                    # Check if there's a category
                    category = self._extract_select_property(properties.get('Kategorie', {}))
                    
                    if category:
                        interests.append({
                            'name': interest_name,
                            'category': category
                        })
                    else:
                        interests.append(interest_name)
            
            # Update cache
            self.interests_cache = interests
            self.interests_cache_time = current_time
            
            # Extract the top 25 interests based on priority or recency
            top_interests = interests[:25] if len(interests) > 25 else interests
            
            logger.info(f"Found {len(top_interests)} interests")
            return top_interests
            
        except Exception as e:
            logger.error(f"Error getting interests from Notion: {e}")
            
            # If we have cached interests, use them as fallback
            if self.interests_cache is not None:
                logger.info("Using cached interests as fallback")
                return self.interests_cache
                
            # Fallback to hardcoded interests as a last resort
            logger.info("Using hardcoded interests as fallback")
            return [
                "Coding", "Programming", "AI", "Machine Learning", "Python",
                "Web Development", "Productivity", "Technology", "Books",
                "Personal Finance", "Investing", "Health", "Fitness",
                "Self-improvement", "Time Management", "Photography",
                "Travel", "Gadgets", "Smart Home", "Coffee",
                "Reading", "Writing", "Music", "Food", "Minimalism"
            ]
    
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
    
    async def extract_interests_from_page(self, page_id="1e8d42a1faf5801797f1e32471a5a152"):
        """
        Extract interests directly from a Notion page content
        
        Args:
            page_id: The Notion page ID to extract from
            
        Returns:
            list: List of interests
        """
        try:
            logger.info(f"Fetching content from Notion page {page_id}")
            
            # Get the page
            page = await asyncio.to_thread(
                self.notion.pages.retrieve,
                page_id=page_id
            )
            
            # Get the page blocks
            blocks = await asyncio.to_thread(
                self.notion.blocks.children.list,
                block_id=page_id
            )
            
            # Extract text content from blocks
            interests = []
            
            for block in blocks.get('results', []):
                block_type = block.get('type')
                
                if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3', 'bulleted_list_item', 'numbered_list_item']:
                    text_content = block.get(block_type, {}).get('rich_text', [])
                    text = ''.join([t.get('plain_text', '') for t in text_content])
                    
                    # Simple processing to extract interests from text
                    # This is a basic approach - for production, you'd want more sophisticated NLP
                    if text and block_type in ['bulleted_list_item', 'numbered_list_item']:
                        # List items are likely direct interests
                        interests.append(text.strip())
                    elif ":" in text and block_type in ['paragraph']:
                        # Look for formats like "Interest: description"
                        parts = text.split(':', 1)
                        if len(parts) > 0 and len(parts[0].strip()) < 30:  # Likely a term, not a long sentence
                            interests.append(parts[0].strip())
            
            logger.info(f"Extracted {len(interests)} interests from page content")
            
            # Take top 25 if there are more
            top_interests = interests[:25] if len(interests) > 25 else interests
            
            return top_interests
        
        except Exception as e:
            logger.error(f"Error extracting interests from page: {e}")
            return [] 