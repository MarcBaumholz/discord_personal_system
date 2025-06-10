# 🍽️ Calories Bot

An intelligent Discord bot that analyzes food images using AI vision, estimates calories, and automatically saves the data to a Notion database for dietary tracking.

## 🌟 Features

- **AI-Powered Food Recognition**: Uses OpenRouter's vision models to identify food items
- **Calorie Estimation**: Provides accurate calorie estimates based on portion size and food type
- **Automatic Database Storage**: Saves all analysis results to your Notion FoodIate database
- **Real-time Analysis**: Processes images instantly when uploaded to Discord
- **Confidence Scoring**: Shows how confident the AI is in its analysis
- **Rich Discord Integration**: Beautiful embeds with analysis results and status updates

## 🛠️ Tech Stack

- **Python 3.11+**: Core programming language
- **discord.py**: Discord bot framework
- **OpenRouter API**: AI vision analysis (using free qwen/qwen2-vl-7b-instruct model)
- **Notion API**: Database storage and management
- **aiohttp**: Async HTTP requests for image processing

## 📋 Prerequisites

1. **Discord Bot Token**: Create a bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. **OpenRouter API Key**: Sign up for free at [OpenRouter](https://openrouter.ai/keys)
3. **Notion Integration**: Create an integration at [Notion Integrations](https://www.notion.so/my-integrations)
4. **Notion Database Access**: Ensure your integration has access to database `20ed42a1faf5807497c2f350ff84ea8d`
5. **Discord Channel Access**: Bot needs access to channel `1382099540391497818`

## 🚀 Installation

### 1. Clone and Setup

```bash
cd discord/bots/Calories_bot

# Create virtual environment
python3 -m venv calories_env
source calories_env/bin/activate  # On Windows: calories_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp env_example.txt .env

# Edit .env file with your credentials
nano .env
```

Required environment variables:
```env
DISCORD_TOKEN=your_discord_bot_token_here
CALORIES_CHANNEL_ID=1382099540391497818
NOTION_TOKEN=your_notion_token_here
FOODIATE_DB_ID=20ed42a1faf5807497c2f350ff84ea8d
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token to your `.env` file
4. Invite bot to your server with these permissions:
   - Send Messages
   - Read Message History
   - Attach Files
   - Use Slash Commands
   - Add Reactions

### 4. Notion Database Setup

Your Notion database should have these properties:
- **Food** (Title): The identified food name
- **Calories** (Text): Estimated calories with "kcal" unit
- **date** (Date): When the analysis was performed
- **person** (Select): Single choice field with available names (e.g., "Marc", "Nick")
- **confidence** (Number): Analysis confidence score (0-100)
- **Picture** (Files): The uploaded food image

## 🎮 Usage

### Basic Usage

1. **Start the bot**:
   ```bash
   python calories_bot.py
   ```

2. **Upload food images**: Simply upload any food image to the calories channel (ID: 1382099540391497818)

3. **Get instant analysis**: The bot will automatically:
   - Download and analyze your image
   - Identify the food item(s)
   - Estimate calories
   - Save everything to your Notion database
   - Reply with detailed results

### Available Commands

- `!help_calories` - Show detailed help information
- `!test_analysis` - Test bot connectivity and readiness

### Example Workflow

1. User uploads image of pizza slice to calories channel
2. Bot responds: "🔄 Analyzing your food image..."
3. AI analyzes the image using OpenRouter vision model
4. Bot saves results to Notion database
5. Bot replies with rich embed showing:
   - Food identified: "Pizza slice"
   - Estimated calories: "285 kcal"
   - Confidence: "92.5%"
   - Description: "Single slice of pepperoni pizza"
   - Database status: "✅ Saved to FoodIate"

## 🤖 AI Model Information

### Recommended Free Model
**Model**: `qwen/qwen2-vl-7b-instruct`
- **Provider**: OpenRouter
- **Cost**: FREE (with rate limits)
- **Capabilities**: Excellent food recognition and calorie estimation
- **Strengths**: Works well with common foods, decent portion estimation

### Alternative Free Models
- `meta-llama/llama-3.2-11b-vision-instruct:free`
- `google/gemini-flash-1.5-8b`

## 📊 Notion Database Schema

The bot expects these exact property names in your Notion database:

| Property Name | Type | Description |
|---------------|------|-------------|
| `Food` | Title | Primary food name |
| `Calories` | Rich Text | Estimated calories with unit |
| `date` | Date | Analysis timestamp |
| `person` | Select | Single choice from available names |
| `confidence` | Number | Confidence score (0-100) |
| `Picture` | Files | Food image |

## 🔧 Configuration Options

### Supported Image Formats
- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- WebP (.webp)

### Channel Configuration
The bot is hardcoded to monitor channel ID `1382099540391497818`. To change this:
1. Update `CALORIES_CHANNEL_ID` in your `.env` file
2. Restart the bot

## 🧪 Testing

### Basic Connectivity Test
```bash
# In Discord calories channel
!test_analysis
```

This will show:
- ✅ Discord connection status
- ✅ OpenRouter API readiness
- ✅ Notion database connectivity

### Full Pipeline Test
1. Upload any food image to the calories channel
2. Wait for bot processing message
3. Verify analysis results in Discord
4. Check Notion database for new entry

## 🐛 Troubleshooting

### Common Issues

**Bot not responding to images**:
- Check bot has permissions in the channel
- Verify `CALORIES_CHANNEL_ID` in .env
- Ensure image format is supported

**AI analysis failing**:
- Verify `OPENROUTER_API_KEY` is valid
- Check OpenRouter free tier limits
- Try with clearer, well-lit food images

**Notion save failing**:
- Verify `NOTION_TOKEN` has database access
- Check database ID is correct: `20ed42a1faf5807497c2f350ff84ea8d`
- Ensure all required properties exist in database

**Dependencies issues**:
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

### Debug Mode
Add debug logging by modifying the bot:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance

- **Average Response Time**: 15-30 seconds
- **Accuracy**: ~80-90% for common foods
- **Rate Limits**: OpenRouter free tier limits apply
- **Image Size**: Up to 25MB (Discord limit)

## 🔒 Security & Privacy

- Images are temporarily processed but not stored locally
- Discord image URLs are used directly (they expire automatically)
- API keys are stored securely in environment variables
- No personal data is collected beyond Discord usernames

## 🚀 Deployment

### Running as a Service (Linux)
```bash
# Create systemd service
sudo nano /etc/systemd/system/calories-bot.service
```

```ini
[Unit]
Description=Calories Discord Bot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Documents/discord/bots/Calories_bot
Environment=PATH=/home/pi/Documents/discord/bots/Calories_bot/calories_env/bin
ExecStart=/home/pi/Documents/discord/bots/Calories_bot/calories_env/bin/python calories_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable calories-bot.service
sudo systemctl start calories-bot.service
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with sample food images
4. Submit a pull request

## 📄 License

This project is open source. Please check individual API terms of service:
- [OpenRouter Terms](https://openrouter.ai/terms)
- [Discord Terms](https://discord.com/terms)
- [Notion Terms](https://www.notion.so/terms)

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for specific error messages
3. Test individual components (Discord, OpenRouter, Notion)
4. Verify all API keys and permissions

## 🔄 Version History

- **v1.0.0** - Initial release with core functionality
  - AI food recognition using OpenRouter
  - Automatic Notion database integration
  - Discord embed responses
  - Basic error handling and logging 