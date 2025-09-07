"""
Scheduler for Erinnerungen Bot
Handles automated daily reminders for birthdays and waste collection
"""

import logging
import schedule
import time
import asyncio
from datetime import datetime
import pytz
from typing import Optional
import discord

logger = logging.getLogger('erinnerungen_bot.scheduler')

class ErinnerungsScheduler:
    """Manages scheduled tasks for reminders"""
    
    def __init__(self, bot, channel_id: int, geburtstage_manager, muellkalender_manager):
        """
        Initialize scheduler
        
        Args:
            bot: Discord bot instance
            channel_id: Discord channel ID for notifications
            geburtstage_manager: Birthday manager instance
            muellkalender_manager: Waste calendar manager instance
        """
        self.bot = bot
        self.channel_id = channel_id
        self.geburtstage_manager = geburtstage_manager
        self.muellkalender_manager = muellkalender_manager
        self.timezone = pytz.timezone('Europe/Berlin')
        self.running = False
        
        logger.info(f"Scheduler initialized for channel {channel_id}")
        
        # Schedule tasks
        self._setup_schedule()
    
    def _setup_schedule(self):
        """Set up scheduled tasks"""
        # Birthday check at 07:00 daily
        schedule.every().day.at("07:00").do(self._run_birthday_check)
        
        # Waste collection check at 18:00 daily (6pm) - one day in advance
        schedule.every().day.at("18:00").do(self._run_waste_check)
        
        # Test check every 10 minutes (remove in production)
        # schedule.every(10).minutes.do(self._run_test_check)
        
        logger.info("Scheduled tasks configured:")
        logger.info("- Birthday check: 07:00 daily")
        logger.info("- Waste collection check: 18:00 daily (one day in advance)")
    
    def start(self):
        """Start the scheduler in a loop"""
        self.running = True
        logger.info("Scheduler started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Continue after error
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Scheduler stopped")
    
    def _run_birthday_check(self):
        """Run birthday check (synchronous wrapper)"""
        try:
            logger.info("Running scheduled birthday check")
            
            # Run async birthday check in the bot's event loop
            asyncio.run_coroutine_threadsafe(
                self._async_birthday_check(),
                self.bot.loop
            )
            
        except Exception as e:
            logger.error(f"Error in scheduled birthday check: {e}")
    
    def _run_waste_check(self):
        """Run waste collection check (synchronous wrapper)"""
        try:
            logger.info("Running scheduled waste collection check")
            
            # Run async waste check in the bot's event loop
            asyncio.run_coroutine_threadsafe(
                self._async_waste_check(),
                self.bot.loop
            )
            
        except Exception as e:
            logger.error(f"Error in scheduled waste check: {e}")
    
    def _run_test_check(self):
        """Run test check (for debugging)"""
        try:
            logger.info("Running test check")
            now = datetime.now(self.timezone)
            
            asyncio.run_coroutine_threadsafe(
                self._send_message(f"🔄 Test-Check um {now.strftime('%H:%M:%S')}"),
                self.bot.loop
            )
            
        except Exception as e:
            logger.error(f"Error in test check: {e}")
    
    async def _async_birthday_check(self):
        """Async birthday check and notification"""
        try:
            # Check for today's birthdays
            birthdays = await self.geburtstage_manager.check_todays_birthdays()
            
            if birthdays:
                for birthday_message in birthdays:
                    await self._send_message(birthday_message)
                    logger.info("Birthday notification sent")
            else:
                logger.info("No birthdays today - no notification sent")
                
        except Exception as e:
            logger.error(f"Error in async birthday check: {e}")
    
    async def _async_waste_check(self):
        """Async waste collection check and notification"""
        try:
            # Check for tomorrow's waste collection
            waste_info = await self.muellkalender_manager.check_tomorrows_collection()
            
            if waste_info:
                await self._send_message(waste_info)
                logger.info("Waste collection notification sent")
            else:
                logger.info("No waste collection tomorrow - no notification sent")
                
        except Exception as e:
            logger.error(f"Error in async waste check: {e}")
    
    async def _send_message(self, message: str):
        """
        Send message to Discord channel
        
        Args:
            message: Message to send
        """
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                await channel.send(message)
                logger.info(f"Message sent to channel {self.channel_id}")
            else:
                logger.error(f"Channel {self.channel_id} not found")
                
        except Exception as e:
            logger.error(f"Error sending message to Discord: {e}")
    
    def get_next_runs(self) -> dict:
        """
        Get next scheduled run times
        
        Returns:
            Dictionary with next run information
        """
        try:
            jobs_info = {}
            
            for job in schedule.jobs:
                job_name = str(job.job_func).split('.')[-1].replace('>', '')
                next_run = job.next_run
                if next_run:
                    jobs_info[job_name] = next_run.strftime('%Y-%m-%d %H:%M:%S')
            
            return jobs_info
            
        except Exception as e:
            logger.error(f"Error getting next runs: {e}")
            return {}
    
    async def manual_birthday_check(self) -> str:
        """
        Manually trigger birthday check
        
        Returns:
            Result message
        """
        try:
            birthdays = await self.geburtstage_manager.check_todays_birthdays()
            
            if birthdays:
                for birthday_message in birthdays:
                    await self._send_message(birthday_message)
                return f"✅ {len(birthdays)} Geburtstag(e) gefunden und gesendet"
            else:
                return "ℹ️ Keine Geburtstage heute"
                
        except Exception as e:
            logger.error(f"Error in manual birthday check: {e}")
            return f"❌ Fehler beim Geburtstag-Check: {e}"
    
    async def manual_waste_check(self) -> str:
        """
        Manually trigger waste collection check
        
        Returns:
            Result message
        """
        try:
            waste_info = await self.muellkalender_manager.check_tomorrows_collection()
            
            if waste_info:
                await self._send_message(waste_info)
                return "✅ Müll-Erinnerung gefunden und gesendet"
            else:
                return "ℹ️ Keine Müllabholung morgen"
                
        except Exception as e:
            logger.error(f"Error in manual waste check: {e}")
            return f"❌ Fehler beim Müll-Check: {e}" 