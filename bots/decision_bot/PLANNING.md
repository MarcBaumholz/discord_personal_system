# 🧠 Decision Bot - Planning Document

## 🎯 Goal
Build a Discord bot that analyzes user questions/decisions against their personal values, goals, and life data stored in CSV files. The bot provides personalized guidance on whether decisions align with the user's authentic self and offers actionable next steps.

## 👤 User Stories
- As a user, I can ask questions about life decisions in Discord
- As a user, I want the bot to analyze if my decision aligns with my values and goals
- As a user, I want detailed, personalized responses based on my uploaded data
- As a user, I want actionable next steps and recommendations
- As a user, I can upload CSV files with my personal data to improve recommendations

## 📦 Data Model
**Entities:**
- User Profile (values, goals, identity, preferences)
- CSV Data Files (uploaded personal information)
- Decision Questions (user queries)
- Analysis Results (bot responses with alignment scores)

**Data Sources:**
- CSV files in `/upload` folder containing:
  - Personal values and priorities
  - Life goals and aspirations  
  - Identity markers and personality traits
  - Past decisions and outcomes
  - What brings joy and fulfillment

## 🔪 MVP Definition
**Core Features:**
1. CSV file loading and parsing from `/upload` folder
2. Discord bot responding to specific channel (1384282192171110412)
3. OpenRouter API integration for decision analysis
4. Personalized response generation based on user data
5. Actionable next steps and recommendations

**Must Have:**
- Load personal data from CSV files
- Analyze decision alignment with values/goals
- Generate detailed, thoughtful responses
- Provide actionable recommendations
- Environment variable configuration

## 🧱 Architecture Components
1. **Discord Bot Handler** - Message processing and responses
2. **CSV Data Loader** - Parse and load user personal data
3. **OpenRouter Service** - LLM API integration for analysis
4. **Decision Analyzer** - Core logic for alignment analysis
5. **Response Generator** - Format personalized recommendations

## ⚙️ Tech Stack
- **Language:** Python 3.11+
- **Discord:** discord.py
- **CSV Processing:** pandas
- **API:** OpenRouter (DeepSeek model)
- **Environment:** python-dotenv
- **Logging:** built-in logging module

## 🚀 Development Process
1. Create basic bot structure with Discord integration
2. Implement CSV data loading from `/upload` folder
3. Build OpenRouter service for LLM integration
4. Create decision analysis logic with detailed prompting
5. Implement response formatting for Discord
6. Test with sample data and questions
7. Add error handling and logging

## 📁 File Structure
```
decision_bot/
├── decision_bot.py          # Main bot file
├── csv_data_loader.py       # CSV file processing
├── openrouter_service.py    # LLM API integration
├── decision_analyzer.py     # Core analysis logic
├── upload/                  # User CSV data files
├── requirements.txt         # Dependencies
├── README.md               # Documentation
└── PLANNING.md            # This file
```

## 🔧 Environment Variables
```
DISCORD_TOKEN=your_discord_bot_token
OPENROUTER_API_KEY=your_openrouter_api_key
DECISION_CHANNEL_ID=1384282192171110412
```

## 🎨 Response Format
Each bot response will include:
1. **Alignment Analysis** - How well the decision fits user's values/goals
2. **Detailed Reasoning** - Why it does/doesn't align with personal data
3. **Actionable Steps** - Concrete next actions to take
4. **Reflection Questions** - Additional considerations
5. **Risk Assessment** - Potential challenges or benefits

## 🧪 Testing Strategy
- Test CSV loading with sample personal data
- Test decision analysis with various question types
- Test Discord integration and message formatting
- Test error handling for missing data/API failures
- Mock OpenRouter API calls for unit testing

## 🔒 Data Privacy
- CSV files stored locally in `/upload` folder
- No personal data sent to logs
- Secure API key management via environment variables
- User data only processed for analysis, not stored permanently 