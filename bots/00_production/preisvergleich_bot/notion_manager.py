import os
import logging
import re
from typing import List, Dict, Any, Optional
from notion_client import Client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('notion_manager')

class NotionProductManager:
    def __init__(self, notion_token: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize the Notion Product Manager for accessing the watchlist
        
        Args:
            notion_token: Notion API integration token
            database_id: ID of the Notion database containing products
        """
        self.notion_token = notion_token or os.getenv("NOTION_TOKEN")
        if not self.notion_token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN in .env or pass as argument.")
        
        # Get the database ID and clean it if needed
        raw_database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        if not raw_database_id:
            raise ValueError("Notion database ID is required. Set NOTION_DATABASE_ID in .env or pass as argument.")
        
        # Clean the database ID if it's in URL format
        self.database_id = self._clean_database_id(raw_database_id)
        
        self.notion = Client(auth=self.notion_token)
        logger.info("NotionProductManager initialized")
    
    def _clean_database_id(self, database_id: str) -> str:
        """
        Clean the database ID if it's in URL format
        
        Args:
            database_id: Raw database ID (might be in URL format)
            
        Returns:
            Clean database ID
        """
        # Check if it's a URL-like format with query parameters
        if '?' in database_id:
            # Extract the ID part before the query parameters
            database_id = database_id.split('?')[0]
        
        # If it contains slashes, extract the last part
        if '/' in database_id:
            database_id = database_id.split('/')[-1]
            
        # Use regex to extract just the ID part if it's in a complex format
        match = re.search(r'([a-f0-9]{32})', database_id)
        if match:
            database_id = match.group(1)
            
        logger.info(f"Using Notion database ID: {database_id}")
        return database_id
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """
        Retrieve all products from the Notion watchlist database
        
        Returns:
            List of product dictionaries with name and price information
        """
        try:
            logger.info(f"Querying Notion database: {self.database_id}")
            response = self.notion.databases.query(database_id=self.database_id)
            
            products = []
            
            for item in response.get("results", []):
                try:
                    # Extract product name (assuming it's a title property named "Produktname")
                    product_name = item["properties"].get("Produktname", {}).get("title", [])
                    if not product_name:
                        continue
                    
                    name = product_name[0]["plain_text"]
                    
                    # Extract regular price (assuming it's a number property named "Normalpreis")
                    regular_price = item["properties"].get("Normalpreis", {}).get("number")
                    
                    product = {
                        "name": name,
                        "normal_price": regular_price
                    }
                    
                    products.append(product)
                    
                except (KeyError, IndexError) as e:
                    logger.error(f"Error extracting product data: {e}")
                    continue
            
            logger.info(f"Retrieved {len(products)} products from Notion database")
            return products
            
        except Exception as e:
            logger.error(f"Error querying Notion database: {e}")
            return [] 