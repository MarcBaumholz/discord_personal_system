# Preisvergleich Bot

A Discord bot that automatically tracks product prices from a Notion database and notifies about special offers every Sunday. It uses AI-powered web search via LangChain and LangGraph to find the best deals.

## Features

- Connects to a Notion database to read the product watchlist
- Uses LangChain and LangGraph to create an intelligent agent for finding deals
- Searches the web for current product offers using the Tavily search API
- Automatically runs every Sunday evening
- Posts detailed offer notifications to Discord when deals are found

## Setup

1. Create a `.env` file with required tokens:
   ```
   DISCORD_TOKEN=your_discord_token
   DISCORD_CHANNEL_ID=1367031179278290986
   NOTION_TOKEN=your_notion_integration_token
   NOTION_DATABASE_ID=your_notion_database_id
   OPENROUTER_API_KEY=your_openrouter_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   python preisvergleich_bot.py
   ```

## Architecture

The bot uses a simple and focused architecture:

1. **Notion Integration**: Reads products from a Notion database
2. **AI Agent**: Uses LangChain and OpenRouter to search for product offers
3. **Discord Integration**: Sends notifications when offers are found
4. **Scheduler**: Runs the check every Sunday evening

## Notion Database Format

The Notion database should have the following properties:
- `Produktname` (title): Name of the product
- `Normalpreis` (number): Regular price of the product

## Dependencies

- discord.py: Discord API wrapper
- notion-client: Notion API integration
- langchain: Agent framework
- langgraph: Graph-based workflow for agents
- tavily-python: Web search API 