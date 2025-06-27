#!/usr/bin/env python3
"""
Tagebuch Bot Setup Validator
Helps validate the environment configuration before running the bot.
"""

import os
import sys
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError, HTTPResponseError, RequestTimeoutError
import discord

def load_environment():
    """Load environment variables"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        print("❌ .env file not found. Please copy env.example to .env and configure your tokens.")
        return False
    
    load_dotenv(env_path)
    return True

def validate_discord_token():
    """Validate Discord bot token"""
    token = os.getenv("DISCORD_TOKEN")
    if not token or token == "your_discord_bot_token_here":
        print("❌ DISCORD_TOKEN not configured")
        print("   Please set your Discord bot token in .env file")
        return False
    
    if len(token) < 50:  # Discord tokens are typically longer
        print("⚠️  DISCORD_TOKEN seems too short - please verify")
        return False
    
    print("✅ DISCORD_TOKEN configured")
    return True

def validate_notion_config():
    """Validate Notion configuration"""
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("TAGEBUCH_DATABASE_ID")
    
    if not token or token == "your_notion_integration_token_here":
        print("❌ NOTION_TOKEN not configured")
        print("   Please set your Notion integration token in .env file")
        return False
    
    if not database_id:
        print("❌ TAGEBUCH_DATABASE_ID not configured")
        return False
    
    print("✅ NOTION_TOKEN configured")
    print("✅ TAGEBUCH_DATABASE_ID configured")
    
    # Test connection
    try:
        notion = Client(auth=token)
        database = notion.databases.retrieve(database_id=database_id)
        print("✅ Notion database connection successful")
        database_name = database.get('title', [{}])[0].get('plain_text', 'Unknown')
        print(f"   Database: {database_name}")
        return True
    except (APIResponseError, HTTPResponseError, RequestTimeoutError) as e:
        print(f"❌ Notion connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error connecting to Notion: {e}")
        return False

def validate_channel_config():
    """Validate Discord channel configuration"""
    channel_id = os.getenv("TAGEBUCH_CHANNEL_ID")
    if not channel_id:
        print("❌ TAGEBUCH_CHANNEL_ID not configured")
        return False
    
    try:
        int(channel_id)
        print("✅ TAGEBUCH_CHANNEL_ID configured")
        return True
    except ValueError:
        print("❌ TAGEBUCH_CHANNEL_ID must be a number")
        return False

def print_setup_instructions():
    """Print setup instructions"""
    print("\n" + "="*60)
    print("🔧 SETUP INSTRUCTIONS")
    print("="*60)
    print()
    print("1. Discord Bot Setup:")
    print("   - Go to https://discord.com/developers/applications")
    print("   - Create a new application and bot")
    print("   - Copy the bot token to DISCORD_TOKEN in .env")
    print("   - Invite bot to your server with message permissions")
    print()
    print("2. Notion Integration Setup:")
    print("   - Go to https://www.notion.so/my-integrations")
    print("   - Create a new integration")
    print("   - Copy the integration token to NOTION_TOKEN in .env")
    print("   - Share your Tagebuch database with the integration")
    print()
    print("3. Channel Configuration:")
    print("   - Right-click on your Discord channel")
    print("   - Select 'Copy ID' (Developer Mode must be enabled)")
    print("   - Paste the ID to TAGEBUCH_CHANNEL_ID in .env")
    print()

def main():
    """Main validation function"""
    print("🔍 Tagebuch Bot Setup Validator")
    print("="*40)
    
    if not load_environment():
        print_setup_instructions()
        return False
    
    discord_ok = validate_discord_token()
    notion_ok = validate_notion_config()
    channel_ok = validate_channel_config()
    
    print("\n" + "="*40)
    print("📊 VALIDATION SUMMARY")
    print("="*40)
    
    if discord_ok and notion_ok and channel_ok:
        print("✅ All configuration valid! Bot is ready to run.")
        print("\nRun the bot with:")
        print("python tagebuch_bot.py")
        return True
    else:
        print("❌ Configuration incomplete. Please fix the issues above.")
        print_setup_instructions()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 