#!/usr/bin/env python3
"""
Production Bot Starter
Simple script to start all bots from the 00_production folder
"""

import subprocess
import sys
import os
import time
import signal
import platform
import logging
import json
import threading
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/Documents/discord/runBots/logs/production_bots.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionBotManager:
    def __init__(self):
        self.base_path = "/home/pi/Documents/discord/bots/00_production"
        self.processes = []
        self.start_time = datetime.now()
        
        # Auto-discover production bots
        self.bots = self._discover_production_bots()
        
    def _discover_production_bots(self):
        """Automatically discover all bot files in production folders"""
        bots = []
        
        try:
            production_path = Path(self.base_path)
            if not production_path.exists():
                logger.error(f"Production path does not exist: {self.base_path}")
                return bots
            
            # Scan each subdirectory for bot files
            for bot_dir in production_path.iterdir():
                if bot_dir.is_dir():
                    bot_name = bot_dir.name
                    
                    # Look for common bot file patterns
                    possible_files = [
                        f"{bot_name.lower()}_bot.py",
                        f"{bot_name.lower()}.py", 
                        "bot.py",
                        f"{bot_name}_bot.py"
                    ]
                    
                    for filename in possible_files:
                        bot_file = bot_dir / filename
                        if bot_file.exists():
                            bots.append({
                                "name": bot_name.replace("_", " ").title() + " Bot",
                                "path": str(bot_file),
                                "directory": str(bot_dir),
                                "folder": bot_name
                            })
                            logger.info(f"📁 Discovered: {bot_name} -> {filename}")
                            break
                    else:
                        logger.warning(f"⚠️  No bot file found in {bot_dir}")
            
            logger.info(f"🔍 Found {len(bots)} production bots")
            return bots
            
        except Exception as e:
            logger.error(f"Error discovering bots: {e}")
            return bots
    
    def start_all_bots(self):
        """Start all discovered production bots"""
        logger.info("=" * 60)
        logger.info("🚀 STARTING ALL PRODUCTION BOTS")
        logger.info("=" * 60)
        
        if not self.bots:
            logger.error("❌ No bots discovered! Check the production folder.")
            return False
        
        successful_starts = 0
        
        for bot in self.bots:
            try:
                logger.info(f"🔄 Starting {bot['name']}...")
                
                # Create environment for the bot
                env = os.environ.copy()
                env['PYTHONPATH'] = bot['directory']
                env['PYTHONUNBUFFERED'] = '1'
                
                # Start the bot process
                process = subprocess.Popen(
                    [sys.executable, bot['path']],
                    cwd=bot['directory'],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Store process info
                self.processes.append({
                    "name": bot['name'],
                    "process": process,
                    "path": bot['path'],
                    "directory": bot['directory'],
                    "start_time": datetime.now()
                })
                
                logger.info(f"✅ {bot['name']} started with PID {process.pid}")
                successful_starts += 1
                
                # Small delay between starts
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Failed to start {bot['name']}: {e}")
        
        logger.info("=" * 60)
        logger.info(f"📊 SUMMARY: {successful_starts}/{len(self.bots)} bots started successfully")
        logger.info("=" * 60)
        
        if successful_starts > 0:
            self._print_status()
            return True
        else:
            logger.error("❌ No bots started successfully!")
            return False
    
    def _print_status(self):
        """Print current status of all bots"""
        print("\n" + "=" * 80)
        print("🤖 PRODUCTION BOTS STATUS")
        print("=" * 80)
        
        print(f"{'Bot Name':<25} {'Status':<10} {'PID':<8} {'Uptime':<15}")
        print("-" * 80)
        
        for proc_info in self.processes:
            process = proc_info['process']
            
            if process.poll() is None:
                status = "🟢 RUNNING"
                pid = str(process.pid)
                uptime = self._format_uptime(proc_info['start_time'])
            else:
                status = "🔴 STOPPED"
                pid = "N/A"
                uptime = "N/A"
            
            print(f"{proc_info['name']:<25} {status:<10} {pid:<8} {uptime:<15}")
        
        print("=" * 80)
        print(f"⏱️  System Uptime: {self._format_uptime(self.start_time)}")
        print(f"🕒 Last Update: {datetime.now().strftime('%H:%M:%S')}")
        print("Press Ctrl+C to stop all bots")
        print("=" * 80 + "\n")
    
    def _format_uptime(self, start_time):
        """Format uptime as human readable string"""
        uptime = datetime.now() - start_time
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if uptime.days > 0:
            return f"{uptime.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    
    def monitor_bots(self):
        """Monitor running bots and report status"""
        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                failed_bots = []
                for proc_info in self.processes:
                    if proc_info['process'].poll() is not None:
                        failed_bots.append(proc_info)
                
                if failed_bots:
                    logger.warning(f"⚠️  {len(failed_bots)} bot(s) have stopped:")
                    for bot in failed_bots:
                        logger.warning(f"   - {bot['name']} (was PID {bot['process'].pid})")
                        self.processes.remove(bot)
                
                # Print status every 5 minutes
                if int(time.time()) % 300 == 0:
                    self._print_status()
                
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                time.sleep(60)
    
    def stop_all_bots(self):
        """Stop all running bots gracefully"""
        logger.info("=" * 60)
        logger.info("🛑 STOPPING ALL PRODUCTION BOTS")
        logger.info("=" * 60)
        
        for proc_info in self.processes:
            try:
                process = proc_info['process']
                if process.poll() is None:  # Still running
                    logger.info(f"🔄 Stopping {proc_info['name']} (PID {process.pid})...")
                    
                    # Try graceful shutdown first
                    process.terminate()
                    
                    # Wait up to 10 seconds for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        logger.info(f"✅ {proc_info['name']} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        # Force kill if still running
                        logger.warning(f"⚡ Force killing {proc_info['name']}")
                        process.kill()
                        process.wait()
                        logger.info(f"✅ {proc_info['name']} force stopped")
                else:
                    logger.info(f"ℹ️  {proc_info['name']} was already stopped")
                    
            except Exception as e:
                logger.error(f"❌ Error stopping {proc_info['name']}: {e}")
        
        logger.info("=" * 60)
        logger.info("✅ ALL BOTS STOPPED")
        logger.info("=" * 60)

def main():
    """Main function"""
    # Create logs directory if it doesn't exist
    os.makedirs('/home/pi/Documents/discord/runBots/logs', exist_ok=True)
    
    bot_manager = ProductionBotManager()
    
    try:
        # Start all bots
        success = bot_manager.start_all_bots()
        
        if not success:
            logger.error("Failed to start bots. Exiting.")
            return 1
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=bot_manager.monitor_bots, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        logger.info("🔄 Monitoring started. Press Ctrl+C to stop all bots.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("👤 Shutdown requested by user...")
        bot_manager.stop_all_bots()
        return 0
        
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        bot_manager.stop_all_bots()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
