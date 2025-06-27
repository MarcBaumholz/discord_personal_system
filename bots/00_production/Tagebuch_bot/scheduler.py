"""
Scheduler for Tagebuch Bot
Handles daily reminders at 22:00
"""

import schedule
import asyncio
import logging
import threading
import time
from datetime import datetime
import pytz
import os
import discord

logger = logging.getLogger('tagebuch_bot.scheduler')

class ReminderScheduler:
    """Handles scheduling of daily journal reminders"""
    
    def __init__(self, bot_instance):
        """
        Initialize scheduler
        
        Args:
            bot_instance: The Discord bot instance
        """
        self.bot = bot_instance
        self.timezone = pytz.timezone("Europe/Berlin")
        self.is_running = False
        self.scheduler_thread = None
        
        logger.info("Reminder Scheduler initialized")
    
    def start_scheduler(self):
        """Start the scheduler thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule daily reminder at 22:00
        schedule.every().day.at("22:00").do(self._trigger_reminder)
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("📅 Daily reminder scheduled for 22:00")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _trigger_reminder(self):
        """Trigger the daily reminder"""
        logger.info("🔔 Triggering daily journal reminder")
        
        # Create a task to send the reminder message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._send_reminder())
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
        finally:
            loop.close()
    
    async def _send_reminder(self):
        """Send the daily reminder message to Discord"""
        try:
            channel_id = int(os.getenv("TAGEBUCH_CHANNEL_ID"))
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                logger.error(f"Could not find channel with ID: {channel_id}")
                return
            
            # Create reminder message
            embed = discord.Embed(
                title="📔 Tagebuch-Erinnerung",
                description="Zeit für deinen täglichen Tagebucheintrag!",
                color=0x5865F2
            )
            
            embed.add_field(
                name="💭 Heute reflektieren",
                value="Schreibe einfach deine Gedanken des Tages hier in den Chat.\n\n"
                      "• Wie war dein Tag?\n"
                      "• Was hast du erlebt?\n" 
                      "• Wofür bist du dankbar?",
                inline=False
            )
            
            embed.set_footer(text="Dein Eintrag wird automatisch in Notion gespeichert 📝")
            
            await channel.send(embed=embed)
            logger.info("✅ Daily reminder sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending reminder message: {e}")
    
    def create_reminder_message(self):
        """Create the reminder message text for testing"""
        return ("📔 **Tagebuch-Erinnerung**\n\n"
                "Zeit für deinen täglichen Tagebucheintrag!\n\n"
                "💭 **Heute reflektieren:**\n"
                "• Wie war dein Tag?\n"
                "• Was hast du erlebt?\n"
                "• Wofür bist du dankbar?\n\n"
                "Schreibe einfach deine Gedanken hier in den Chat.")
    
    def test_reminder(self):
        """Test the reminder system (for debugging)"""
        logger.info("🧪 Testing reminder system")
        # Use asyncio.create_task to run in the existing event loop
        asyncio.create_task(self._send_reminder()) 