# YouTube Bot Setup Guide

## Overview
This bot automatically fetches videos from your YouTube subscriptions and posts them to Discord daily. It supports both OAuth (for personal subscriptions) and API key access (for public channels).

## Prerequisites
1. Discord Bot Token
2. YouTube Data API v3 Key
3. Google OAuth2 Credentials (optional, for personal subscriptions)

## Step 1: Create YouTube Data API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the YouTube Data API v3:
   - Go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create API Key:
   - Go to "APIs & Services" → "Credentials"
   - Click "+ CREATE CREDENTIALS" → "API Key"
   - Copy the generated API key
   - **Important**: Restrict the API key to YouTube Data API v3 for security

## Step 2: Create OAuth2 Credentials (Optional)

**Only needed if you want to access your personal YouTube subscriptions**

1. In Google Cloud Console → "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Choose "Desktop application"
4. Download the JSON file or copy Client ID and Client Secret

## Step 3: Configure Environment Variables

Edit your `.env` file in the discord folder:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
YOUTUBE_CHANNEL_ID=your_discord_channel_id_here

# YouTube API Configuration
YOUTUBE_API_KEY=your_youtube_api_key_here

# OAuth2 Configuration (Optional - for personal subscriptions)
GoogleClientID=your_google_client_id_here
GoogleClientkey=your_google_client_secret_here
```

## Step 4: Install Dependencies

```bash
cd discord/bots/youtube_bot
pip install -r requirements.txt
```

## Step 5: First Run & OAuth Setup

1. **Start the bot:**
   ```bash
   python youtube_bot.py
   ```

2. **If you configured OAuth credentials:**
   - The bot will automatically open a browser window for OAuth authorization
   - Log in to your Google account
   - Grant permission to access your YouTube subscriptions
   - The bot will save credentials to `token.pickle` for future use

3. **Test the bot:**
   - In Discord: `!status` - Check if bot is running
   - In Discord: `!subscriptions` - Test OAuth and show subscription count
   - In Discord: `!oauth_videos` - Get videos from your subscriptions

## Features

### Automatic Daily Updates
- Runs every day at 9 AM
- Posts videos from yesterday published by your subscriptions
- Falls back to popular tech channels if OAuth is not configured
- Final fallback to trending videos

### Manual Commands
- `!status` - Check bot status
- `!yesterday` - Get yesterday's videos manually
- `!trending` - Get trending tech videos
- `!search <query>` - Search for videos
- `!subscriptions` - Test OAuth functionality
- `!oauth_videos` - Get videos from personal subscriptions

### Fallback Behavior
1. **Primary**: Your personal subscriptions (via OAuth)
2. **Secondary**: Predefined popular tech channels
3. **Tertiary**: Trending technology videos

## File Structure
```
youtube_bot/
├── youtube_bot.py          # Main bot file
├── requirements.txt        # Python dependencies
├── SETUP_GUIDE.md         # This guide
├── .env                   # Environment variables (create this)
└── token.pickle           # OAuth credentials (auto-generated)
```

## Troubleshooting

### "API key not valid" Error
- Make sure you've created a YouTube Data API v3 key (not OAuth credentials)
- Verify the API key is correctly set in `.env` as `YOUTUBE_API_KEY`
- Check that YouTube Data API v3 is enabled in your Google Cloud project

### OAuth Issues
- Delete `token.pickle` and restart the bot to re-authenticate
- Make sure OAuth credentials are correctly set in `.env`
- Ensure you've granted permission for YouTube scope during authentication

### No Videos Found
- Check that your subscriptions have posted videos in the last 24 hours
- The bot will automatically fall back to popular channels and trending videos
- Use `!subscriptions` to verify OAuth is working

### Permission Denied
- Verify Discord bot has permission to send messages in the target channel
- Check that `YOUTUBE_CHANNEL_ID` matches your Discord channel ID

## Security Notes
- Keep your `.env` file secure and never commit it to version control
- Restrict your YouTube API key to YouTube Data API v3 only
- The `token.pickle` file contains sensitive OAuth tokens - keep it secure
- Consider rotating your API keys periodically

## Support
- Check Discord bot logs for detailed error messages
- Use `!status` to verify bot connectivity
- Test OAuth with `!subscriptions` command
- Manual testing with `!oauth_videos` command
