# 🏥 Health Bot - Project Planning

## 🎯 Goal
Build an automated health monitoring bot that fetches daily calorie data from Oura Ring API, analyzes health status, and sends personalized health insights with actionable tips to a Discord channel every morning.

## 👤 User Stories
- As a user, I want to receive my daily calorie burn data automatically so I can track my health progress
- As a user, I want personalized health status assessment based on my Oura Ring data
- As a user, I want actionable tips for the next day based on my previous day's metrics
- As a user, I want this information delivered automatically to my Discord channel

## 📦 Data Model
```
Entities:
- HealthData(date, total_calories, active_calories, inactive_calories, steps, activity_score)
- User(discord_id, oura_access_token)
- HealthStatus(status_level, message, tips)

Relations:
- User has many HealthData entries
- HealthData generates one HealthStatus
```

## 🔪 MVP Features
1. **Oura API Integration**: Fetch daily activity data (calories, steps, activity score)
2. **Health Analysis**: Analyze calorie burn vs. recommended levels
3. **Status Generation**: Generate health status (Excellent/Good/Average/Needs Improvement)
4. **Tip Generation**: Provide 2-3 actionable tips based on data
5. **Discord Integration**: Send formatted message to specific channel
6. **Scheduler**: Run automatically every morning at 8:00 AM

## 🔭 Architecture
**Mode**: Production-ready bot with proper error handling and logging

**Components**:
- Oura API Client (data fetching)
- Health Analyzer (status assessment)
- Tip Generator (recommendations)
- Discord Bot (message sending)
- Scheduler (daily automation)

## ⚙️ Tech Stack
- **Language**: Python 3.11
- **Framework**: discord.py
- **APIs**: Oura API v2
- **Scheduler**: APScheduler
- **Data**: Local JSON storage
- **Environment**: Virtual environment

## 🏗️ File Structure
```
health_bot/
├── health_bot.py          # Main bot entry point
├── oura_client.py         # Oura API integration
├── health_analyzer.py     # Health status analysis
├── tip_generator.py       # Generate personalized tips
├── scheduler.py           # Daily task scheduling
├── config.py             # Configuration management
├── requirements.txt      # Dependencies
├── .env.example         # Environment variables template
└── tests/               # Unit tests
    ├── test_oura_client.py
    ├── test_health_analyzer.py
    └── test_tip_generator.py
```

## 🚀 Development Process
1. Setup virtual environment and dependencies
2. Implement Oura API client with error handling
3. Build health analysis logic
4. Create tip generation system
5. Integrate Discord bot functionality
6. Add scheduling for daily automation
7. Write comprehensive tests
8. Deploy and test in production

## 📊 Health Analysis Logic
**Status Levels**:
- **Excellent** (90-100%): Calories > target + high activity
- **Good** (70-89%): Calories near target + moderate activity  
- **Average** (50-69%): Calories below target but acceptable
- **Needs Improvement** (<50%): Very low activity/calories

**Target Values**:
- Base daily calories: 2000-2500 (adjustable)
- Minimum active calories: 400-500
- Steps target: 8000-10000 