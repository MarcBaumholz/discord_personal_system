# Money Bot

Discord bot that automatically tracks money entries from a specific Discord channel and saves them to a Notion database.

## Features

- 💰 Automatically processes text and image messages in the money channel
- 🤖 Uses AI (OpenRouter) to analyze text and images for money information
- 📊 Extracts amount, category, and description
- 💾 Saves entries to Notion database with proper formatting
- ✅ Provides visual feedback with reactions

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `../../.env`:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `NOTION_TOKEN`: Your Notion integration token
   - `OPENROUTER_API_KEY`: Your OpenRouter API key

3. Set up the Notion database with these properties:
   - Name (title)
   - Amount (number)
   - kategorie (select)
   - Beschreibung (rich text)
   - Date (date)
   - Bilder (files) - optional

## Usage

The bot monitors the money channel (ID: 1396903503624016024) and automatically:
- Analyzes text messages for money amounts and categories
- Analyzes images (receipts, bills) for expense information
- Saves valid entries to the Notion database
- Responds with reactions and confirmation messages

## Commands

- `!status`: Check if the bot is running and monitoring the channel

## Database Structure

The bot saves entries to Notion with:
- **Name**: Description of the expense
- **Amount**: Amount in euros
- **kategorie**: Category (Food, Transport, Shopping, Bills, etc.)
- **Beschreibung**: Full description
- **Date**: When the entry was created
- **Bilder**: Images if attached