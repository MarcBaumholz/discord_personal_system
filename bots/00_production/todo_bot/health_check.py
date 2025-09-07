#!/usr/bin/env python3
"""
Todo Bot Health Check & Monitoring
"""
import os
import sys
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('/home/pi/Documents/discord/bots/00_production/.env')

async def check_todoist_health():
    """Check if Todoist API is reachable"""
    api_key = os.getenv('TODOIST_API_KEY')
    if not api_key:
        return False, "No API key found"
    
    headers = {"Authorization": f"Bearer {api_key}"}
    url = "https://api.todoist.com/rest/v2/tasks"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    tasks = await response.json()
                    return True, f"OK - {len(tasks)} active tasks"
                else:
                    return False, f"HTTP {response.status}"
    except Exception as e:
        return False, f"Error: {e}"

def check_log_health():
    """Check if bot is logging properly"""
    log_file = "/home/pi/Documents/discord/bots/00_production/todo_bot/todo_bot.log"
    
    if not os.path.exists(log_file):
        return False, "No log file found"
    
    try:
        # Check if log file was modified in the last 10 minutes
        last_modified = os.path.getmtime(log_file)
        time_diff = datetime.now().timestamp() - last_modified
        
        if time_diff < 600:  # 10 minutes
            return True, f"Log active (last update: {int(time_diff)}s ago)"
        else:
            return False, f"Log stale (last update: {int(time_diff)}s ago)"
    except Exception as e:
        return False, f"Error reading log: {e}"

async def main():
    """Run health checks"""
    if len(sys.argv) > 1 and sys.argv[1] == "--docker":
        # Docker health check mode - minimal output
        todoist_ok, _ = await check_todoist_health()
        sys.exit(0 if todoist_ok else 1)
    
    # Full health check mode
    print(f"🏥 Todo Bot Health Check - {datetime.now()}")
    print("=" * 50)
    
    # Check Todoist API
    todoist_ok, todoist_msg = await check_todoist_health()
    status_emoji = "✅" if todoist_ok else "❌"
    print(f"{status_emoji} Todoist API: {todoist_msg}")
    
    # Check log health
    log_ok, log_msg = check_log_health()
    status_emoji = "✅" if log_ok else "❌"
    print(f"{status_emoji} Bot Logs: {log_msg}")
    
    # Overall health
    overall_health = todoist_ok and log_ok
    print(f"\n{'✅ HEALTHY' if overall_health else '❌ UNHEALTHY'}")
    
    return 0 if overall_health else 1

if __name__ == "__main__":
    # Support Docker health check with --docker flag
    if len(sys.argv) > 1 and sys.argv[1] == "--docker":
        # Minimal health check for Docker
        import asyncio
        try:
            exit_code = asyncio.run(main())
        except:
            exit_code = 1
        sys.exit(exit_code)
    else:
        # Full interactive health check
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
