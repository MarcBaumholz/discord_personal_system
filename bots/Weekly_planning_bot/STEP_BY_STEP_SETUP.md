# Weekly Planning Bot - Step-by-Step Setup & Usage Guide

## 🚀 Complete Integration Guide

### Prerequisites
- Python 3.8+ installed
- Discord account
- Notion account (optional but recommended)
- OpenRouter account (for AI features)

---

## Step 1: Environment Setup ⚙️

### 1.1 Navigate to Bot Directory
```bash
cd /home/pi/Documents/discord/bots/Weekly_planning_bot
```

### 1.2 Activate Virtual Environment
```bash
source weekly_env/bin/activate
```

### 1.3 Verify Dependencies
```bash
pip list | grep -E "(discord|notion|requests|pytz|dotenv)"
```

---

## Step 2: Get Required API Keys 🔑

### 2.1 Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it "Weekly Planning Bot"
4. Go to "Bot" section
5. Click "Add Bot"
6. Copy the Token (keep it secret!)
7. Enable these intents:
   - ✅ Message Content Intent
   - ✅ Server Members Intent

### 2.2 Discord Channel ID
1. Enable Developer Mode in Discord: Settings → Advanced → Developer Mode
2. Right-click on your target channel → "Copy ID"
3. Save this ID for later

### 2.3 OpenRouter API Key (Free)
1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for free account
3. Go to "Keys" section
4. Create new API key
5. Copy the key

### 2.4 Notion Setup (Optional)
1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New Integration"
3. Name it "Weekly Planning Bot"
4. Copy the Internal Integration Token
5. Create a database with these properties:
   - **Date** (Date)
   - **Focus** (Multi-select)
   - **Goals** (Text)
   - **Monday** through **Sunday** (Text)
6. Share database with your integration
7. Copy database ID from URL

---

## Step 3: Configure Environment Variables 📝

### 3.1 Edit the .env File
```bash
nano .env
```

### 3.2 Update with Real Credentials
```env
# Discord Configuration
DISCORD_TOKEN=your_actual_discord_bot_token_here
WEEKLY_PLANNING_CHANNEL_ID=your_channel_id_here

# Notion Configuration (optional - bot works without it)
NOTION_TOKEN=your_notion_integration_token_here
WEEKLY_PLANNING_DATABASE_ID=your_notion_database_id_here

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3.3 Save and Exit
Press `Ctrl + X`, then `Y`, then `Enter`

---

## Step 4: Bot Permissions Setup 🛡️

### 4.1 Invite Bot to Your Server
1. In Discord Developer Portal, go to "OAuth2 → URL Generator"
2. Select these scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select these permissions:
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Add Reactions
   - ✅ Use Slash Commands
4. Copy the generated URL and open in browser
5. Select your server and authorize

---

## Step 5: Launch the Bot 🎯

### 5.1 Start the Bot
```bash
cd /home/pi/Documents/discord/bots/Weekly_planning_bot
source weekly_env/bin/activate
python weekly_planning_bot.py
```

### 5.2 Verify Bot is Online
You should see:
```
INFO - weekly_planning_bot - Logged in as WeeklyPlanningBot#1234
INFO - weekly_planning_bot - Weekly Planning Bot is ready!
```

### 5.3 Check Discord
The bot should:
- Appear online in your server
- Send a welcome message to your designated channel
- Post a sample weekly plan automatically

---

## Step 6: How to Use the Bot 📖

### 6.1 Basic Commands

#### View Current Weekly Plan
```
!plan
```
**What it does:** Shows your current weekly plan with tasks, goals, and progress

#### Generate New Plan
```
!plan new
```
**What it does:** Creates a fresh weekly plan (same data, newly formatted)

#### Family Planning
```
!plan family
```
**What it does:** Generates a comprehensive family weekly plan with meals, chores, and events

#### Get Help
```
!plan help
```
**What it does:** Shows all available commands and features

### 6.2 Interactive Features

#### Emoji Reactions
React to any bot message with these emojis:

- **📊** → View detailed weekly statistics
- **🔄** → Regenerate the current plan
- **👨‍👧‍👦** → Generate family plan

#### Example Usage:
1. Bot posts a weekly plan
2. You react with 📊
3. Bot shows detailed stats about your week

### 6.3 Sample Interaction Flow

```
You: !plan
Bot: [Posts beautiful weekly plan with progress bars and emojis]

You: [React with 📊]
Bot: [Shows detailed statistics - productivity, time distribution, etc.]

You: !plan family
Bot: [Posts comprehensive family plan with meals, chores, events]

