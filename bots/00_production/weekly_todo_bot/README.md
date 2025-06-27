# Daily Todo Bot 📋

A Discord bot that helps manage daily household tasks through an interactive todo list with emoji reactions.

## 🎯 What It Does

The Daily Todo Bot creates an interactive daily todo list in your Discord channel where users can:
- View daily household tasks
- Mark tasks as complete using emoji reactions
- Toggle tasks back to incomplete
- Automatically reset tasks daily
- Persist progress throughout the day

## 🏠 Default Daily Todos

1. Clean bathroom
2. Clean bedroom  
3. Take out trash
4. Do laundry
5. Vacuum living room
6. Wash dishes
7. Make bed

## 🚀 How to Use

### Basic Commands
- Type `✅` or `:white_check_mark:` to display the todo list
- Type `!help_todo` for help information

### Marking Todos Complete
1. Bot displays the todo list with number reactions (1️⃣, 2️⃣, etc.)
2. Click on the number reaction to mark that todo as complete
3. Status changes from ⬜ to ✅ in real-time
4. Click the same number again to toggle it back to incomplete

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Discord bot token
- Discord server with a designated channel

### Installation

1. **Clone or download the bot files**
   ```bash
   cd discord/bots/daily_todo_bot
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv todo_env
   source todo_env/bin/activate  # On Windows: todo_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` and add your credentials:
   ```
   DISCORD_TOKEN=your_bot_token_here
   HAUSHALTSPLAN_CHANNEL_ID=your_channel_id_here
   ```

5. **Run the bot**
   ```bash
   python daily_todo_bot.py
   ```

### Getting Discord Credentials

1. **Bot Token**: 
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to "Bot" section
   - Copy the token

2. **Channel ID**:
   - Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
   - Right-click on your channel and select "Copy ID"

## 🧪 Testing

### Run Functionality Test
```bash
python test_bot_functionality.py
```

### Run Interactive Simulation
```bash
python demo_simulation.py
```

The simulation shows exactly how the bot works in Discord without requiring actual Discord connection.

## 📁 File Structure

```
daily_todo_bot/
├── daily_todo_bot.py          # Main bot code
├── test_bot_functionality.py  # Unit tests
├── demo_simulation.py         # Interactive demo
├── requirements.txt           # Dependencies
├── env_example.txt           # Environment template
├── completed_todos.json      # Persistent data (auto-created)
├── PLAN.md                   # Implementation plan
└── README.md                 # This file
```

## 🔧 Technical Details

### Features
- ✅ Automatic startup and welcome message
- 📋 Interactive todo list with emoji reactions  
- 🔄 Real-time status updates
- 👥 Multi-user support
- 💾 Persistent data storage (JSON)
- 📅 Daily automatic reset
- ❓ Help command support
- 🎨 Rich embed formatting

### Data Persistence
- Todos are saved to `completed_todos.json`
- Data persists through bot restarts
- Automatically resets at midnight (new day)

### Bot Permissions Required
- Send Messages
- Read Message History  
- Add Reactions
- Use External Emojis
- Embed Links

## 🤝 Usage Example

```
[10:30] Alice: ✅
[10:30] 🤖 Daily Todo Bot: Showing daily todos...

📋 Daily Todos
React with the number to mark a todo as complete.
──────────────────────────────────────────────────
1️⃣ 1. Clean bathroom - Status: ⬜
2️⃣ 2. Clean bedroom - Status: ⬜
3️⃣ 3. Take out trash - Status: ⬜
... etc

[10:32] Alice reacts with 1️⃣
[10:32] ✅ Clean bathroom marked as complete!

[10:35] Bob: !help_todo
[10:35] 🤖 Daily Todo Bot: [Help message displayed]
```

## 🔒 Security Notes

- Keep your Discord token secure and never commit it to version control
- The bot only responds in the designated haushaltsplan channel
- All data is stored locally in JSON format

## 🎉 What We Accomplished

1. ✅ **Environment Setup**: Created virtual environment and installed dependencies
2. ✅ **Code Analysis**: Reviewed and understood the bot functionality  
3. ✅ **Testing**: Created comprehensive test suite demonstrating all features
4. ✅ **Simulation**: Built interactive demo showing Discord interactions
5. ✅ **Documentation**: Created complete setup and usage instructions

The bot is fully functional and ready to deploy to Discord! 