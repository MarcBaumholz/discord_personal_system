import os
import asyncio
import logging
from dotenv import load_dotenv

from notion_manager import NotionProductManager
from simple_agent import SimpleOfferSearchAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_simple')

# Load environment variables
load_dotenv()

async def test_offer_search():
    """Test function to check for offers using the simplified agent"""
    try:
        # Initialize our services
        notion_manager = NotionProductManager()
        offer_agent = SimpleOfferSearchAgent()
        
        # Get products from Notion database
        products = notion_manager.get_watchlist()
        if not products:
            logger.warning("No products found in the watchlist")
            return
        
        logger.info(f"Found {len(products)} products: {[p['name'] for p in products]}")
        
        # Find offers using the simplified agent
        logger.info("Searching for offers using simplified agent...")
        results = offer_agent.find_offers(products)
        
        if not results.get("success", False):
            error_msg = results.get("error", "Unknown error")
            logger.error(f"Error finding offers: {error_msg}")
            return
        
        offers = results.get("offers", [])
        
        if not offers:
            logger.info("No offers found")
            # Print the raw response for debugging
            raw_response = results.get("raw_response", "No raw response available")
            logger.info(f"Raw response: {raw_response}")
            return
        
        # Print the offers
        logger.info(f"Found {len(offers)} offers!")
        for offer in offers:
            product_name = offer.get("product_name", "Unknown Product")
            store = offer.get("store", "Unknown Store")
            regular_price = offer.get("regular_price")
            offer_price = offer.get("offer_price")
            savings_percent = offer.get("savings_percent", 0)
            valid_until = offer.get("valid_until", "Unknown")
            
            logger.info(f"OFFER: {product_name} at {store} - €{regular_price:.2f} → €{offer_price:.2f} ({savings_percent:.1f}% off) - Valid until: {valid_until}")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_offer_search()) 