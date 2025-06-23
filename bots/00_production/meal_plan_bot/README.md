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