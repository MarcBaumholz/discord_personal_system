import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_agent')

class SimpleOfferSearchAgent:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize a simple agent for finding product offers
        
        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY in .env or pass as argument.")
        
        # Default stores to check for offers
        self.default_stores = ["Rewe", "Kaufland", "Edeka", "Lidl", "Aldi Süd", "Penny"]
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost"  # Required by OpenRouter
        }
        logger.info("SimpleOfferSearchAgent initialized")
    
    def find_offers(self, products: List[Dict[str, Any]], 
                   stores: Optional[List[str]] = None,
                   region: str = "Baden-Württemberg") -> Dict[str, Any]:
        """
        Find current offers for the specified products
        
        Args:
            products: List of product dictionaries with 'name' and 'normal_price' keys
            stores: List of store names to check (defaults to standard stores)
            region: Region to check for offers
            
        Returns:
            Dictionary with search results and metadata
        """
        if stores is None:
            stores = self.default_stores
            
        # Extract product names
        product_names = [p["name"] for p in products]
        products_str = ", ".join(product_names)
        stores_str = ", ".join(stores)
        
        prompt = f"""You are an expert at finding product deals and offers.

I need you to find the best current offers for the following products:
{products_str}

Look for these products in these stores: {stores_str}

These are German stores, and I'm looking for offers in the {region} region.

For each product, please find:
1. The current regular price
2. Any special offer price
3. Which store has the best price
4. When the offer is valid until
5. Any special conditions (loyalty card, app-only, etc.)

IMPORTANT: Only include products that have an actual discount. Do not include regular prices unless they are on sale.

Please respond with a JSON array of objects. Each object should have:
- product_name: Name of the product
- store: Store with the offer
- regular_price: Regular non-discounted price as a number
- offer_price: Discounted price as a number
- savings_percent: Percentage saved as a number
- valid_until: End date of the offer in YYYY-MM-DD format
- conditions: Any special conditions for the offer
- offer_link: Link to the offer online if available

To find this information, you should search the internet for current flyers, promotions, and digital offers from these stores in Germany.
"""
        
        try:
            logger.info(f"Searching for offers for {len(products)} products")
            
            # Prepare the request
            payload = {
                "model": "meta-llama/llama-3.1-8b-instruct:free",  # Updated to newest free model
                "temperature": 0.2,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            }
            
            # Make the request to OpenRouter
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            output = result["choices"][0]["message"]["content"]
            
            # Try to extract JSON from the response
            try:
                # Extract JSON if it's embedded in text
                if "```json" in output:
                    json_part = output.split("```json")[1].split("```")[0].strip()
                    offers_data = json.loads(json_part)
                elif "```" in output:
                    json_part = output.split("```")[1].split("```")[0].strip()
                    offers_data = json.loads(json_part)
                elif output.strip().startswith("[") and output.strip().endswith("]"):
                    offers_data = json.loads(output)
                else:
                    # Try to find JSON-like structure in the text
                    import re
                    match = re.search(r'\[\s*{.*}\s*\]', output, re.DOTALL)
                    if match:
                        offers_data = json.loads(match.group(0))
                    else:
                        logger.warning(f"Could not extract JSON from response: {output}")
                        offers_data = []
                
                # Process the results
                processed_offers = []
                for offer in offers_data:
                    # Only include offers with both prices
                    if "regular_price" in offer and "offer_price" in offer:
                        # Convert prices to float if they're strings
                        if isinstance(offer["regular_price"], str):
                            offer["regular_price"] = float(offer["regular_price"].replace(',', '.').replace('€', ''))
                        if isinstance(offer["offer_price"], str):
                            offer["offer_price"] = float(offer["offer_price"].replace(',', '.').replace('€', ''))
                        
                        # Only include if it's an actual offer (price reduction)
                        if offer["regular_price"] > offer["offer_price"]:
                            # Calculate savings if not included
                            if "savings_percent" not in offer:
                                savings = ((offer["regular_price"] - offer["offer_price"]) / offer["regular_price"]) * 100
                                offer["savings_percent"] = round(savings, 1)
                                
                            processed_offers.append(offer)
                
                return {
                    "success": True,
                    "offers": processed_offers,
                    "timestamp": datetime.now().isoformat(),
                    "raw_response": output
                }
                
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.error(f"Error processing response: {e}")
                return {
                    "success": False,
                    "error": f"Error processing response: {e}",
                    "raw_output": output,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in offer search agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 