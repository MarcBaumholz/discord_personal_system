"""
Test suite for the Preisvergleich Bot
Following TDD principles - tests define expected behavior
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Import the modules we're testing
from notion_manager import NotionProductManager
from simple_agent import SimpleOfferSearchAgent
from scheduler import OfferScheduler


class TestNotionProductManager:
    """Test cases for NotionProductManager"""
    
    def test_init_with_valid_credentials(self):
        """Test that NotionProductManager initializes correctly with valid credentials"""
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token',
            'NOTION_DATABASE_ID': 'test_db_id'
        }):
            manager = NotionProductManager()
            assert manager.notion_token == 'test_token'
            assert manager.database_id == 'test_db_id'
    
    def test_init_missing_token_raises_error(self):
        """Test that missing NOTION_TOKEN raises ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Notion token is required"):
                NotionProductManager()
    
    def test_init_missing_database_id_raises_error(self):
        """Test that missing NOTION_DATABASE_ID raises ValueError"""
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token'
        }, clear=True):
            with pytest.raises(ValueError, match="Notion database ID is required"):
                NotionProductManager()
    
    def test_clean_database_id_with_url_format(self):
        """Test that database ID is cleaned when in URL format"""
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token',
            'NOTION_DATABASE_ID': '1e5d42a1faf580fe9450efa4d13cc4a2?v=1e5d42a1faf580e3bd44000ca336eeec&pvs=4'
        }):
            manager = NotionProductManager()
            assert manager.database_id == '1e5d42a1faf580fe9450efa4d13cc4a2'
    
    def test_clean_database_id_without_url_format(self):
        """Test that clean database ID remains unchanged"""
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token',
            'NOTION_DATABASE_ID': 'clean_db_id'
        }):
            manager = NotionProductManager()
            assert manager.database_id == 'clean_db_id'
    
    @patch('notion_manager.Client')
    def test_get_watchlist_success(self, mock_client):
        """Test successful retrieval of watchlist"""
        # Mock the Notion client response
        mock_response = {
            'results': [
                {
                    'properties': {
                        'Name': {'title': [{'plain_text': 'Test Product'}]},
                        'Price': {'number': 99.99},
                        'URL': {'url': 'https://example.com/product'}
                    }
                }
            ]
        }
        mock_client.return_value.databases.query.return_value = mock_response
        
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token',
            'NOTION_DATABASE_ID': 'test_db_id'
        }):
            manager = NotionProductManager()
            products = manager.get_watchlist()
            
            assert len(products) == 1
            assert products[0]['name'] == 'Test Product'
            assert products[0]['price'] == 99.99
            assert products[0]['url'] == 'https://example.com/product'
    
    @patch('notion_manager.Client')
    def test_get_watchlist_handles_notion_error(self, mock_client):
        """Test that get_watchlist handles Notion API errors gracefully"""
        mock_client.return_value.databases.query.side_effect = Exception("API Error")
        
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token',
            'NOTION_DATABASE_ID': 'test_db_id'
        }):
            manager = NotionProductManager()
            products = manager.get_watchlist()
            
            assert products == []


class TestSimpleOfferSearchAgent:
    """Test cases for SimpleOfferSearchAgent"""
    
    def test_init(self):
        """Test that SimpleOfferSearchAgent initializes correctly"""
        agent = SimpleOfferSearchAgent()
        assert agent is not None
    
    @patch('simple_agent.requests.get')
    def test_search_offers_success(self, mock_get):
        """Test successful offer search"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'offers': [
                {
                    'title': 'Test Product Offer',
                    'price': 89.99,
                    'discount': '10%',
                    'url': 'https://example.com/offer'
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        agent = SimpleOfferSearchAgent()
        offers = agent.search_offers('Test Product')
        
        assert len(offers) == 1
        assert offers[0]['title'] == 'Test Product Offer'
        assert offers[0]['price'] == 89.99
    
    @patch('simple_agent.requests.get')
    def test_search_offers_handles_api_error(self, mock_get):
        """Test that search_offers handles API errors gracefully"""
        mock_get.side_effect = Exception("API Error")
        
        agent = SimpleOfferSearchAgent()
        offers = agent.search_offers('Test Product')
        
        assert offers == []


class TestOfferScheduler:
    """Test cases for OfferScheduler"""
    
    def test_init(self):
        """Test that OfferScheduler initializes correctly"""
        scheduler = OfferScheduler()
        assert scheduler is not None
    
    def test_schedule_sunday_check(self):
        """Test that Sunday check can be scheduled"""
        scheduler = OfferScheduler()
        test_callback = Mock()
        
        # Should not raise an exception
        scheduler.schedule_sunday_check(test_callback)


class TestBotIntegration:
    """Integration tests for the bot functionality"""
    
    @patch('preisvergleich_bot.NotionProductManager')
    @patch('preisvergleich_bot.SimpleOfferSearchAgent')
    @patch('preisvergleich_bot.OfferScheduler')
    async def test_check_offers_with_products(self, mock_scheduler, mock_agent, mock_notion):
        """Test the check_offers function with products in watchlist"""
        # Mock the notion manager
        mock_notion_instance = Mock()
        mock_notion_instance.get_watchlist.return_value = [
            {'name': 'Test Product', 'price': 99.99, 'url': 'https://example.com'}
        ]
        mock_notion.return_value = mock_notion_instance
        
        # Mock the offer agent
        mock_agent_instance = Mock()
        mock_agent_instance.search_offers.return_value = [
            {'title': 'Test Product Sale', 'price': 79.99, 'discount': '20%', 'url': 'https://sale.com'}
        ]
        mock_agent.return_value = mock_agent_instance
        
        # Mock the scheduler
        mock_scheduler.return_value = Mock()
        
        # Import and test the function
        from preisvergleich_bot import check_offers
        
        # This should run without errors
        try:
            await check_offers()
        except Exception as e:
            pytest.fail(f"check_offers raised an exception: {e}")
    
    @patch('preisvergleich_bot.NotionProductManager')
    @patch('preisvergleich_bot.SimpleOfferSearchAgent')
    @patch('preisvergleich_bot.OfferScheduler')
    async def test_check_offers_with_no_products(self, mock_scheduler, mock_agent, mock_notion):
        """Test the check_offers function with empty watchlist"""
        # Mock the notion manager to return empty list
        mock_notion_instance = Mock()
        mock_notion_instance.get_watchlist.return_value = []
        mock_notion.return_value = mock_notion_instance
        
        # Mock other services
        mock_agent.return_value = Mock()
        mock_scheduler.return_value = Mock()
        
        # Import and test the function
        from preisvergleich_bot import check_offers
        
        # This should run without errors and handle empty list gracefully
        try:
            await check_offers()
        except Exception as e:
            pytest.fail(f"check_offers with empty list raised an exception: {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
