#!/usr/bin/env python3
"""
Monthly Report Scheduler
Handles automatic scheduling and execution of monthly calorie reports
"""

import schedule
import time
import asyncio
from datetime import datetime, timedelta
import os
import threading
from typing import Optional
from dotenv import load_dotenv

# Import our custom modules
from monthly_report import MonthlyReportGenerator

# Import logging system
from logger_config import bot_logger

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

class MonthlyReportScheduler:
    """Handles scheduling and automatic execution of monthly reports"""
    
    def __init__(self):
        self.report_generator = MonthlyReportGenerator()
        self.is_running = False
        self.scheduler_thread = None
        
    def schedule_monthly_reports(self):
        """Schedule monthly reports to run on the 1st of each month at 09:00"""
        try:
            # Schedule for the 1st of every month at 09:00
            schedule.every().month.at("09:00").do(self._run_monthly_reports_sync)
            
            # Also schedule a test run every day at 10:00 for debugging (can be removed in production)
            # schedule.every().day.at("10:00").do(self._run_test_report_sync)
            
            print("📅 Monthly reports scheduled for 1st of each month at 09:00")
            print("🔧 Scheduler is ready!")
            
        except Exception as e:
            print(f"❌ Error scheduling monthly reports: {e}")
    
    def _run_monthly_reports_sync(self):
        """Synchronous wrapper for running monthly reports"""
        try:
            print(f"🚀 Triggered monthly reports at {datetime.now()}")
            
            # Calculate previous month
            now = datetime.now()
            if now.month == 1:
                target_year = now.year - 1
                target_month = 12
            else:
                target_year = now.year
                target_month = now.month - 1
            
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self._run_monthly_reports_async(target_year, target_month)
                )
                print(f"✅ Monthly reports completed: {result}")
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Error in monthly reports sync wrapper: {e}")
    
    async def _run_monthly_reports_async(self, year: int, month: int) -> dict:
        """Async function to run monthly reports"""
        try:
            print(f"📊 Running monthly reports for {month}/{year}")
            
            # Initialize Discord bot connection
            bot_task = asyncio.create_task(self.report_generator.run_bot())
            
            # Wait a moment for bot to connect
            await asyncio.sleep(5)
            
            # Send all monthly reports
            results = await self.report_generator.send_all_monthly_reports(year, month)
            
            # Cancel bot task
            bot_task.cancel()
            
            return results
            
        except Exception as e:
            print(f"❌ Error running monthly reports: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_test_report_sync(self):
        """Test function that can be scheduled for debugging"""
        try:
            print(f"🧪 Running test report at {datetime.now()}")
            
            # Calculate current month for testing
            now = datetime.now()
            target_year = now.year
            target_month = now.month
            
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self._run_test_report_async(target_year, target_month)
                )
                print(f"✅ Test report completed: {result}")
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Error in test report: {e}")
    
    async def _run_test_report_async(self, year: int, month: int) -> dict:
        """Async test function"""
        try:
            print(f"🧪 Testing monthly report functionality for {month}/{year}")
            
            # Get users with data
            users = self.report_generator.data_extractor.get_all_users(year, month)
            
            if users:
                # Test with first user only
                test_user = users[0]
                report_data = await self.report_generator.generate_monthly_report(year, month, test_user)
                
                return {
                    'success': True,
                    'test_user': test_user,
                    'report_generated': report_data.get('success', False)
                }
            else:
                return {
                    'success': False,
                    'message': 'No users found for testing'
                }
                
        except Exception as e:
            print(f"❌ Error in test report async: {e}")
            return {'success': False, 'error': str(e)}
    
    def start_scheduler(self):
        """Start the scheduler in a separate thread"""
        try:
            if self.is_running:
                print("⚠️ Scheduler is already running")
                return
            
            self.is_running = True
            
            # Schedule the jobs
            self.schedule_monthly_reports()
            
            # Start scheduler in a separate thread
            self.scheduler_thread = threading.Thread(target=self._run_scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            print("🚀 Monthly report scheduler started!")
            
        except Exception as e:
            print(f"❌ Error starting scheduler: {e}")
            self.is_running = False
    
    def _run_scheduler_loop(self):
        """Main scheduler loop"""
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except Exception as e:
            print(f"❌ Error in scheduler loop: {e}")
        finally:
            self.is_running = False
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        try:
            self.is_running = False
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            schedule.clear()
            print("🛑 Monthly report scheduler stopped")
            
        except Exception as e:
            print(f"❌ Error stopping scheduler: {e}")
    
    def run_manual_report(self, year: Optional[int] = None, month: Optional[int] = None):
        """
        Manually trigger a monthly report
        
        Args:
            year: Target year (defaults to previous month)
            month: Target month (defaults to previous month)
        """
        try:
            # Default to previous month if not specified
            if year is None or month is None:
                now = datetime.now()
                if now.month == 1:
                    year = now.year - 1
                    month = 12
                else:
                    year = now.year
                    month = now.month - 1
            
            print(f"🔧 Manually triggering monthly report for {month}/{year}")
            
            # Run the sync wrapper
            self._run_monthly_reports_sync()
            
        except Exception as e:
            print(f"❌ Error in manual report: {e}")
    
    def get_scheduler_status(self) -> dict:
        """Get current scheduler status"""
        try:
            next_runs = []
            for job in schedule.jobs:
                next_runs.append({
                    'job': str(job.job_func),
                    'next_run': job.next_run.isoformat() if job.next_run else None
                })
            
            return {
                'is_running': self.is_running,
                'jobs_scheduled': len(schedule.jobs),
                'next_runs': next_runs,
                'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
            }
            
        except Exception as e:
            print(f"❌ Error getting scheduler status: {e}")
            return {'error': str(e)}

# Command-line interface
def main():
    """Main function for command-line usage"""
    import sys
    
    scheduler = MonthlyReportScheduler()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            print("🚀 Starting monthly report scheduler...")
            scheduler.start_scheduler()
            
            try:
                # Keep the main thread alive
                while scheduler.is_running:
                    time.sleep(10)
                    status = scheduler.get_scheduler_status()
                    print(f"📊 Scheduler status: {status}")
                    
            except KeyboardInterrupt:
                print("\n🛑 Stopping scheduler...")
                scheduler.stop_scheduler()
                
        elif command == "manual":
            print("🔧 Running manual monthly report...")
            if len(sys.argv) >= 4:
                year = int(sys.argv[2])
                month = int(sys.argv[3])
                scheduler.run_manual_report(year, month)
            else:
                scheduler.run_manual_report()
                
        elif command == "status":
            status = scheduler.get_scheduler_status()
            print(f"📊 Scheduler Status: {status}")
            
        elif command == "test":
            print("🧪 Running test report...")
            scheduler._run_test_report_sync()
            
        else:
            print("❌ Unknown command. Use: start, manual, status, or test")
    else:
        print("""
📅 Monthly Report Scheduler

Usage:
  python scheduler.py start                 # Start the scheduler
  python scheduler.py manual               # Run manual report for previous month
  python scheduler.py manual 2024 1       # Run manual report for specific month
  python scheduler.py status              # Check scheduler status
  python scheduler.py test                # Run test report

The scheduler will automatically run monthly reports on the 1st of each month at 09:00.
        """)

if __name__ == "__main__":
    main() 