# Meal Plan Bot

A Discord bot that generates weekly meal plans using Notion integration, OpenRouter AI, and Todoist.

## Features

- Fetches recipes from a Notion database
- Randomly selects 3 recipes for weekly meal planning
- Generates comprehensive meal prep plans and shopping lists
- Automatically adds shopping list items to your Todoist Einkaufsliste project
- Responds to thumbs up emoji reactions

## Usage

Simply react with 👍 in the erinnerungen channel to get meal suggestions for Sunday prep. The bot will:

1. Fetch recipes from your Notion database and select 3 random ones
2. Generate a detailed meal prep plan and shopping list
3. Extract the shopping list and add all items to your Todoist Einkaufsliste project
4. Send both the shopping list and complete meal plan to the Discord channel

## Configuration

- ERINNERUNGEN_CHANNEL_ID: 1361083869729919046
- Requires DISCORD_TOKEN, NOTION_TOKEN, OPENROUTER_API_KEY, and TODOIST_API_KEY in .env

## Dependencies

- discord.py
- python-dotenv
- requests
- json
- re

## ✅ Current Status (September 2025)

**🟡 BOT READY FOR DEPLOYMENT**

The Meal Plan Bot is fully developed and ready to run, but not currently deployed in Docker.

### Development Status
- **Code**: ✅ Complete and functional
- **Docker**: ❌ Not currently containerized
- **Deployment**: 🟡 Ready for manual startup
- **Last Update**: September 2025

### Features Ready
- ✅ **Notion Integration**: Fetches recipes from Notion database
- ✅ **AI Meal Planning**: Uses OpenRouter AI for comprehensive meal prep plans
- ✅ **Todoist Integration**: Automatically adds shopping lists to Todoist
- ✅ **Discord Integration**: Responds to thumbs up reactions
- ✅ **Shopping List Generation**: Extracts and organizes shopping items
- ✅ **Meal Prep Planning**: Detailed preparation instructions

### To Deploy
1. Set up environment variables in `.env` (DISCORD_TOKEN, NOTION_TOKEN, OPENROUTER_API_KEY, TODOIST_API_KEY)
2. Ensure Notion database has recipe data
3. Run: `python meal_plan_bot.py`
4. Consider Docker containerization for production use 