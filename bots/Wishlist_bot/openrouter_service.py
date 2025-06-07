import os
import logging
import requests
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('wishlist_bot.openrouter_service')

class OpenRouterService:
    """Service to interact with OpenRouter LLM API for product suggestions"""
    
    def __init__(self):
        """Initialize OpenRouter service"""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        logger.info("Initializing OpenRouter Service")
    
    async def get_product_suggestions(self, interest, search_results=None, num_products=5):
        """
        Generate product suggestions based on interest and search results
        
        Args:
            interest: The interest to generate suggestions for
            search_results: Optional search results to incorporate
            num_products: Number of products to suggest
            
        Returns:
            list: List of product suggestions
        """
        try:
            # Create the prompt based on the interest and search results
            if search_results:
                prompt = f"""As a personal shopping assistant, suggest {num_products} interesting products related to the interest "{interest}" based on these search results:

{search_results}

For each product, provide:
1. Product name
2. Short description (1-2 sentences)
3. Approximate price range
4. URL (create a reasonable one if not in search results)
5. Image URL (create a reasonable one if not in search results)

Format as JSON:
[
  {{
    "name": "Product Name",
    "description": "Short description of the product.",
    "price": "$XX-$XX",
    "url": "https://example.com/product",
    "image_url": "https://example.com/image.jpg"
  }}
]

Only include the JSON array in your response, no introduction or explanation.
"""
            else:
                prompt = f"""As a personal shopping assistant, suggest {num_products} interesting products related to the interest "{interest}".

For each product, provide:
1. Product name
2. Short description (1-2 sentences)
3. Approximate price range
4. URL (create a reasonable one)
5. Image URL (create a reasonable one)

Format as JSON:
[
  {{
    "name": "Product Name",
    "description": "Short description of the product.",
    "price": "$XX-$XX",
    "url": "https://example.com/product",
    "image_url": "https://example.com/image.jpg"
  }}
]

Only include the JSON array in your response, no introduction or explanation.
"""

            # Call OpenRouter API
            response = await self._call_openrouter_api(prompt)
            
            try:
                # Parse the JSON response
                products = json.loads(response)
                logger.info(f"Generated {len(products)} product suggestions for {interest}")
                return products
            except json.JSONDecodeError:
                logger.error(f"Error parsing product suggestions JSON: {response}")
                return []
            
        except Exception as e:
            logger.error(f"Error generating product suggestions: {e}")
            return []
    
    async def get_product_search_queries(self, interests, num_queries=3):
        """
        Generate search queries for finding products based on interests
        
        Args:
            interests: List of interests
            num_queries: Number of search queries to generate
            
        Returns:
            list: List of search queries
        """
        try:
            # Create a prompt to generate search queries
            interests_str = ", ".join(interests[:5])  # Limit to top 5 interests
            
            prompt = f"""As a personal shopping assistant, generate {num_queries} specific search queries to find interesting products based on these interests: {interests_str}.

Make the queries specific and targeted to find unique, high-quality products a tech-savvy person would like.

Format as JSON:
[
  "search query 1",
  "search query 2",
  "search query 3"
]

Only include the JSON array in your response, no introduction or explanation.
"""

            # Call OpenRouter API
            response = await self._call_openrouter_api(prompt)
            
            try:
                # Parse the JSON response
                queries = json.loads(response)
                logger.info(f"Generated {len(queries)} search queries for interests")
                return queries
            except json.JSONDecodeError:
                logger.error(f"Error parsing search queries JSON: {response}")
                return []
            
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            return []
    
    async def analyze_search_results(self, search_results, interest):
        """
        Analyze search results to extract products
        
        Args:
            search_results: Raw search results text
            interest: The interest being searched for
            
        Returns:
            list: List of product objects
        """
        try:
            # Create a prompt to analyze search results
            prompt = f"""As a personal shopping assistant, analyze these search results for products related to the interest "{interest}":

{search_results}

Extract the top 5 most interesting and relevant products. For each product, provide:
1. Product name
2. Short description (1-2 sentences)
3. Price (extract from results or estimate)
4. URL (extract from results if available)
5. Image URL (extract from results if available)

Format as JSON:
[
  {{
    "name": "Product Name",
    "description": "Short description of the product.",
    "price": "$XX-$XX",
    "url": "https://example.com/product",
    "image_url": "https://example.com/image.jpg"
  }}
]

Only include the JSON array in your response, no introduction or explanation.
"""

            # Call OpenRouter API
            response = await self._call_openrouter_api(prompt)
            
            try:
                # Parse the JSON response
                products = json.loads(response)
                logger.info(f"Extracted {len(products)} products from search results for {interest}")
                return products
            except json.JSONDecodeError:
                logger.error(f"Error parsing products JSON from search results: {response}")
                return []
            
        except Exception as e:
            logger.error(f"Error analyzing search results: {e}")
            return []
    
    async def _call_openrouter_api(self, prompt):
        """
        Call the OpenRouter API
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            str: The response content
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek/deepseek-chat-v3-0324:free",  # Using DeepSeek model as requested
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that provides product suggestions based on interests."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Make the API call asynchronously
            response = await asyncio.to_thread(
                requests.post,
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
            
            logger.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
            return ""
            
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return "" 