# Preisvergleich Bot - Design Document

## Overview

The Preisvergleich Bot is designed to track products in a Notion database and search for special offers in various stores. It uses an AI reasoning agent (via OpenRouter) to perform web searches and extract detailed offer information, which is then posted to a Discord channel.

## Key Components

### 1. Discord Integration (`preisvergleich_bot.py`)
- Handles bot initialization and command processing
- Manages interactions with the Discord API
- Implements commands for managing the product watchlist
- Formats and sends offer information to Discord using embeds

### 2. Notion Integration (`notion_client.py`)
- Connects to the Notion API
- Retrieves the product watchlist from a specified database
- Updates product information with new offer details
- Manages adding and removing products from the watchlist

### 3. Offer Finding (`offer_finder.py`)
- Uses OpenRouter to access reasoning LLMs like DeepSeek or Claude
- Creates detailed prompts for the LLM to search for product offers
- Processes responses and extracts structured data
- Filters valid offers (actual price reductions)

### 4. Scheduling (`scheduler.py`)
- Manages the weekly schedule for price checks
- Runs a background thread for timing
- Provides utilities for checking when the next run will occur

## Data Flow

1. **Watchlist Retrieval**:
   - Bot fetches product watchlist from Notion database
   - Each product has a name and possibly a regular price

2. **Offer Search**:
   - Product data is passed to the offer finder
   - Offer finder creates a detailed prompt for the LLM
   - LLM performs web searches and returns structured data
   - Results are parsed and validated

3. **Notification**:
   - Valid offers are formatted as Discord embeds
   - Offers are posted to the specified Discord channel
   - Offer information is also updated in the Notion database

4. **Persistence**:
   - Offer information is stored in the Notion database
   - Regular prices and offer details are maintained for comparison

## Command Structure

The bot supports these commands:

- `!check_offers`: Manually trigger a check for current offers
- `!add_product [product_name]`: Add a product to the watchlist
- `!remove_product [product_name]`: Remove a product from the watchlist
- `!list_products`: Show all products in the watchlist
- `!next_check`: Show when the next scheduled check will run

## Scheduling Logic

The bot is configured to run checks every Sunday evening. This is managed by a background thread that:

1. Runs a scheduler to check for pending tasks
2. Executes the offer check when scheduled
3. Updates the "next run time" for user queries

## Security Considerations

- API keys are stored in environment variables (not hardcoded)
- The bot validates Discord channel IDs before posting
- Error handling prevents sensitive information leakage

## Scalability

The system is designed to scale in several ways:

1. **Product Volume**: Can handle many products in the watchlist
2. **Multiple Stores**: Search across various retail stores
3. **Regional Support**: Can be configured for different regions
4. **Command Extension**: New commands can be easily added

## LLM Prompt Engineering

The prompts for the LLM are carefully designed to:

1. Provide clear search parameters (products, stores, region)
2. Guide the LLM through a step-by-step reasoning process
3. Specify sources to check for offer information
4. Request structured data in a consistent JSON format
5. Include examples of expected output formatting

## Future Enhancements

Potential future improvements include:

1. Price history tracking and trend analysis
2. Image attachments for products in Discord messages
3. User notification preferences (DMs, mentions)
4. Support for product categories and filtering
5. Integration with more product data sources 