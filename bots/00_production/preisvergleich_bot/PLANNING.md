# Preisvergleich Bot - Implementation Plan

## 🎯 Goal
Test and run the preisvergleich Discord bot that automatically tracks product prices from a Notion database, searches for offers using AI, and notifies users via Discord. The bot should run scheduled checks every Sunday and respond to manual "producthunt" commands.

## 👤 User Stories
- As a user, I want the bot to automatically check for product deals every Sunday evening
- As a user, I want to manually trigger a check by typing "producthunt" in Discord
- As a user, I want to receive formatted notifications when deals are found
- As a user, I want the bot to read my product watchlist from Notion database

## 📦 Data Model
**Entities:**
- **Product**: name, normal_price (from Notion database)
- **Offer**: product_name, store, regular_price, offer_price, savings_percent, valid_until, conditions, offer_link
- **NotionDatabase**: Produktname (title), Normalpreis (number)

**Relations:**
- Notion database contains multiple products
- Each product can have multiple offers from different stores

## 🔪 MVP Features
1. **Environment Setup**: Configure .env with all required API keys
2. **Notion Integration**: Read product watchlist from database
3. **AI Offer Search**: Use OpenRouter to find current deals
4. **Discord Integration**: Send formatted offer notifications
5. **Scheduling**: Automatic Sunday evening checks
6. **Manual Trigger**: Respond to "producthunt" command
7. **Error Handling**: Graceful error handling and logging

## 📝 System Architecture
```
Discord Bot (preisvergleich_bot.py)
├── Notion Manager (notion_manager.py) → Notion API
├── Simple Agent (simple_agent.py) → OpenRouter API
├── Scheduler (scheduler.py) → Background thread
└── Discord Client → Discord API
```

## 🔭 Current Status
**Implemented:**
- Basic Discord bot structure
- Notion database integration
- AI-powered offer search via OpenRouter
- Sunday scheduling functionality
- Test scripts for components

**Missing:**
- Manual "producthunt" command handler
- Proper environment setup
- Testing and verification

## 🧱 Technical Stack
- **Backend**: Python 3.8+
- **Discord**: discord.py
- **Database**: Notion API
- **AI**: OpenRouter (DeepSeek model)
- **Scheduling**: schedule library
- **Environment**: python-dotenv

## ⚙️ Implementation Process
1. **Environment Setup**: Create .env file with API keys
2. **Test Components**: Verify Notion, OpenRouter, Discord connections
3. **Add Command Handler**: Implement "producthunt" command
4. **Integration Test**: Run full workflow test
5. **Deploy Bot**: Start the bot with full functionality
6. **Monitoring**: Verify scheduled runs and manual triggers

## 🚀 Deployment Strategy
- Use virtual environment for dependency isolation
- Run bot as persistent process
- Log all operations for debugging
- Handle API rate limits and errors gracefully

## 🔒 Security Considerations
- Store API keys in .env file (not in code)
- Validate Discord channel permissions
- Handle API errors without exposing sensitive data
- Use minimal required permissions for integrations 