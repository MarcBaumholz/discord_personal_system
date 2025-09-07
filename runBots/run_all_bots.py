import subprocess
import sys
import os
import time
import signal
import platform
import logging
import json
import threading
from datetime import datetime, timedelta
import glob

# Auto-discover bots from all subdirectories
def discover_bots():
    """Automatically discover all bot files in the bots directory"""
    # Use curated list of known bots to avoid false positives
    known_bots = [
        {"name": "Allgemeine Wohl Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/allgemeineWohl", "allgemeine_wohl_bot.py")},
        {"name": "Calories Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/Calories_bot", "calories_bot.py")},
        {"name": "Health Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/health_bot", "health_bot.py")},
        {"name": "Decision Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/decision_bot", "decision_bot.py")},
        {"name": "Erinnerungen Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/Erinnerungen_bot", "erinnerungen_bot.py")},
        {"name": "Tagebuch Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/Tagebuch_bot", "tagebuch_bot.py")},
        {"name": "Preisvergleich Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/preisvergleich_bot", "preisvergleich_bot.py")},
        {"name": "Meal Plan Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/meal_plan_bot", "meal_plan_bot.py")},
        {"name": "Weekly Todo Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/weekly_todo_bot", "weekly_todo_bot.py")},
        {"name": "Money Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/money_bot-1", "bot.py")},
        {"name": "YouTube Bot", "path": os.path.join("/home/pi/Documents/discord/bots/00_production/youtube_bot", "youtube_bot.py")},
        {"name": "Learning Bot", "path": os.path.join("/home/pi/Documents/discord/bots/learning_bot", "learning_bot.py")},
        {"name": "LinkedIn Network Analyzer", "path": os.path.join("/home/pi/Documents/discord/bots/linkedin_bot", "linkedin_bot.py")},
        # {"name": "Personal RSS Bot", "path": os.path.join("/home/pi/Documents/discord/bots/personal_RSS_bot/src", "start_bot.py")},
        {"name": "Weekly Planning Bot", "path": os.path.join("/home/pi/Documents/discord/bots/Weekly_planning_bot", "weekly_planning_bot.py")},
    ]
    
    # Add directory information for each bot
    for bot in known_bots:
        bot["directory"] = os.path.dirname(bot["path"])
    
    return known_bots

# Get all bots
bots = discover_bots()
processes = []
system_start_time = datetime.now()

# Enhanced logging setup - using console only to avoid permission issues
def setup_logging():
    """Setup logging configuration"""
    try:
        # Try to create logs directory and set up file logging
        os.makedirs('/home/pi/Documents/discord/runBots/logs', exist_ok=True)
        log_file = '/home/pi/Documents/discord/runBots/logs/bot_runner.log'
        
        # Check if we can write to the log file
        with open(log_file, 'a') as f:
            f.write(f"Log test - {datetime.now()}\n")
        
        # If successful, use both file and console logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        return True
    except Exception as e:
        # If file logging fails, use console only
        print(f"Warning: Could not set up file logging ({e}), using console only")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        return False

# Setup logging
file_logging_available = setup_logging()
logger = logging.getLogger(__name__)

