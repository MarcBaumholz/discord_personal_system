import pytest
import asyncio
import os
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add path for importing bot modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bots', 'meal_plan_bot'))

# Import bot module
import meal_plan_bot

class TestMealPlanBot:
    """Test suite for Meal Plan Bot"""
    
    @pytest.fixture
    def mock_bot(self, mock_env_vars):
        """Create bot instance with mocked dependencies"""
        with patch('meal_plan_bot.bot') as mock_bot:
            mock_bot.user = Mock()
            mock_bot.user.name = "MealPlanBot"
            mock_bot.get_channel = Mock()
            yield mock_bot
    
    def test_get_notion_headers(self):
        """Test Notion API headers generation"""
        with patch.dict(os.environ, {"NOTION_TOKEN": "test_token"}):
            headers = meal_plan_bot.get_notion_headers()
            
            assert "Authorization" in headers
            assert "Bearer test_token" in headers["Authorization"]
            assert headers["Content-Type"] == "application/json"
            assert headers["Notion-Version"] == "2022-06-28"
    
    def test_find_recipe_database(self, mock_requests):
        """Test finding recipe database in Notion"""
        # Mock successful search response
        mock_requests['post'].return_value.json.return_value = {
            'results': [
                {
                    'id': 'test-db-id',
                    'title': [
                        {'plain_text': 'Rezepte schnell'}
                    ]
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = meal_plan_bot.find_recipe_database()
        
        assert result is True
        assert meal_plan_bot.NOTION_DATABASE_ID == 'test-db-id'
        mock_requests['post'].assert_called_once()
    
    def test_get_recipes_from_notion(self, mock_requests, sample_recipes):
        """Test getting recipes from Notion database"""
        # Set database ID
        meal_plan_bot.NOTION_DATABASE_ID = "test-db-id"
        
        # Mock database query response
        mock_requests['post'].return_value.json.return_value = {
            'results': [
                {
                    'id': 'recipe1',
                    'properties': {
                        'Rezeptname': {
                            'title': [
                                {'plain_text': 'Spaghetti Bolognese'}
                            ]
                        }
                    }
                },
                {
                    'id': 'recipe2',
                    'properties': {
                        'Rezeptname': {
                            'title': [
                                {'plain_text': 'Chicken Curry'}
                            ]
                        }
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        recipes = meal_plan_bot.get_recipes_from_notion()
        
        assert len(recipes) == 2
        assert recipes[0]['name'] == 'Spaghetti Bolognese'
        assert recipes[1]['name'] == 'Chicken Curry'
        assert recipes[0]['id'] == 'recipe1'
    
    def test_get_todoist_headers(self):
        """Test Todoist API headers generation"""
        with patch.dict(os.environ, {"TODOIST_API_KEY": "test_todoist_key"}):
            headers = meal_plan_bot.get_todoist_headers()
            
            assert "Authorization" in headers
            assert "Bearer test_todoist_key" in headers["Authorization"]
            assert headers["Content-Type"] == "application/json"
    
    def test_extract_shopping_list(self):
        """Test extracting shopping list from meal plan text"""
        meal_plan_text = """
        # Meal Plan for Sunday
        
        ## Shopping List:
        - Spaghetti 500g
        - Ground beef 400g
        - Tomatoes 3 pieces
        - Onions 2 pieces
        
        ## Prep Schedule:
        1. Start at 10 AM
        2. Prep vegetables
        """
        
        shopping_list = meal_plan_bot.extract_shopping_list(meal_plan_text)
        
        assert "Spaghetti 500g" in shopping_list
        assert "Ground beef 400g" in shopping_list
        assert "Prep Schedule" not in shopping_list
    
    def test_format_shopping_list_for_todoist(self):
        """Test formatting shopping list for Todoist"""
        shopping_list_text = """
        VEGETABLES:
        - Tomatoes 3 pieces
        - Onions 2 pieces
        
        MEAT:
        - Ground beef 400g
        """
        
        items = meal_plan_bot.format_shopping_list_for_todoist(shopping_list_text)
        
        assert len(items) == 3
        assert items[0]['content'] == 'Tomatoes 3 pieces'
        assert 'VEGETABLES' in items[0]['description']
        assert items[2]['content'] == 'Ground beef 400g'
        assert 'MEAT' in items[2]['description']
    
    def test_add_to_todoist(self, mock_requests):
        """Test adding items to Todoist"""
        # Mock projects response
        mock_requests['get'].return_value.json.return_value = [
            {
                'id': 123,
                'name': 'Einkaufsliste'
            }
        ]
        mock_requests['get'].return_value.status_code = 200
        
        # Mock task creation response
        mock_requests['post'].return_value.status_code = 200
        
        items = [
            {
                'content': 'Milk 1L',
                'description': 'From meal plan - Category: Dairy'
            },
            {
                'content': 'Bread',
                'description': 'From meal plan - Category: Bakery'
            }
        ]
        
        added_items = meal_plan_bot.add_to_todoist(items)
        
        assert len(added_items) == 2
        assert 'Milk 1L' in added_items
        assert 'Bread' in added_items
    
    def test_generate_meal_plan(self, mock_requests, sample_recipes):
        """Test generating meal plan with OpenRouter"""
        selected_recipes = sample_recipes[:3]
        
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': """
                        # Meal Prep Plan for Sunday
                        
                        ## Selected Meals:
                        1. Spaghetti Bolognese - Classic Italian pasta dish
                        2. Chicken Curry - Spicy and flavorful
                        3. Vegetable Stir Fry - Quick and healthy
                        
                        ## SHOPPING LIST:
                        - Spaghetti 500g
                        - Ground beef 400g
                        - Chicken breast 600g
                        - Mixed vegetables 800g
                        
                        ## Prep Schedule:
                        - 10:00 AM: Start prep
                        - 11:00 AM: Cook sauces
                        - 12:00 PM: Package meals
                        """
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = meal_plan_bot.generate_meal_plan(selected_recipes)
        
        assert "Meal Prep Plan" in result
        assert "Spaghetti Bolognese" in result
        assert "SHOPPING LIST" in result
        assert mock_requests['post'].called
    
    @pytest.mark.asyncio
    async def test_generate_weekly_meal_plan(self, mock_discord_channel, mock_requests, sample_recipes):
        """Test complete weekly meal plan generation workflow"""
        # Mock finding recipes
        with patch('meal_plan_bot.get_recipes_from_notion', return_value=sample_recipes), \
             patch('meal_plan_bot.generate_meal_plan') as mock_generate, \
             patch('meal_plan_bot.extract_shopping_list') as mock_extract, \
             patch('meal_plan_bot.format_shopping_list_for_todoist') as mock_format, \
             patch('meal_plan_bot.add_to_todoist') as mock_add_todoist, \
             patch('meal_plan_bot.send_long_message') as mock_send_long:
            
            mock_generate.return_value = "Test meal plan"
            mock_extract.return_value = "- Milk\n- Bread"
            mock_format.return_value = [{'content': 'Milk', 'description': 'Test'}]
            mock_add_todoist.return_value = ['Milk']
            
            await meal_plan_bot.generate_weekly_meal_plan(mock_discord_channel)
            
            # Verify all steps were called
            assert mock_discord_channel.send.call_count >= 4  # Multiple status messages
            mock_generate.assert_called_once()
            mock_extract.assert_called_once()
            mock_format.assert_called_once()
            mock_add_todoist.assert_called_once()
            mock_send_long.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_long_message_short(self, mock_discord_channel):
        """Test sending short message (under limit)"""
        short_content = "This is a short message"
        
        await meal_plan_bot.send_long_message(mock_discord_channel, short_content)
        
        mock_discord_channel.send.assert_called_once_with(short_content)
    
    @pytest.mark.asyncio
    async def test_send_long_message_long(self, mock_discord_channel):
        """Test sending long message (over limit)"""
        # Create a message over 1900 characters
        long_content = "A" * 2000
        
        await meal_plan_bot.send_long_message(mock_discord_channel, long_content)
        
        # Should be called multiple times for parts
        assert mock_discord_channel.send.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_on_message_thumbs_up_trigger(self, mock_discord_message, mock_discord_channel):
        """Test on_message event with thumbs up trigger"""
        mock_discord_message.content = "👍"
        mock_discord_message.channel.id = int(os.getenv("ERINNERUNGEN_CHANNEL_ID"))
        mock_discord_message.author = Mock()
        mock_discord_message.author.name = "TestUser"
        
        with patch('meal_plan_bot.generate_weekly_meal_plan') as mock_generate:
            await meal_plan_bot.on_message(mock_discord_message)
            
            # Verify reactions were added
            mock_discord_message.add_reaction.assert_called_with("🔍")
            mock_discord_message.remove_reaction.assert_called_with("🔍", meal_plan_bot.bot.user)
            mock_discord_message.add_reaction.assert_called_with("✅")
            mock_generate.assert_called_once_with(mock_discord_message.channel)
    
    @pytest.mark.asyncio
    async def test_help_meal_command(self, mock_discord_channel):
        """Test help command functionality"""
        # Create a mock context
        ctx = Mock()
        ctx.channel.id = int(os.getenv("ERINNERUNGEN_CHANNEL_ID"))
        ctx.send = AsyncMock()
        
        await meal_plan_bot.help_meal(ctx)
        
        # Verify help message was sent
        ctx.send.assert_called_once()
        help_text = ctx.send.call_args[0][0]
        assert "Meal Plan Bot Help" in help_text
        assert "weekly meal plan" in help_text
    
    def test_extract_shopping_list_no_section(self):
        """Test extracting shopping list when no clear section exists"""
        meal_plan_text = """
        # Meal Plan
        
        Some general text about cooking.
        """
        
        shopping_list = meal_plan_bot.extract_shopping_list(meal_plan_text)
        
        # Should return empty string or minimal content
        assert len(shopping_list) <= 50  # Minimal content
    
    def test_format_shopping_list_empty(self):
        """Test formatting empty shopping list"""
        items = meal_plan_bot.format_shopping_list_for_todoist("")
        
        assert isinstance(items, list)
        assert len(items) == 0

if __name__ == "__main__":
    pytest.main([__file__]) 