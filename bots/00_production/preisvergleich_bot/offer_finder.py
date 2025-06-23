import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('offer_finder')

class OfferFinder:
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek/deepseek-chat-v3-0324:free"):
        """
        Initialize the OfferFinder with OpenRouter API key
        
        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env variable)
            model: LLM model to use for web search and reasoning
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY in .env or pass as argument.")
        
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Default stores to check for offers
        self.default_stores = ["Rewe", "Kaufland", "Edeka", "Lidl", "Aldi Süd", "Penny"]
        
        logger.info(f"OfferFinder initialized with model: {model}")
    
    def create_prompt(self, products: List[Dict[str, str]], 
                      stores: Optional[List[str]] = None, 
                      region: str = "Baden-Württemberg") -> str:
        """
        Create a detailed prompt for the LLM to search for product offers
        
        Args:
            products: List of product dictionaries with 'name' and 'normal_price' keys
            stores: List of store names to check (defaults to standard stores)
            region: Region to check for offers
            
        Returns:
            Formatted prompt for the LLM
        """
        if stores is None:
            stores = self.default_stores
            
        products_str = ", ".join([p["name"] for p in products])
        stores_str = ", ".join(stores)
        
        today = datetime.now().strftime("%d.%m.%Y")
        
        # Create a comprehensive prompt for the LLM to guide its web search
        prompt = f"""
        # Task: Find current product offers and deals
        
        Today is {today}. You are an agent specializing in finding the best deals and offers.
        
        ## Search Parameters:
        - Products: {products_str}
        - Stores: {stores_str}
        - Region: {region}
        - Timeframe: Current and upcoming two weeks
        
        ## Process:
        1. For each product, search for current and upcoming special offers in the specified stores.
        2. Use these sources:
           - Official store websites and apps
           - Digital flyers and promotional materials
           - Deal aggregator websites (kaufda.de, meinprospekt.de, marktguru.de, etc.)
           - Consumer portals and price comparison sites
        
        3. For each product, determine:
           - Regular price
           - Current offer price (if any)
           - Offer validity period
           - Any special conditions (app-only, loyalty card required, etc.)
           - Which store has the offer
        
        4. Reasons step-by-step:
           - Which sources would have the most accurate and current information?
           - How reliable is each source?
           - Are there regional variations to consider?
           - Could there be other relevant offers I should include?
        
        ## Response Format:
        Respond with a JSON structure containing an array of offer objects. Each offer should have:
        1. product_name: Name of the product
        2. store: Store where the offer is available
        3. regular_price: Regular price in euros (numeric value only)
        4. offer_price: Special offer price in euros (numeric value only)
        5. start_date: Start date of the offer (YYYY-MM-DD format, or null if unknown)
        6. end_date: End date of the offer (YYYY-MM-DD format, or null if unknown)
        7. conditions: Any special conditions for the offer
        8. source: Source of the information (website, app, etc.)
        
        If no offers are found for a product, include it with a null offer_price.
        
        Sample response format:
        ```json
        [
          {{
            "product_name": "Product A",
            "store": "Store X",
            "regular_price": 9.99,
            "offer_price": 7.99,
            "start_date": "2023-05-01",
            "end_date": "2023-05-07",
            "conditions": "Only with Store X app",
            "source": "Store X website"
          }},
          {{
            "product_name": "Product B",
            "store": null,
            "regular_price": 5.99,
            "offer_price": null,
            "start_date": null,
            "end_date": null,
            "conditions": null,
            "source": null
          }}
        ]
        ```
        
        Important: Return ONLY the JSON array with no additional text or explanation.
        """
        
        return prompt
    
    def query_llm(self, prompt: str, temperature: float = 0.2, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Send a query to the LLM through OpenRouter
        
        Args:
            prompt: The prompt to send
            temperature: Creativity parameter (lower for more deterministic results)
            max_tokens: Maximum tokens in the response
            
        Returns:
            Response from the LLM
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            logger.info(f"Querying OpenRouter with model: {self.model}")
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying OpenRouter: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return {"error": str(e)}
    
    def find_product_offers(self, products: List[Dict[str, str]], 
                           stores: Optional[List[str]] = None,
                           region: str = "Baden-Württemberg") -> Dict[str, Any]:
        """
        Main function to find offers for the specified products
        
        Args:
            products: List of product dictionaries with 'name' and 'normal_price' keys
            stores: List of store names to check
            region: Region to check for offers
            
        Returns:
            Dictionary with search results and metadata
        """
        # Create the prompt for the LLM
        prompt = self.create_prompt(products, stores, region)
        
        # Query the LLM
        response = self.query_llm(prompt)
        
        # Handle error response
        if "error" in response:
            logger.error(f"Error in LLM response: {response['error']}")
            return {
                "success": False,
                "error": response["error"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract and parse the content
        try:
            content = response["choices"][0]["message"]["content"]
            
            # Attempt to parse the JSON response
            try:
                # Remove any markdown code block indicators if present
                if content.startswith("```json"):
                    content = content.split("```json")[1]
                if content.endswith("```"):
                    content = content.split("```")[0]
                
                # Clean and parse the JSON
                content = content.strip()
                offers_data = json.loads(content)
                
                return {
                    "success": True,
                    "query_info": {
                        "products": [p["name"] for p in products],
                        "stores": stores or self.default_stores,
                        "region": region,
                        "timestamp": datetime.now().isoformat()
                    },
                    "offers": offers_data
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                return {
                    "success": False,
                    "error": f"Failed to parse JSON from LLM response: {e}",
                    "raw_content": content,
                    "timestamp": datetime.now().isoformat()
                }
                
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting content from LLM response: {e}")
            return {
                "success": False,
                "error": f"Error extracting content from LLM response: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def filter_valid_offers(self, offers_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter offers to only include valid offers (with a price reduction)
        
        Args:
            offers_data: The complete offers data from find_product_offers
            
        Returns:
            List of offers that represent actual discounts
        """
        if not offers_data.get("success", False) or "offers" not in offers_data:
            return []
        
        valid_offers = []
        
        for offer in offers_data["offers"]:
            # Check if this is an actual offer with a price reduction
            if (offer.get("offer_price") is not None and 
                offer.get("regular_price") is not None and
                offer.get("offer_price") < offer.get("regular_price")):
                valid_offers.append(offer)
        
        return valid_offers 