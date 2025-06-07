import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('offer_agent')

class OfferSearchAgent:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OfferSearchAgent with OpenRouter API key
        
        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY in .env or pass as argument.")
        
        # Set up Tavily API key for web search (if available)
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not self.tavily_api_key:
            logger.warning("TAVILY_API_KEY not found in environment variables. Web search may not work.")
            os.environ["TAVILY_API_KEY"] = "dummy_key"  # Will be replaced by OpenRouter
            
        logger.info("OfferSearchAgent initialized")
        
        # Default stores to check for offers
        self.default_stores = ["Rewe", "Kaufland", "Edeka", "Lidl", "Aldi Süd", "Penny"]
        
        # Create LLM instance connected to OpenRouter
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            model="deepseek/deepseek-chat-v3-0324:free",
            temperature=0.2,
            max_tokens=2000,
            streaming=False
        )
        
        # Create tools
        self.tools = [self.search_tool()]
        
        # Create agent
        self.agent = self._create_agent()
    
    def search_tool(self):
        """Create a web search tool"""
        return TavilySearchResults(max_results=5)
    
    def _create_agent(self):
        """Create a LangChain agent for offer searching"""
        # Create a template for structured reasoning
        template = """
        You are an expert at searching for product offers and deals.
        
        Your task is to find the best offers for specific products in German supermarkets.
        
        The user will provide you with products to search for.
        
        Use the available tools to search for current offers and respond with a JSON structure of your findings.
        
        For each product:
        1. Find the regular price
        2. Find the best offer price
        3. Identify which store has this offer
        4. Determine when the offer is valid (start and end dates)
        5. Note any conditions for the offer
        
        IMPORTANT: Only report actual discounted prices. Do not include regular prices unless they represent a genuine discount.
        
        Return your final answer as a JSON array with objects containing:
        - product_name: Name of the product
        - store: Store with the best offer
        - regular_price: Regular non-discounted price (numeric)
        - offer_price: Discounted price (numeric)
        - savings_percent: Percentage saved (numeric)
        - valid_until: End date of the offer (YYYY-MM-DD format)
        - conditions: Any special conditions for the offer
        - offer_link: Link to the offer online (if available)
        
        ONLY include products that have a current discount offer.
        """
        
        # Create the agent with the required scratchpad
        prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
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
        
        # Create search query
        query = f"""
        Find the best current offers for these products: {products_str}
        
        Look in these stores: {stores_str}
        
        Region: {region}
        
        For each product, I need:
        1. The store with the lowest price
        2. The regular price
        3. The offer price
        4. How long the offer is valid
        5. Any conditions (like loyalty card requirements)
        
        Only include products that actually have a discount or special offer right now.
        """
        
        try:
            logger.info(f"Searching for offers for {len(products)} products")
            result = self.agent.invoke({"input": query})
            
            # Extract offer information from the agent's response
            try:
                # Try to extract JSON from the response
                output = result.get("output", "")
                
                # Extract JSON if it's embedded in text
                if "```json" in output:
                    json_part = output.split("```json")[1].split("```")[0].strip()
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
                    "timestamp": datetime.now().isoformat()
                }
                
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.error(f"Error processing agent response: {e}")
                return {
                    "success": False,
                    "error": f"Error processing agent response: {e}",
                    "raw_output": str(result),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in offer search agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 