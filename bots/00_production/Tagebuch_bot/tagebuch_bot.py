#!/usr/bin/env python3
"""
Tagebuch Bot - Discord Journal Bot
Automatically saves journal entries to Notion database with daily reminders.
"""

import discord
from discord.ext import commands
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Import our custom modules
from notion_manager import NotionManager
from text_processor import TextProcessor
from scheduler import ReminderScheduler

env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TAGEBUCH_CHANNEL_ID = int(os.getenv("TAGEBUCH_CHANNEL_ID", "1384289197115838625"))

if not DISCORD_TOKEN or DISCORD_TOKEN == "your_discord_bot_token_here":
    print("❌ DISCORD_TOKEN not configured properly!")
    print("Please run: python setup_validator.py")
    print("to configure your tokens correctly.")
    exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tagebuch_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('tagebuch_bot')

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize components
notion_manager = None
text_processor = None
scheduler = None

@bot.event
async def on_ready():
    """Bot startup event"""
    global notion_manager, text_processor, scheduler
    
    logger.info(f"🤖 {bot.user} is now online!")
    logger.info(f"📍 Monitoring channel ID: {TAGEBUCH_CHANNEL_ID}")
    
    try:
        # Initialize components
        notion_manager = NotionManager()
        text_processor = TextProcessor()
        scheduler = ReminderScheduler(bot)
        
        # Start the daily reminder scheduler
        scheduler.start_scheduler()
        
        logger.info("✅ All components initialized successfully")
        
        # Send startup message to Discord channel
        try:
            channel = bot.get_channel(TAGEBUCH_CHANNEL_ID)
            if channel:
                startup_message = (
                    "📔 **Tagebuch Bot ist online!** 🤖\n\n"
                    "Ich helfe dir beim Tagebuch schreiben! Das kann ich:\n"
                    "• ✍️ Automatisch Tagebucheinträge erkennen und speichern\n"
                    "• 📝 Intelligente Titel für deine Einträge generieren\n"
                    "• 💾 Direkt in deine Notion-Datenbank speichern\n"
                    "• ⏰ Tägliche Erinnerungen um 22:00 Uhr senden\n"
                    "• 🔄 Automatische Textformatierung für Notion\n\n"
                    "**Befehle:**\n"
                    "• `!tagebuch_help` - Detaillierte Hilfe anzeigen\n"
                    "• `!tagebuch_test` - Test-Eintrag erstellen\n"
                    "• `!tagebuch_reminder` - Test-Erinnerung senden\n\n"
                    "Schreibe einfach deine Gedanken in diesen Chat!\n"
                    "Ich erkenne automatisch Tagebucheinträge und speichere sie."
                )
                await channel.send(startup_message)
                logger.info("✅ Startup notification sent to tagebuch channel")
            else:
                logger.error(f"Could not find channel with ID {TAGEBUCH_CHANNEL_ID}")
        except Exception as e:
            logger.error(f"❌ Error sending startup notification: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}")
        raise

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    # Ignore bot messages and messages not in target channel
    if message.author.bot or message.channel.id != TAGEBUCH_CHANNEL_ID:
        return
    
    # Ignore command messages
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # Process potential journal entry
    await process_journal_entry(message)

async def process_journal_entry(message):
    """Process a potential journal entry"""
    try:
        text = message.content.strip()
        
        # Validate text using text processor
        if not text_processor.validate_text(text):
            logger.info(f"Message too short or invalid from {message.author}: {text[:50]}...")
            return
        
        # Generate title
        title = text_processor.generate_title(text)
        
        # Format text for Notion
        formatted_text = text_processor.format_text_for_notion(text)
        
        # Save to Notion
        result = await notion_manager.create_journal_entry(title, formatted_text)
        
        if result["success"]:
            # Send confirmation message
            embed = discord.Embed(
                title="✅ Tagebucheintrag gespeichert!",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📖 Titel",
                value=f"`{title}`",
                inline=False
            )
            
            embed.add_field(
                name="📅 Datum",
                value=datetime.now().strftime("%d.%m.%Y"),
                inline=True
            )
            
            embed.add_field(
                name="📝 Text (Vorschau)",
                value=f"{formatted_text[:100]}{'...' if len(formatted_text) > 100 else ''}",
                inline=False
            )
            
            embed.set_footer(text="Dein Eintrag wurde erfolgreich in Notion gespeichert!")
            
            await message.reply(embed=embed)
            logger.info(f"✅ Journal entry saved for {message.author}: '{title}'")
            
        else:
            # Error message
            error_embed = discord.Embed(
                title="❌ Fehler beim Speichern",
                description="Dein Tagebucheintrag konnte nicht gespeichert werden.",
                color=0xff0000
            )
            
            error_embed.add_field(
                name="Grund",
                value=f"```{result.get('error', 'Unbekannter Fehler')}```",
                inline=False
            )
            
            await message.reply(embed=error_embed)
            logger.error(f"❌ Failed to save journal entry: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error processing journal entry: {e}")
        
        # Send generic error message
        await message.reply("❌ Ein unerwarteter Fehler ist aufgetreten. Bitte versuche es später erneut.")

@bot.command(name="tagebuch_help")
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="📔 Tagebuch Bot - Hilfe",
        description="Automatische Speicherung deiner Tagebucheinträge in Notion",
        color=0x5865F2
    )
    
    embed.add_field(
        name="🔍 Wie es funktioniert",
        value="Schreibe einfach deine Gedanken in diesen Chat. "
              "Der Bot erkennt automatisch Tagebucheinträge und speichert sie in Notion.",
        inline=False
    )
    
    embed.add_field(
        name="⏰ Tägliche Erinnerung",
        value="Jeden Abend um 22:00 Uhr erhältst du eine Erinnerung zum Tagebuch schreiben.",
        inline=False
    )
    
    embed.add_field(
        name="📋 Befehle",
        value="`!tagebuch_help` - Diese Hilfe anzeigen\n"
              "`!tagebuch_test` - Test-Eintrag erstellen",
        inline=False
    )
    
    embed.set_footer(text="Deine Einträge werden automatisch mit Titel und Datum versehen.")
    
    await ctx.send(embed=embed)

@bot.command(name="tagebuch_test")
async def test_command(ctx):
    """Create a test journal entry"""
    try:
        test_title = "Test-Eintrag"
        test_text = f"Dies ist ein Test-Eintrag erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr."
        
        result = await notion_manager.create_journal_entry(test_title, test_text)
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Test erfolgreich!",
                description="Test-Eintrag wurde erfolgreich in Notion gespeichert.",
                color=0x00ff00
            )
            
            embed.add_field(
                name="Page ID",
                value=f"`{result['page_id']}`",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Test fehlgeschlagen: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in test command: {e}")
        await ctx.send(f"❌ Test-Fehler: {str(e)}")

@bot.command(name="tagebuch_reminder")
async def test_reminder(ctx):
    """Test the daily reminder (admin only)"""
    if scheduler:
        try:
            await scheduler._send_reminder()
            await ctx.send("🔔 Test-Erinnerung wurde ausgelöst!")
        except Exception as e:
            logger.error(f"Error in test reminder: {e}")
            await ctx.send(f"❌ Fehler beim Senden der Test-Erinnerung: {str(e)}")
    else:
        await ctx.send("❌ Scheduler ist nicht initialisiert")

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Tagebuch Bot...")
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if scheduler:
            scheduler.stop_scheduler()
        logger.info("Bot shutdown complete") 