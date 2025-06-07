import os
import asyncio
import logging
from dotenv import load_dotenv

from notion_manager import NotionProductManager
from agent import OfferSearchAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_offers')

# Load environment variables
load_dotenv()

async def test_offer_search():
    """Test function to check for offers"""
    try:
        # Initialize our services
        notion_manager = NotionProductManager()
        offer_agent = OfferSearchAgent()
        
        # Get products from Notion database
        products = notion_manager.get_watchlist()
        if not products:
            logger.warning("No products found in the watchlist")
            return
        
        logger.info(f"Found {len(products)} products: {[p['name'] for p in products]}")
        
        # Find offers using the agent
        logger.info("Searching for offers...")
        results = offer_agent.find_offers(products)
        
        if not results.get("success", False):
            error_msg = results.get("error", "Unknown error")
            logger.error(f"Error finding offers: {error_msg}")
            return
        
        offers = results.get("offers", [])
        
        if not offers:
            logger.info("No offers found")
            return
        
        # Print the offers
        logger.info(f"Found {len(offers)} offers!")
        for offer in offers:
            product_name = offer.get("product_name", "Unknown Product")
            store = offer.get("store", "Unknown Store")
            regular_price = offer.get("regular_price")
            offer_price = offer.get("offer_price")
            savings_percent = offer.get("savings_percent", 0)
            
            logger.info(f"OFFER: {product_name} at {store} - €{regular_price:.2f} → €{offer_price:.2f} ({savings_percent:.1f}% off)")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_offer_search()) 