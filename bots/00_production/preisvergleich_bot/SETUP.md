# Preisvergleich Bot - Setup Guide

This guide will walk you through setting up and running the Preisvergleich Bot, which checks for product sales from a Notion database and posts notifications to a Discord channel.

## Prerequisites

1. A Discord account with a bot set up
2. A Notion account with a database for tracking products
3. An OpenRouter.ai account for AI capabilities
4. Python 3.8+ installed on your system

## Step 1: Prepare Your Notion Database

1. Create a new database in Notion to track products
2. Add the following properties to your database:
   - `Produktname` (Title): Name of the product
   - `Normalpreis` (Number): Regular/normal price of the product
3. Add your products to the database with their names and regular prices
4. Share the database with your Notion integration (details below)

## Step 2: Set Up API Keys

1. **Discord Bot Setup**:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and set up a bot
   - Enable necessary intents (at minimum, Message Content intent)
   - Copy the bot token for later use
   - Invite the bot to your server with proper permissions

2. **Notion API Setup**:
   - Go to [Notion Integrations](https://www.notion.so/my-integrations)
   - Create a new integration for your workspace
   - Name it "Preisvergleich Bot" or similar
   - Copy the integration token for later use
   - In your Notion database, click "Share" and add your integration

3. **OpenRouter Setup**:
   - Create an account at [OpenRouter.ai](https://openrouter.ai/)
   - Generate an API key
   - Copy the API key for later use

## Step 3: Configure Environment Variables

1. Create a `.env` file in the project root directory
2. Add the following variables:
   ```
   # Discord Configuration
   DISCORD_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_discord_channel_id

   # Notion Configuration
   NOTION_TOKEN=your_notion_api_token
   NOTION_DATABASE_ID=your_notion_database_id

   # OpenRouter Configuration
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

3. To find your Discord channel ID:
   - Enable Developer Mode in Discord (Settings > Advanced)
   - Right-click on the channel and select "Copy ID"

4. To find your Notion database ID:
   - Open your database in Notion
   - Copy the ID from the URL (it's typically a 32-character string in the URL)

## Step 4: Install Dependencies

Run the following command to install all required dependencies:

```bash
pip install -r requirements.txt
```

## Step 5: Test the System

Before setting up the full bot, you can test each component separately:

1. Test Discord connection:
   ```bash
   python test_discord.py
   ```
   This should send a test message to your Discord channel.

2. Test the complete workflow:
   ```bash
   python test_workflow.py
   ```
   This will fetch products from Notion, search for offers, and post results to Discord.

## Step 6: Run the Bot

Once testing is complete, you can run the full bot:

```bash
python preisvergleich_bot.py
```

The bot will:
1. Connect to Discord
2. Initialize all necessary services
3. Schedule weekly checks every Sunday at 8 PM
4. Post offer notifications to the designated Discord channel

## Troubleshooting

1. **Discord Connection Issues**:
   - Verify the bot token is correct
   - Ensure the bot has been invited to your server
   - Check that the channel ID is correct and the bot has permission to send messages

2. **Notion Connection Issues**:
   - Verify the Notion API token is correct
   - Ensure the database is shared with your integration
   - Check that the database has the correct properties (`Produktname` and `Normalpreis`)

3. **OpenRouter Issues**:
   - Verify the API key is correct
   - Ensure you have credits available in your OpenRouter account

## Customization

You can customize the bot's behavior by modifying the following files:

- `preisvergleich_bot.py`: Main bot file, controls Discord interaction and scheduling
- `simple_agent.py`: Controls the AI agent for searching offers
- `scheduler.py`: Modifies the scheduling logic (e.g., changing the day or time)

To change the scheduled check time, edit the `schedule_sunday_check` call in `preisvergleich_bot.py`. 