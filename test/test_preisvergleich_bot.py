import pytest
import asyncio
import os
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add path for importing bot modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bots', 'preisvergleich_bot'))

# Import bot modules
from notion_manager import NotionProductManager
from offer_finder import OfferFinder
from simple_agent import SimpleOfferSearchAgent

class TestPreisvergleichBot:
    """Test suite for Preisvergleich Bot"""
    
    @pytest.fixture
    def notion_manager(self, mock_env_vars):
        """Create NotionProductManager instance with mocked client"""
        with patch('notion_manager.Client') as mock_client, \
             patch.dict(os.environ, {"PREISVERGLEICH_DATABASE_ID": "test-db-id"}):
            manager = NotionProductManager()
            manager.notion = mock_client
            yield manager
    
    @pytest.fixture
    def offer_finder(self, mock_env_vars):
        """Create OfferFinder instance"""
        finder = OfferFinder(api_key="test_key")
        yield finder
    
    @pytest.fixture
    def simple_agent(self, mock_env_vars):
        """Create SimpleOfferSearchAgent instance"""
        agent = SimpleOfferSearchAgent(api_key="test_key")
        yield agent
    
    def test_notion_manager_clean_database_id(self, notion_manager):
        """Test cleaning database ID from various formats"""
        # Test URL format with query parameters
        url_id = "https://notion.so/database/abc123def456?v=xyz789"
        cleaned = notion_manager._clean_database_id(url_id)
        assert len(cleaned) <= 32  # Should be cleaned
        
        # Test simple ID
        simple_id = "abc123def456ghi789jkl012mno345pq"
        cleaned = notion_manager._clean_database_id(simple_id)
        assert cleaned == simple_id
        
        # Test ID with slashes
        slash_id = "workspace/database/abc123def456ghi789jkl012mno345pq"
        cleaned = notion_manager._clean_database_id(slash_id)
        assert cleaned == "abc123def456ghi789jkl012mno345pq"
    
    @pytest.mark.asyncio
    async def test_notion_manager_get_watchlist(self, notion_manager, sample_notion_products):
        """Test getting product watchlist from Notion"""
        # Mock Notion response
        mock_response = {
            'results': [
                {
                    'properties': {
                        'Produktname': {
                            'title': [
                                {'plain_text': 'Milch 1L'}
                            ]
                        },
                        'Normalpreis': {
                            'number': 1.29
                        }
                    }
                },
                {
                    'properties': {
                        'Produktname': {
                            'title': [
                                {'plain_text': 'Brot Vollkorn'}
                            ]
                        },
                        'Normalpreis': {
                            'number': 2.49
                        }
                    }
                }
            ]
        }
        
        with patch.object(notion_manager.notion.databases, 'query', return_value=mock_response):
            products = notion_manager.get_watchlist()
            
            assert len(products) == 2
            assert products[0]['name'] == 'Milch 1L'
            assert products[0]['normal_price'] == 1.29
            assert products[1]['name'] == 'Brot Vollkorn'
            assert products[1]['normal_price'] == 2.49
    
    def test_offer_finder_create_prompt(self, offer_finder, sample_notion_products):
        """Test creating search prompt for LLM"""
        prompt = offer_finder.create_prompt(
            sample_notion_products,
            stores=["Rewe", "Edeka"],
            region="Baden-Württemberg"
        )
        
        assert "Milch 1L" in prompt
        assert "Brot Vollkorn" in prompt
        assert "Rewe" in prompt
        assert "Edeka" in prompt
        assert "Baden-Württemberg" in prompt
        assert "JSON" in prompt
        assert datetime.now().strftime("%d.%m.%Y") in prompt
    
    def test_offer_finder_query_llm(self, offer_finder, mock_requests):
        """Test querying LLM through OpenRouter"""
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': 'Test LLM response'
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        response = offer_finder.query_llm("Test prompt")
        
        assert 'choices' in response
        assert response['choices'][0]['message']['content'] == 'Test LLM response'
        mock_requests['post'].assert_called_once()
    
    def test_offer_finder_find_product_offers(self, offer_finder, sample_notion_products, mock_requests):
        """Test finding product offers"""
        # Mock successful LLM response with valid JSON
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '''[
                            {
                                "product_name": "Milch 1L",
                                "store": "Rewe",
                                "regular_price": 1.29,
                                "offer_price": 0.99,
                                "start_date": "2025-01-13",
                                "end_date": "2025-01-20",
                                "conditions": null,
                                "source": "Rewe website"
                            }
                        ]'''
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = offer_finder.find_product_offers(sample_notion_products)
        
        assert result['success'] is True
        assert 'offers' in result
        assert len(result['offers']) == 1
        assert result['offers'][0]['product_name'] == 'Milch 1L'
        assert result['offers'][0]['store'] == 'Rewe'
    
    def test_offer_finder_filter_valid_offers(self, offer_finder):
        """Test filtering valid offers (with price reductions)"""
        offers_data = {
            'success': True,
            'offers': [
                {
                    'product_name': 'Milch 1L',
                    'regular_price': 1.29,
                    'offer_price': 0.99,  # Valid offer
                    'store': 'Rewe'
                },
                {
                    'product_name': 'Brot',
                    'regular_price': 2.49,
                    'offer_price': 2.49,  # No discount
                    'store': 'Edeka'
                },
                {
                    'product_name': 'Butter',
                    'regular_price': 1.99,
                    'offer_price': None,  # No offer
                    'store': None
                }
            ]
        }
        
        valid_offers = offer_finder.filter_valid_offers(offers_data)
        
        assert len(valid_offers) == 1
        assert valid_offers[0]['product_name'] == 'Milch 1L'
        assert valid_offers[0]['offer_price'] < valid_offers[0]['regular_price']
    
    @pytest.mark.asyncio
    async def test_simple_agent_find_offers(self, simple_agent, sample_notion_products, mock_requests):
        """Test simple agent finding offers"""
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '''Ich habe nach Angeboten für die Produkte gesucht:
                        
                        Milch 1L:
                        - Rewe: Normalpreis 1,29€, Angebot 0,99€ (bis 20.01.2025)
                        
                        Brot Vollkorn:
                        - Keine aktuellen Angebote gefunden'''
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = await simple_agent.find_offers(sample_notion_products)
        
        assert result['success'] is True
        assert 'analysis' in result
        assert 'Milch 1L' in result['analysis']
        assert 'Rewe' in result['analysis']
    
    def test_offer_finder_handle_json_decode_error(self, offer_finder, sample_notion_products, mock_requests):
        """Test handling JSON decode errors"""
        # Mock invalid JSON response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': 'Invalid JSON response from LLM'
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = offer_finder.find_product_offers(sample_notion_products)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Failed to parse JSON' in result['error']
        assert 'raw_content' in result
    
    def test_offer_finder_handle_api_error(self, offer_finder, sample_notion_products, mock_requests):
        """Test handling API errors"""
        # Mock API error
        mock_requests['post'].side_effect = Exception("API connection failed")
        
        result = offer_finder.find_product_offers(sample_notion_products)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'API connection failed' in result['error']
    
    def test_offer_finder_default_stores(self, offer_finder):
        """Test default store configuration"""
        assert hasattr(offer_finder, 'default_stores')
        assert isinstance(offer_finder.default_stores, list)
        assert len(offer_finder.default_stores) > 0
        
        # Check for common German stores
        stores = offer_finder.default_stores
        assert any('Rewe' in store for store in stores)
        assert any('Edeka' in store for store in stores)
        assert any('Lidl' in store for store in stores)
    
    @pytest.mark.asyncio
    async def test_simple_agent_create_prompt(self, simple_agent, sample_notion_products):
        """Test prompt creation for simple agent"""
        prompt = simple_agent._create_search_prompt(
            sample_notion_products,
            stores=["Rewe", "Edeka"]
        )
        
        assert "Milch 1L" in prompt
        assert "Brot Vollkorn" in prompt
        assert "Rewe" in prompt
        assert "Edeka" in prompt
        assert "Angebote" in prompt  # German for offers
        assert "Preise" in prompt    # German for prices
    
    def test_notion_manager_error_handling(self, notion_manager):
        """Test error handling in Notion manager"""
        # Mock API error
        with patch.object(notion_manager.notion.databases, 'query', side_effect=Exception("API Error")):
            products = notion_manager.get_watchlist()
            
            # Should return empty list on error
            assert isinstance(products, list)
            assert len(products) == 0
    
    def test_offer_finder_json_extraction(self, offer_finder):
        """Test JSON extraction from various response formats"""
        # Test with markdown code block
        content_with_markdown = '''Here are the offers:
        ```json
        [{"product_name": "Test", "store": "Rewe"}]
        ```
        '''
        
        # Mock response structure
        response = {
            'choices': [
                {
                    'message': {
                        'content': content_with_markdown
                    }
                }
            ]
        }
        
        with patch.object(offer_finder, 'query_llm', return_value=response):
            result = offer_finder.find_product_offers([{"name": "Test", "normal_price": 1.0}])
            
            assert result['success'] is True
            assert len(result['offers']) == 1
            assert result['offers'][0]['product_name'] == 'Test'

if __name__ == "__main__":
    pytest.main([__file__]) 