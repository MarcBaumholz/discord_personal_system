import discord
from discord.ext import commands, tasks
import os
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Import our modules
from notion_manager import NotionManager
from openrouter_service import OpenRouterService
from product_finder import ProductFinder
from product_presenter import ProductPresenter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wishlist_bot')

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WISHLIST_CHANNEL_ID = int(os.getenv("WISHLIST_CHANNEL_ID"))

# Set timezone to Europe/Berlin
TIMEZONE = pytz.timezone('Europe/Berlin')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Service instances
notion_manager = None
openrouter_service = None
product_finder = None
product_presenter = None

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    global notion_manager, openrouter_service, product_finder, product_presenter
    
    logger.info(f"Logged in as {bot.user}")
    logger.info(f"Using wishlist channel ID: {WISHLIST_CHANNEL_ID}")
    
    # Initialize services
    try:
        notion_manager = NotionManager()
        openrouter_service = OpenRouterService()
        product_finder = ProductFinder(openrouter_service, notion_manager)
        product_presenter = ProductPresenter(bot, WISHLIST_CHANNEL_ID)
        
        # Start background tasks
        weekly_product_suggestions.start()
        
        # Send welcome message
        channel = bot.get_channel(WISHLIST_CHANNEL_ID)
        if channel:
            await channel.send("🛍️ Wishlist Bot is online! I'll help you discover products based on your interests. Use commands like `!wishlist find` to get started.")
            
        logger.info("Wishlist Bot is ready!")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Process commands
    await bot.process_commands(message)

@tasks.loop(hours=168)  # Weekly
async def weekly_product_suggestions():
    """Send weekly product suggestions based on interests"""
    try:
        channel = bot.get_channel(WISHLIST_CHANNEL_ID)
        if not channel:
            logger.error(f"Channel not found: {WISHLIST_CHANNEL_ID}")
            return
        
        await channel.send("🔍 Looking for interesting products matching your interests this week...")
        
        # Get interests from Notion
        interests = await notion_manager.get_interests()
        
        if not interests:
            await channel.send("No interests found in your Notion database. Please add some interests!")
            return
        
        # Choose 3 random interests to focus on this week
        interests_subset = product_finder.select_random_interests(interests, 3)
        
        # Find products for each interest
        for interest in interests_subset:
            try:
                products = await product_finder.find_products_for_interest(interest)
                
                if products:
                    await channel.send(f"**Products related to your interest in {interest}:**")
                    for product in products[:3]:  # Show top 3 products
                        await product_presenter.present_product(product, channel)
                else:
                    await channel.send(f"Couldn't find interesting products for {interest} this time.")
            except Exception as e:
                logger.error(f"Error finding products for {interest}: {e}")
    
    except Exception as e:
        logger.error(f"Error in weekly product suggestions: {e}")

@weekly_product_suggestions.before_loop
async def before_suggestions():
    """Wait until the bot is ready before starting the task"""
    await bot.wait_until_ready()

@bot.command(name="wishlist")
async def wishlist_command(ctx, action="help", *args):
    """Handle wishlist commands"""
    if ctx.channel.id != WISHLIST_CHANNEL_ID:
        await ctx.send("Please use this command in the wishlist channel.")
        return
    
    try:
        if action == "find":
            # Find products for a specific interest or query
            query = " ".join(args) if args else None
            
            if not query:
                # No specific query, use random interest
                interests = await notion_manager.get_interests()
                if interests:
                    query = product_finder.select_random_interests(interests, 1)[0]
                    await ctx.send(f"🔍 Looking for products related to your interest in **{query}**...")
                else:
                    await ctx.send("No interests found in your Notion database. Please add some interests or specify a search query.")
                    return
            else:
                await ctx.send(f"🔍 Looking for products related to **{query}**...")
            
            # Find and present products
            products = await product_finder.find_products_for_interest(query)
            
            if products:
                for product in products[:5]:  # Show top 5 products
                    await product_presenter.present_product(product, ctx)
            else:
                await ctx.send(f"Couldn't find interesting products for {query}.")
                
        elif action == "interests":
            # Show current interests from Notion
            interests = await notion_manager.get_interests()
            
            if interests:
                # Format interests in a nice way
                interests_text = "🧠 **Your Current Interests:**\n\n"
                
                # Group by categories if available
                categorized = {}
                for interest in interests:
                    if isinstance(interest, dict) and 'category' in interest:
                        category = interest['category']
                        if category not in categorized:
                            categorized[category] = []
                        categorized[category].append(interest['name'])
                    else:
                        if 'Uncategorized' not in categorized:
                            categorized['Uncategorized'] = []
                        categorized['Uncategorized'].append(interest if isinstance(interest, str) else interest['name'])
                
                # Format by category
                for category, items in categorized.items():
                    interests_text += f"**{category}**\n"
                    for item in items:
                        interests_text += f"• {item}\n"
                    interests_text += "\n"
                
                await ctx.send(interests_text)
            else:
                await ctx.send("No interests found in your Notion database.")
                
        elif action == "deals":
            # Find discounted products
            await ctx.send("🔍 Looking for deals and discounts on products matching your interests...")
            
            interests = await notion_manager.get_interests()
            if not interests:
                await ctx.send("No interests found in your Notion database. Please add some interests!")
                return
                
            deals = await product_finder.find_discounted_products(interests)
            
            if deals:
                await ctx.send("🎁 **Found these deals for you:**")
                for deal in deals[:5]:  # Show top 5 deals
                    await product_presenter.present_product(deal, ctx)
            else:
                await ctx.send("Couldn't find any interesting deals at the moment. Try again later!")
                
        elif action == "help":
            await post_help(ctx)
        else:
            await ctx.send("Unknown command. Try `!wishlist help` for available commands.")
    except Exception as e:
        logger.error(f"Error handling wishlist command: {e}")
        await ctx.send("Sorry, there was an error processing your request.")

async def post_help(ctx):
    """Post help information"""
    help_text = """
🛍️ **Wishlist Bot Help**

**Commands:**
- `!wishlist find [query]` - Find products matching your interests or a specific query
- `!wishlist interests` - Show your current interests from Notion
- `!wishlist deals` - Find deals on products matching your interests
- `!wishlist help` - Show this help message

I'll also automatically suggest products weekly based on your interests!
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN) 