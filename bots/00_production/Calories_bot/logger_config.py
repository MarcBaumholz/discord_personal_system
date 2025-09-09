#!/usr/bin/env python3
"""
Logging Configuration for Calories Bot
Comprehensive logging system for all bot activities
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

class CaloriesBotLogger:
    """Centralized logging system for the Calories Bot"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.setup_logging_directories()
        self.setup_loggers()
        
    def setup_logging_directories(self):
        """Create logging directory structure"""
        directories = [
            self.log_dir,
            os.path.join(self.log_dir, "food_analysis"),
            os.path.join(self.log_dir, "monthly_reports"),
            os.path.join(self.log_dir, "errors"),
            os.path.join(self.log_dir, "user_activity"),
            os.path.join(self.log_dir, "system")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def setup_loggers(self):
        """Setup different loggers for different activities"""
        
        # Main bot logger
        self.main_logger = self._create_logger(
            "calories_bot_main",
            os.path.join(self.log_dir, "system", "main.log"),
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        
        # Food analysis logger
        self.food_logger = self._create_logger(
            "food_analysis",
            os.path.join(self.log_dir, "food_analysis", "analysis.log"),
            "%(asctime)s | %(message)s"
        )
        
        # Monthly reports logger
        self.reports_logger = self._create_logger(
            "monthly_reports",
            os.path.join(self.log_dir, "monthly_reports", "reports.log"),
            "%(asctime)s | %(message)s"
        )
        
        # Error logger
        self.error_logger = self._create_logger(
            "errors",
            os.path.join(self.log_dir, "errors", "errors.log"),
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        
        # User activity logger
        self.activity_logger = self._create_logger(
            "user_activity",
            os.path.join(self.log_dir, "user_activity", "activity.log"),
            "%(asctime)s | %(message)s"
        )
    
    def _create_logger(self, name: str, file_path: str, format_string: str) -> logging.Logger:
        """Create a logger with rotating file handler"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create rotating file handler (max 10MB, keep 5 backups)
        file_handler = RotatingFileHandler(
            file_path, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(format_string)
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        return logger
    
    def log_bot_startup(self, bot_info: Dict[str, Any]):
        """Log bot startup information"""
        self.main_logger.info("=" * 50)
        self.main_logger.info("🤖 CALORIES BOT STARTUP")
        self.main_logger.info("=" * 50)
        self.main_logger.info(f"Bot User: {bot_info.get('bot_user', 'Unknown')}")
        self.main_logger.info(f"Channel ID: {bot_info.get('channel_id', 'Unknown')}")
        self.main_logger.info(f"Database ID: {bot_info.get('database_id', 'Unknown')}")
        self.main_logger.info("🚀 Bot is ready and monitoring for food images")
        
        # Save startup info as JSON
        startup_file = os.path.join(self.log_dir, "system", f"startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(startup_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "event": "bot_startup",
                **bot_info
            }, f, indent=2)
    
    def log_food_analysis(self, analysis_data: Dict[str, Any]):
        """Log food analysis event"""
        user = analysis_data.get('user', 'Unknown')
        food_name = analysis_data.get('food_name', 'Unknown')
        calories = analysis_data.get('calories', 0)
        confidence = analysis_data.get('confidence', 0)
        
        # Text log
        self.food_logger.info(f"👤 User: {user} | 🥗 Food: {food_name} | 🔥 Calories: {calories} kcal | 🎯 Confidence: {confidence}%")
        
        # JSON log for detailed data
        analysis_file = os.path.join(
            self.log_dir, 
            "food_analysis", 
            f"analysis_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        # Append to daily JSON file
        analysis_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "food_analysis",
            **analysis_data
        }
        
        self._append_to_json_file(analysis_file, analysis_entry)
        
        # Log user activity
        self.activity_logger.info(f"🍽️ {user} analyzed food: {food_name} ({calories} kcal)")
    
    def log_monthly_report(self, report_data: Dict[str, Any]):
        """Log monthly report generation"""
        user = report_data.get('username', 'Unknown')
        month = report_data.get('month', 0)
        year = report_data.get('year', 0)
        success = report_data.get('success', False)
        
        if success:
            stats = report_data.get('stats', {})
            total_calories = stats.get('total_calories', 0)
            days_tracked = stats.get('days_tracked', 0)
            
            # Text log
            self.reports_logger.info(f"📊 MONTHLY REPORT | User: {user} | Period: {month}/{year} | Total: {total_calories} kcal | Days: {days_tracked}")
            
            # Detailed activity log
            self.activity_logger.info(f"📊 {user} generated monthly report for {month}/{year}")
        else:
            error_msg = report_data.get('message', 'Unknown error')
            self.reports_logger.info(f"❌ MONTHLY REPORT FAILED | User: {user} | Period: {month}/{year} | Error: {error_msg}")
            self.error_logger.error(f"Monthly report failed for {user} ({month}/{year}): {error_msg}")
        
        # JSON log
        report_file = os.path.join(
            self.log_dir, 
            "monthly_reports", 
            f"reports_{year}_{month:02d}.json"
        )
        
        report_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "monthly_report",
            **report_data
        }
        
        self._append_to_json_file(report_file, report_entry)
    
    def log_user_command(self, user: str, command: str, channel: str):
        """Log user command usage"""
        self.activity_logger.info(f"⚡ {user} used command: {command} in {channel}")
        
        # JSON log for commands
        command_file = os.path.join(
            self.log_dir, 
            "user_activity", 
            f"commands_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        command_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "user_command",
            "user": user,
            "command": command,
            "channel": channel
        }
        
        self._append_to_json_file(command_file, command_entry)
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log error events"""
        self.error_logger.error(f"❌ {error_type}: {error_message}")
        
        if context:
            self.error_logger.error(f"Context: {context}")
        
        # JSON log for errors
        error_file = os.path.join(
            self.log_dir, 
            "errors", 
            f"errors_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        self._append_to_json_file(error_file, error_entry)
    
    def log_warning(self, warning_type: str, warning_message: str, context: Dict[str, Any] = None):
        """Log warning events"""
        self.error_logger.warning(f"⚠️ {warning_type}: {warning_message}")
        
        if context:
            self.error_logger.warning(f"Context: {context}")
        
        # JSON log for warnings
        error_file = os.path.join(
            self.log_dir, 
            "errors", 
            f"errors_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        warning_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "warning",
            "warning_type": warning_type,
            "warning_message": warning_message,
            "context": context or {}
        }
        
        self._append_to_json_file(error_file, warning_entry)
    
    def log_system_event(self, event_type: str, details: Dict[str, Any]):
        """Log system events"""
        self.main_logger.info(f"🔧 SYSTEM EVENT: {event_type}")
        for key, value in details.items():
            self.main_logger.info(f"  {key}: {value}")
        
        # JSON log
        system_file = os.path.join(
            self.log_dir, 
            "system", 
            f"system_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        system_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "system_event",
            "event_type": event_type,
            **details
        }
        
        self._append_to_json_file(system_file, system_entry)
    
    def _append_to_json_file(self, file_path: str, entry: Dict[str, Any]):
        """Append entry to JSON file (creates array if file doesn't exist)"""
        try:
            # Read existing data
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                data = []
            
            # Append new entry
            data.append(entry)
            
            # Write back to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.error_logger.error(f"Failed to write to JSON file {file_path}: {e}")
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get summary of logging activity"""
        try:
            summary = {
                "log_directory": self.log_dir,
                "directories": [],
                "recent_activity": {}
            }
            
            # Get directory sizes and file counts
            for root, dirs, files in os.walk(self.log_dir):
                if files:
                    rel_path = os.path.relpath(root, self.log_dir)
                    summary["directories"].append({
                        "path": rel_path,
                        "file_count": len(files),
                        "files": files
                    })
            
            return summary
            
        except Exception as e:
            self.error_logger.error(f"Failed to get log summary: {e}")
            return {"error": str(e)}

# Global logger instance
bot_logger = CaloriesBotLogger() 