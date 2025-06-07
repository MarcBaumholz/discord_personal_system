# Routine Bot

A Discord bot that integrates with Notion to fetch routine data and uses OpenRouter's LLM to prepare and post daily routines to a Discord channel.

## Features

- Connects to Notion API to fetch routine data from your routine database
- Uses OpenRouter LLM to format and enhance your routine with suggestions
- Automatically posts daily routines to a designated Discord channel
- Schedules messages based on the time of day and routine type
- Sends reminders for upcoming routine activities
- **NEW:** Extracts detailed routine steps from Notion notes
- **NEW:** Interactive morning/evening routines with step-by-step checklists
- **NEW:** Track routine progress with reaction-based checkmarks
- **NEW:** DeepSeek LLM integration for intelligent routine step generation and formatting

## Implementation

1. **Notion Integration**
   - Fetch routine database entries
   - Parse routine data including time, duration, and status
   - Track routine history and completion
   - Extract detailed steps from routine notes

2. **OpenRouter/DeepSeek LLM Integration**
   - Generate personalized routines based on tracked data
   - Format routines in a clear, readable format
   - Add motivational elements and suggestions
   - **NEW:** Transform raw routine notes into clear, structured steps
   - **NEW:** Generate sensible default steps for routines without notes
   - **NEW:** Create consistent, actionable routine checklists

3. **Discord Scheduling**
   - Time-based posting of routines
   - Morning routine at 8:00 AM and evening routine at 10:00 PM
   - Interactive commands for routine management
   - Emoji reactions for step completion tracking
   - **NEW:** Consolidated step checklists with number reactions (1️⃣, 2️⃣, etc.)

## Routine Steps Enhancement

The bot now uses DeepSeek's AI to transform your raw routine notes into well-structured steps:

1. **Input Processing**:
   - Takes your notes from Notion (even if just rough bullet points)
   - Analyzes the routine type and time of day

2. **Step Generation**:
   - Creates logical, ordered steps for your routine
   - Breaks complex actions into simpler steps
   - Ensures steps are concise and action-oriented
   - Generates 5-10 steps per routine

3. **Presentation**:
   - Presents steps as a numbered list in Discord
   - Adds emoji reaction numbers for each step
   - Lets you track progress with checkmarks
   - Updates the list in real-time as you complete steps

4. **Persistence**:
   - Updates routine status in Notion when completed
   - Provides completion celebration message

## Configuration

The bot requires the following environment variables:
- `DISCORD_TOKEN` - Your Discord bot token
- `NOTION_TOKEN` - Your Notion API token
- `NOTION_ROUTINE_DATABASE_ID` - The ID of your Notion routine database
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `ROUTINE_CHANNEL_ID` - Discord channel ID for posting routines (1366687489720451114)

## Notion Database Setup

To work properly with the routine steps feature, your Notion database should have:

1. A **Notes** property (Rich text) - Used to store the routine steps
   - Format each step on a new line (bullet points and numbered lists are automatically parsed)
   - Example: 
     ```
     1. Drink a glass of water
     2. Meditate for 5 minutes
     3. Stretch for 3 minutes
     ```

2. Required properties:
   - **Routine Name** (Title) - Name of the routine
     - **NEW:** The bot can now identify morning/evening routines by having "morning" or "evening" in the name
   - **Time of Day** (Select) - Values should include "Morning", "Afternoon", or "Evening"
   - **Frequency** (Select) - Values like "Daily", "Weekdays", "Weekends", or specific days
   - **Status** (Select) - Values like "Not Started", "In Progress", "Completed"

**Note:** The bot will find morning/evening routines in two ways:
1. Looking for routines with "Time of Day" set to "Morning" or "Evening"
2. Looking for routines with "morning" or "evening" in their name (case insensitive)

## Running the Bot

### Installation

1. Clone the repository
2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Configuration

1. Create a `.env` file in the root directory with the following variables:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   NOTION_TOKEN=your_notion_token
   NOTION_ROUTINE_DATABASE_ID=your_database_id
   OPENROUTER_API_KEY=your_openrouter_key
   ROUTINE_CHANNEL_ID=your_channel_id
   ```

### Running

Start the bot with:
```
python routine_bot.py
```

## Testing the New Features

### Testing Morning/Evening Routines

You can test the new functionality in the following ways:

1. **Using emoji triggers:**
   - Type `:one:` in the routine channel to trigger the morning routine
   - Type `:two:` in the routine channel to trigger the evening routine

2. **Using commands:**
   - Type `!routine morning` to see your morning routine steps
   - Type `!routine evening` to see your evening routine steps

3. **Testing scheduled posts:**
   - For immediate testing, you can temporarily modify the check times in `routine_scheduler.py`
   - Change the time conditions in the `check_and_post_routines` method to match the current time

### Testing Step Generation with DeepSeek

1. **With existing notes:**
   - Add bullet points or numbered lists to your routine's "Notes" field in Notion
   - Trigger the routine in Discord to see how DeepSeek transforms and structures your notes

2. **Without notes:**
   - Create a new routine in Notion with an empty "Notes" field
   - DeepSeek will automatically generate sensible default steps based on the routine name and time of day

3. **Interactive step completion:**
   - Click the number emoji (1️⃣, 2️⃣, etc.) corresponding to a step to mark it as complete
   - The message will update in real-time to show a checkmark ✅ for completed steps
   - Click the ✅ reaction to mark the entire routine as complete at once

4. **Testing fallback mechanisms:**
   - If you want to test the system without DeepSeek, you can temporarily modify the API key in the `.env` file
   - The system will fall back to using your raw notes from Notion if DeepSeek is unavailable

## Usage

The bot runs automatically to post routines at scheduled times. It also supports the following commands:

- `!routine today` - Shows your routines for today
- `!routine tomorrow` - Shows planned routines for tomorrow
- `!routine morning` - Shows your morning routine with steps
- `!routine evening` - Shows your evening routine with steps
- `!routine help` - Displays help information

### Emoji Triggers

- 📢 or `:loudspeaker:` - Quickly show today's routines
- :one: - Show your morning routine with steps
- :two: - Show your evening routine with steps

### Morning and Evening Routines

The bot will automatically:
- Post morning routine at 8:00 AM
- Post evening routine at 10:00 PM

Each routine will display steps extracted from the routine's Notes field in Notion. Click the ✅ checkmark under each step to mark it as complete.

## Dependencies

- discord.py
- notion-client
- python-dotenv
- requests
- schedule
- dateutil
- pytz 