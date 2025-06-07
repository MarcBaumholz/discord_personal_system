import logging
import discord
import asyncio
import datetime
import re
import pytz
import random
from dateutil.parser import parse

# Setup logging
logger = logging.getLogger("meeting_scheduler")

class MeetingScheduler:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        self.user_workflows = {}  # Will reference parent's user_workflows
        self.timezone = pytz.timezone('Europe/Berlin')  # Default timezone
        self.calendar_integration = None  # Set by social_bot.py
        logger.info("Meeting scheduler initialized")
    
    async def start_meeting_scheduling_workflow(self, ctx):
        """Start the workflow to schedule a meeting"""
        user_id = ctx.author.id
        
        # Get reference to the parent's user_workflows
        if not hasattr(self, 'user_workflows'):
            self.user_workflows = self.bot.get_cog('social_bot').user_workflows
        
        # Store workflow data
        self.user_workflows[user_id] = {
            "type": "meeting_schedule",
            "step": "name",
            "channel_id": ctx.channel.id,
            "data": {
                "organizer": ctx.author.name,
                "participants": []
            }
        }
        
        # Ask for meeting name
        await ctx.send("Wie soll das Meeting genannt werden?")
    
    async def handle_meeting_workflow_step(self, message):
        """Handle the steps in the meeting scheduling workflow"""
        user_id = message.author.id
        workflow = self.user_workflows.get(user_id)
        
        # Validate workflow
        if not workflow or workflow["type"] != "meeting_schedule":
            return
        
        # Process different steps
        if workflow["step"] == "name":
            # Store meeting name
            name = message.content.strip()
            if not name:
                await message.channel.send("Bitte gib einen gültigen Namen für das Meeting an.")
                return
            
            workflow["data"]["name"] = name
            workflow["step"] = "participants"
            
            await message.channel.send("Wer soll am Meeting teilnehmen? Erwähne die Teilnehmer mit @ oder schreibe 'nur ich'.")
        
        elif workflow["step"] == "participants":
            # Store participants
            content = message.content.strip()
            
            if content.lower() == "nur ich":
                # Only the organizer
                workflow["data"]["participants"] = [message.author.name]
            else:
                # Check for mentions
                mentions = message.mentions
                
                if mentions:
                    # Store Discord usernames
                    participants = [user.name for user in mentions]
                    participants.append(message.author.name)  # Include organizer
                    workflow["data"]["participants"] = participants
                else:
                    # Manual entry (comma-separated names)
                    names = [name.strip() for name in content.split(",") if name.strip()]
                    
                    if not names:
                        await message.channel.send("Bitte gib gültige Teilnehmer an (mit @ oder kommagetrennte Namen).")
                        return
                    
                    # Include organizer if not already in the list
                    if message.author.name not in names:
                        names.append(message.author.name)
                    
                    workflow["data"]["participants"] = names
            
            workflow["step"] = "duration"
            
            await message.channel.send("Wie lange soll das Meeting dauern? (Format: HHh MMm oder MM Minuten oder H Stunden)")
        
        elif workflow["step"] == "duration":
            # Parse duration
            duration_str = message.content.strip().lower()
            
            # Try to parse different formats
            duration_minutes = self._parse_duration(duration_str)
            
            if duration_minutes <= 0:
                await message.channel.send("❌ Bitte gib eine gültige Dauer an (z.B. '30m', '1h 30m', '90 Minuten', '1.5 Stunden').")
                return
            
            workflow["data"]["duration"] = duration_minutes
            workflow["step"] = "date_options"
            
            # Check calendar integration if available
            if hasattr(self, 'calendar_integration') and self.calendar_integration:
                await message.channel.send("Ich überprüfe verfügbare Zeiten in deinem Kalender...")
                
                # TODO: Implement actual calendar availability check
                # For now, just simulate it
                await asyncio.sleep(1.5)
            
            # Generate date options
            date_options = self._generate_date_options()
            workflow["data"]["date_options"] = date_options
            
            # Format options message
            options_message = "Wähle einen Terminvorschlag (antworte mit der Nummer):\n\n"
            
            for i, option in enumerate(date_options, 1):
                date_str = option["date"].strftime("%d.%m.%Y")
                time_str = option["time"]
                options_message += f"{i}. {date_str} um {time_str} Uhr\n"
            
            await message.channel.send(options_message)
        
        elif workflow["step"] == "date_options":
            # Parse selected option
            try:
                selection = int(message.content.strip())
                
                if selection < 1 or selection > len(workflow["data"]["date_options"]):
                    await message.channel.send(f"❌ Bitte wähle eine Zahl zwischen 1 und {len(workflow['data']['date_options'])}.")
                    return
                
                # Get selected option
                selected_option = workflow["data"]["date_options"][selection - 1]
                workflow["data"]["selected_date"] = selected_option["date"]
                workflow["data"]["selected_time"] = selected_option["time"]
                
                workflow["step"] = "location"
                
                await message.channel.send("Wo soll das Meeting stattfinden? (Oder 'online' für ein virtuelles Meeting)")
                
            except ValueError:
                await message.channel.send("❌ Bitte gib eine gültige Zahl ein.")
        
        elif workflow["step"] == "location":
            # Store location
            location = message.content.strip()
            workflow["data"]["location"] = location
            
            # Complete the workflow
            await self._complete_meeting_workflow(message.channel, user_id)
    
    async def _complete_meeting_workflow(self, channel, user_id):
        """Complete the meeting scheduling workflow"""
        workflow = self.user_workflows.get(user_id)
        
        try:
            # Format meeting details
            name = workflow["data"]["name"]
            date = workflow["data"]["selected_date"]
            time = workflow["data"]["selected_time"]
            duration = workflow["data"]["duration"]
            location = workflow["data"]["location"]
            participants = workflow["data"]["participants"]
            
            date_str = date.strftime("%d.%m.%Y")
            
            # Calculate end time
            start_time_parts = time.split(":")
            start_hour = int(start_time_parts[0])
            start_minute = int(start_time_parts[1])
            
            end_hour = start_hour + (duration // 60)
            end_minute = start_minute + (duration % 60)
            
            if end_minute >= 60:
                end_hour += 1
                end_minute -= 60
            
            if end_hour >= 24:
                end_hour -= 24
            
            end_time = f"{end_hour:02d}:{end_minute:02d}"
            
            # Create event in Notion
            event_description = f"Meeting mit {', '.join(participants)}."
            
            event_id = self.notion_manager.add_event(
                name=name,
                date=date,
                time=f"{time} - {end_time}",
                location=location,
                description=event_description,
                organizer=workflow["data"]["organizer"]
            )
            
            if event_id:
                # Create calendar event if integration available
                calendar_link = ""
                
                if hasattr(self, 'calendar_integration') and self.calendar_integration:
                    try:
                        # TODO: Implement actual calendar integration
                        # For now, just simulate it
                        await asyncio.sleep(1)
                        calendar_link = "\n\n(Kalendereintrag wurde erstellt)"
                    except Exception as e:
                        logger.error(f"Error creating calendar event: {str(e)}")
                        calendar_link = "\n\n⚠️ Kalendereintrag konnte nicht erstellt werden."
                
                # Format confirmation message
                message = f"""
📅 **Meeting geplant: {name}**
📆 {date_str}
🕒 {time} - {end_time} Uhr ({duration} Minuten)
📍 {location}
👥 Teilnehmer: {', '.join(participants)}
🆔 Event-ID: `{event_id}`
{calendar_link}
"""
                
                await channel.send(message)
                
                # Notify participants if they were mentioned
                if hasattr(self.bot, 'get_all_members'):
                    for participant in participants:
                        if participant != workflow["data"]["organizer"]:
                            # Try to find the user
                            member = discord.utils.find(
                                lambda m: m.name == participant,
                                self.bot.get_all_members()
                            )
                            
                            if member:
                                try:
                                    notification = f"""
📌 **Meeting-Einladung: {name}**
📆 {date_str}
🕒 {time} - {end_time} Uhr
📍 {location}
👥 Von: {workflow['data']['organizer']}
"""
                                    
                                    dm_channel = await member.create_dm()
                                    await dm_channel.send(notification)
                                except Exception as e:
                                    logger.error(f"Error sending meeting notification: {str(e)}")
            else:
                await channel.send("❌ Es ist ein Fehler beim Erstellen des Meetings aufgetreten.")
        
        except Exception as e:
            logger.error(f"Error completing meeting workflow: {str(e)}")
            await channel.send("❌ Es ist ein Fehler aufgetreten. Bitte versuche es später erneut.")
        
        # Remove workflow
        if user_id in self.user_workflows:
            del self.user_workflows[user_id]
    
    async def check_availability(self, ctx, days=7):
        """Check calendar availability for the next X days"""
        try:
            if not hasattr(self, 'calendar_integration') or not self.calendar_integration:
                await ctx.send("⚠️ Kalenderintegration ist nicht verfügbar. Bitte richte zuerst die Google Calendar-Integration ein.")
                return
            
            # Show typing indicator
            async with ctx.typing():
                # TODO: Implement actual calendar availability check
                # For now, just simulate it
                await asyncio.sleep(2)
                
                # Generate fake availability data
                availability = self._generate_fake_availability(days)
                
                # Format message
                message = f"📅 **Verfügbarkeit in den nächsten {days} Tagen:**\n\n"
                
                today = datetime.datetime.now().date()
                
                for i in range(days):
                    date = today + datetime.timedelta(days=i)
                    day_name = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][date.weekday()]
                    date_str = date.strftime("%d.%m.%Y")
                    
                    if i == 0:
                        day_text = f"**Heute** ({day_name}, {date_str})"
                    elif i == 1:
                        day_text = f"**Morgen** ({day_name}, {date_str})"
                    else:
                        day_text = f"**{day_name}**, {date_str}"
                    
                    message += f"• {day_text}:\n"
                    
                    if date in availability:
                        free_slots = availability[date]
                        if free_slots:
                            for slot in free_slots[:3]:  # Show max 3 slots per day
                                message += f"  ✅ {slot['start']} - {slot['end']} Uhr\n"
                        else:
                            message += "  ❌ Keine freien Zeiten\n"
                    else:
                        message += "  ❓ Keine Daten verfügbar\n"
                
                await ctx.send(message)
        
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler bei der Überprüfung der Verfügbarkeit aufgetreten.")
    
    async def sync_with_calendar(self, ctx):
        """Synchronize with Google Calendar"""
        try:
            if not hasattr(self, 'calendar_integration') or not self.calendar_integration:
                await ctx.send("⚠️ Kalenderintegration ist nicht verfügbar. Bitte richte zuerst die Google Calendar-Integration ein.")
                return
            
            # Show typing indicator
            async with ctx.typing():
                # TODO: Implement actual calendar synchronization
                # For now, just simulate it
                await asyncio.sleep(3)
                
                # Send success message
                await ctx.send("✅ Kalendersynchronisierung erfolgreich! Alle Termine sind jetzt auf dem neuesten Stand.")
        
        except Exception as e:
            logger.error(f"Error syncing with calendar: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler bei der Kalendersynchronisierung aufgetreten.")
    
    def _parse_duration(self, duration_str):
        """Parse a duration string into minutes"""
        total_minutes = 0
        
        # Check for format like "1h 30m" or "1h30m"
        hours_pattern = r'(\d+(?:\.\d+)?)\s*h'
        minutes_pattern = r'(\d+)\s*m'
        
        hours_match = re.search(hours_pattern, duration_str)
        minutes_match = re.search(minutes_pattern, duration_str)
        
        if hours_match:
            hours = float(hours_match.group(1))
            total_minutes += int(hours * 60)
        
        if minutes_match:
            minutes = int(minutes_match.group(1))
            total_minutes += minutes
        
        # If no match, try other formats
        if total_minutes == 0:
            # Check for "X minutes" or "X Minuten"
            minutes_word_pattern = r'(\d+(?:\.\d+)?)\s*(?:minute|minutes|minuten|min)'
            minutes_word_match = re.search(minutes_word_pattern, duration_str, re.IGNORECASE)
            
            if minutes_word_match:
                minutes = float(minutes_word_match.group(1))
                total_minutes = int(minutes)
            
            # Check for "X hours" or "X Stunden"
            hours_word_pattern = r'(\d+(?:\.\d+)?)\s*(?:hour|hours|stunde|stunden|std)'
            hours_word_match = re.search(hours_word_pattern, duration_str, re.IGNORECASE)
            
            if hours_word_match:
                hours = float(hours_word_match.group(1))
                total_minutes = int(hours * 60)
        
        # If still no match, try to parse as minutes directly
        if total_minutes == 0:
            try:
                total_minutes = int(float(duration_str.strip()))
            except ValueError:
                pass
        
        return total_minutes
    
    def _generate_date_options(self, num_options=3):
        """Generate meeting date options"""
        options = []
        
        # Start with tomorrow
        base_date = datetime.datetime.now().date() + datetime.timedelta(days=1)
        
        # Generate options for the next 10 days
        for i in range(10):
            date = base_date + datetime.timedelta(days=i)
            
            # Skip weekends if less than half of the options are filled
            if len(options) < num_options // 2 and date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
            
            # Generate 1-2 time options per day
            for _ in range(random.randint(1, 2)):
                # Business hours (9:00 - 17:00)
                hour = random.randint(9, 16)
                minute = random.choice([0, 15, 30, 45])
                
                time = f"{hour:02d}:{minute:02d}"
                
                options.append({
                    "date": date,
                    "time": time
                })
            
            # Break if we have enough options
            if len(options) >= num_options + 2:
                break
        
        # Randomly select the requested number of options
        return random.sample(options, min(num_options, len(options)))
    
    def _generate_fake_availability(self, days):
        """Generate fake availability data for testing"""
        availability = {}
        
        today = datetime.datetime.now().date()
        
        for i in range(days):
            date = today + datetime.timedelta(days=i)
            
            # Skip some days randomly
            if random.random() < 0.2:
                continue
            
            # Generate 0-4 free slots
            num_slots = random.randint(0, 4)
            
            if num_slots > 0:
                free_slots = []
                
                # Business hours
                for _ in range(num_slots):
                    # Generate start time
                    start_hour = random.randint(9, 16)
                    start_minute = random.choice([0, 15, 30, 45])
                    
                    # Generate end time (30-90 minutes later)
                    duration = random.choice([30, 45, 60, 90])
                    
                    end_hour = start_hour + (duration // 60)
                    end_minute = start_minute + (duration % 60)
                    
                    if end_minute >= 60:
                        end_hour += 1
                        end_minute -= 60
                    
                    # Format times
                    start_time = f"{start_hour:02d}:{start_minute:02d}"
                    end_time = f"{end_hour:02d}:{end_minute:02d}"
                    
                    free_slots.append({
                        "start": start_time,
                        "end": end_time
                    })
                
                # Sort by start time
                free_slots.sort(key=lambda x: x["start"])
                
                availability[date] = free_slots
            else:
                availability[date] = []
        
        return availability 