import os
import discord
import logging
import asyncio
from dotenv import load_dotenv
from typing import List, Dict, Any
from datetime import datetime

# Import our custom modules
from notion_manager import NotionProductManager
from simple_agent import SimpleOfferSearchAgent
from scheduler import OfferScheduler
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('preisvergleich_bot')

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
if CHANNEL_ID:
    CHANNEL_ID = int(CHANNEL_ID)

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent for commands
client = discord.Client(intents=intents)

# Initialize our services
notion_manager = None
offer_agent = None
scheduler = None

@client.event
async def on_ready():
    """Called when the bot is ready"""
    global notion_manager, offer_agent, scheduler
    
    logger.info(f"Logged in as {client.user}")
    
    if not CHANNEL_ID:
        logger.error("DISCORD_CHANNEL_ID not set in environment variables")
        await client.close()
        return
    
    logger.info(f"Using channel ID: {CHANNEL_ID}")
    
    # Initialize our services
    try:
        notion_manager = NotionProductManager()
        offer_agent = SimpleOfferSearchAgent()
        scheduler = OfferScheduler()
        
        # Schedule weekly check for Sunday evening at 8 PM
        scheduler.schedule_sunday_check(lambda: asyncio.create_task(check_offers()))
        
        logger.info("Preisvergleich Bot is ready!")
        
        # Send startup message
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            startup_message = (
                "🔍 **Preisvergleich Bot ist online!** 🤖\n\n"
                "Ich überwache Produktpreise für dich! Das kann ich:\n"
                "• 👀 Automatische Überwachung deiner Notion-Wunschliste\n"
                "• 💰 Wöchentliche Angebots-Checks (Sonntags 20:00)\n"
                "• 🏷️ Preisvergleiche und Rabatt-Benachrichtigungen\n"
                "• 📊 Detaillierte Angebots-Informationen mit Links\n"
                "• 💸 Berechnung der Gesamt-Ersparnis\n\n"
                "**Befehle:**\n"
                "• `producthunt` - Sofortige Angebots-Suche starten\n\n"
                "Ich checke automatisch jeden Sonntag um 20:00 Uhr!\n"
                "Stelle sicher, dass deine Wunschliste in Notion aktuell ist."
            )
            await channel.send(startup_message)
        else:
            logger.error(f"Could not find channel with ID {CHANNEL_ID}")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

@client.event
async def on_message(message):
    """Handle incoming messages"""
    # Don't respond to ourselves
    if message.author == client.user:
        return
    
    # Check if message is in the correct channel
    if message.channel.id != CHANNEL_ID:
        return
    
    # Handle the producthunt command
    if message.content.lower().strip() == "producthunt":
        logger.info(f"Manual offer check triggered by {message.author}")
        await message.add_reaction("🔍")  # Add reaction to show we're processing
        await message.channel.send("🔍 **Manual offer check triggered!** Starting search...")
        await check_offers()

async def check_offers():
    """Check for offers and send notifications"""
    logger.info("Starting scheduled offer check")
    
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        logger.error(f"Could not find channel with ID {CHANNEL_ID}")
        return
    
    try:
        # Get products from Notion database
        products = notion_manager.get_watchlist()
        if not products:
            logger.warning("No products found in the watchlist")
            return
        
        logger.info(f"Checking offers for {len(products)} products")
        
        # Find offers using the agent
        results = offer_agent.find_offers(products)
        
        if not results.get("success", False):
            error_msg = results.get("error", "Unknown error")
            logger.error(f"Error finding offers: {error_msg}")
            return
        
        offers = results.get("offers", [])
        
        if not offers:
            logger.info("No offers found")
            return
        
        # Send notifications for each offer
        await send_offer_notifications(channel, offers)
        
    except Exception as e:
        logger.error(f"Error in offer check task: {e}")

async def send_offer_notifications(channel, offers: List[Dict[str, Any]]):
    """Send offer notifications to the Discord channel"""
    if not offers:
        return
    
    # Send a header message
    await channel.send("🔥 **ANGEBOTE GEFUNDEN!** 🔥")
    
    # Send each offer as a separate message
    for offer in offers:
        product_name = offer.get("product_name", "Unknown Product")
        store = offer.get("store", "Unknown Store")
        regular_price = offer.get("regular_price")
        offer_price = offer.get("offer_price")
        savings_percent = offer.get("savings_percent")
        valid_until = offer.get("valid_until", "Unknown")
        conditions = offer.get("conditions", "")
        offer_link = offer.get("offer_link", "")
        
        # Format the message
        message = f"**{product_name}** ist im Angebot bei **{store}**!\n"
        message += f"💰 Regulärer Preis: **€{regular_price:.2f}**\n"
        message += f"🏷️ Angebotspreis: **€{offer_price:.2f}**\n"
        message += f"✨ Du sparst: **{savings_percent:.1f}%**\n"
        
        if valid_until and valid_until != "Unknown":
            message += f"⏱️ Gültig bis: **{valid_until}**\n"
        
        if conditions:
            message += f"ℹ️ Bedingungen: {conditions}\n"
            
        if offer_link:
            message += f"🔗 [Zum Angebot]({offer_link})\n"
        
        # Create an embed for the offer
        embed = discord.Embed(
            title=f"🏷️ {product_name}",
            description=message,
            color=0x00ff00
        )
        
        embed.timestamp = datetime.utcnow()
        
        await channel.send(embed=embed)
    
    # Send a footer message
    total_savings = sum([(o.get("regular_price", 0) - o.get("offer_price", 0)) for o in offers])
    await channel.send(f"💸 Gesamt-Ersparnis wenn du alles kaufst: **€{total_savings:.2f}**")

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set in environment variables")
        exit(1)
        
    client.run(DISCORD_TOKEN) 