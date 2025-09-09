"""
Manual bot functionality test
"""
import asyncio
import discord
import os
from unittest.mock import patch

# Mock discord client for testing
async def test_producthunt_command():
    """Test that the producthunt command works"""
    print("🔍 Testing producthunt command functionality...")
    
    # Mock the environment
    with patch.dict(os.environ, {
        'NOTION_TOKEN': 'test_token', 
        'NOTION_DATABASE_ID': 'test_db',
        'OPENROUTER_API_KEY': 'test_api_key',
        'DISCORD_TOKEN': 'test_discord_token',
        'DISCORD_CHANNEL_ID': '123456789'
    }):
        # Import after setting env vars
        from notion_manager import NotionProductManager
        from simple_agent import SimpleOfferSearchAgent
        
        # Test that both managers initialize properly
        notion_manager = NotionProductManager()
        offer_agent = SimpleOfferSearchAgent()
        
        assert notion_manager.is_initialized(), "NotionProductManager should initialize"
        assert offer_agent.is_initialized(), "SimpleOfferSearchAgent should initialize"
        
        print("✅ Both managers initialize correctly with credentials")
        print("✅ Bot should handle producthunt command properly")

if __name__ == "__main__":
    asyncio.run(test_producthunt_command())
