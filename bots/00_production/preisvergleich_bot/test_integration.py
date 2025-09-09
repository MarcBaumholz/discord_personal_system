"""
Simple integration test for the fixed bot
"""
import os
import sys
from unittest.mock import patch, Mock

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_notion_manager_initialization():
    """Test that NotionProductManager handles missing credentials gracefully"""
    from notion_manager import NotionProductManager
    
    # Test with missing environment variables
    with patch.dict(os.environ, {}, clear=True):
        manager = NotionProductManager()
        assert not manager.is_initialized()
        
        # Should return empty list without crashing
        products = manager.get_watchlist()
        assert products == []
        print("✅ NotionProductManager handles missing credentials gracefully")

def test_notion_manager_with_valid_env():
    """Test NotionProductManager with valid environment variables"""
    from notion_manager import NotionProductManager
    
    with patch.dict(os.environ, {
        'NOTION_TOKEN': 'test_token',
        'NOTION_DATABASE_ID': '1e5d42a1faf580fe9450efa4d13cc4a2?v=xyz'
    }):
        with patch('notion_manager.Client') as mock_client:
            manager = NotionProductManager()
            assert manager.is_initialized()
            assert manager.database_id == '1e5d42a1faf580fe9450efa4d13cc4a2'
            print("✅ NotionProductManager initializes correctly with valid credentials")

def test_simple_agent():
    """Test SimpleOfferSearchAgent initialization"""
    from simple_agent import SimpleOfferSearchAgent
    
    # Test with missing environment variables
    with patch.dict(os.environ, {}, clear=True):
        agent = SimpleOfferSearchAgent()
        assert not agent.is_initialized()
        print("✅ SimpleOfferSearchAgent handles missing credentials gracefully")
    
    # Test with valid environment variables
    with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
        agent = SimpleOfferSearchAgent()
        assert agent.is_initialized()
        print("✅ SimpleOfferSearchAgent initializes successfully with credentials")

if __name__ == "__main__":
    print("Running integration tests...\n")
    test_notion_manager_initialization()
    test_notion_manager_with_valid_env()
    test_simple_agent()
    print("\n🎉 All tests passed! The bot should now handle initialization errors gracefully.")
