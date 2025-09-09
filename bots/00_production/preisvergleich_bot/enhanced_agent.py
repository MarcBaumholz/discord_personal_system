import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI
from bs4 import BeautifulSoup
import time
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced_agent')

class EnhancedOfferSearchAgent:
    def __init__(self, api_key: Optional[str] = None, tavily_key: Optional[str] = None):
        """
        Initialize an enhanced agent for finding product offers with live web search
        
        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env variable)
            tavily_key: Tavily API key for web search (defaults to TAVILY_API_KEY env variable)
        """
        try:
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            self.tavily_key = tavily_key or os.getenv("TAVILY_API_KEY")
            
            if not self.api_key:
                logger.error("OpenRouter API key is missing. Set OPENROUTER_API_KEY in .env or pass as argument.")
                self.initialized = False
                return
            
            # Initialize OpenAI client for OpenRouter
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
            
            # Initialize Tavily for web search
            if self.tavily_key:
                from tavily import TavilyClient
                self.tavily = TavilyClient(api_key=self.tavily_key)
                self.web_search_enabled = True
                logger.info("Tavily web search enabled")
            else:
                self.tavily = None
                self.web_search_enabled = False
                logger.warning("Tavily API key not found. Web search disabled.")
            
            # Regional store configuration for Baden-Württemberg
            self.regional_stores = {
                "Rewe": {
                    "prospect_urls": [
                        "https://www.rewe.de/angebote/",
                        "https://www.rewe.de/angebote/aktuelle-woche/",
                        "https://www.rewe.de/angebote/naechste-woche/"
                    ],
                    "search_terms": ["angebote", "prospekt", "rabatt", "reduziert"]
                },
                "Kaufland": {
                    "prospect_urls": [
                        "https://www.kaufland.de/angebote/",
                        "https://www.kaufland.de/angebote/aktuelle-woche/",
                        "https://www.kaufland.de/angebote/naechste-woche/"
                    ],
                    "search_terms": ["angebote", "prospekt", "rabatt", "reduziert"]
                },
                "Edeka": {
                    "prospect_urls": [
                        "https://www.edeka.de/angebote/",
                        "https://www.edeka.de/angebote/aktuelle-woche/",
                        "https://www.edeka.de/angebote/naechste-woche/"
                    ],
                    "search_terms": ["angebote", "prospekt", "rabatt", "reduziert"]
                },
                "Lidl": {
                    "prospect_urls": [
                        "https://www.lidl.de/angebote/",
                        "https://www.lidl.de/angebote/aktuelle-woche/",
                        "https://www.lidl.de/angebote/naechste-woche/"
                    ],
                    "search_terms": ["angebote", "prospekt", "rabatt", "reduziert"]
                },
                "Aldi Süd": {
                    "prospect_urls": [
                        "https://www.aldi-sued.de/angebote/",
                        "https://www.aldi-sued.de/angebote/aktuelle-woche/",
                        "https://www.aldi-sued.de/angebote/naechste-woche/"
                    ],
                    "search_terms": ["angebote", "prospekt", "rabatt", "reduziert"]
                },
                "Penny": {
                    "prospect_urls": [
                        "https://www.penny.de/angebote/",
                        "https://www.penny.de/angebote/aktuelle-woche/",
                        "https://www.penny.de/angebote/naechste-woche/"
                    ],
                    "search_terms": ["angebote", "prospekt", "rabatt", "reduziert"]
                }
            }
            
            self.region = "Baden-Württemberg"
            self.initialized = True
            logger.info("EnhancedOfferSearchAgent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error during EnhancedOfferSearchAgent initialization: {e}")
            self.initialized = False
    
    def is_initialized(self) -> bool:
        """Check if the EnhancedOfferSearchAgent is properly initialized"""
        return getattr(self, 'initialized', False)
    
    def search_web_for_offers(self, product_name: str, store: str) -> Dict[str, Any]:
        """
        Search the web for current offers for a specific product at a specific store
        
        Args:
            product_name: Name of the product to search for
            store: Store name to search in
            
        Returns:
            Dictionary with search results
        """
        if not self.web_search_enabled:
            return {"success": False, "error": "Web search not enabled"}
        
        try:
            # Calculate current week and next week for search terms
            today = datetime.now()
            current_week_start = today - timedelta(days=today.weekday())
            current_week_end = current_week_start + timedelta(days=6)
            next_week_start = current_week_end + timedelta(days=1)
            next_week_end = next_week_start + timedelta(days=6)
            
            # Create multiple search queries for current offers
            search_queries = [
                f"{product_name} {store} angebot {today.strftime('%Y')} {today.strftime('%m')} prospekt",
                f"{product_name} {store} rabatt aktuell {current_week_start.strftime('%d.%m')} {current_week_end.strftime('%d.%m')}",
                f"{product_name} {store} angebot {next_week_start.strftime('%d.%m')} {next_week_end.strftime('%d.%m')}",
                f"{product_name} {store} reduziert {today.strftime('%Y')} woche",
                f"{store} prospekt {product_name} {today.strftime('%Y')} {today.strftime('%m')}"
            ]
            
            all_results = []
            
            # Search with multiple queries to get comprehensive results
            for query in search_queries:
                try:
                    # Use Tavily to search for current offers
                    search_results = self.tavily.search(
                        query=query,
                        search_depth="advanced",
                        max_results=3,
                        include_domains=[
                            f"{store.lower().replace(' ', '')}.de", 
                            "prospekt.de", 
                            "rabattcode.de",
                            "meinprospekt.de",
                            "kaufda.de",
                            "marktguru.de"
                        ]
                    )
                    
                    # Extract relevant information from search results
                    for result in search_results.get('results', []):
                        all_results.append({
                            'title': result.get('title', ''),
                            'content': result.get('content', ''),
                            'url': result.get('url', ''),
                            'score': result.get('score', 0),
                            'query_used': query
                        })
                    
                    # Add delay between searches to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Search query failed: {query} - {e}")
                    continue
            
            # Remove duplicates and sort by score
            unique_results = []
            seen_urls = set()
            for result in all_results:
                if result['url'] not in seen_urls:
                    unique_results.append(result)
                    seen_urls.add(result['url'])
            
            # Sort by score (highest first) and take top 5
            unique_results.sort(key=lambda x: x['score'], reverse=True)
            top_results = unique_results[:5]
            
            return {
                "success": True,
                "results": top_results,
                "queries_used": search_queries,
                "total_found": len(all_results)
            }
            
        except Exception as e:
            logger.error(f"Error in web search for {product_name} at {store}: {e}")
            return {"success": False, "error": str(e)}
    
    def create_detailed_prompt(self, products: List[Dict[str, Any]], web_search_data: Dict[str, Any]) -> str:
        """
        Create a detailed prompt for the AI agent with web search data
        
        Args:
            products: List of products to search for
            web_search_data: Web search results for context
            
        Returns:
            Detailed prompt string
        """
        product_names = [p["name"] for p in products]
        products_str = ", ".join(product_names)
        
        # Calculate current week and next week date ranges
        today = datetime.now()
        current_week_start = today - timedelta(days=today.weekday())
        current_week_end = current_week_start + timedelta(days=6)
        next_week_start = current_week_end + timedelta(days=1)
        next_week_end = next_week_start + timedelta(days=6)
        
        current_week_str = f"{current_week_start.strftime('%d.%m.%Y')} - {current_week_end.strftime('%d.%m.%Y')}"
        next_week_str = f"{next_week_start.strftime('%d.%m.%Y')} - {next_week_end.strftime('%d.%m.%Y')}"
        
        # Build web search context
        web_context = ""
        if web_search_data.get("success"):
            web_context = "\n\nLIVE WEB SEARCH DATA:\n"
            for store, data in web_search_data.items():
                if isinstance(data, dict) and data.get("success"):
                    web_context += f"\n{store} Search Results:\n"
                    for result in data.get("results", [])[:3]:  # Top 3 results per store
                        web_context += f"- {result.get('title', '')}\n"
                        web_context += f"  Content: {result.get('content', '')[:200]}...\n"
                        web_context += f"  URL: {result.get('url', '')}\n\n"
        
        prompt = f"""Du bist ein Experte für das Finden von Produktangeboten und Rabatten in Deutschland, speziell in der Region {self.region}.

AUFGABE: Finde die besten AKTUELLEN Angebote für folgende Produkte:
{products_str}

ZEITRAUM (KRITISCH WICHTIG):
- AKTUELLE WOCHE: {current_week_str}
- NÄCHSTE WOCHE: {next_week_str}
- Heute ist der {today.strftime('%d.%m.%Y')}
- Suche NUR nach Angeboten die in diesen beiden Wochen gültig sind!

REGIONALE STORES (Baden-Württemberg):
- Rewe, Kaufland, Edeka, Lidl, Aldi Süd, Penny

WICHTIGE ANWEISUNGEN:
1. Suche NUR nach echten Rabatten und Angeboten (nicht reguläre Preise)
2. Konzentriere dich auf die Region Baden-Württemberg
3. Prüfe aktuelle Prospekte und Online-Angebote für DIESE und NÄCHSTE WOCHE
4. Berücksichtige auch App-exklusive Angebote und Treuekarten-Rabatte
5. Suche nach zeitlich begrenzten Aktionen und Sonderangeboten
6. IGNORIERE alle Angebote die vor {current_week_start.strftime('%d.%m.%Y')} oder nach {next_week_end.strftime('%d.%m.%Y')} gültig sind
7. Fokussiere auf Prospekte und Angebote die JETZT oder in den nächsten 14 Tagen aktiv sind

{web_context}

FÜR JEDES PRODUKT finde:
- Aktueller regulärer Preis
- Angebotspreis (nur wenn reduziert)
- Store mit dem besten Angebot
- Gültigkeitsdauer des Angebots (MUSS zwischen {current_week_start.strftime('%d.%m.%Y')} und {next_week_end.strftime('%d.%m.%Y')} liegen)
- Besondere Bedingungen (App, Treuekarte, Mindestbestellwert)
- Direkter Link zum Angebot

ANTWORT-FORMAT (JSON Array):
```json
[
  {{
    "product_name": "Produktname",
    "store": "Store Name",
    "regular_price": 5.99,
    "offer_price": 3.99,
    "savings_percent": 33.4,
    "valid_until": "{next_week_end.strftime('%Y-%m-%d')}",
    "conditions": "App-exklusiv, Mindestbestellwert 20€",
    "offer_link": "https://store.de/angebot",
    "confidence": 0.85
  }}
]
```

WICHTIG: 
- Nur Angebote mit echten Preisreduktionen einbeziehen
- Confidence Score: 0.0-1.0 basierend auf Datenqualität
- Gültigkeitsdaten MÜSSEN zwischen {current_week_start.strftime('%Y-%m-%d')} und {next_week_end.strftime('%Y-%m-%d')} liegen
- Wenn keine aktuellen Angebote gefunden, leeres Array zurückgeben
- IGNORIERE alle veralteten Angebote von 2024 oder früher!"""

        return prompt
    
    def find_offers(self, products: List[Dict[str, Any]], 
                   stores: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Find current offers for the specified products using web search and AI analysis
        
        Args:
            products: List of product dictionaries with 'name' and 'normal_price' keys
            stores: List of store names to check (defaults to regional stores)
            
        Returns:
            Dictionary with search results and metadata
        """
        if not self.is_initialized():
            logger.error("EnhancedOfferSearchAgent is not properly initialized. Cannot find offers.")
            return {
                "offers": [],
                "total_savings": 0,
                "successful_searches": 0,
                "error": "Agent not properly initialized"
            }
        
        if stores is None:
            stores = list(self.regional_stores.keys())
        
        logger.info(f"Searching for offers for {len(products)} products using enhanced agent")
        
        # Step 1: Perform web search for each product
        web_search_data = {}
        for product in products:
            product_name = product["name"]
            web_search_data[product_name] = {}
            
            for store in stores:
                logger.info(f"Searching web for {product_name} at {store}")
                search_result = self.search_web_for_offers(product_name, store)
                web_search_data[product_name][store] = search_result
                
                # Add delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
        
        # Step 2: Create detailed prompt with web search data
        detailed_prompt = self.create_detailed_prompt(products, web_search_data)
        
        # Step 3: Use AI to analyze the web search data and find offers
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://preisvergleich-bot.local",
                    "X-Title": "Preisvergleich Bot",
                },
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[
                    {
                        "role": "user",
                        "content": detailed_prompt
                    }
                ],
                temperature=0.1,  # Lower temperature for more consistent results
                max_tokens=3000
            )
            
            output = completion.choices[0].message.content
            
            # Parse the JSON response
            try:
                # Extract JSON from the response
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
                
                # Process and validate the results
                processed_offers = []
                for offer in offers_data:
                    if self._validate_offer(offer):
                        processed_offers.append(offer)
                
                logger.info(f"Found {len(processed_offers)} valid offers")
                
                return {
                    "success": True,
                    "offers": processed_offers,
                    "timestamp": datetime.now().isoformat(),
                    "web_search_data": web_search_data,
                    "raw_response": output
                }
                
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.error(f"Error processing AI response: {e}")
                return {
                    "success": False,
                    "error": f"Error processing AI response: {e}",
                    "raw_output": output,
                    "web_search_data": web_search_data,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in enhanced offer search: {e}")
            return {
                "success": False,
                "error": str(e),
                "web_search_data": web_search_data,
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_offer(self, offer: Dict[str, Any]) -> bool:
        """
        Validate that an offer has the required fields and makes sense
        
        Args:
            offer: Offer dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["product_name", "store", "regular_price", "offer_price"]
        
        # Check required fields
        for field in required_fields:
            if field not in offer:
                return False
        
        # Check that prices are numbers
        try:
            regular_price = float(offer["regular_price"])
            offer_price = float(offer["offer_price"])
        except (ValueError, TypeError):
            return False
        
        # Check that it's actually a discount
        if regular_price <= offer_price:
            return False
        
        # Check that savings percentage is reasonable
        if "savings_percent" in offer:
            try:
                savings = float(offer["savings_percent"])
                if savings < 0 or savings > 100:
                    return False
            except (ValueError, TypeError):
                return False
        
        # CRITICAL: Check date validity - only allow current and next week offers
        if "valid_until" in offer and offer["valid_until"]:
            try:
                from datetime import datetime
                today = datetime.now()
                current_week_start = today - timedelta(days=today.weekday())
                next_week_end = current_week_start + timedelta(days=13)  # 2 weeks from now
                
                # Parse the valid_until date
                if isinstance(offer["valid_until"], str):
                    valid_date = datetime.strptime(offer["valid_until"], "%Y-%m-%d")
                else:
                    valid_date = offer["valid_until"]
                
                # Check if the offer is within the valid timeframe
                if valid_date < current_week_start or valid_date > next_week_end:
                    logger.info(f"Rejecting offer {offer.get('product_name', 'Unknown')} - date {offer['valid_until']} is outside valid range")
                    return False
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse date {offer.get('valid_until', 'Unknown')}: {e}")
                # If we can't parse the date, reject the offer to be safe
                return False
        
        return True
