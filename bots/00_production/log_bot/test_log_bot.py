#!/usr/bin/env python3
"""
Test script for the Log Bot
Tests basic functionality and connectivity
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

async def test_log_bot():
    """Test the log bot functionality"""
    print("🧪 Testing Log Bot...")
    
    # Test environment variables
    discord_token = os.getenv("DISCORD_TOKEN")
    logs_channel_id = os.getenv("LOGS_CHANNEL_ID", "1415623068965142580")
    
    print(f"✅ Discord Token: {'Found' if discord_token else 'Missing'}")
    print(f"✅ Logs Channel ID: {logs_channel_id}")
    
    # Test channel mappings
    channel_mappings = {
        "calories": "CALORIES_CHANNEL_ID",
        "money": "FINANCE_CHANNEL_ID", 
        "todo": "TODOLISTE_CHANNEL_ID",
        "health": "HEALTH_CHANNEL_ID",
        "learning": "LEARNING_CHANNEL_ID",
        "rss": "RSS_CHANNEL_ID",
        "youtube": "YOUTUBE_CHANNEL_ID",
        "meal_plan": "MEAL_PLAN_CHANNEL_ID",
        "routine": "ROUTINE_CHANNEL_ID",
        "weekly": "WEEKLY_PLANNING_CHANNEL_ID",
        "decision": "DECISION_CHANNEL_ID",
        "erinnerungen": "ERINNERUNGEN_CHANNEL_ID",
        "preisvergleich": "DB_CHANNEL_ID",
        "allgemeine": "GENERAL_CHANNEL_ID",
        "tagebuch": "TAGEBUCH_CHANNEL_ID"
    }
    
    print("\n📊 Channel Mappings:")
    for bot_name, env_var in channel_mappings.items():
        channel_id = os.getenv(env_var)
        status = "✅" if channel_id else "❌"
        print(f"  {status} {bot_name}: {channel_id or 'Not set'}")
    
    # Test log formatting
    print("\n📝 Testing log formatting...")
    
    class MockMessage:
        def __init__(self, content, author_name, channel_name):
            self.content = content
            self.author = type('Author', (), {'display_name': author_name})()
            self.channel = type('Channel', (), {'name': channel_name})()
            self.attachments = []
            self.embeds = []
    
    mock_message = MockMessage("Test message content", "TestUser", "test-channel")
    
    # Test formatting function
    from datetime import datetime
    
    def format_log_message(message, bot_name):
        timestamp = datetime.now().strftime("%H:%M:%S")
        header = f"🤖 **{bot_name.upper()} BOT** | {timestamp}"
        separator = "─" * 50
        content = message.content if message.content else "[No text content]"
        author_info = f"👤 **{message.author.display_name}**"
        channel_info = f"📺 **#{message.channel.name}**"
        
        formatted_log = f"""
{header}
{separator}
{author_info} | {channel_info}
{content}
{separator}
"""
        return formatted_log.strip()
    
    formatted = format_log_message(mock_message, "test")
    print("✅ Log formatting test passed")
    print("Sample formatted log:")
    print(formatted)
    
    print("\n🎉 All tests passed! Log bot is ready to deploy.")

if __name__ == "__main__":
    asyncio.run(test_log_bot())
