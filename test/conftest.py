import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json

# Add the bots directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bots'))

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_discord_bot():
    """Mock Discord bot instance"""
    bot = Mock()
    bot.user = Mock()
    bot.user.name = "TestBot"
    bot.user.id = 123456789
    bot.get_channel = Mock()
    bot.wait_until_ready = AsyncMock()
    return bot

@pytest.fixture
def mock_discord_channel():
    """Mock Discord channel"""
    channel = Mock()
    channel.id = 1234567890
    channel.send = AsyncMock()
    channel.name = "test-channel"
    return channel

@pytest.fixture
def mock_discord_message():
    """Mock Discord message"""
    message = Mock()
    message.author = Mock()
    message.author.id = 987654321
    message.author.name = "TestUser"
    message.channel = Mock()
    message.channel.id = 1234567890
    message.content = "test message"
    message.add_reaction = AsyncMock()
    message.remove_reaction = AsyncMock()
    message.reply = AsyncMock()
    message.edit = AsyncMock()
    return message

@pytest.fixture
def mock_discord_reaction():
    """Mock Discord reaction"""
    reaction = Mock()
    reaction.emoji = "✅"
    reaction.message = Mock()
    return reaction

@pytest.fixture
def mock_discord_user():
    """Mock Discord user"""
    user = Mock()
    user.id = 987654321
    user.name = "TestUser"
    user.display_name = "Test User"
    return user

@pytest.fixture
def mock_notion_client():
    """Mock Notion client"""
    client = Mock()
    client.databases = Mock()
    client.databases.query = Mock()
    client.pages = Mock()
    client.pages.retrieve = Mock()
    client.blocks = Mock()
    client.blocks.children = Mock()
    client.blocks.children.list = Mock()
    return client

@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response"""
    return {
        "choices": [
            {
                "message": {
                    "content": "Test AI response"
                }
            }
        ]
    }

@pytest.fixture
def sample_notion_products():
    """Sample product data from Notion"""
    return [
        {
            "name": "Milch 1L",
            "normal_price": 1.29
        },
        {
            "name": "Brot Vollkorn",
            "normal_price": 2.49
        },
        {
            "name": "Äpfel 1kg",
            "normal_price": 3.99
        }
    ]

@pytest.fixture
def sample_routines():
    """Sample routine data"""
    return [
        {
            "id": "routine1",
            "name": "Morgenroutine",
            "time": "07:00",
            "notes": "Aufstehen, Duschen, Anziehen, Frühstück",
            "day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        },
        {
            "id": "routine2", 
            "name": "Abendroutine",
            "time": "21:00",
            "notes": "Zähne putzen, Lesen, Schlafen",
            "day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
    ]

@pytest.fixture
def sample_weekly_plan():
    """Sample weekly planning data"""
    return {
        "id": "weekly-plan-1",
        "date": "2025-01-13",
        "focus_areas": ["Work", "Health", "Learning"],
        "weekly_goals": "1. Complete project\n2. Exercise 3 times\n3. Read book",
        "tasks": {
            "Monday": [
                {"title": "Team meeting", "completed": True, "time": "09:00"},
                {"title": "Work on project", "completed": False, "time": "11:00"}
            ],
            "Tuesday": [
                {"title": "Gym session", "completed": False, "time": "18:00"}
            ]
        }
    }

@pytest.fixture
def sample_recipes():
    """Sample recipe data"""
    return [
        {"id": "recipe1", "name": "Spaghetti Bolognese"},
        {"id": "recipe2", "name": "Chicken Curry"},
        {"id": "recipe3", "name": "Vegetable Stir Fry"},
        {"id": "recipe4", "name": "Fish Tacos"},
        {"id": "recipe5", "name": "Beef Stew"}
    ]

@pytest.fixture
def sample_interests():
    """Sample user interests"""
    return [
        "Programming",
        "Photography", 
        "Cooking",
        "Technology",
        "Books"
    ]

@pytest.fixture 
def mock_env_vars():
    """Mock environment variables"""
    env_vars = {
        "DISCORD_TOKEN": "test_discord_token",
        "NOTION_TOKEN": "test_notion_token",
        "OPENROUTER_API_KEY": "test_openrouter_key",
        "TODOIST_API_KEY": "test_todoist_key",
        "HAUSHALTSPLAN_CHANNEL_ID": "1361083769427202291",
        "ERINNERUNGEN_CHANNEL_ID": "1361083869729919046",
        "TODOLISTE_CHANNEL_ID": "1361083732638957669",
        "WEEKLY_PLANNING_CHANNEL_ID": "1234567890",
        "WISHLIST_CHANNEL_ID": "1234567891",
        "FINANCE_CHANNEL_ID": "1234567892"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def mock_requests():
    """Mock requests module for API calls"""
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get:
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"success": True}
        
        yield {"post": mock_post, "get": mock_get}

@pytest.fixture
def sample_todos():
    """Sample todo items"""
    return [
        "Clean bathroom",
        "Do laundry", 
        "Vacuum living room",
        "Wash dishes",
        "Make bed"
    ]

@pytest.fixture
def sample_completed_todos():
    """Sample completed todos JSON structure"""
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "completed": ["Clean bathroom", "Make bed"]
    } 