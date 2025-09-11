#!/usr/bin/env python3
"""
API Call Monitor for OpenRouter
Tracks API calls across all bots and provides daily reporting
"""

import os
import json
import asyncio
from datetime import datetime, date
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class APICallMonitor:
    """Monitors API calls to OpenRouter across all bots"""
    
    def __init__(self, data_file: str = "api_calls.json"):
        self.data_file = data_file
        self.data = self._load_data()
        self.lock = asyncio.Lock()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load API call data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "daily_calls": {},
                    "total_calls": 0,
                    "last_reset": datetime.now().strftime("%Y-%m-%d")
                }
        except Exception as e:
            logger.error(f"Error loading API call data: {e}")
            return {
                "daily_calls": {},
                "total_calls": 0,
                "last_reset": datetime.now().strftime("%Y-%m-%d")
            }
    
    def _save_data(self):
        """Save API call data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving API call data: {e}")
    
    async def track_api_call(self, bot_name: str, model: str, success: bool = True):
        """Track an API call to OpenRouter"""
        async with self.lock:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Initialize today's data if not exists
            if today not in self.data["daily_calls"]:
                self.data["daily_calls"][today] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "by_bot": {},
                    "by_model": {}
                }
            
            # Update counters
            self.data["daily_calls"][today]["total_calls"] += 1
            self.data["total_calls"] += 1
            
            if success:
                self.data["daily_calls"][today]["successful_calls"] += 1
            else:
                self.data["daily_calls"][today]["failed_calls"] += 1
            
            # Track by bot
            if bot_name not in self.data["daily_calls"][today]["by_bot"]:
                self.data["daily_calls"][today]["by_bot"][bot_name] = 0
            self.data["daily_calls"][today]["by_bot"][bot_name] += 1
            
            # Track by model
            if model not in self.data["daily_calls"][today]["by_model"]:
                self.data["daily_calls"][today]["by_model"][model] = 0
            self.data["daily_calls"][today]["by_model"][model] += 1
            
            # Save data
            self._save_data()
            
            logger.info(f"📊 API Call tracked: {bot_name} -> {model} ({'success' if success else 'failed'})")
    
    def get_daily_stats(self, target_date: str = None) -> Dict[str, Any]:
        """Get statistics for a specific day"""
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        if target_date not in self.data["daily_calls"]:
            return {
                "date": target_date,
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "by_bot": {},
                "by_model": {}
            }
        
        return {
            "date": target_date,
            **self.data["daily_calls"][target_date]
        }
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get total statistics across all time"""
        return {
            "total_calls": self.data["total_calls"],
            "last_reset": self.data["last_reset"],
            "days_tracked": len(self.data["daily_calls"])
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove data older than specified days"""
        cutoff_date = datetime.now().date()
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days_to_keep)
        
        dates_to_remove = []
        for date_str in self.data["daily_calls"].keys():
            try:
                data_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if data_date < cutoff_date:
                    dates_to_remove.append(date_str)
            except ValueError:
                continue
        
        for date_str in dates_to_remove:
            del self.data["daily_calls"][date_str]
        
        if dates_to_remove:
            self._save_data()
            logger.info(f"🧹 Cleaned up {len(dates_to_remove)} old data entries")

# Global instance
api_monitor = APICallMonitor()

def track_openrouter_call(bot_name: str, model: str, success: bool = True):
    """Convenience function to track OpenRouter API calls"""
    asyncio.create_task(api_monitor.track_api_call(bot_name, model, success))
