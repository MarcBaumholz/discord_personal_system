import os
import discord
from discord.ext import commands, tasks
import asyncio
from dotenv import load_dotenv
import datetime
import pytz
import logging

# Import modules
from water_tracker import WaterTracker
from sleep_tracker import SleepTracker
from mood_tracker import MoodTracker
from meditation_module import MeditationModule
from medication_reminder import MedicationReminder
from notion_manager import NotionManager
from report_generator import ReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("health_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("health_bot")

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
HEALTH_CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize modules
notion_manager = None
water_tracker = None
sleep_tracker = None
mood_tracker = None
meditation_module = None
medication_reminder = None
report_generator = None

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    global notion_manager, water_tracker, sleep_tracker, mood_tracker, meditation_module, medication_reminder, report_generator
    
    logger.info(f'Bot logged in as {bot.user}')
    
    # Initialize Notion manager
    notion_manager = NotionManager()
    
    # Initialize tracking modules
    water_tracker = WaterTracker(bot, notion_manager)
    sleep_tracker = SleepTracker(bot, notion_manager)
    mood_tracker = MoodTracker(bot, notion_manager)
    meditation_module = MeditationModule(bot, notion_manager)
    medication_reminder = MedicationReminder(bot, notion_manager)
    
    # Initialize report generator
    report_generator = ReportGenerator(notion_manager)
    
    # Start tasks
    water_reminder.start()
    daily_health_check.start()
    daily_sleep_reminder.start()
    
    # Send startup message
    channel = bot.get_channel(HEALTH_CHANNEL_ID)
    if channel:
        await channel.send("🌱 Health & Wellness Bot ist online! Tippe `!health help` für eine Übersicht der Befehle.")

@tasks.loop(minutes=90)
async def water_reminder():
    """Sends water reminders every 90 minutes during active hours"""
    now = datetime.datetime.now(pytz.timezone('Europe/Berlin'))
    
    # Only send reminders between 8am and 10pm
    if 8 <= now.hour < 22:
        channel = bot.get_channel(HEALTH_CHANNEL_ID)
        if channel:
            await channel.send("💧 Zeit für ein Glas Wasser! Tracke deinen Konsum mit `!water [Menge in ml]`")

@tasks.loop(time=datetime.time(hour=21, minute=30, tzinfo=pytz.timezone('Europe/Berlin')))
async def daily_sleep_reminder():
    """Sends a reminder to prepare for sleep"""
    channel = bot.get_channel(HEALTH_CHANNEL_ID)
    if channel:
        await channel.send("😴 Zeit, den Tag abzuschließen! Bereite dich auf einen erholsamen Schlaf vor.")

@tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=pytz.timezone('Europe/Berlin')))
async def daily_health_check():
    """Daily morning check-in for health metrics"""
    channel = bot.get_channel(HEALTH_CHANNEL_ID)
    if channel:
        await channel.send("🌞 Guten Morgen! Wie geht es dir heute?\n"
                         "1. Wie hast du geschlafen? `!sleep [Stunden]`\n"
                         "2. Wie ist deine Stimmung? `!mood [1-10]`\n"
                         "3. Plane deine Achtsamkeitsübung `!meditate`")

@bot.command(name="health")
async def health_command(ctx, action="help", timeframe="daily"):
    """Main health command handler"""
    if ctx.channel.id != HEALTH_CHANNEL_ID:
        return
    
    if action == "help":
        await send_help_message(ctx)
    elif action == "report":
        if timeframe in ["daily", "weekly", "monthly"]:
            await report_generator.generate_report(ctx, timeframe)
        else:
            await ctx.send("❌ Bitte wähle einen gültigen Zeitraum: daily, weekly, monthly")

@bot.command(name="water")
async def water_command(ctx, amount: int = None):
    """Track water consumption"""
    if ctx.channel.id != HEALTH_CHANNEL_ID:
        return
    
    if amount is None:
        await ctx.send("❌ Bitte gib eine Wassermenge an. Beispiel: `!water 250`")
        return
    
    await water_tracker.track_water(ctx, amount)

@bot.command(name="sleep")
async def sleep_command(ctx, hours: float = None):
    """Track sleep duration"""
    if ctx.channel.id != HEALTH_CHANNEL_ID:
        return
    
    if hours is None:
        await ctx.send("❌ Bitte gib die Schlafstunden an. Beispiel: `!sleep 7.5`")
        return
    
    await sleep_tracker.track_sleep(ctx, hours)

@bot.command(name="mood")
async def mood_command(ctx, rating: int = None):
    """Track mood on a scale of 1-10"""
    if ctx.channel.id != HEALTH_CHANNEL_ID:
        return
    
    if rating is None or not (1 <= rating <= 10):
        await ctx.send("❌ Bitte bewerte deine Stimmung von 1-10. Beispiel: `!mood 8`")
        return
    
    await mood_tracker.track_mood(ctx, rating)

@bot.command(name="meditate")
async def meditate_command(ctx, minutes: int = None):
    """Start a meditation timer or get meditation suggestions"""
    if ctx.channel.id != HEALTH_CHANNEL_ID:
        return
    
    await meditation_module.handle_meditation(ctx, minutes)

@bot.command(name="med")
async def medication_command(ctx, action=None, *args):
    """Medication tracking and reminders"""
    if ctx.channel.id != HEALTH_CHANNEL_ID:
        return
    
    if action is None:
        await ctx.send("❌ Bitte gib eine Aktion an: `track` oder `remind`")
        return
    
    await medication_reminder.handle_medication(ctx, action, args)

async def send_help_message(ctx):
    """Send the help message with available commands"""
    help_text = """
🌱 **Health & Wellness Bot - Hilfe**

**Allgemeine Befehle:**
`!health help` - Zeigt diese Hilfe an
`!health report [daily/weekly/monthly]` - Zeigt Gesundheitsberichte

**Tracking-Befehle:**
`!water [Menge in ml]` - Trackt deinen Wasserkonsum
`!sleep [Stunden]` - Trackt deine Schlafstunden
`!mood [1-10]` - Trackt deine Stimmung auf einer Skala von 1-10

**Achtsamkeit & Meditation:**
`!meditate` - Zeigt Meditationsoptionen
`!meditate [Minuten]` - Startet einen Meditationstimer

**Medikamente & Vitamine:**
`!med track [Medikament]` - Trackt die Einnahme eines Medikaments
`!med remind [Medikament] [Zeit in HH:MM]` - Setzt eine Erinnerung
"""
    await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN) 