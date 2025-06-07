import logging
import discord
import asyncio
import datetime
import pytz
import re
from dateutil.parser import parse

# Setup logging
logger = logging.getLogger("event_planner")

class EventPlanner:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        self.user_workflows = {}  # Will reference parent's user_workflows
        self.event_messages = {}  # Store event announcement messages for reactions
        logger.info("Event planner initialized")
    
    async def start_create_event_workflow(self, ctx):
        """Start the workflow to create a new event"""
        user_id = ctx.author.id
        
        # Get reference to the parent's user_workflows
        if not hasattr(self, 'user_workflows'):
            self.user_workflows = self.bot.get_cog('social_bot').user_workflows
        
        # Store workflow data
        self.user_workflows[user_id] = {
            "type": "event_create",
            "step": "name",
            "channel_id": ctx.channel.id,
            "data": {
                "organizer": ctx.author.name
            }
        }
        
        # Ask for event name
        await ctx.send("Wie soll das Event heißen?")
    
    async def handle_event_workflow_step(self, message):
        """Handle the steps in the event creation workflow"""
        user_id = message.author.id
        workflow = self.user_workflows.get(user_id)
        
        # Validate workflow
        if not workflow or workflow["type"] != "event_create":
            return
        
        # Process different steps
        if workflow["step"] == "name":
            # Store event name
            name = message.content.strip()
            if not name:
                await message.channel.send("Bitte gib einen gültigen Namen für das Event an.")
                return
            
            workflow["data"]["name"] = name
            workflow["step"] = "date"
            
            await message.channel.send(f"An welchem Datum soll **{name}** stattfinden? (Format: TT.MM.YYYY)")
        
        elif workflow["step"] == "date":
            # Parse the date
            try:
                date_str = message.content.strip()
                event_date = self._parse_date(date_str)
                
                workflow["data"]["date"] = event_date
                workflow["step"] = "time"
                
                await message.channel.send("Um wie viel Uhr? (Format: HH:MM oder 'ganztägig')")
            
            except ValueError:
                await message.channel.send("❌ Bitte gib ein gültiges Datum an (Format: TT.MM.YYYY).")
        
        elif workflow["step"] == "time":
            # Store time
            time_str = message.content.strip()
            
            if time_str.lower() == "ganztägig":
                workflow["data"]["time"] = "ganztägig"
            else:
                # Validate time format
                if not re.match(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$", time_str):
                    await message.channel.send("❌ Bitte gib eine gültige Uhrzeit im Format HH:MM an.")
                    return
                
                workflow["data"]["time"] = time_str
            
            workflow["step"] = "location"
            
            await message.channel.send("Wo findet das Event statt?")
        
        elif workflow["step"] == "location":
            # Store location
            location = message.content.strip()
            workflow["data"]["location"] = location
            
            workflow["step"] = "description"
            
            await message.channel.send("Füge eine Beschreibung hinzu (oder 'keine'):")
        
        elif workflow["step"] == "description":
            # Store description
            description = message.content.strip()
            if description.lower() != "keine":
                workflow["data"]["description"] = description
            
            # Complete the workflow
            await self._complete_event_workflow(message.channel, user_id)
    
    async def _complete_event_workflow(self, channel, user_id):
        """Complete the event creation workflow"""
        workflow = self.user_workflows.get(user_id)
        
        try:
            # Add to Notion
            event_id = self.notion_manager.add_event(
                name=workflow["data"]["name"],
                date=workflow["data"]["date"],
                time=workflow["data"].get("time"),
                location=workflow["data"].get("location"),
                description=workflow["data"].get("description"),
                organizer=workflow["data"].get("organizer")
            )
            
            if event_id:
                # Format date
                date_str = workflow["data"]["date"].strftime("%d.%m.%Y")
                
                # Format time
                time_str = workflow["data"].get("time", "")
                if time_str:
                    time_str = f" um {time_str} Uhr"
                
                # Format location
                location_str = workflow["data"].get("location", "")
                if location_str:
                    location_str = f" @ {location_str}"
                
                # Prepare announcement message
                message = f"""
🎉 **Neues Event: {workflow["data"]["name"]}**
📅 {date_str}{time_str}{location_str}
👤 Organisiert von: {workflow["data"].get("organizer", "Unbekannt")}
"""

                if workflow["data"].get("description"):
                    message += f"📝 {workflow['data']['description']}\n"
                
                message += "\nReagiere mit ✅ um teilzunehmen, und mit ❓ für vielleicht."
                
                # Send announcement
                event_message = await channel.send(message)
                
                # Add reactions for RSVP
                await event_message.add_reaction("✅")
                await event_message.add_reaction("❓")
                
                # Store message ID for reaction handling
                self.event_messages[event_message.id] = {
                    "event_id": event_id,
                    "name": workflow["data"]["name"]
                }
                
                # Confirmation
                await channel.send(f"✅ Event wurde erstellt! Event-ID: `{event_id}`")
            else:
                await channel.send("❌ Es ist ein Fehler beim Erstellen des Events aufgetreten.")
        
        except Exception as e:
            logger.error(f"Error completing event workflow: {str(e)}")
            await channel.send("❌ Es ist ein Fehler aufgetreten. Bitte versuche es erneut.")
        
        # Remove workflow
        if user_id in self.user_workflows:
            del self.user_workflows[user_id]
    
    async def list_upcoming_events(self, ctx, days=30):
        """List upcoming events"""
        upcoming = self.notion_manager.get_upcoming_events(days=days)
        
        if not upcoming:
            await ctx.send(f"Keine anstehenden Events in den nächsten {days} Tagen.")
            return
        
        # Prepare message
        today = datetime.datetime.now().date()
        message = f"📅 **Anstehende Events (nächste {days} Tage)**\n\n"
        
        for event in upcoming:
            # Calculate days until
            days_until = (event["date"] - today).days
            
            # Display days
            if days_until == 0:
                days_text = "**HEUTE!** 🎉"
            elif days_until == 1:
                days_text = "**MORGEN!** 📌"
            else:
                days_text = f"in {days_until} Tagen"
            
            # Format time
            time_text = f" um {event['time']} Uhr" if event.get('time') else ""
            
            # Format location
            location_text = f" @ {event['location']}" if event.get('location') else ""
            
            message += f"• **{event['name']}** {days_text}: {event['date'].strftime('%d.%m.%Y')}{time_text}{location_text}\n"
            message += f"  ID: `{event['id']}` | Status: {event['status']}\n"
        
        await ctx.send(message)
    
    async def show_event_details(self, ctx, event_id):
        """Show details of a specific event"""
        event = self.notion_manager.get_event(event_id)
        
        if not event:
            await ctx.send(f"❌ Kein Event mit der ID '{event_id}' gefunden.")
            return
        
        # Prepare message
        message = f"""
📌 **Event: {event['name']}**
📅 {event['date'].strftime('%d.%m.%Y')}
"""
        
        if event.get('time'):
            message += f"🕒 {event['time']} Uhr\n"
        
        if event.get('location'):
            message += f"📍 {event['location']}\n"
        
        if event.get('description'):
            message += f"📝 {event['description']}\n"
        
        if event.get('organizer'):
            message += f"👤 Organisiert von: {event['organizer']}\n"
        
        message += f"🏷️ Status: {event['status']}\n"
        
        # TODO: Add participants when relational data is fully implemented
        
        await ctx.send(message)
    
    async def invite_to_event(self, ctx, event_id, invitees):
        """Invite users to an event"""
        event = self.notion_manager.get_event(event_id)
        
        if not event:
            await ctx.send(f"❌ Kein Event mit der ID '{event_id}' gefunden.")
            return
        
        if not invitees:
            await ctx.send("❌ Keine Benutzer zum Einladen angegeben.")
            return
        
        # Prepare invitation message
        invite_message = f"""
📨 **Event-Einladung: {event['name']}**
📅 {event['date'].strftime('%d.%m.%Y')}
"""
        
        if event.get('time'):
            invite_message += f"🕒 {event['time']} Uhr\n"
        
        if event.get('location'):
            invite_message += f"📍 {event['location']}\n"
        
        invite_message += f"\nBitte reagiere mit ✅ für Zusage, ❓ für vielleicht, oder ❌ für Absage."
        
        # Send invitation to each user
        success_count = 0
        fail_count = 0
        
        for user in invitees:
            try:
                dm_channel = await user.create_dm()
                invite_msg = await dm_channel.send(invite_message)
                
                # Add reaction options
                await invite_msg.add_reaction("✅")
                await invite_msg.add_reaction("❓")
                await invite_msg.add_reaction("❌")
                
                # Store message for reaction tracking (would need additional handling)
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error sending invitation to {user.name}: {str(e)}")
                fail_count += 1
        
        # Confirmation message
        if success_count > 0:
            await ctx.send(f"✅ {success_count} Einladungen wurden versendet!")
        
        if fail_count > 0:
            await ctx.send(f"⚠️ {fail_count} Einladungen konnten nicht versendet werden.")
    
    async def cancel_event(self, ctx, event_id):
        """Cancel an event"""
        event = self.notion_manager.get_event(event_id)
        
        if not event:
            await ctx.send(f"❌ Kein Event mit der ID '{event_id}' gefunden.")
            return
        
        # Confirm cancellation
        confirmation_msg = await ctx.send(f"Möchtest du das Event '{event['name']}' wirklich absagen? Reagiere mit ✅ zum Bestätigen oder ❌ zum Abbrechen.")
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirmation_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == "✅":
                success = self.notion_manager.cancel_event(event_id)
                
                if success:
                    await ctx.send(f"✅ Event '{event['name']}' wurde abgesagt.")
                    
                    # Notify channel
                    cancel_message = f"🚫 **Event abgesagt: {event['name']}** (war geplant für {event['date'].strftime('%d.%m.%Y')})"
                    await ctx.send(cancel_message)
                    
                else:
                    await ctx.send("❌ Es ist ein Fehler beim Absagen des Events aufgetreten.")
            
            else:
                await ctx.send("❌ Absage abgebrochen.")
        
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Zeit abgelaufen. Absage abgebrochen.")
    
    async def handle_reaction(self, reaction, user):
        """Handle reactions to event messages (RSVPs)"""
        # Check if this is an event message we're tracking
        if reaction.message.id not in self.event_messages:
            return
        
        # Get event info
        event_info = self.event_messages[reaction.message.id]
        event_id = event_info["event_id"]
        event_name = event_info["name"]
        
        # Handle response
        emoji = str(reaction.emoji)
        
        if emoji == "✅":
            # User is attending
            response = "attending"
            status_text = "nimmt teil"
        elif emoji == "❓":
            # User is tentative
            response = "tentative"
            status_text = "nimmt vielleicht teil"
        else:
            # Not a tracked reaction
            return
        
        # Here we would update the participants list in Notion
        # This would require additional Notion API implementation to handle relations
        
        # Log the response
        logger.info(f"User {user.name} RSVP'd {response} to event {event_name}")
        
        # Send a DM confirmation to the user
        try:
            dm_channel = await user.create_dm()
            await dm_channel.send(f"✅ Deine Antwort wurde gespeichert! Du {status_text} am Event **{event_name}**.")
        except Exception as e:
            logger.error(f"Error sending confirmation DM: {str(e)}")
    
    async def check_upcoming_events(self):
        """Check for upcoming events and send reminders"""
        try:
            channel_id = int(self.bot.get_cog('social_bot').EVENT_CHANNEL_ID)
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error("Event channel not found for event reminders")
                return
            
            today = datetime.datetime.now().date()
            
            # Check for events today
            todays_events = self.notion_manager.get_events_by_date(today)
            
            if todays_events:
                message = "📌 **Heutige Events:** 📌\n\n"
                
                for event in todays_events:
                    time_text = f" um {event['time']} Uhr" if event.get('time') else ""
                    location_text = f" @ {event['location']}" if event.get('location') else ""
                    
                    message += f"• **{event['name']}**{time_text}{location_text}\n"
                    
                    if event.get('description'):
                        message += f"  📝 {event['description']}\n"
                
                await channel.send(message)
            
            # Check for events tomorrow
            tomorrow = today + datetime.timedelta(days=1)
            tomorrows_events = self.notion_manager.get_events_by_date(tomorrow)
            
            if tomorrows_events:
                message = "🔔 **Morgige Events:** 🔔\n\n"
                
                for event in tomorrows_events:
                    time_text = f" um {event['time']} Uhr" if event.get('time') else ""
                    location_text = f" @ {event['location']}" if event.get('location') else ""
                    
                    message += f"• **{event['name']}**{time_text}{location_text}\n"
                
                await channel.send(message)
        
        except Exception as e:
            logger.error(f"Error checking upcoming events: {str(e)}")
    
    def get_events_for_date(self, date):
        """Get events for a specific date (wrapper for notion_manager)"""
        return self.notion_manager.get_events_by_date(date)
    
    def get_upcoming_events(self, days=30):
        """Get upcoming events (wrapper for notion_manager)"""
        return self.notion_manager.get_upcoming_events(days=days)
    
    def _parse_date(self, date_str):
        """Parse a date string in various formats"""
        # Try to parse with dateutil
        try:
            date = parse(date_str, dayfirst=True)
            return date.date()
        except ValueError:
            pass
        
        # Try common German formats
        formats = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',    # DD-MM-YYYY
            r'(\d{1,2})\/(\d{1,2})\/(\d{4})'   # DD/MM/YYYY
        ]
        
        for format_pattern in formats:
            match = re.match(format_pattern, date_str)
            if match:
                groups = match.groups()
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                return datetime.date(year, month, day)
        
        # If nothing worked, raise error
        raise ValueError("Invalid date format") 