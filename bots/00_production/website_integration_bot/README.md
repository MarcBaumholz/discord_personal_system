# Website Integration Bot

Ein Discord Bot, der die GitHub Pages Website der Production Bots in Discord integriert und Live-Status-Updates bereitstellt.

## Features

- **Rich Website Embed**: Schöner Embed mit Website-Link und Bot-Status
- **Live Bot Monitoring**: Überwacht alle Production Bots und zeigt deren Status
- **Automatische Updates**: Postet Website-Embed beim Start
- **Status Commands**: Manuelle Befehle für Website und Bot-Status

## Setup

1. **Environment Variables** (in main `.env`):
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

2. **Dependencies installieren**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Bot starten**:
   ```bash
   python website_bot.py
   ```

## Commands

- `!website` - Website Embed posten
- `!botstatus` - Detaillierten Bot-Status anzeigen  
- `!help_website` - Hilfe anzeigen

## Channel

Der Bot postet automatisch in Channel ID: `1361083427264266425` (#overview)

## Website

Die integrierte Website: https://MarcBaumholz.github.io/discord_personal_system/

## ✅ Current Status (September 2025)

**🟡 BOT READY FOR DEPLOYMENT**

The Website Integration Bot is fully developed and ready to run, but not currently deployed in Docker.

### Development Status
- **Code**: ✅ Complete and functional
- **Docker**: ❌ Not currently containerized
- **Deployment**: 🟡 Ready for manual startup
- **Last Update**: September 2025

### Features Ready
- ✅ **Website Integration**: Rich embeds with GitHub Pages website link
- ✅ **Live Bot Monitoring**: Monitors all production bots and shows their status
- ✅ **Automatic Updates**: Posts website embed on startup
- ✅ **Status Commands**: Manual commands for website and bot status
- ✅ **Discord Integration**: Full Discord bot functionality

### To Deploy
1. Set up environment variables in `.env` (DISCORD_TOKEN)
2. Run: `python website_bot.py`
3. Consider Docker containerization for production use
