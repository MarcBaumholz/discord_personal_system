# YouTube Bot

Discord bot that automatically fetches YouTube videos from subscriptions and posts them to a Discord channel.

## Features

- 📅 **Daily Auto-Posts**: Automatically fetches and posts videos from yesterday at 9 AM
- 🔥 **Trending Videos**: Gets trending tech videos as fallback
- 🔍 **Video Search**: Search for specific videos
- 📺 **Rich Embeds**: Beautiful Discord embeds with thumbnails and metadata
- ⚡ **Rate Limited**: Respects Discord and YouTube API limits

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `../../.env`:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `GoogleClientkey`: Your YouTube Data API key
   - `GoogleClientID`: Your Google Client ID

3. Update the channel ID in the code:
   - `YOUTUBE_CHANNEL_ID = 1397292430239469669`

## Usage

The bot automatically posts videos daily at 9 AM. You can also use these commands:

### Commands

- `!status` - Check if the bot is running
- `!yesterday` - Manually fetch yesterday's videos
- `!trending` - Get trending tech videos
- `!search <query>` - Search for specific videos

### Example
```
!search python tutorial
!trending
!yesterday
```

## How it Works

1. **Daily Task**: Runs every 24 hours at 9 AM
2. **API Calls**: Uses YouTube Data API v3 to fetch videos
3. **Time Frame**: Gets videos published in the last 24 hours
4. **Channels**: Currently uses popular tech channels (can be extended with OAuth for personal subscriptions)
5. **Formatting**: Creates rich Discord embeds with video info
6. **Fallback**: If no subscription videos found, shows trending tech videos

## Channels Monitored

Currently monitors these popular tech channels:
- Google Developers
- Fireship
- freeCodeCamp
- Programming with Mosh
- Ben Eater

*Note: For personal subscriptions, OAuth implementation would be needed*

## Rate Limits

- Respects YouTube API quotas
- Implements Discord rate limiting (1 second between batches)
- Limits to 10 videos per message (Discord embed limit)

## Logs

Check `youtube_bot.log` for detailed operation logs.
