import logging
import discord
import asyncio
import datetime
import re
import pytz
import os
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger("medication_reminder")

class MedicationReminder:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        self.reminders = {}  # Store active reminders - format: {user_id: {med_name: reminder_obj}}
        self.channel_id = int(os.getenv('CHANNEL_ID'))
        logger.info("Medication reminder module initialized")
        
        # Start the reminder checker
        self.bot.loop.create_task(self.check_reminders())
    
    async def handle_medication(self, ctx, action, args):
        """Handle medication tracking and reminders"""
        if not args:
            await ctx.send("❌ Bitte gib den Namen des Medikaments an.")
            return
        
        if action == "track":
            await self.track_medication(ctx, " ".join(args))
        elif action == "remind":
            if len(args) < 2:
                await ctx.send("❌ Bitte gib das Medikament und die Zeit an. Beispiel: `!med remind Vitamin D 09:00`")
                return
            
            med_name = " ".join(args[:-1])
            time_str = args[-1]
            
            # Validate time format
            if not re.match(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$", time_str):
                await ctx.send("❌ Bitte gib die Zeit im Format HH:MM an (z.B. 09:00).")
                return
            
            await self.set_reminder(ctx, med_name, time_str)
        elif action == "list":
            await self.list_medications(ctx)
        elif action == "cancel":
            med_name = " ".join(args)
            await self.cancel_reminder(ctx, med_name)
        else:
            await ctx.send("❌ Unbekannte Aktion. Verfügbare Aktionen: `track`, `remind`, `list`, `cancel`.")
    
    async def track_medication(self, ctx, medication):
        """Track medication intake"""
        try:
            # Get current date
            today = datetime.datetime.now().date()
            
            # Get or create today's entry
            daily_entry = self.notion_manager.get_or_create_daily_entry(today)
            
            # Get current medications
            current_meds = daily_entry.get("medications", [])
            
            # Add the new medication if not already tracked today
            if medication not in current_meds:
                current_meds.append(medication)
                
                # Update the database
                result = self.notion_manager.update_daily_entry(daily_entry["id"], {"medications": current_meds})
                
                if not result:
                    await ctx.send("❌ Es ist ein Fehler beim Speichern aufgetreten. Bitte versuche es später erneut.")
                    return
                
                await ctx.send(f"💊 {medication} als eingenommen markiert.")
            else:
                await ctx.send(f"ℹ️ {medication} wurde heute bereits getrackt.")
            
            # Cancel any pending reminder for this medication today
            user_id = ctx.author.id
            if user_id in self.reminders and medication in self.reminders[user_id]:
                self.reminders[user_id][medication]["canceled"] = True
                await ctx.send(f"Erinnerung für {medication} heute abgesagt, da bereits eingenommen.")
        
        except Exception as e:
            logger.error(f"Error tracking medication: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler beim Tracking aufgetreten. Bitte versuche es später erneut.")
    
    async def set_reminder(self, ctx, medication, time_str):
        """Set a reminder for medication"""
        try:
            user_id = ctx.author.id
            
            # Parse time
            hour, minute = map(int, time_str.split(":"))
            
            # Get the next occurrence of this time
            now = datetime.datetime.now(pytz.timezone('Europe/Berlin'))
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the time is already past for today, set for tomorrow
            if target_time <= now:
                target_time = target_time + datetime.timedelta(days=1)
            
            # Calculate seconds until the target time
            seconds_until = (target_time - now).total_seconds()
            
            # Initialize user's reminders if not exist
            if user_id not in self.reminders:
                self.reminders[user_id] = {}
            
            # Save reminder data
            self.reminders[user_id][medication] = {
                "time": target_time,
                "canceled": False,
                "channel_id": ctx.channel.id
            }
            
            # Confirm the reminder
            await ctx.send(f"⏰ Ich werde dich um {time_str} Uhr an {medication} erinnern.")
            
            # Schedule the reminder
            self.bot.loop.create_task(self.schedule_reminder(user_id, medication, seconds_until))
            
        except Exception as e:
            logger.error(f"Error setting reminder: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler beim Setzen der Erinnerung aufgetreten. Bitte versuche es später erneut.")
    
    async def schedule_reminder(self, user_id, medication, seconds_until):
        """Schedule a reminder for the specified time"""
        try:
            # Wait until the reminder time
            await asyncio.sleep(seconds_until)
            
            # Check if reminder wasn't canceled
            if (user_id in self.reminders and 
                medication in self.reminders[user_id] and 
                not self.reminders[user_id][medication]["canceled"]):
                
                # Get channel to send reminder
                channel_id = self.reminders[user_id][medication]["channel_id"]
                channel = self.bot.get_channel(channel_id)
                
                if channel:
                    user = self.bot.get_user(user_id)
                    mention = user.mention if user else "User"
                    
                    # Send reminder
                    message = await channel.send(
                        f"💊 **Medikamentenerinnerung:** {mention}, es ist Zeit für {medication}!\n"
                        f"Wenn du es eingenommen hast, reagiere mit ✅ oder tippe `!med track {medication}`"
                    )
                    
                    # Add reaction for easy tracking
                    await message.add_reaction("✅")
                    
                    # Set up reaction handler
                    def check(reaction, user):
                        return (user.id == user_id and 
                                str(reaction.emoji) == "✅" and 
                                reaction.message.id == message.id)
                    
                    try:
                        # Wait for reaction
                        _, _ = await self.bot.wait_for('reaction_add', timeout=3600.0, check=check)
                        
                        # Track medication if reaction added
                        ctx = await self.bot.get_context(message)
                        await self.track_medication(ctx, medication)
                        
                    except asyncio.TimeoutError:
                        # No reaction within the hour
                        pass
                
                # Remove the reminder
                if user_id in self.reminders and medication in self.reminders[user_id]:
                    del self.reminders[user_id][medication]
        
        except Exception as e:
            logger.error(f"Error in reminder task: {str(e)}")
    
    async def cancel_reminder(self, ctx, medication):
        """Cancel a medication reminder"""
        user_id = ctx.author.id
        
        if user_id in self.reminders and medication in self.reminders[user_id]:
            self.reminders[user_id][medication]["canceled"] = True
            await ctx.send(f"⏰ Erinnerung für {medication} abgesagt.")
        else:
            await ctx.send(f"❌ Keine aktive Erinnerung für {medication} gefunden.")
    
    async def list_medications(self, ctx):
        """List active medication reminders and tracked medications for today"""
        user_id = ctx.author.id
        
        # Get today's tracked medications from Notion
        today = datetime.datetime.now().date()
        daily_entry = self.notion_manager.get_or_create_daily_entry(today)
        tracked_meds = daily_entry.get("medications", [])
        
        # Get active reminders
        active_reminders = []
        if user_id in self.reminders:
            for med, details in self.reminders[user_id].items():
                if not details["canceled"]:
                    time_str = details["time"].strftime("%H:%M")
                    active_reminders.append(f"• {med} um {time_str} Uhr")
        
        # Prepare message
        message = "📋 **Medikamentenübersicht für heute:**\n\n"
        
        if tracked_meds:
            message += "**Eingenommen:**\n"
            for med in tracked_meds:
                message += f"✅ {med}\n"
        else:
            message += "**Eingenommen:** Noch keine Medikamente getrackt heute.\n"
        
        message += "\n**Aktive Erinnerungen:**\n"
        if active_reminders:
            message += "\n".join(active_reminders)
        else:
            message += "Keine aktiven Erinnerungen."
        
        await ctx.send(message)
    
    async def check_reminders(self):
        """Periodically check if any reminders need to be rescheduled"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                now = datetime.datetime.now(pytz.timezone('Europe/Berlin'))
                
                # Check all reminders
                for user_id in list(self.reminders.keys()):
                    for med in list(self.reminders[user_id].keys()):
                        details = self.reminders[user_id][med]
                        
                        # Skip if canceled
                        if details["canceled"]:
                            continue
                        
                        # If reminder time has passed and wasn't triggered
                        if details["time"] < now:
                            # Calculate time for tomorrow
                            next_time = details["time"] + datetime.timedelta(days=1)
                            
                            # Update reminder
                            self.reminders[user_id][med]["time"] = next_time
                            
                            # Calculate seconds until next time
                            seconds_until = (next_time - now).total_seconds()
                            
                            # Schedule the reminder
                            self.bot.loop.create_task(
                                self.schedule_reminder(user_id, med, seconds_until)
                            )
                            
                            logger.info(f"Rescheduled reminder for {med} to tomorrow")
            
            except Exception as e:
                logger.error(f"Error in reminder check task: {str(e)}")
            
            # Check every hour
            await asyncio.sleep(3600) 