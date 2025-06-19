import os
import discord
import logging
import asyncio
from dotenv import load_dotenv
from typing import Optional

from decision_analyzer import DecisionAnalyzer

# Load environment variables from parent directory
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('decision_bot')

# Load environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Hardcoded as per requirements
DISCORD_CHANNEL_ID = int(os.getenv("LIFE_QUESTIONS"))
# Validate environment
if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN not found in environment variables")
    exit(1)

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Initialize decision analyzer
decision_analyzer = None

@client.event
async def on_ready():
    """Called when the bot is ready"""
    global decision_analyzer
    
    logger.info(f"Logged in as {client.user}")
    logger.info(f"Target channel ID: {DISCORD_CHANNEL_ID}")
    
    try:
        # Initialize decision analyzer
        decision_analyzer = DecisionAnalyzer("./upload")
        
        # Load user data
        success = await decision_analyzer.initialize()
        
        # Send startup message to channel
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            if success:
                status = decision_analyzer.get_user_data_status()
                await channel.send(
                    f"🧠 **Decision Bot ist online!**\n\n"
                    f"📊 **Daten-Status:** {status['files_found']} CSV-Dateien geladen\n"
                    f"📋 **Kategorien:** {', '.join(status['categories'])}\n\n"
                    f"💬 Stelle mir eine Entscheidungsfrage und ich analysiere sie anhand deiner persönlichen Daten!"
                )
            else:
                await channel.send(
                    "🤖 **Decision Bot ist online!**\n\n"
                    "⚠️ Keine persönlichen Daten gefunden. Lade CSV-Dateien in den `/upload` Ordner hoch, um personalisierte Entscheidungsanalysen zu erhalten.\n\n"
                    "💬 Du kannst trotzdem Fragen stellen - ich erkläre dir dann, welche Daten ich benötige!"
                )
        else:
            logger.error(f"Could not find channel with ID {DISCORD_CHANNEL_ID}")
        
        logger.info("Decision Bot is ready!")
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")

@client.event
async def on_message(message):
    """Handle incoming messages"""
    # Don't respond to ourselves
    if message.author == client.user:
        return
    
    # Only respond in the designated channel
    if message.channel.id != DISCORD_CHANNEL_ID:
        return
    
    # Handle special commands
    if message.content.lower().strip() == "!status":
        await handle_status_command(message)
        return
    
    if message.content.lower().strip() == "!reload":
        await handle_reload_command(message)
        return
    
    if message.content.lower().strip() == "!help":
        await handle_help_command(message)
        return
    
    # Handle decision questions
    if len(message.content.strip()) > 10:  # Minimum question length
        await handle_decision_question(message)

async def handle_decision_question(message):
    """Handle a decision question from the user"""
    try:
        logger.info(f"Processing decision question from {message.author}")
        
        # Add thinking reaction
        await message.add_reaction("🤔")
        
        # Show typing indicator
        async with message.channel.typing():
            # Analyze the question
            if decision_analyzer:
                analysis = await decision_analyzer.analyze_question(message.content)
                
                if analysis:
                    # Split response if it's too long for Discord
                    if len(analysis) > 2000:
                        parts = split_message(analysis, 2000)
                        for part in parts:
                            await message.channel.send(part)
                    else:
                        await message.channel.send(analysis)
                    
                    # Add success reaction
                    await message.add_reaction("✅")
            else:
                await message.channel.send("⚠️ Decision Analyzer ist nicht initialisiert.")
        
    except Exception as e:
        logger.error(f"Error handling decision question: {e}")
        await message.channel.send("❌ Ein Fehler ist aufgetreten bei der Analyse.")

async def handle_status_command(message):
    """Handle the status command"""
    try:
        if decision_analyzer:
            status = decision_analyzer.get_user_data_status()
            
            status_msg = f"📊 **Decision Bot Status**\n\n"
            status_msg += f"🔄 **Daten geladen:** {'✅ Ja' if status['loaded'] else '❌ Nein'}\n"
            status_msg += f"📁 **CSV-Dateien:** {status['files_found']}\n"
            
            if status['categories']:
                status_msg += f"📋 **Verfügbare Kategorien:**\n"
                for category in status['categories']:
                    status_msg += f"   • {category}\n"
            
            await message.channel.send(status_msg)
        else:
            await message.channel.send("❌ Decision Analyzer ist nicht verfügbar.")
            
    except Exception as e:
        logger.error(f"Error handling status command: {e}")

async def handle_reload_command(message):
    """Handle the reload command"""
    try:
        logger.info(f"Reload requested by {message.author}")
        await message.add_reaction("🔄")
        
        global decision_analyzer
        decision_analyzer = DecisionAnalyzer("./upload")
        success = await decision_analyzer.initialize()
        
        if success:
            await message.channel.send("✅ **Daten erfolgreich neu geladen!**")
        else:
            await message.channel.send("⚠️ **Keine CSV-Dateien gefunden.**")
            
    except Exception as e:
        logger.error(f"Error handling reload command: {e}")

async def handle_help_command(message):
    """Handle the help command"""
    help_text = """🧠 **Decision Bot - Hilfe**

**🎯 Zweck:**
Ich analysiere deine Entscheidungsfragen anhand deiner persönlichen Werte, Ziele und Erfahrungen.

**💬 Verwendung:**
Stelle einfach eine Frage oder beschreibe eine Entscheidung.

**📁 CSV-Daten benötigt:**
• `values.csv` - Werte und Prinzipien
• `goals.csv` - Ziele und Aspirationen
• `identity.csv` - Persönlichkeit
• `experiences.csv` - Erfahrungen

**🔧 Befehle:**
• `!status` - Datenstatus
• `!reload` - Daten neu laden
• `!help` - Diese Hilfe

Frag mich alles! 🚀"""
    
    await message.channel.send(help_text)

def split_message(text: str, max_length: int = 2000) -> list:
    """Split a long message into chunks for Discord"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    lines = text.split('\n')
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# Run the bot
if __name__ == "__main__":
    try:
        client.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1) 