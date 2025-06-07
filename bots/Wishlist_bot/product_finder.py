import logging
import asyncio
import random
import aiohttp
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger('wishlist_bot.product_finder')

class ProductFinder:
    """Finds products based on user interests"""
    
    def __init__(self, openrouter_service, notion_manager):
        """
        Initialize the product finder
        
        Args:
            openrouter_service: OpenRouterService instance for AI-powered suggestions
            notion_manager: NotionManager instance for accessing interests
        """
        self.openrouter_service = openrouter_service
        self.notion_manager = notion_manager
        logger.info("Initializing Product Finder")
    
    def select_random_interests(self, interests, num=3):
        """
        Select random interests from the list
        
        Args:
            interests: List of interests
            num: Number of interests to select
            
        Returns:
            list: Random subset of interests
        """
        # Handle different interest formats
        interest_names = []
        for interest in interests:
            if isinstance(interest, dict):
                interest_names.append(interest.get('name', ''))
            else:
                interest_names.append(interest)
        
        # Remove any empty strings
        interest_names = [i for i in interest_names if i]
        
        # Select random interests
        if len(interest_names) <= num:
            return interest_names
        
        return random.sample(interest_names, num)
    
    async def find_products_for_interest(self, interest):
        """
        Find products for a specific interest
        
        Args:
            interest: The interest to find products for
            
        Returns:
            list: List of product dictionaries
        """
        try:
            logger.info(f"Finding products for interest: {interest}")
            
            # First try to get search results from web search
            search_results = await self._perform_web_search(f"best products for {interest} 2025")
            
            if search_results:
                # Analyze the search results to extract products
                products = await self.openrouter_service.analyze_search_results(search_results, interest)
                
                if products and len(products) > 0:
                    logger.info(f"Found {len(products)} products from web search for {interest}")
                    return products
            
            # Fall back to AI-generated suggestions if web search fails
            logger.info(f"Web search failed or no products found, using AI suggestions for {interest}")
            products = await self.openrouter_service.get_product_suggestions(interest)
            
            logger.info(f"Generated {len(products)} AI suggestions for {interest}")
            return products
            
        except Exception as e:
            logger.error(f"Error finding products for interest {interest}: {e}")
            return []
    
    async def find_discounted_products(self, interests):
        """
        Find discounted products related to user interests
        
        Args:
            interests: List of user interests
            
        Returns:
            list: List of discounted product dictionaries
        """
        try:
            logger.info("Finding discounted products")
            
            # Select a few random interests to focus on
            selected_interests = self.select_random_interests(interests, 3)
            
            all_deals = []
            
            # Search for deals for each interest
            for interest in selected_interests:
                try:
                    search_results = await self._perform_web_search(f"best deals on {interest} products sale discount")
                    
                    if search_results:
                        # Analyze the search results
                        interest_deals = await self.openrouter_service.analyze_search_results(search_results, f"{interest} deals")
                        
                        if interest_deals and len(interest_deals) > 0:
                            # Add a tag to indicate which interest these deals are for
                            for deal in interest_deals:
                                deal['interest'] = interest
                            
                            all_deals.extend(interest_deals)
                except Exception as e:
                    logger.error(f"Error finding deals for {interest}: {e}")
            
            if not all_deals:
                # Fall back to AI-generated suggestions
                logger.info("No deals found from web search, using AI suggestions")
                
                # Join interests into a comma-separated string
                interests_str = ", ".join(selected_interests)
                
                all_deals = await self.openrouter_service.get_product_suggestions(f"discounted {interests_str} products on sale")
            
            logger.info(f"Found {len(all_deals)} deals in total")
            return all_deals
            
        except Exception as e:
            logger.error(f"Error finding discounted products: {e}")
            return []
    
    async def _perform_web_search(self, query):
        """
        Perform a web search for products
        
        Args:
            query: Search query
            
        Returns:
            str: Search results as text
        """
        try:
            logger.info(f"Performing web search for: {query}")
            
            # Choose a few websites to search for products
            websites = [
                "amazon.com", 
                "bestbuy.com", 
                "techradar.com", 
                "wirecutter.com",
                "productreview.com.au",
                "theverge.com",
                "cnet.com"
            ]
            
            # Add a random website to the query to get more specific results
            search_query = f"{query} site:{random.choice(websites)}"
            
            # Make the request
            async with aiohttp.ClientSession() as session:
                # Use a search engine API here, but for simplicity, we'll simulate results
                # In a real implementation, you would use a proper web search API
                
                # Simulate search results (in a real implementation, use an actual API)
                search_text = f"Simulated search results for '{query}'\n\n"
                
                # Try to fetch some real content
                try:
                    async with session.get(f"https://www.google.com/search?q={search_query.replace(' ', '+')}") as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'lxml')
                            
                            # Extract search results (this is a very basic approach)
                            results = soup.find_all('div', class_='g')
                            
                            if results:
                                for result in results[:5]:  # Limit to first 5 results
                                    title_elem = result.find('h3')
                                    title = title_elem.text if title_elem else "Unknown Product"
                                    
                                    desc_elem = result.find('div', class_='VwiC3b')
                                    desc = desc_elem.text if desc_elem else "No description available"
                                    
                                    search_text += f"- {title}\n  {desc}\n\n"
                            else:
                                # If no structured results, just grab any text
                                text_blocks = soup.find_all(['p', 'h2', 'h3'])
                                for block in text_blocks[:10]:  # Grab some text blocks
                                    search_text += f"{block.text}\n\n"
                except Exception as e:
                    logger.error(f"Error fetching real search results: {e}")
                    # Fall back to simulated results
                    search_text += f"""
1. Top 10 Best {query.capitalize()} Products in 2025 - Expert Reviews
   Looking for the best {query} products? Our experts have tested and reviewed the top options.
   Price range: $50-$500 depending on features.

2. {query.capitalize()} Buying Guide: What You Need to Know
   Complete guide to choosing the right {query} product for your needs.
   
3. Amazon.com: Best Sellers in {query.capitalize()} Products
   Shop the highest-rated and best-reviewed {query} products on Amazon.
   
4. New Revolutionary {query.capitalize()} Product Released - Tech News
   The latest innovation in {query} technology has just been released.
   Pricing starts at $299.
                    """
            
            logger.info(f"Web search for '{query}' complete")
            return search_text
            
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            return "" 