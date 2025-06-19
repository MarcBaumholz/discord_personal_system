# 📋 Calories Bot - Comprehensive Logging System

## 🎯 Overview
The Calories Bot now includes a complete logging system that tracks all bot activities, user interactions, food analyses, monthly reports, errors, and system events. All logs are stored locally in organized directories with both human-readable text logs and structured JSON data.

## 📁 Log Directory Structure

```
logs/
├── food_analysis/           # Food image analysis events
│   ├── analysis.log        # Text log of all analyses
│   ├── analysis_20250619.json  # Daily JSON data
│   └── analysis_20250620.json
├── monthly_reports/         # Monthly report generation
│   ├── reports.log         # Text log of reports
│   ├── reports_2025_06.json   # Monthly JSON data
│   └── reports_2025_07.json
├── user_activity/          # User interactions and commands
│   ├── activity.log        # Text log of user actions
│   ├── commands_20250619.json # Daily command usage
│   └── commands_20250620.json
├── errors/                 # Error tracking and debugging
│   ├── errors.log          # Text log of all errors
│   ├── errors_20250619.json   # Daily error data
│   └── errors_20250620.json
└── system/                 # System events and status
    ├── main.log            # Main system log
    ├── system_20250619.json   # Daily system events
    ├── startup_20250619_134523.json  # Bot startup logs
    └── startup_20250620_091045.json
```

## 📊 What Gets Logged

### 🍽️ Food Analysis Events
- **User**: Who uploaded the image
- **Food Identified**: What the AI recognized
- **Calories**: Estimated calorie count
- **Confidence**: AI confidence percentage
- **Image URL**: Discord attachment link
- **Notion Save Status**: Whether data was saved successfully
- **Timestamp**: When analysis occurred

**Example Log Entry:**
```json
{
  "timestamp": "2025-06-19T13:45:30.123456",
  "event": "food_analysis",
  "user": "Marc",
  "food_name": "Pizza slice",
  "calories": 285,
  "confidence": 92.5,
  "description": "Single slice of pepperoni pizza",
  "image_url": "https://cdn.discordapp.com/...",
  "saved_to_notion": true
}
```

### 📊 Monthly Reports
- **User**: Who requested or received the report
- **Period**: Month and year of the report
- **Statistics**: All calorie data and metrics
- **Success Status**: Whether report generated successfully
- **Chart Information**: File paths and sizes
- **Requester**: Who triggered the report (for manual commands)

**Example Log Entry:**
```json
{
  "timestamp": "2025-06-19T13:50:15.789012",
  "event": "monthly_report",
  "username": "Marc",
  "month": 5,
  "year": 2025,
  "success": true,
  "stats": {
    "total_calories": 25500,
    "average_daily": 850,
    "days_tracked": 30,
    "max_daily": 1200,
    "min_daily": 600
  },
  "requested_by": "Marc",
  "chart_path": "/path/to/chart.png"
}
```

### 👤 User Activity
- **Commands Used**: All bot commands executed
- **Image Uploads**: When users upload food images
- **Channel Information**: Where actions occurred
- **Timing**: When each action happened

**Example Log Entry:**
```json
{
  "timestamp": "2025-06-19T14:00:00.000000",
  "event": "user_command",
  "user": "Marc",
  "command": "month_command",
  "channel": "#calories"
}
```

### ❌ Error Tracking
- **Error Type**: Category of error (AI_ANALYSIS_FAILED, NOTION_SAVE_FAILED, etc.)
- **Error Message**: Detailed error description
- **Context**: User, file, or system context
- **Stack Traces**: For debugging complex issues

**Example Log Entry:**
```json
{
  "timestamp": "2025-06-19T14:05:30.555555",
  "event": "error",
  "error_type": "AI_ANALYSIS_FAILED",
  "error_message": "Could not analyze food image",
  "context": {
    "user": "Marc",
    "image_url": "https://cdn.discordapp.com/..."
  }
}
```

### 🔧 System Events
- **Bot Startup**: When bot starts and configuration
- **Chart Generation**: File creation and cleanup
- **User Matching**: Discord to Notion username mapping
- **Database Connections**: API status and health

