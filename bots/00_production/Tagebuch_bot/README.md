# 📔 Tagebuch Bot - Discord Journal Bot

Automatically saves journal entries to Notion database with daily reminders.

## ✨ Features

- **Daily Reminders**: Sends reminder at 22:00 daily
- **Auto-Save**: Saves journal entries to Notion automatically
- **Smart Titles**: Generates titles from your text
- **Rich Discord Integration**: Beautiful embeds and confirmations
- **German Language**: Designed for German journal entries

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone/navigate to the project
cd discord/bots/Tagebuch_bot

# Activate virtual environment
source tagebuch_env/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### 2. Configure Tokens

```bash
# Copy environment template
cp env.example .env

# Edit .env with your tokens
nano .env
```

### 3. Validate Setup

```bash
# Run setup validator
python setup_validator.py
```

### 4. Test Bot Logic

```bash
# Test without real tokens
python test_bot_logic.py
```

### 5. Run the Bot

```bash
# Start the bot
python tagebuch_bot.py
```

## 🔧 Configuration

### Required Environment Variables

```env
# Discord Bot Token
DISCORD_TOKEN=your_discord_bot_token_here

# Notion Integration Token  
NOTION_TOKEN=your_notion_integration_token_here

# Database ID (extracted from Notion URL)
TAGEBUCH_DATABASE_ID=214d42a1faf5803193c6c71b7d4d7c3f

# Discord Channel ID
TAGEBUCH_CHANNEL_ID=1384289197115838625

# Timezone (optional)
TIMEZONE=Europe/Berlin
```

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application → Bot
3. Copy bot token to `DISCORD_TOKEN`
4. Enable "Message Content Intent" 
5. Invite bot to server with permissions:
   - Send Messages
   - Read Message History
   - Use Slash Commands

### Notion Integration Setup

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create new internal integration
3. Copy internal integration token to `NOTION_TOKEN`
4. Share your Tagebuch database with the integration:
   - Open database in Notion
   - Click "Share" → "Invite"
   - Add your integration

### Database Structure

Your Notion database should have these properties:
- **Titel** (Title) - Title property
- **Datum** (Date) - Date property  
- **Text** (Rich Text) - Rich text property

## 📱 Usage

### Writing Journal Entries

Simply write your thoughts in the configured Discord channel:

```
Heute war ein wunderschöner Tag! Ich habe viel gelernt und bin dankbar für die vielen positiven Begegnungen.
```

The bot will:
1. Generate a title: "war ein wunderschöner Tag"
2. Save to Notion with today's date
3. Send confirmation message

### Bot Commands

- `!tagebuch_help` - Show help information
- `!tagebuch_test` - Create test entry
- `!tagebuch_reminder` - Test reminder system

### Daily Reminders

Every day at 22:00 (Europe/Berlin timezone), the bot sends:

> 📔 **Tagebuch-Erinnerung**
> 
> Zeit für deinen täglichen Tagebucheintrag!
> 
> 💭 **Heute reflektieren:**
> • Wie war dein Tag?
> • Was hast du erlebt?  
> • Wofür bist du dankbar?

## 🧪 Testing

### Test Scripts

1. **Setup Validator**: `python setup_validator.py`
   - Validates token configuration
   - Tests Notion connection
   - Provides setup instructions

2. **Logic Tests**: `python test_bot_logic.py`
   - Tests all components without real tokens
   - Validates text processing
   - Checks scheduler logic

3. **Component Tests**: `python test_components.py`
   - Tests individual components
   - Requires configured tokens

### Manual Testing

1. Send test message in Discord channel
2. Check Notion database for new entry
3. Verify confirmation message
4. Test reminder with `!tagebuch_reminder`

## 📁 Project Structure

```
Tagebuch_bot/
├── tagebuch_bot.py           # Main bot file
├── notion_manager.py         # Notion API integration
├── text_processor.py         # Text processing & titles
├── scheduler.py              # Daily reminder system
├── setup_validator.py        # Setup validation script
├── test_bot_logic.py         # Logic testing without tokens
├── test_components.py        # Component testing with tokens
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
├── env.example              # Environment template
├── README.md                # This file
├── PLANNING.md              # Project planning
├── TASK.md                  # Task tracking
└── tagebuch_env/            # Virtual environment
```

## 🔍 Troubleshooting

### Common Issues

**Bot doesn't respond to messages:**
- Check `TAGEBUCH_CHANNEL_ID` is correct
- Verify bot has permissions in channel
- Ensure bot is online in Discord

**Notion saves fail:**
- Run `python setup_validator.py`
- Check `NOTION_TOKEN` is valid
- Verify database is shared with integration
- Check database has required properties

**Daily reminders not working:**
- Check timezone configuration
- Verify bot stays running continuously
- Check logs for scheduler errors

### Debugging

```bash
# Check logs
tail -f tagebuch_bot.log

# Test individual components
python test_bot_logic.py

# Validate configuration
python setup_validator.py
```

### Getting Help

1. Check the logs in `tagebuch_bot.log`
2. Run validation scripts
3. Verify all environment variables
4. Test with simple messages first

## ✅ Current Status (September 2025)

**🟢 BOT IS LIVE AND OPERATIONAL**

The Tagebuch Bot is currently running in a Docker container and fully functional.

### Bot Status
- **Container**: `tagebuch_bot_tagebuch-bot` - Running (Healthy)
- **Uptime**: 38+ hours
- **Health Check**: ✅ Healthy
- **Last Restart**: September 8, 2025

### Recent Updates
- ✅ **Stable Operation**: Bot running continuously without issues
- ✅ **Docker Health Checks**: Automated monitoring and restart capability
- ✅ **Notion Integration**: Active database connectivity for journal entries
- ✅ **Daily Reminders**: Working 22:00 daily reminder system
- ✅ **Smart Title Generation**: Automatic title creation from journal text

### Tested Functionality
- ✅ Journal entry processing and saving to Notion
- ✅ Daily reminder system (22:00 Europe/Berlin timezone)
- ✅ Smart title generation from German text
- ✅ Discord message processing and confirmations
- ✅ Notion database integration with proper field mapping

## 📄 License

This project is part of the Discord bots collection. 