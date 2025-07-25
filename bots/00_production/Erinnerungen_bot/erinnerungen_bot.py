#!/usr/bin/env python3
"""
Erinnerungen Bot - Main Entry Point
Automatically sends daily reminders for birthdays and waste collection
"""

import discord
from discord.ext import commands
import os
import logging
import asyncio
from datetime import datetime
import pytz
from dotenv import load_dotenv
import threading
import time

# Import custom modules
from notion_manager import NotionManager
from geburtstage import GeburtstageManager
from muellkalender import MuellkalenderManager
from scheduler import ErinnerungsScheduler

# Load environment variables from parent directory
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('erinnerungen_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('erinnerungen_bot')

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ERINNERUNGEN_CHANNEL_ID = int(os.getenv("ERINNERUNGEN_CHANNEL_ID"))
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Europe/Berlin"))

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Service instances
notion_manager = None
geburtstage_manager = None
muellkalender_manager = None 
scheduler = None

@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is ready and serving {len(bot.guilds)} guilds')
    
    # Initialize managers
    global notion_manager, geburtstage_manager, muellkalender_manager, scheduler
    
    try:
        # Initialize Notion manager
        notion_manager = NotionManager()
        logger.info("Notion manager initialized")
        
        # Initialize birthday manager
        geburtstage_manager = GeburtstageManager(notion_manager)
        logger.info("Geburtstage manager initialized")
        
        # Initialize waste calendar manager  
        muellkalender_manager = MuellkalenderManager()
        logger.info("Müllkalender manager initialized")
        
        # Initialize scheduler
        scheduler = ErinnerungsScheduler(
            bot, 
            ERINNERUNGEN_CHANNEL_ID,
            geburtstage_manager,
            muellkalender_manager
        )
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=scheduler.start, daemon=True)
        scheduler_thread.start()
        logger.info("Scheduler started")
        
        # Send startup message to Discord channel
        try:
            channel = bot.get_channel(ERINNERUNGEN_CHANNEL_ID)
            if channel:
                startup_message = (
                    "🔔 **Erinnerungen Bot ist online!** 🤖\n\n"
                    "Ich helfe dir bei deinen täglichen Erinnerungen! Das kann ich:\n"
                    "• 🎂 Überwache Geburtstage und sende tägliche Erinnerungen\n"
                    "• 🗑️ Erinnere an Müllabholung am Vorabend\n"
                    "• 📅 Zeige wöchentliche Übersichten für kommende Ereignisse\n"
                    "• 🔄 Automatische tägliche Checks um 7:00 Uhr\n"
                    "• 💾 Integriert mit Notion für Geburtstags-Datenbank\n\n"
                    "**Befehle:**\n"
                    "• `!test_geburtstage` - Teste Geburtstags-Check\n"
                    "• `!test_muell` - Teste Müllkalender-Check\n"
                    "• `!remind` - Zeige wöchentliche Übersicht\n\n"
                    "Automatische Erinnerungen sind aktiviert!\n"
                    "Ich checke täglich Geburtstage und Müllabholung für dich."
                )
                await channel.send(startup_message)
                logger.info("✅ Startup notification sent to erinnerungen channel")
            else:
                logger.error(f"Could not find channel with ID {ERINNERUNGEN_CHANNEL_ID}")
        except Exception as e:
            logger.error(f"❌ Error sending startup notification: {e}")
        
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

@bot.command(name='test_geburtstage')
async def test_geburtstage(ctx):
    """Test command for birthday checks"""
    if geburtstage_manager:
        try:
            birthdays = await geburtstage_manager.check_todays_birthdays()
            if birthdays:
                for birthday in birthdays:
                    await ctx.send(f"🎉 **Geburtstag heute!** {birthday}")
            else:
                await ctx.send("Keine Geburtstage heute.")
        except Exception as e:
            await ctx.send(f"Fehler beim Abrufen der Geburtstage: {e}")
            logger.error(f"Error in test_geburtstage: {e}")
    else:
        await ctx.send("Geburtstage-Manager nicht initialisiert.")

