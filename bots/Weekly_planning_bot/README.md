# Weekly Planning Bot

A Discord bot that helps you plan and visualize your week using data from Notion and AI-powered formatting.

## Features

- 📅 **Weekly Planning View**: Displays your weekly plan in a visually appealing Discord message
- 🎯 **Focus Areas**: Highlights your focus areas for the week
- 🏆 **Weekly Goals**: Shows your goals for the week
- 📋 **Daily Tasks**: Lists tasks for each day with time and completion status
- 📊 **Statistics**: Provides detailed stats about task completion and productivity
- 🤖 **AI-Powered**: Uses OpenRouter API to generate beautiful, formatted plans
- 🔄 **Interactive**: React with emojis to view stats or regenerate plans
- 👨‍👧‍👦 **Family Planning**: Creates detailed family weekly plans with meals, events, and chores

## Setup

1. Create a Discord bot and get your token from the [Discord Developer Portal](https://discord.com/developers/applications)
2. Set up a Notion database for weekly planning with the following properties:
   - `Date` (Date): The date of the weekly plan
   - `Focus` (Multi-select): Your focus areas for the week
   - `Goals` (Text): Your weekly goals
   - `Monday` through `Sunday` (Text): Tasks for each day of the week
3. Get your Notion API key from [Notion Integrations](https://www.notion.so/my-integrations)
4. Get your OpenRouter API key from [OpenRouter](https://openrouter.ai/)
5. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
6. Create a `.env` file with the following variables:
   ```
   DISCORD_TOKEN=your_discord_token
   NOTION_TOKEN=your_notion_token
   WEEKLY_PLANNING_DATABASE_ID=your_notion_database_id
   WEEKLY_PLANNING_CHANNEL_ID=your_discord_channel_id
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

## Usage

### Commands

- `!plan` - Show your current weekly plan
- `!plan new` - Generate a new weekly plan
- `!plan family` - Generate a family weekly plan
- `!plan help` - Show help information

### Emoji Triggers

- 📊 - Show detailed statistics for your week
- 🔄 - Regenerate your weekly plan
- 👨‍👧‍👦 - Generate a family weekly plan

## Notion Database Format

### Weekly Planning Database

Create a database in Notion with the following properties:

1. **Date** (Date): The date of the weekly plan
2. **Focus** (Multi-select): Your focus areas for the week (e.g., Work, Health, Learning)
3. **Goals** (Text): Your weekly goals in a numbered list format
4. **Monday-Sunday** (Text): One property for each day with tasks in the format:
   ```
   [ ] 09:00 - Task one
   [x] 11:00 - Task two (completed)
   Task without time
   ```

## Running the Bot

Run the bot using:

```
python weekly_planning_bot.py
```

The bot will automatically send reminders every Sunday to plan your upcoming week.

## Example Output

### Standard Weekly Plan
```
# 📅 Weekly Plan: Week 32 (August 10, 2023)

## 🎯 Focus Areas
`Work`, `Health`, `Learning`, `Social`

## 🏆 Weekly Goals
1. Complete project milestone
2. Exercise 3 times
3. Finish online course
4. Connect with 2 friends

## 📋 Weekly Overview
Progress: 7/28 tasks completed (25%)
██████████░░░░░░░░ 25%

### 🔵 Monday
✅ `09:30` Morning standup
✅ `11:00` Project planning
✅ `12:30` Lunch walk
✅ `14:00` Code review

### 🔵 Tuesday
✅ `10:00` Team meeting
✅ `11:30` Work on feature X
✅ `18:00` Gym session
⬜ `21:00` Reading

...additional days...

> 💪 You've got this! Keep pushing forward.
```

### Family Weekly Plan
```
# 👨‍👧‍👦 Family Weekly Plan - Week 32 (August 10, 2023)

## 🗓️ Weekly Overview

### 👨 Dad | 👧 Child 1 | 👦 Child 2

## Monday
- **Present**: 👨 👧 👦
- **Meals**: 
  - 🍳 Breakfast: Cereal and fruits
  - 🍱 Lunch: Packed sandwiches
  - 🍽️ Dinner: Pasta with vegetables
- **Evening**: Homework time (6-7 PM)
- **Events**: 👧 Ballet class (5 PM)
- **Chores**: 👨 Take out Paper/Cardboard bin (Blue)

...additional days...

## Weekend Plans
### Saturday
- **Present**: 👨 👧 👦
- **Morning**: Farmer's market trip (9-11 AM)
- **Afternoon**: Park visit (2-4 PM)
- **Meals**: Brunch at 11 AM, Barbecue dinner
- **Events**: 👦 Friend's birthday party (4-6 PM)

...
```

## Family Planning Features

The family planning functionality (`!plan family` or 👨‍👧‍👦 emoji) creates a comprehensive weekly view for a family that includes:

1. **Presence Tracking**: Shows which family members are home each day
2. **Meal Planning**: Details breakfast, lunch, and dinner plans for the family
3. **Grocery Shopping**: Assigns grocery shopping responsibilities 
4. **Evening & Weekend Activities**: Highlights important evening activities and weekend plans
5. **Important Events**: Lists each family member's important events
6. **Trash Schedule**: Stuttgart-specific trash collection schedule with assignments
7. **Calendar View**: Presents everything in a clean, scannable calendar format

This feature is perfect for coordinating family schedules and ensuring everyone knows their responsibilities for the week.

## Customization

You can customize the bot by modifying:

- The fallback formatting in `_create_fallback_weekly_plan()` method
- The prompt used for AI generation in `format_weekly_plan()` method
- The sample data and statistics in the respective generator methods
- The family plan generation in `generate_family_plan()` method

## Troubleshooting

If you encounter issues:

1. Check your `.env` file for correct API keys and IDs
2. Ensure your Notion database has the correct properties
3. Verify your bot has the necessary permissions in Discord
4. Check the logs for error messages

## Dependencies

- discord.py
- notion-client
- requests
- python-dotenv
- pytz 