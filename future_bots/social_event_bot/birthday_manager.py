import logging
import discord
import asyncio
import datetime
import re
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

# Setup logging
logger = logging.getLogger("birthday_manager")

class BirthdayManager:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        self.user_workflows = self.bot.get_cog('social_bot').user_workflows
        logger.info("Birthday manager initialized")
    
    async def start_add_birthday_workflow(self, ctx, name, date_str):
        """Start the workflow to add a birthday"""
        user_id = ctx.author.id
        
        # Parse the date
        try:
            birth_date = self._parse_date(date_str)
            
            # Store workflow data
            self.user_workflows[user_id] = {
                "type": "birthday_add",
                "name": name,
                "birth_date": birth_date,
                "step": "relation",
                "channel_id": ctx.channel.id,
                "data": {}
            }
            
            # Ask for relationship
            await ctx.send(f"In welcher Beziehung stehst du zu {name}? (Familie, Freund, Kollege, Andere)")
        
        except ValueError:
            await ctx.send("❌ Bitte gib ein gültiges Datum an (Format: TT.MM.YYYY oder TT.MM).")
    
    async def handle_birthday_workflow_step(self, message):
        """Handle the steps in the birthday addition workflow"""
        user_id = message.author.id
        workflow = self.user_workflows.get(user_id)
        
        # Validate workflow
        if not workflow or workflow["type"] != "birthday_add":
            return
        
        # Process different steps
        if workflow["step"] == "relation":
            # Store relation
            relation = message.content.strip()
            if relation.lower() not in ["familie", "freund", "kollege", "andere"]:
                await message.channel.send("Bitte wähle eine der folgenden Optionen: Familie, Freund, Kollege, Andere")
                return
            
            workflow["data"]["relation"] = relation.capitalize()
            workflow["step"] = "notes"
            
            await message.channel.send(f"Möchtest du Notizen zu {workflow['name']} hinzufügen? (Schreibe die Notizen oder 'nein')")
        
        elif workflow["step"] == "notes":
            # Store notes
            notes = message.content.strip()
            if notes.lower() != "nein":
                workflow["data"]["notes"] = notes
            
            workflow["step"] = "gift_ideas"
            
            await message.channel.send(f"Hast du Geschenkideen für {workflow['name']}? (Schreibe die Ideen oder 'nein')")
        
        elif workflow["step"] == "gift_ideas":
            # Store gift ideas
            gift_ideas = message.content.strip()
            if gift_ideas.lower() != "nein":
                workflow["data"]["gift_ideas"] = gift_ideas
            
            # Complete the workflow
            await self._complete_birthday_workflow(message.channel, user_id)
    
    async def _complete_birthday_workflow(self, channel, user_id):
        """Complete the birthday addition workflow"""
        workflow = self.user_workflows.get(user_id)
        
        try:
            # Add to Notion
            success = self.notion_manager.add_birthday(
                workflow["name"],
                workflow["birth_date"],
                relation=workflow["data"].get("relation"),
                notes=workflow["data"].get("notes"),
                gift_ideas=workflow["data"].get("gift_ideas")
            )
            
            if success:
                # Calculate age if full birth date was provided
                age_text = ""
                if workflow["birth_date"].year != 1900:
                    age = relativedelta(datetime.datetime.now(), workflow["birth_date"]).years
                    age_text = f" ({age} Jahre alt)"
                
                # Format date
                date_str = workflow["birth_date"].strftime("%d.%m.")
                if workflow["birth_date"].year != 1900:
                    date_str = workflow["birth_date"].strftime("%d.%m.%Y")
                
                await channel.send(f"✅ Geburtstag von {workflow['name']} am {date_str}{age_text} wurde hinzugefügt!")
            else:
                await channel.send("❌ Es ist ein Fehler beim Speichern des Geburtstags aufgetreten. Bitte versuche es später erneut.")
        
        except Exception as e:
            logger.error(f"Error completing birthday workflow: {str(e)}")
            await channel.send("❌ Es ist ein Fehler aufgetreten. Bitte versuche es erneut.")
        
        # Remove workflow
        if user_id in self.user_workflows:
            del self.user_workflows[user_id]
    
    async def list_upcoming_birthdays(self, ctx, days=30):
        """List upcoming birthdays"""
        upcoming = self.notion_manager.get_upcoming_birthdays(days=days)
        
        if not upcoming:
            await ctx.send(f"Keine anstehenden Geburtstage in den nächsten {days} Tagen.")
            return
        
        # Prepare message
        today = datetime.datetime.now().date()
        message = f"🎂 **Anstehende Geburtstage (nächste {days} Tage)**\n\n"
        
        for birthday in upcoming:
            # Get this year's birthday
            this_year = datetime.datetime(
                today.year if birthday["date"].month > today.month or 
                (birthday["date"].month == today.month and birthday["date"].day >= today.day) 
                else today.year + 1,
                birthday["date"].month,
                birthday["date"].day
            ).date()
            
            # Calculate days until
            days_until = (this_year - today).days
            
            # Display days
            if days_until == 0:
                days_text = "**HEUTE!** 🎉"
            elif days_until == 1:
                days_text = "**MORGEN!** 🎂"
            else:
                days_text = f"in {days_until} Tagen"
            
            # Calculate age if birth year is known
            age_text = ""
            if birthday["birth_year"] != 1900:
                current_age = today.year - birthday["birth_year"]
                birthday_age = current_age if this_year > today else current_age + 1
                age_text = f" ({birthday_age}. Geburtstag)"
            
            # Add relation if available
            relation_text = f" - {birthday['relation']}" if birthday['relation'] else ""
            
            message += f"• **{birthday['name']}** {days_text}: {birthday['date'].strftime('%d.%m.')}{age_text}{relation_text}\n"
        
        await ctx.send(message)
    
    async def remove_birthday(self, ctx, name):
        """Remove a birthday entry by name"""
        # Try to get the birthday
        birthday = self.notion_manager.get_birthday(name)
        
        if not birthday:
            await ctx.send(f"❌ Kein Geburtstag für '{name}' gefunden.")
            return
        
        # Confirm deletion
        confirmation_msg = await ctx.send(f"Möchtest du den Geburtstag von {name} wirklich löschen? Reagiere mit ✅ zum Bestätigen oder ❌ zum Abbrechen.")
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirmation_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == "✅":
                success = self.notion_manager.remove_birthday(name)
                
                if success:
                    await ctx.send(f"✅ Geburtstag von {name} wurde gelöscht.")
                else:
                    await ctx.send("❌ Es ist ein Fehler beim Löschen des Geburtstags aufgetreten.")
            
            else:
                await ctx.send("❌ Löschung abgebrochen.")
        
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Zeit abgelaufen. Löschung abgebrochen.")
    
    async def check_upcoming_birthdays(self):
        """Check for upcoming birthdays and send reminders"""
        try:
            channel = self.bot.get_channel(int(self.bot.get_cog('social_bot').EVENT_CHANNEL_ID))
            if not channel:
                logger.error("Event channel not found for birthday reminders")
                return
            
            today = datetime.datetime.now().date()
            
            # Check for today's birthdays
            todays_birthdays = self.notion_manager.get_birthdays_by_date(today)
            if todays_birthdays:
                message = "🎂 **Heutige Geburtstage!** 🎉\n\n"
                
                for birthday in todays_birthdays:
                    # Calculate age if birth year is known
                    age_text = ""
                    if birthday["birth_year"] != 1900:
                        age = today.year - birthday["birth_year"]
                        age_text = f" ({age}. Geburtstag)"
                    
                    message += f"• **{birthday['name']}**{age_text}\n"
                
                await channel.send(message)
            
            # Check for birthdays in 3 days
            in_three_days = today + datetime.timedelta(days=3)
            upcoming_birthdays = self.notion_manager.get_birthdays_by_date(in_three_days)
            
            if upcoming_birthdays:
                message = "🔔 **Geburtstage in 3 Tagen:**\n\n"
                
                for birthday in upcoming_birthdays:
                    # Calculate age if birth year is known
                    age_text = ""
                    if birthday["birth_year"] != 1900:
                        age = in_three_days.year - birthday["birth_year"]
                        age_text = f" ({age}. Geburtstag)"
                    
                    message += f"• **{birthday['name']}**{age_text}\n"
                    
                    # Add gift ideas if available
                    if birthday["gift_ideas"]:
                        message += f"  💡 Geschenkideen: {birthday['gift_ideas']}\n"
                
                await channel.send(message)
            
            # Check for birthdays in a week
            in_a_week = today + datetime.timedelta(days=7)
            week_birthdays = self.notion_manager.get_birthdays_by_date(in_a_week)
            
            if week_birthdays:
                message = "📅 **Geburtstage in einer Woche:**\n\n"
                
                for birthday in week_birthdays:
                    message += f"• **{birthday['name']}** am {in_a_week.strftime('%d.%m.')}\n"
                
                await channel.send(message)
        
        except Exception as e:
            logger.error(f"Error checking upcoming birthdays: {str(e)}")
    
    def get_birthdays_for_date(self, date):
        """Get birthdays for a specific date (wrapper for notion_manager)"""
        return self.notion_manager.get_birthdays_by_date(date)
    
    def get_upcoming_birthdays(self, days=30):
        """Get upcoming birthdays (wrapper for notion_manager)"""
        return self.notion_manager.get_upcoming_birthdays(days=days)
    
    def _parse_date(self, date_str):
        """Parse a date string in various formats"""
        # Try to parse with dateutil
        try:
            # Try to parse complete date (with year)
            date = parse(date_str, dayfirst=True)
            return date.date()
        except ValueError:
            pass
        
        # Try common German formats
        formats = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',    # DD-MM-YYYY
            r'(\d{1,2})\/(\d{1,2})\/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})\.(\d{1,2})\.',         # DD.MM.
            r'(\d{1,2})-(\d{1,2})',            # DD-MM
            r'(\d{1,2})\/(\d{1,2})'            # DD/MM
        ]
        
        for format_pattern in formats:
            match = re.match(format_pattern, date_str)
            if match:
                groups = match.groups()
                
                if len(groups) == 3:  # With year
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                    return datetime.date(year, month, day)
                elif len(groups) == 2:  # Without year
                    day, month = int(groups[0]), int(groups[1])
                    # Use a placeholder year
                    return datetime.date(1900, month, day)
        
        # If nothing worked, raise error
        raise ValueError("Invalid date format") 