**Example Log Entry:**
```json
{
  "timestamp": "2025-06-19T13:45:00.000000",
  "event": "bot_startup",
  "bot_user": "CaloriesBot#1234",
  "channel_id": 1382099540391497818,
  "database_id": "20ed42a1faf5807497c2f350ff84ea8d",
  "openrouter_configured": true,
  "notion_configured": true
}
```

## 🎮 How to Use Logging

### 📋 View Log Information
Use the `!logs` command in Discord to see logging status:

```
!logs
```

This shows:
- 📁 Log directory location
- 📚 Log categories and file counts
- 🔍 Available log types
- 📝 Logging features

### 📊 Log Features

#### 🔄 Automatic Rotation
- **File Size Limit**: 10MB per log file
- **Backup Count**: Keeps 5 backup files
- **Automatic Cleanup**: Old logs are archived automatically

#### 📅 Daily Organization
- **JSON Files**: Organized by date (YYYYMMDD format)
- **Text Logs**: Continuous with rotation
- **Monthly Reports**: Organized by year/month

#### 🏷️ Structured Data
- **JSON Format**: All data in structured JSON for analysis
- **Text Format**: Human-readable logs for quick viewing
- **Searchable**: Easy to grep and search through logs

## 🛠️ Technical Implementation

### Logger Configuration
```python
from logger_config import bot_logger

# Log different types of events
bot_logger.log_food_analysis(analysis_data)
bot_logger.log_monthly_report(report_data)
bot_logger.log_user_command(user, command, channel)
bot_logger.log_error(error_type, message, context)
bot_logger.log_system_event(event_type, details)
```

### File Management
- **Rotating Handlers**: Prevent disk space issues
- **Thread-Safe**: Multiple processes can log safely
- **Error Resilient**: Logging failures don't crash the bot

## 📈 Monitoring and Analysis

### 🔍 Quick Log Analysis
```bash
# View recent food analysis
tail -f logs/food_analysis/analysis.log

# Check for errors
tail -f logs/errors/errors.log

# Monitor user activity
tail -f logs/user_activity/activity.log

# View system events
tail -f logs/system/main.log
```

### 📊 JSON Data Analysis
```bash
# Count daily food analyses
jq length logs/food_analysis/analysis_20250619.json

# Average calories from food logs
jq '[.[].calories] | add / length' logs/food_analysis/analysis_20250619.json

# List all error types
jq '.[].error_type' logs/errors/errors_20250619.json
```

## 🔒 Privacy and Security

### 📋 Data Handling
- **Local Storage**: All logs stored locally, not sent anywhere
- **Image URLs**: Discord URLs logged for debugging but expire
- **User Data**: Only Discord display names logged
- **No Secrets**: API keys and tokens never logged

### 🧹 Cleanup and Maintenance
- **Automatic Rotation**: Prevents log files from growing too large
- **Configurable Retention**: Can adjust how long logs are kept
- **Manual Cleanup**: Old logs can be manually removed if needed

## 🎯 Benefits of Comprehensive Logging

### 🐛 Debugging and Troubleshooting
- **Error Tracking**: Quick identification of issues
- **User Context**: See what users were doing when errors occurred
- **System Health**: Monitor bot performance and reliability

### 📊 Usage Analytics
- **Popular Features**: See which commands are used most
- **User Engagement**: Track when and how users interact
- **Performance Metrics**: Monitor response times and success rates

### 📈 Improvement Insights
- **AI Accuracy**: Track confidence scores over time
- **User Patterns**: Understand usage patterns
- **Feature Adoption**: See how new features are received

## 🚀 Future Enhancements

### Potential Additions
- **Log Viewer Web Interface**: Web-based log browsing
- **Real-time Monitoring**: Live dashboards for bot health
- **Alert System**: Notifications for critical errors
- **Log Analytics**: Advanced statistics and trends
- **Export Features**: CSV/Excel export for analysis

---

## 📋 Summary

The Calories Bot now has enterprise-grade logging that tracks:
- ✅ Every food analysis with full details
- ✅ All monthly reports and statistics
- ✅ Complete user activity and commands
- ✅ Comprehensive error tracking
- ✅ System events and health monitoring

All logs are automatically organized, rotated, and stored in both human-readable and machine-readable formats for maximum flexibility and utility! 