def format_uptime(start_time):
    """Format uptime as human readable string"""
    if not start_time:
        return "Unknown"
    
    uptime = datetime.now() - start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def update_status_file():
    """Update the JSON status file for dashboard consumption"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs('/home/pi/Documents/discord/runBots/data', exist_ok=True)
        
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "system_start_time": system_start_time.isoformat(),
            "system_uptime": format_uptime(system_start_time),
            "total_bots": len(bots),
            "running_count": 0,
            "stopped_count": 0,
            "failed_count": 0,
            "bots": []
        }
        
        # Update bot statuses
        for bot in bots:
            bot_data = {
                "name": bot["name"],
                "path": bot["path"],
                "directory": bot.get("directory", ""),
                "status": "unknown",
                "pid": None,
                "uptime": "Not started",
                "start_time": None,
                "working_dir": bot.get("directory", "")
            }
            
            # Find corresponding process
            process_info = None
            for p in processes:
                if p["name"] == bot["name"]:
                    process_info = p
                    break
            
            if process_info:
                if process_info["process"].poll() is None:
                    # Process is running
                    bot_data["status"] = "running"
                    bot_data["pid"] = process_info["process"].pid
                    bot_data["start_time"] = process_info["start_time"].isoformat()
                    bot_data["uptime"] = format_uptime(process_info["start_time"])
                    bot_data["working_dir"] = process_info.get("working_dir", "")
                    status_data["running_count"] += 1
                else:
                    # Process has stopped
                    bot_data["status"] = "stopped"
                    bot_data["start_time"] = process_info["start_time"].isoformat()
                    status_data["stopped_count"] += 1
            else:
                # Bot never started or failed to start
                bot_data["status"] = "failed"
                status_data["failed_count"] += 1
            
            status_data["bots"].append(bot_data)
        
        # Write to status file
        with open('/home/pi/Documents/discord/runBots/data/bot_status.json', 'w') as f:
            json.dump(status_data, f, indent=2)
        
        return status_data
        
    except Exception as e:
        logger.error(f"Error updating status file: {e}")
        return None

def validate_bot_files():
    """Validate that all bot files exist before starting"""
    missing_bots = []
    for bot in bots:
        if not os.path.exists(bot['path']):
            missing_bots.append(bot)
            logger.warning(f"Bot file not found: {bot['path']}")
    
    if missing_bots:
        logger.error(f"Found {len(missing_bots)} missing bot files:")
        for bot in missing_bots:
            logger.error(f"  - {bot['name']}: {bot['path']}")
    
    return [bot for bot in bots if bot not in missing_bots]

def print_status_table():
    """Print a formatted table of bot statuses to console"""
    print("\n" + "="*80)
    print("🤖 DISCORD BOTS STATUS DASHBOARD")
    print("="*80)
    
    # Update status and get data
    status_data = update_status_file()
    if not status_data:
        print("❌ Could not generate status data")
        return
    
    # Print summary
    print(f"📊 SUMMARY:")
    print(f"   Total Bots: {status_data['total_bots']}")
    print(f"   ✅ Running: {status_data['running_count']}")
    print(f"   ⏹️  Stopped: {status_data['stopped_count']}")
    print(f"   ❌ Failed: {status_data['failed_count']}")
    print(f"   ⏱️  System Uptime: {status_data['system_uptime']}")
    print(f"   🕒 Last Update: {datetime.now().strftime('%H:%M:%S')}")
    
    print(f"\n📋 BOT DETAILS:")
    print(f"{'Bot Name':<20} {'Status':<10} {'PID':<8} {'Uptime':<15} {'Path'}")
    print("-" * 80)
    
    for bot in status_data['bots']:
        status_icon = {
            'running': '✅',
            'stopped': '⏹️',
            'failed': '❌',
            'unknown': '❓'
        }.get(bot['status'], '❓')
        
        pid_str = str(bot['pid']) if bot['pid'] else 'N/A'
        
        print(f"{bot['name']:<20} {status_icon} {bot['status']:<7} {pid_str:<8} {bot['uptime']:<15} {bot['path']}")
    
    print("="*80 + "\n")

def start_bots():
    """Start all available Discord bots"""
    logger.info("="*50)
    logger.info("STARTING DISCORD BOT DEPLOYMENT")
    logger.info("="*50)
    
    # Log file logging status
    if file_logging_available:
        logger.info("✅ File logging enabled: /home/pi/Documents/discord/runBots/logs/bot_runner.log")
    else:
        logger.info("⚠️ File logging disabled - using console only")
    
    # Validate bot files exist
    available_bots = validate_bot_files()
    
    if not available_bots:
        logger.error("No valid bot files found! Exiting...")
        return False
    
    logger.info(f"Found {len(available_bots)} available bots out of {len(bots)} total")
    
    successful_starts = 0
    
    for bot in available_bots:
        logger.info(f"Starting {bot['name']}...")
        try:
            # Create a new process for each bot with proper environment
            env = os.environ.copy()
            env['PYTHONPATH'] = '/home/pi/Documents/discord/runBots'
            env['PYTHONUNBUFFERED'] = '1'
            # Add bot startup environment variable
            env['BOT_STARTUP_MESSAGE'] = 'true'
            env['BOT_NAME'] = bot['name']
            env['BOT_LOCATION'] = f"Docker Container - {bot.get('directory', 'root')}"
            
            # Determine working directory based on bot location
            bot_dir = os.path.dirname(bot['path'])
            if bot_dir:
                working_dir = os.path.join('/home/pi/Documents/discord/runBots', bot_dir)
            else:
                working_dir = '/home/pi/Documents/discord/runBots'
            
            process = subprocess.Popen(
                [sys.executable, bot['path']], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env,
                cwd=working_dir  # Set working directory to bot's directory
            )
            
            processes.append({
                "name": bot['name'], 
                "process": process,
                "path": bot['path'],
                "start_time": datetime.now(),
                "working_dir": working_dir
            })
            
            logger.info(f"✅ {bot['name']} started with PID {process.pid} in {working_dir}")
            successful_starts += 1
            
            # Small delay between bot starts to prevent overwhelming the system
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"❌ Error starting {bot['name']}: {e}")
    
    # Create health check file
    try:
        with open('/home/pi/Documents/discord/runBots/data/bots_running', 'w') as f:
            f.write(f'running:{successful_starts}/{len(available_bots)}:{datetime.now().isoformat()}')
        logger.info("✅ Health check file created")
    except Exception as e:
        logger.error(f"❌ Error creating health check file: {e}")
    
    # Update initial status
    update_status_file()
    
    logger.info("="*50)
    logger.info(f"DEPLOYMENT COMPLETE: {successful_starts}/{len(available_bots)} bots started successfully")
    logger.info("="*50)
    
    # Print initial status table
    print_status_table()
    
    if successful_starts > 0:
        logger.info("🌐 Dashboard will be available at: http://localhost:8080")
        logger.info("Press Ctrl+C to stop all bots")
        return True
    else:
        logger.error("No bots started successfully!")
        return False

def monitor_bots():
    """Monitor bot processes and restart failed ones"""
    while True:
        try:
            failed_bots = []
            for p in processes:
                if p["process"].poll() is not None:  # Process has terminated
                    failed_bots.append(p)
            
            if failed_bots:
                logger.warning(f"Detected {len(failed_bots)} failed bots")
                for failed_bot in failed_bots:
                    logger.warning(f"Bot {failed_bot['name']} (PID {failed_bot['process'].pid}) has stopped")
                    # Remove from active processes
                    processes.remove(failed_bot)

                    # Retry starting the bot
                    logger.info(f"Retrying {failed_bot['name']}...")
                    try:
                        process = subprocess.Popen(
                            [sys.executable, failed_bot['path']], 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True,
                            env=os.environ.copy(),
                            cwd=failed_bot['working_dir']
                        )

                        processes.append({
                            "name": failed_bot['name'], 
                            "process": process,
                            "path": failed_bot['path'],
                            "start_time": datetime.now(),
                            "working_dir": failed_bot['working_dir']
                        })

                        logger.info(f"✅ {failed_bot['name']} restarted with PID {process.pid}")
                    except Exception as e:
                        logger.error(f"❌ Error restarting {failed_bot['name']}: {e}")

            # Update status file
            update_status_file()
            
            # Update health check
            with open('/home/pi/Documents/discord/runBots/data/bots_running', 'w') as f:
                active_count = len([p for p in processes if p["process"].poll() is None])
                f.write(f'running:{active_count}/{len(bots)}:{datetime.now().isoformat()}')
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in bot monitoring: {e}")
            time.sleep(60)  # Wait longer if there's an error

def status_printer():
    """Print status table periodically"""
    while True:
        try:
            time.sleep(60)  # Print status every minute
            print_status_table()
        except Exception as e:
            logger.error(f"Error in status printer: {e}")
            time.sleep(60)

def stop_bots():
    """Stop all running bots gracefully"""
    logger.info("="*50)
    logger.info("STOPPING ALL BOTS...")
    logger.info("="*50)
    
    for p in processes:
        try:
            logger.info(f"Stopping {p['name']} (PID: {p['process'].pid})...")
            
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(p["process"].pid)])
            else:
                # Send SIGTERM first (graceful shutdown)
                os.kill(p["process"].pid, signal.SIGTERM)
                time.sleep(5)  # Give it time to shutdown gracefully
                
                # Check if still running
                if p["process"].poll() is None:
                    logger.warning(f"Force killing {p['name']}")
                    os.kill(p["process"].pid, signal.SIGKILL)
            
            logger.info(f"✅ Stopped {p['name']}")
            
        except Exception as e:
            logger.error(f"❌ Error stopping {p['name']}: {e}")
    
    # Remove health check file
    try:
        os.remove('/home/pi/Documents/discord/runBots/data/bots_running')
        logger.info("✅ Health check file removed")
    except:
        pass
    
    # Remove status file
    try:
        os.remove('/home/pi/Documents/discord/runBots/data/bot_status.json')
        logger.info("✅ Status file removed")
    except:
        pass
    
    logger.info("="*50)
    logger.info("ALL BOTS STOPPED")
    logger.info("="*50)

if __name__ == "__main__":
    try:
        if start_bots():
            # Start monitoring in separate threads
            monitor_thread = threading.Thread(target=monitor_bots, daemon=True)
            monitor_thread.start()
            
            # Start status printer thread
            status_thread = threading.Thread(target=status_printer, daemon=True)
            status_thread.start()
            
            # Keep the main script running
            while True:
                time.sleep(1)
        else:
            logger.error("Failed to start bots. Exiting.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
        stop_bots()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        stop_bots()
        sys.exit(1)