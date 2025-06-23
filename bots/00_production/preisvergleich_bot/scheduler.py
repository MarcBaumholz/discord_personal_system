import schedule
import time
import threading
import logging
from typing import Callable, Optional
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scheduler')

class OfferScheduler:
    def __init__(self):
        """Initialize the scheduler for Sunday offer checking"""
        self.scheduler_thread = None
        self.running = False
        self.next_run_time = None
        logger.info("OfferScheduler initialized")
    
    def schedule_sunday_check(self, check_function, hour: int = 20, minute: int = 0):
        """
        Schedule the weekly Sunday evening check
        
        Args:
            check_function: Function to call for the check
            hour: Hour to run (24-hour format, default: 20 = 8 PM)
            minute: Minute to run (default: 0)
        """
        schedule_time = f"{hour:02d}:{minute:02d}"
        logger.info(f"Scheduling weekly offer check for Sunday at {schedule_time}")
        
        # Schedule for Sunday evening
        schedule.every().sunday.at(schedule_time).do(check_function)
        
        # Calculate next run time
        self._update_next_run_time()
        
        # Start the scheduler thread if not already running
        if not self.running:
            self.start()
    
    def _run_scheduler(self):
        """Run the scheduler thread"""
        logger.info("Scheduler thread started")
        self.running = True
        
        while self.running:
            schedule.run_pending()
            self._update_next_run_time()
            time.sleep(60)  # Check every minute
    
    def _update_next_run_time(self):
        """Update the next scheduled run time"""
        jobs = schedule.get_jobs()
        if jobs:
            self.next_run_time = jobs[0].next_run
    
    def start(self):
        """Start the scheduler thread"""
        if self.scheduler_thread is not None and self.scheduler_thread.is_alive():
            logger.warning("Scheduler thread is already running")
            return
        
        logger.info("Starting scheduler thread")
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
    
    def stop(self):
        """Stop the scheduler thread"""
        logger.info("Stopping scheduler thread")
        self.running = False
        
        if self.scheduler_thread is not None:
            self.scheduler_thread.join(timeout=2.0)
            
        schedule.clear()
        self.next_run_time = None
    
    def get_next_run_formatted(self) -> Optional[str]:
        """
        Get a formatted string of when the next check will run
        
        Returns:
            Formatted string with next run time or None if not scheduled
        """
        if not self.next_run_time:
            return None
        
        return self.next_run_time.strftime("%A, %d %B %Y at %H:%M")
    
    def get_time_until_next_run(self) -> Optional[str]:
        """
        Get a human-readable string of time until next run
        
        Returns:
            Human-readable time until next run or None if not scheduled
        """
        if not self.next_run_time:
            return None
        
        now = datetime.now()
        time_diff = self.next_run_time - now
        
        if time_diff.total_seconds() <= 0:
            return "any moment now"
        
        days, seconds = time_diff.days, time_diff.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        time_str = []
        if days > 0:
            time_str.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            time_str.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 and days == 0:  # Only show minutes if less than a day away
            time_str.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        return ", ".join(time_str) 