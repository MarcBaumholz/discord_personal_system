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
        try:
            self.notion_token = notion_token or os.getenv("NOTION_TOKEN")
            if not self.notion_token:
                logger.error("Notion token is missing. Set NOTION_TOKEN in .env or pass as argument.")
                self.notion = None
                self.database_id = None
                return
            
            # Get the database ID and clean it if needed
            raw_database_id = database_id or os.getenv("NOTION_DATABASE_ID")
            if not raw_database_id:
                logger.error("Notion database ID is missing. Set NOTION_DATABASE_ID in .env or pass as argument.")
                self.notion = None
                self.database_id = None
                return
            
            # Clean the database ID if it's in URL format
            self.database_id = self._clean_database_id(raw_database_id)
            
            # Initialize the Notion client with error handling
            try:
                self.notion = Client(auth=self.notion_token)
                logger.info("NotionProductManager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Notion client: {e}")
                self.notion = None
                self.database_id = None
        except Exception as e:
            logger.error(f"Error during NotionProductManager initialization: {e}")
            self.notion = None
            self.database_id = None
    
    def is_initialized(self) -> bool:
        """
        Check if the NotionProductManager is properly initialized
        
        Returns:
            True if initialized, False otherwise
        """
        return self.notion is not None and self.database_id is not None
    
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
        if not self.is_initialized():
            logger.error("NotionProductManager is not properly initialized. Cannot retrieve watchlist.")
            return []
        
        try:
            logger.info(f"Querying Notion database: {self.database_id}")
            response = self.notion.databases.query(database_id=self.database_id)
            
            products = []
            
            for item in response.get("results", []):
                try:
                    # Try different possible property names for product name
                    product_name = None
                    for name_field in ["Produktname", "Name", "Product", "Title"]:
                        name_prop = item["properties"].get(name_field, {})
                        if name_prop.get("title"):
                            product_name = name_prop["title"][0]["plain_text"]
                            break
                    
                    if not product_name:
                        logger.warning("Product name not found in Notion item, skipping")
                        continue
                    
                    # Try different possible property names for price
                    regular_price = None
                    for price_field in ["Normalpreis", "Price", "Normal Price", "Regular Price"]:
                        price_prop = item["properties"].get(price_field, {})
                        if price_prop.get("number") is not None:
                            regular_price = price_prop["number"]
                            break
                    
                    # Try to get URL if available
                    url = None
                    for url_field in ["URL", "Link", "Product URL"]:
                        url_prop = item["properties"].get(url_field, {})
                        if url_prop.get("url"):
                            url = url_prop["url"]
                            break
                    
                    product = {
                        "name": product_name,
                        "normal_price": regular_price,
                        "url": url
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