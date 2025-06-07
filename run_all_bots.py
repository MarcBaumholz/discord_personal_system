import subprocess
import sys
import os
import time
import signal
import platform
import logging

# Path to the bots
bots = [
    {"name": "Todo Bot", "path": os.path.join("bots", "todo_bot", "bot.py")},
    {"name": "Daily Todo Bot", "path": os.path.join("bots", "daily_todo_bot", "daily_todo_bot.py")},
    {"name": "Meal Plan Bot", "path": os.path.join("bots", "meal_plan_bot", "meal_plan_bot.py")},
    {"name": "Routine Bot", "path": os.path.join("bots", "routine_bot", "routine_bot.py")},
    {"name": "Plan Bot", "path": os.path.join("bots", "plan_bot", "plan_bot.py")},
    {"name": "Weekly Planning Bot", "path": os.path.join("bots", "Weekly_planning_bot", "weekly_planning_bot.py")}
]

processes = []

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_bots():
    for bot in bots:
        logger.info(f"Starting {bot['name']}...")
        try:
            # Create a new process for each bot
            process = subprocess.Popen([sys.executable, bot['path']], 
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      universal_newlines=True)
            processes.append({"name": bot['name'], "process": process})
            logger.info(f"{bot['name']} started with PID {process.pid}")
        except Exception as e:
            logger.error(f"Error starting {bot['name']}: {e}")
    
    # Create health check file
    with open('/tmp/bots_running', 'w') as f:
        f.write('running')
    
    logger.info(f"\nAll {len(processes)} bots are now running!")
    logger.info("Press Ctrl+C to stop all bots")

def stop_bots():
    logger.info("\nStopping all bots...")
    for p in processes:
        try:
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(p["process"].pid)])
            else:
                os.kill(p["process"].pid, signal.SIGTERM)
            logger.info(f"Stopped {p['name']}")
        except Exception as e:
            logger.error(f"Error stopping {p['name']}: {e}")
    
    # Remove health check file
    try:
        os.remove('/tmp/bots_running')
    except:
        pass
    
    logger.info("All bots have been stopped")

if __name__ == "__main__":
    try:
        start_bots()
        
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_bots()
    except Exception as e:
        logger.error(f"Error: {e}")
        stop_bots() 