@bot.command(name='test_muell')
async def test_muell(ctx):
    """Test command for waste calendar checks"""
    if muellkalender_manager:
        try:
            waste_info = await muellkalender_manager.check_tomorrows_collection()
            if waste_info:
                await ctx.send(f"🗑️ **Müll-Erinnerung!** {waste_info}")
            else:
                await ctx.send("Keine Müllabholung morgen.")
        except Exception as e:
            await ctx.send(f"Fehler beim Abrufen des Müllkalenders: {e}")
            logger.error(f"Error in test_muell: {e}")
    else:
        await ctx.send("Müllkalender-Manager nicht initialisiert.")

@bot.command(name='remind')
async def remind_weekly(ctx):
    """Show upcoming birthdays and waste collection for the next week"""
    try:
        logger.info("Processing remind command for weekly overview")
        
        # Initialize response message
        response_parts = []
        
        # Get upcoming birthdays
        if geburtstage_manager:
            try:
                upcoming_birthdays = await geburtstage_manager.get_upcoming_birthdays(days_ahead=7)
                birthday_summary = geburtstage_manager.format_upcoming_birthdays_summary(upcoming_birthdays)
                response_parts.append(birthday_summary)
                logger.info(f"Found {len(upcoming_birthdays)} upcoming birthdays")
            except Exception as e:
                logger.error(f"Error getting upcoming birthdays: {e}")
                response_parts.append("❌ Fehler beim Abrufen der Geburtstage.")
        else:
            response_parts.append("❌ Geburtstage-Manager nicht verfügbar.")
        
        # Get upcoming waste collections
        if muellkalender_manager:
            try:
                upcoming_collections = await muellkalender_manager.get_next_week_collections()
                waste_summary = muellkalender_manager.format_weekly_collections(upcoming_collections)
                response_parts.append(waste_summary)
                logger.info(f"Found {len(upcoming_collections)} upcoming waste collections")
            except Exception as e:
                logger.error(f"Error getting upcoming waste collections: {e}")
                response_parts.append("❌ Fehler beim Abrufen des Müllkalenders.")
        else:
            response_parts.append("❌ Müllkalender-Manager nicht verfügbar.")
        
        # Send response
        full_response = "\n\n" + "="*50 + "\n\n".join(response_parts)
        
        # Split into multiple messages if too long (Discord limit is 2000 chars)
        if len(full_response) > 1900:
            for part in response_parts:
                await ctx.send(part)
        else:
            await ctx.send(full_response)
            
        logger.info("Remind command completed successfully")
        
    except Exception as e:
        await ctx.send(f"❌ Fehler beim Erstellen der Wochenübersicht: {e}")
        logger.error(f"Error in remind command: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    """Global error handler"""
    logger.error(f'Error in event {event}: {args}', exc_info=True)

@bot.event  
async def on_command_error(ctx, error):
    """Command error handler"""
    logger.error(f'Command error: {error}', exc_info=True)
    await ctx.send(f"Ein Fehler ist aufgetreten: {error}")

def main():
    """Main entry point"""
    if DISCORD_TOKEN == "your_discord_bot_token_here":
        logger.error("DISCORD_TOKEN not found or is placeholder")
        logger.error("Please update .env file with real Discord bot token")
        logger.error("Get token from: https://discord.com/developers/applications")
        logger.error("Or run: python test_bot.py for demo mode")
        return
    
    if not ERINNERUNGEN_CHANNEL_ID:
        logger.error("ERINNERUNGEN_CHANNEL_ID not found in environment variables")
        return
    
    logger.info("Starting Erinnerungen Bot...")
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        logger.error("Hint: Check if Discord token is valid")
        logger.error("For testing without real tokens, run: python test_bot.py")

if __name__ == "__main__":
    main() 