You: [React with 🔄]
Bot: [Regenerates family plan with updated content]
```

---

## Step 7: Notion Integration (Advanced) 📊

### 7.1 Create Notion Database
If you want to use real Notion data instead of mock data:

1. Create a new database in Notion
2. Add these exact properties:
   - **Date** (Date) - When this weekly plan starts
   - **Focus** (Multi-select) - Your focus areas
   - **Goals** (Text) - Your weekly goals
   - **Monday** (Text) - Monday tasks
   - **Tuesday** (Text) - Tuesday tasks
   - **Wednesday** (Text) - Wednesday tasks
   - **Thursday** (Text) - Thursday tasks
   - **Friday** (Text) - Friday tasks
   - **Saturday** (Text) - Saturday tasks
   - **Sunday** (Text) - Sunday tasks

### 7.2 Format Tasks in Notion
Use this format in daily columns:
```
[ ] 09:00 - Team meeting
[x] 11:00 - Project work (completed)
[ ] 14:00 - Lunch with client
Review documents
Call supplier
```

### 7.3 Share Database with Integration
1. In your Notion database, click "Share"
2. "Invite" → Select your "Weekly Planning Bot" integration
3. Copy database ID from URL and update .env file

---

## Step 8: Automation & Reminders 🔔

### 8.1 Automatic Sunday Reminders
The bot automatically sends planning reminders every Sunday. No setup required!

### 8.2 Keep Bot Running (Optional)
To keep bot running 24/7:

```bash
# Install screen to run in background
sudo apt install screen

# Start bot in screen session
screen -S weekly_bot
cd /home/pi/Documents/discord/bots/Weekly_planning_bot
source weekly_env/bin/activate
python weekly_planning_bot.py

# Detach with Ctrl+A, then D
# Reattach later with: screen -r weekly_bot
```

---

## 🎯 Usage Examples

### Example 1: Personal Weekly Planning
```
You: !plan
Bot: 
# 📅 Weekly Plan: Week 45 (November 6, 2023)

## 🎯 Focus Areas
`Work`, `Health`, `Learning`, `Family`

## 🏆 Weekly Goals
1. Complete project milestone
2. Exercise 3 times
3. Finish online course
4. Plan family trip

## 📋 Weekly Overview
Progress: 7/28 tasks completed (25%)
██████████░░░░░░░░ 25%

### 🔵 Monday
✅ `09:30` Morning standup
✅ `11:00` Project planning
⬜ `14:00` Code review
⬜ `18:00` Gym session

[...continues for all days...]
```

### Example 2: Family Planning
```
You: !plan family
Bot:
# 👨‍👧‍👦 Family Weekly Plan - Week 45 (November 6, 2023)

## Monday
- **Present**: 👨 👧 👦
- **Meals**: 
  - 🍳 Breakfast: Cereal and fruits
  - 🍱 Lunch: Packed sandwiches
  - 🍽️ Dinner: Pasta with vegetables
- **Events**: 👧 Ballet class (5 PM)
- **Chores**: 👨 Take out Paper/Cardboard bin

[...continues for all days...]
```

### Example 3: Statistics View
```
You: [React with 📊]
Bot:
📊 **Weekly Statistics**

**Task Completion by Category:**
- Work: 8/12 (67%)
- Health: 3/5 (60%)
- Learning: 2/4 (50%)
- Personal: 4/7 (57%)

**Most Productive Day:** Tuesday (85% completion)
**Time Distribution:** Work: 24h, Health: 5h, Learning: 6h
```

---

## 🔧 Troubleshooting

### Bot Not Responding?
1. Check bot is online in Discord
2. Verify channel ID in .env file
3. Check bot permissions in server
4. Look at terminal for error messages

### API Errors?
1. Verify all API keys in .env file
2. Check OpenRouter account has credits
3. Ensure Notion database is shared with integration

### Commands Not Working?
1. Make sure you're in the correct channel
2. Check command cooldown (5-second limit)
3. Try `!plan help` to verify bot is responsive

---

## 🎉 You're All Set!

Your Weekly Planning Bot is now fully integrated and ready to help you organize your life! Start with `!plan` to see your first weekly overview, then explore the family planning and statistics features.

The bot will automatically remind you every Sunday to plan your upcoming week, keeping you organized and productive!

---

## 📞 Quick Reference

| Command | Description |
|---------|-------------|
| `!plan` | Show current weekly plan |
| `!plan new` | Generate new plan |
| `!plan family` | Family weekly plan |
| `!plan help` | Show help |
| 📊 emoji | View statistics |
| 🔄 emoji | Regenerate plan |
| 👨‍👧‍👦 emoji | Family plan |

**Bot Channel ID**: Set in WEEKLY_PLANNING_CHANNEL_ID
**Reminders**: Automatic every Sunday
**Cooldown**: 5 seconds between commands 