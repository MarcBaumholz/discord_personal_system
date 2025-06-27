# 🚀 Weekly Planning Bot - Quick Start Guide

## ✅ Bot Status: RUNNING!

Your Weekly Planning Bot is **ALREADY CONFIGURED** and **RUNNING**! 🎉

---

## 🎯 How to Use Right Now

### 1. Find Your Bot
The bot is active in Discord channel: **1361083769427202291**

### 2. Basic Commands

#### 📅 View Your Weekly Plan
```
!plan
```
**Result**: Beautiful weekly overview with tasks, goals, and progress bars

#### 🆕 Generate New Plan  
```
!plan new
```
**Result**: Fresh formatting of your weekly data

#### 👨‍👧‍👦 Family Planning
```
!plan family
```
**Result**: Comprehensive family weekly plan with meals, chores, and schedules

#### ❓ Get Help
```
!plan help
```
**Result**: Complete command list and features

---

## 🎮 Interactive Features

### Emoji Reactions
React to **any bot message** with these emojis:

| Emoji | Action |
|-------|--------|
| 📊 | View detailed weekly statistics |
| 🔄 | Regenerate the current plan |
| 👨‍👧‍👦 | Generate family plan |

### Example Workflow:
1. Type: `!plan`
2. Bot posts your weekly plan
3. React with 📊 to see stats
4. React with 🔄 to regenerate
5. Try `!plan family` for family view

---

## 🔥 What You'll See

### Personal Weekly Plan Example:
```
# 📅 Weekly Plan: Week 26 (June 24, 2024)

## 🎯 Focus Areas
`Work`, `Health`, `Learning`, `Family`

## 🏆 Weekly Goals
1. Complete project milestone
2. Exercise 3 times this week
3. Plan summer vacation

## 📋 Weekly Overview
Progress: 12/28 tasks completed (43%)
████████████░░░░░░░░ 43%

### 🔵 Monday
✅ `09:00` Team standup
✅ `11:00` Project review
⬜ `14:00` Client call
⬜ `18:00` Gym session

### 🔵 Tuesday
⬜ `10:30` Design meeting
⬜ `13:00` Lunch with mentor
⬜ `19:00` Study session

[continues for all days...]
```

### Family Plan Example:
```
# 👨‍👧‍👦 Family Weekly Plan - Week 26

## Monday
- **Present**: 👨 👧 👦
- **Meals**: 
  - 🍳 Breakfast: Pancakes and fruit
  - 🍱 Lunch: School cafeteria
  - 🍽️ Dinner: Spaghetti and salad
- **Events**: 👧 Piano lesson (4 PM)
- **Chores**: 👨 Take out trash (morning)

[continues for all days...]
```

---

## ⚡ Features Already Working

✅ **AI-Powered Formatting** - Beautiful Discord messages
✅ **Notion Integration** - Real data from your planning database  
✅ **Family Planning** - Meals, chores, events coordination
✅ **Statistics** - Productivity tracking and insights
✅ **Auto Reminders** - Sunday planning reminders
✅ **Error Handling** - Fallback to mock data if needed

---

## 🔧 Bot Management

### Check Bot Status
```bash
cd /home/pi/Documents/discord/bots/Weekly_planning_bot
ps aux | grep weekly_planning_bot
```

### Restart Bot (if needed)
```bash
cd /home/pi/Documents/discord/bots/Weekly_planning_bot
source weekly_env/bin/activate
python weekly_planning_bot.py
```

### Stop Bot
```bash
pkill -f weekly_planning_bot.py
```

---

## 📊 Current Configuration

- **Discord Channel**: 1361083769427202291
- **Virtual Environment**: ✅ Active
- **Dependencies**: ✅ Installed  
- **API Keys**: ✅ Configured
- **Notion Database**: ✅ Connected
- **OpenRouter AI**: ✅ Active (DeepSeek free model)

---

## 🎯 Try It Now!

1. **Open Discord**
2. **Go to your planning channel**
3. **Type**: `!plan`
4. **Enjoy your beautiful weekly overview!**

The bot will show your weekly plan with progress tracking, emoji formatting, and interactive features. React with emojis to explore more features!

---

## 🚨 Troubleshooting

**Bot not responding?**
- Check it's in the right channel (ID: 1361083769427202291)
- Wait 5 seconds between commands (cooldown protection)
- Try `!plan help` to test connectivity

**Want to customize?**
- Edit `.env` file for different channel
- Modify Notion database structure
- Update bot messages in the code

---

## 🎉 You're Ready!

Your Weekly Planning Bot is **fully operational**! Start planning your week and explore all the features. The bot will help you stay organized and productive with beautiful visualizations and smart reminders.

**Next**: Try `!plan family` to see the comprehensive family planning features! 