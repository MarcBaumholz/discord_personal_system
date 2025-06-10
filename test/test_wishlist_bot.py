import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add path for importing bot modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bots', 'Wishlist_bot'))

# Import bot modules
from notion_manager import NotionManager
from openrouter_service import OpenRouterService
from product_finder import ProductFinder
from product_presenter import ProductPresenter

class TestWishlistBot:
    """Test suite for Wishlist Bot"""
    
    @pytest.fixture
    def notion_manager(self, mock_env_vars):
        """Create NotionManager instance with mocked client"""
        with patch('notion_manager.Client') as mock_client:
            manager = NotionManager()
            manager.notion = mock_client
            yield manager
    
    @pytest.fixture
    def openrouter_service(self, mock_env_vars):
        """Create OpenRouterService instance"""
        service = OpenRouterService()
        yield service
    
    @pytest.fixture
    def product_finder(self, openrouter_service, notion_manager):
        """Create ProductFinder instance"""
        finder = ProductFinder(openrouter_service, notion_manager)
        yield finder
    
    @pytest.fixture
    def product_presenter(self, mock_discord_bot):
        """Create ProductPresenter instance"""
        presenter = ProductPresenter(mock_discord_bot, 123456789)
        yield presenter
    
    @pytest.mark.asyncio
    async def test_notion_manager_get_interests(self, notion_manager, sample_interests):
        """Test getting interests from Notion"""
        # Mock Notion response
        mock_response = {
            'results': [
                {
                    'properties': {
                        'Name': {
                            'type': 'title',
                            'title': [{'plain_text': 'Programming'}]
                        },
                        'Kategorie': {
                            'type': 'select',
                            'select': {'name': 'Technology'}
                        }
                    }
                },
                {
                    'properties': {
                        'Name': {
                            'type': 'title',
                            'title': [{'plain_text': 'Photography'}]
                        }
                    }
                }
            ]
        }
        
        with patch.object(notion_manager.notion.databases, 'query', return_value=mock_response):
            interests = await notion_manager.get_interests()
            
            assert len(interests) == 2
            assert interests[0]['name'] == 'Programming'
            assert interests[0]['category'] == 'Technology'
            assert interests[1] == 'Photography'
    
    @pytest.mark.asyncio
    async def test_notion_manager_extract_interests_from_page(self, notion_manager):
        """Test extracting interests from a specific page"""
        # Mock page response
        mock_page = {'id': 'test-page-id'}
        
        # Mock blocks response
        mock_blocks = {
            'results': [
                {
                    'type': 'bulleted_list_item',
                    'bulleted_list_item': {
                        'rich_text': [{'plain_text': 'Web Development'}]
                    }
                },
                {
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [{'plain_text': 'AI: Artificial Intelligence'}]
                    }
                }
            ]
        }
        
        with patch.object(notion_manager.notion.pages, 'retrieve', return_value=mock_page), \
             patch.object(notion_manager.notion.blocks.children, 'list', return_value=mock_blocks):
            
            interests = await notion_manager.extract_interests_from_page('test-page-id')
            
            assert 'Web Development' in interests
            assert 'AI' in interests
    
    @pytest.mark.asyncio
    async def test_openrouter_service_get_product_suggestions(self, openrouter_service, mock_requests):
        """Test getting product suggestions"""
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '''[
                            {
                                "name": "MacBook Pro",
                                "description": "Professional laptop for developers",
                                "price": "$1999-$2999",
                                "url": "https://apple.com/macbook-pro",
                                "image_url": "https://example.com/macbook.jpg"
                            }
                        ]'''
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        products = await openrouter_service.get_product_suggestions("Programming", num_products=1)
        
        assert len(products) == 1
        assert products[0]['name'] == 'MacBook Pro'
        assert products[0]['description'] == 'Professional laptop for developers'
        assert mock_requests['post'].called
    
    @pytest.mark.asyncio
    async def test_openrouter_service_get_product_search_queries(self, openrouter_service, mock_requests):
        """Test generating search queries"""
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '["programming keyboards 2025", "developer tools software", "coding accessories"]'
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        queries = await openrouter_service.get_product_search_queries(['Programming', 'Technology'])
        
        assert len(queries) == 3
        assert 'programming keyboards' in queries[0]
        assert mock_requests['post'].called
    
    @pytest.mark.asyncio
    async def test_openrouter_service_analyze_search_results(self, openrouter_service, mock_requests):
        """Test analyzing search results"""
        search_results = """
        MacBook Pro - $1999
        Dell XPS 13 - $1299
        ThinkPad X1 Carbon - $1599
        """
        
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '''[
                            {
                                "name": "MacBook Pro",
                                "description": "High-performance laptop",
                                "price": "$1999",
                                "url": "https://apple.com",
                                "image_url": "https://example.com/image.jpg"
                            }
                        ]'''
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        products = await openrouter_service.analyze_search_results(search_results, "Programming")
        
        assert len(products) == 1
        assert products[0]['name'] == 'MacBook Pro'
        assert mock_requests['post'].called
    
    def test_product_finder_select_random_interests(self, product_finder):
        """Test selecting random interests"""
        interests = [
            {'name': 'Programming', 'category': 'Technology'},
            'Photography',
            'Cooking',
            'Travel',
            'Music'
        ]
        
        selected = product_finder.select_random_interests(interests, 3)
        
        assert len(selected) <= 3
        assert all(isinstance(interest, str) for interest in selected)
    
    @pytest.mark.asyncio
    async def test_product_finder_find_products_for_interest(self, product_finder, mock_requests):
        """Test finding products for a specific interest"""
        # Mock web search and AI response
        with patch.object(product_finder, '_perform_web_search', return_value="MacBook Pro - $1999"), \
             patch.object(product_finder.openrouter_service, 'analyze_search_results') as mock_analyze:
            
            mock_analyze.return_value = [
                {
                    'name': 'MacBook Pro',
                    'description': 'Professional laptop',
                    'price': '$1999',
                    'url': 'https://apple.com',
                    'image_url': 'https://example.com/image.jpg'
                }
            ]
            
            products = await product_finder.find_products_for_interest("Programming")
            
            assert len(products) == 1
            assert products[0]['name'] == 'MacBook Pro'
            mock_analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_product_finder_find_discounted_products(self, product_finder, sample_interests):
        """Test finding discounted products"""
        with patch.object(product_finder, '_perform_web_search', return_value="Sale: MacBook Pro - 20% off"), \
             patch.object(product_finder.openrouter_service, 'analyze_search_results') as mock_analyze:
            
            mock_analyze.return_value = [
                {
                    'name': 'MacBook Pro',
                    'description': 'Professional laptop on sale',
                    'price': '$1599 (was $1999)',
                    'url': 'https://apple.com',
                    'image_url': 'https://example.com/image.jpg',
                    'interest': 'Programming'
                }
            ]
            
            deals = await product_finder.find_discounted_products(sample_interests)
            
            assert len(deals) >= 1
            assert deals[0]['name'] == 'MacBook Pro'
            assert 'interest' in deals[0]
    
    @pytest.mark.asyncio
    async def test_product_finder_perform_web_search(self, product_finder):
        """Test web search functionality"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html><body>Test search results</body></html>")
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await product_finder._perform_web_search("programming keyboards")
            
            assert "programming keyboards" in result
            assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_product_presenter_present_product(self, product_presenter, mock_discord_channel):
        """Test presenting a product in Discord"""
        product = {
            'name': 'MacBook Pro',
            'description': 'Professional laptop for developers',
            'price': '$1999',
            'url': 'https://apple.com/macbook-pro',
            'image_url': 'https://example.com/macbook.jpg',
            'interest': 'Programming'
        }
        
        product_presenter.bot.get_channel.return_value = mock_discord_channel
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            
            mock_session.return_value.__aenter__.return_value.head.return_value.__aenter__.return_value = mock_response
            
            await product_presenter.present_product(product, mock_discord_channel)
            
            mock_discord_channel.send.assert_called_once()
            args = mock_discord_channel.send.call_args[1]
            assert 'embed' in args
    
    @pytest.mark.asyncio
    async def test_product_presenter_generate_product_image(self, product_presenter):
        """Test generating product image"""
        with patch('PIL.Image.new') as mock_image, \
             patch('PIL.ImageDraw.Draw') as mock_draw, \
             patch('PIL.ImageFont.load_default') as mock_font:
            
            mock_image_instance = Mock()
            mock_image.return_value = mock_image_instance
            mock_image_instance.save = Mock()
            
            result = await product_presenter._generate_product_image("Test Product")
            
            assert result is not None
            mock_image.assert_called_once()
    
    def test_product_presenter_get_random_color(self, product_presenter):
        """Test random color generation"""
        color = product_presenter._get_random_color()
        
        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(0 <= c <= 200 for c in color)
    
    def test_product_presenter_wrap_text(self, product_presenter):
        """Test text wrapping functionality"""
        with patch('PIL.ImageFont.load_default') as mock_font:
            mock_font.return_value.getbbox = Mock(return_value=(0, 0, 100, 20))
            
            result = product_presenter._wrap_text("This is a long text that should be wrapped", mock_font.return_value, 150)
            
            assert isinstance(result, str)
            assert '\n' in result or len(result) <= 150

if __name__ == "__main__":
    pytest.main([__file__]) 