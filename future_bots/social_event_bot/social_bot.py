import discord
from discord.ext import commands, tasks
import os
import logging
import asyncio
import datetime
import pytz
from dotenv import load_dotenv

# Import modules
from birthday_manager import BirthdayManager
from event_planner import EventPlanner
from meeting_scheduler import MeetingScheduler
from gift_recommender import GiftRecommender
from notion_manager import NotionManager
from google_calendar import GoogleCalendarIntegration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("social_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("social_bot")

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
EVENT_CHANNEL_ID = int(os.getenv('EVENT_CHANNEL_ID'))

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize modules
notion_manager = None
birthday_manager = None
event_planner = None
meeting_scheduler = None
gift_recommender = None
calendar_integration = None

# User workflows - stores active dialogs
user_workflows = {}

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    global notion_manager, birthday_manager, event_planner, meeting_scheduler, gift_recommender, calendar_integration
    
    logger.info(f'Bot logged in as {bot.user}')
    
    # Initialize Notion manager
    notion_manager = NotionManager()
    
    # Initialize managers
    birthday_manager = BirthdayManager(bot, notion_manager)
    event_planner = EventPlanner(bot, notion_manager)
    meeting_scheduler = MeetingScheduler(bot, notion_manager)
    gift_recommender = GiftRecommender(bot, notion_manager)
    
    # Initialize Google Calendar integration
    calendar_integration = GoogleCalendarIntegration()
    
    # Start tasks
    check_upcoming_birthdays.start()
    check_upcoming_events.start()
    daily_summary.start()
    
    # Send startup message
    channel = bot.get_channel(EVENT_CHANNEL_ID)
    if channel:
        await channel.send("🎉 Social & Event Koordinator Bot ist online! Tippe `!social help` für eine Übersicht der Befehle.")

@tasks.loop(hours=24)
async def check_upcoming_birthdays():
    """Check for upcoming birthdays once per day"""
    await birthday_manager.check_upcoming_birthdays()

@tasks.loop(hours=12)
async def check_upcoming_events():
    """Check for upcoming events twice per day"""
    await event_planner.check_upcoming_events()

@tasks.loop(time=datetime.time(hour=8, minute=0, tzinfo=pytz.timezone('Europe/Berlin')))
async def daily_summary():
    """Send a daily summary of events and birthdays"""
    channel = bot.get_channel(EVENT_CHANNEL_ID)
    if not channel:
        return
    
    # Get today's date
    today = datetime.datetime.now().date()
    
    # Get birthdays
    todays_birthdays = birthday_manager.get_birthdays_for_date(today)
    upcoming_birthdays = birthday_manager.get_upcoming_birthdays(days=7)
    
    # Get events
    todays_events = event_planner.get_events_for_date(today)
    upcoming_events = event_planner.get_upcoming_events(days=7)
    
    # Prepare message
    message = "📅 **Tagesübersicht**\n\n"
    
    # Add today's birthdays
    if todays_birthdays:
        message += "🎂 **Heutige Geburtstage:**\n"
        for birthday in todays_birthdays:
            age = today.year - birthday['birth_year'] if birthday.get('birth_year') else None
            age_text = f" ({age}. Geburtstag)" if age else ""
            message += f"• {birthday['name']}{age_text}\n"
        message += "\n"
    
    # Add today's events
    if todays_events:
        message += "🎯 **Heutige Termine:**\n"
        for event in todays_events:
            time_text = f" um {event['time']}" if event.get('time') else ""
            message += f"• {event['name']}{time_text} @ {event.get('location', 'kein Ort angegeben')}\n"
        message += "\n"
    
    # Add upcoming birthdays
    if upcoming_birthdays and not todays_birthdays:
        message += "🔜 **Anstehende Geburtstage:**\n"
        for birthday in upcoming_birthdays[:3]:  # Show max 3
            days_until = (birthday['date'] - today).days
            message += f"• {birthday['name']} in {days_until} Tagen ({birthday['date'].strftime('%d.%m.')})\n"
        message += "\n"
    
    # Add upcoming events
    if upcoming_events and not todays_events:
        message += "📌 **Anstehende Termine:**\n"
        for event in upcoming_events[:3]:  # Show max 3
            days_until = (event['date'] - today).days
            message += f"• {event['name']} in {days_until} Tagen ({event['date'].strftime('%d.%m.')})\n"
    
    # Only send if we have something to report
    if todays_birthdays or todays_events or upcoming_birthdays or upcoming_events:
        await channel.send(message)

@bot.command(name="social")
async def social_command(ctx, action="help"):
    """Main social command handler"""
    if ctx.channel.id != EVENT_CHANNEL_ID:
        return
    
    if action == "help":
        await send_help_message(ctx)

@bot.command(name="birthday")
async def birthday_command(ctx, action=None, *args):
    """Birthday management commands"""
    if ctx.channel.id != EVENT_CHANNEL_ID:
        return
    
    if not action:
        await ctx.send("❌ Bitte gib eine Aktion an: `add`, `list`, oder `remove`")
        return
    
    if action == "add":
        if len(args) < 2:
            await ctx.send("❌ Bitte gib einen Namen und ein Datum an. Beispiel: `!birthday add Max 15.06.1990`")
            return
        
        name = args[0]
        date_str = args[1]
        
        # Start the add birthday workflow
        await birthday_manager.start_add_birthday_workflow(ctx, name, date_str)
    
    elif action == "list":
        await birthday_manager.list_upcoming_birthdays(ctx)
    
    elif action == "remove":
        if not args:
            await ctx.send("❌ Bitte gib den Namen der Person an. Beispiel: `!birthday remove Max`")
            return
        
        name = args[0]
        await birthday_manager.remove_birthday(ctx, name)

@bot.command(name="gift")
async def gift_command(ctx, action=None, *args):
    """Gift ideas management"""
    if ctx.channel.id != EVENT_CHANNEL_ID:
        return
    
    if not action:
        await ctx.send("❌ Bitte gib eine Aktion an: `idea`, `add`, oder `list`")
        return
    
    if action == "idea":
        if len(args) < 1:
            await ctx.send("❌ Bitte gib den Namen der Person an. Beispiel: `!gift idea Max`")
            return
        
        person = args[0]
        occasion = args[1] if len(args) > 1 else "Geburtstag"
        
        await gift_recommender.generate_gift_ideas(ctx, person, occasion)
    
    elif action == "add":
        if len(args) < 2:
            await ctx.send("❌ Bitte gib den Namen der Person und die Geschenkidee an. Beispiel: `!gift add Max Kopfhörer`")
            return
        
        person = args[0]
        idea = " ".join(args[1:])
        
        await gift_recommender.add_gift_idea(ctx, person, idea)
    
    elif action == "list":
        if not args:
            await ctx.send("❌ Bitte gib den Namen der Person an. Beispiel: `!gift list Max`")
            return
        
        person = args[0]
        await gift_recommender.list_gift_ideas(ctx, person)

@bot.command(name="event")
async def event_command(ctx, action=None, *args):
    """Event planning commands"""
    if ctx.channel.id != EVENT_CHANNEL_ID:
        return
    
    if not action:
        await ctx.send("❌ Bitte gib eine Aktion an: `create`, `list`, `details`, `invite`, oder `cancel`")
        return
    
    if action == "create":
        await event_planner.start_create_event_workflow(ctx)
    
    elif action == "list":
        await event_planner.list_upcoming_events(ctx)
    
    elif action == "details":
        if not args:
            await ctx.send("❌ Bitte gib die Event-ID an. Beispiel: `!event details 1234`")
            return
        
        event_id = args[0]
        await event_planner.show_event_details(ctx, event_id)
    
    elif action == "invite":
        if len(args) < 2:
            await ctx.send("❌ Bitte gib die Event-ID und die zu einladenden Personen an. Beispiel: `!event invite 1234 @Max @Lisa`")
            return
        
        event_id = args[0]
        invitees = ctx.message.mentions
        
        await event_planner.invite_to_event(ctx, event_id, invitees)
    
    elif action == "cancel":
        if not args:
            await ctx.send("❌ Bitte gib die Event-ID an. Beispiel: `!event cancel 1234`")
            return
        
        event_id = args[0]
        await event_planner.cancel_event(ctx, event_id)

@bot.command(name="schedule")
async def schedule_command(ctx, action=None, *args):
    """Meeting scheduling commands"""
    if ctx.channel.id != EVENT_CHANNEL_ID:
        return
    
    if not action:
        await ctx.send("❌ Bitte gib eine Aktion an: `meeting`, `check`, oder `sync`")
        return
    
    if action == "meeting":
        await meeting_scheduler.start_meeting_scheduling_workflow(ctx)
    
    elif action == "check":
        days = int(args[0]) if args and args[0].isdigit() else 7
        await meeting_scheduler.check_availability(ctx, days)
    
    elif action == "sync":
        await meeting_scheduler.sync_with_calendar(ctx)

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reactions for event RSVPs and other interactive elements"""
    if user.bot:
        return
    
    # Let the event planner handle event-related reactions
    await event_planner.handle_reaction(reaction, user)

@bot.event
async def on_message(message):
    """Handle messages for dialogs and workflows"""
    if message.author.bot:
        return
    
    # Check if user has an active workflow
    user_id = message.author.id
    if user_id in user_workflows:
        workflow = user_workflows[user_id]
        
        # Let the appropriate manager handle the workflow
        if workflow["type"] == "birthday_add":
            await birthday_manager.handle_birthday_workflow_step(message)
            return
        elif workflow["type"] == "event_create":
            await event_planner.handle_event_workflow_step(message)
            return
        elif workflow["type"] == "meeting_schedule":
            await meeting_scheduler.handle_meeting_workflow_step(message)
            return
    
    # Process commands if no active workflow
    await bot.process_commands(message)

async def send_help_message(ctx):
    """Send the help message with available commands"""
    help_text = """
🎉 **Social & Event Koordinator Bot - Hilfe**

**Geburtstage & Jubiläen:**
`!birthday add [Name] [Datum]` - Fügt einen Geburtstag hinzu
`!birthday list` - Zeigt anstehende Geburtstage
`!birthday remove [Name]` - Entfernt einen Geburtstag

**Geschenkideen:**
`!gift idea [Person] [Anlass]` - Generiert Geschenkideen
`!gift add [Person] [Idee]` - Speichert eine Geschenkidee
`!gift list [Person]` - Zeigt gespeicherte Geschenkideen

**Event-Planung:**
`!event create` - Startet die Event-Erstellung
`!event list` - Zeigt anstehende Events
`!event details [Event-ID]` - Zeigt Details zu einem Event
`!event invite [Event-ID] @User1 @User2...` - Lädt Benutzer zum Event ein
`!event cancel [Event-ID]` - Sagt ein Event ab

**Terminplanung:**
`!schedule meeting` - Startet die Terminplanung
`!schedule check [Tage]` - Prüft Verfügbarkeit für die nächsten X Tage
`!schedule sync` - Synchronisiert mit Google Kalender
"""
    await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN) 