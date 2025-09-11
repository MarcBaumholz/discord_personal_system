#!/usr/bin/env python3
"""
Shared API Monitor for OpenRouter calls
Can be imported by any bot to track API usage
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional

# Add the log_bot directory to the path
log_bot_dir = os.path.dirname(__file__)
if log_bot_dir not in sys.path:
    sys.path.append(log_bot_dir)

try:
    from api_monitor import api_monitor
except ImportError:
    # Fallback if api_monitor is not available
    api_monitor = None

def track_openrouter_call(bot_name: str, model: str, success: bool = True):
    """Track an OpenRouter API call"""
    if api_monitor:
        try:
            # Run in a new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create a task
                    asyncio.create_task(api_monitor.track_api_call(bot_name, model, success))
                else:
                    # If loop exists but not running, run it
                    loop.run_until_complete(api_monitor.track_api_call(bot_name, model, success))
            except RuntimeError:
                # No event loop, create a new one
                asyncio.run(api_monitor.track_api_call(bot_name, model, success))
        except Exception as e:
            print(f"Warning: Failed to track API call: {e}")
    else:
        print(f"Warning: API monitor not available for {bot_name} -> {model}")

def get_daily_stats(target_date: Optional[str] = None) -> dict:
    """Get daily statistics"""
    if api_monitor:
        try:
            return api_monitor.get_daily_stats(target_date)
        except Exception as e:
            print(f"Warning: Failed to get daily stats: {e}")
    return {"error": "API monitor not available"}

def get_total_stats() -> dict:
    """Get total statistics"""
    if api_monitor:
        try:
            return api_monitor.get_total_stats()
        except Exception as e:
            print(f"Warning: Failed to get total stats: {e}")
    return {"error": "API monitor not available"}
