#!/usr/bin/env python3
"""
Discord Bot Services Startup Script
Runs both the bot runner and dashboard server simultaneously
"""

import subprocess
import sys
import os
import time
import signal
import threading
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global process tracking
processes = []

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, stopping all services...")
    stop_all_services()
    sys.exit(0)

def start_bot_runner():
    """Start the bot runner process"""
    logger.info("🤖 Starting Discord Bot Runner...")
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = '/app'
        env['PYTHONUNBUFFERED'] = '1'
        
        process = subprocess.Popen(
            [sys.executable, '/app/runBots/run_all_bots.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env=env,
            cwd='/app'
        )
        
        processes.append({
            "name": "Bot Runner",
            "process": process,
            "start_time": datetime.now(),
            "type": "bot_runner"
        })
        
        logger.info(f"✅ Bot Runner started with PID {process.pid}")
        return process
        
    except Exception as e:
        logger.error(f"❌ Failed to start Bot Runner: {e}")
        return None

def start_dashboard_server():
    """Start the dashboard server process"""
    logger.info("🌐 Starting Dashboard Server...")
    try:
        # Wait a moment for bot runner to initialize
        time.sleep(5)
        
        env = os.environ.copy()
        env['PYTHONPATH'] = '/app'
        env['PYTHONUNBUFFERED'] = '1'
        
        process = subprocess.Popen(
            [sys.executable, '/app/runBots/dashboard_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env=env,
            cwd='/app'
        )
        
        processes.append({
            "name": "Dashboard Server",
            "process": process,
            "start_time": datetime.now(),
            "type": "dashboard"
        })
        
        logger.info(f"✅ Dashboard Server started with PID {process.pid}")
        logger.info("📊 Dashboard will be available at: http://localhost:8080")
        return process
        
    except Exception as e:
        logger.error(f"❌ Failed to start Dashboard Server: {e}")
        return None

def monitor_processes():
    """Monitor all processes and log output"""
    while True:
        try:
            failed_processes = []
            
            for p in processes:
                if p["process"].poll() is not None:
                    failed_processes.append(p)
                else:
                    # Read and log output (non-blocking)
                    try:
                        # Read available output without blocking
                        while True:
                            line = p["process"].stdout.readline()
                            if not line:
                                break
                            print(f"[{p['name']}] {line.rstrip()}")
                    except:
                        pass
            
            # Handle failed processes
            for failed in failed_processes:
                logger.error(f"❌ {failed['name']} (PID {failed['process'].pid}) has stopped")
                processes.remove(failed)
                
                # Restart critical services
                if failed['type'] == 'bot_runner':
                    logger.info("🔄 Restarting Bot Runner...")
                    start_bot_runner()
                elif failed['type'] == 'dashboard':
                    logger.info("🔄 Restarting Dashboard Server...")
                    start_dashboard_server()
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            logger.error(f"Error in process monitoring: {e}")
            time.sleep(30)

def stop_all_services():
    """Stop all running services gracefully"""
    logger.info("🛑 Stopping all services...")
    
    for p in processes:
        try:
            logger.info(f"Stopping {p['name']} (PID {p['process'].pid})...")
            
            # Send SIGTERM first (graceful shutdown)
            p["process"].terminate()
            
            # Wait for graceful shutdown
            try:
                p["process"].wait(timeout=10)
                logger.info(f"✅ {p['name']} stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if necessary
                logger.warning(f"Force killing {p['name']}")
                p["process"].kill()
                p["process"].wait()
                logger.info(f"✅ {p['name']} force stopped")
                
        except Exception as e:
            logger.error(f"❌ Error stopping {p['name']}: {e}")
    
    logger.info("🛑 All services stopped")

def main():
    """Main startup function"""
    logger.info("="*60)
    logger.info("🚀 STARTING DISCORD BOT SERVICES")
    logger.info("="*60)
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start services
        bot_runner = start_bot_runner()
        dashboard_server = start_dashboard_server()
        
        if not bot_runner:
            logger.error("❌ Failed to start Bot Runner. Exiting.")
            return False
            
        if not dashboard_server:
            logger.warning("⚠️ Dashboard Server failed to start, continuing with bots only")
        
        logger.info("="*60)
        logger.info("✅ ALL SERVICES STARTED SUCCESSFULLY")
        logger.info("📊 Dashboard: http://localhost:8080")
        logger.info("🤖 Bots: Running in background")
        logger.info("🔧 Monitoring: Active")
        logger.info("="*60)
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Keep main process alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal...")
        stop_all_services()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        stop_all_services()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 