import pytest
import asyncio
import json
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch, mock_open
from datetime import datetime

# Add path for importing bot modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bots', 'daily_todo_bot'))

# Import the bot module
import daily_todo_bot

class TestDailyTodoBot:
    """Test suite for Daily Todo Bot"""
    
    @pytest.fixture
    def bot_with_mocks(self, mock_env_vars):
        """Create bot instance with mocked dependencies"""
        with patch('discord.Client'), \
             patch('daily_todo_bot.bot') as mock_bot:
            mock_bot.user = Mock()
            mock_bot.user.name = "DailyTodoBot"
            mock_bot.get_channel = Mock()
            yield mock_bot
    
    @pytest.fixture
    def temp_json_file(self):
        """Create temporary JSON file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"date": "2025-01-13", "completed": []}, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    def test_load_completed_todos_existing_file(self, temp_json_file):
        """Test loading completed todos from existing file"""
        with patch('daily_todo_bot.COMPLETED_TODOS_FILE', temp_json_file):
            result = daily_todo_bot.load_completed_todos()
            
            assert result["date"] == "2025-01-13"
            assert result["completed"] == []
    
    def test_load_completed_todos_no_file(self):
        """Test loading completed todos when file doesn't exist"""
        with patch('daily_todo_bot.COMPLETED_TODOS_FILE', 'nonexistent.json'):
            result = daily_todo_bot.load_completed_todos()
            
            assert "date" in result
            assert "completed" in result
            assert isinstance(result["completed"], list)
    
    def test_save_completed_todos(self, temp_json_file):
        """Test saving completed todos to file"""
        test_data = {
            "date": "2025-01-13",
            "completed": ["Clean bathroom", "Make bed"]
        }
        
        with patch('daily_todo_bot.COMPLETED_TODOS_FILE', temp_json_file):
            daily_todo_bot.save_completed_todos(test_data)
            
            # Verify the file was written correctly
            with open(temp_json_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == test_data
    
    def test_generate_plan_with_items(self):
        """Test plan generation with valid items"""
        from plan_bot.plan_bot import generate_plan
        
        items = ["Task 1", "Task 2", "Task 3"]
        result = generate_plan(items)
        
        assert "📋 **Your Plan**" in result
        assert "1. Task 1" in result
        assert "2. Task 2" in result
        assert "3. Task 3" in result
        assert "Timeline:" in result
        assert "Notes:" in result
    
    @pytest.mark.asyncio
    async def test_send_daily_todos(self, mock_discord_channel, temp_json_file):
        """Test sending daily todos to channel"""
        with patch('daily_todo_bot.COMPLETED_TODOS_FILE', temp_json_file), \
             patch('daily_todo_bot.load_completed_todos') as mock_load, \
             patch('daily_todo_bot.save_completed_todos') as mock_save:
            
            mock_load.return_value = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "completed": ["Clean bathroom"]
            }
            
            await daily_todo_bot.send_daily_todos(mock_discord_channel)
            
            # Verify message was sent
            mock_discord_channel.send.assert_called_once()
            args = mock_discord_channel.send.call_args[1]
            assert 'embed' in args
    
    @pytest.mark.asyncio
    async def test_update_todo_message(self, mock_discord_message, temp_json_file):
        """Test updating todo message with current status"""
        with patch('daily_todo_bot.COMPLETED_TODOS_FILE', temp_json_file), \
             patch('daily_todo_bot.load_completed_todos') as mock_load:
            
            mock_load.return_value = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "completed": ["Clean bathroom", "Make bed"]
            }
            
            await daily_todo_bot.update_todo_message(mock_discord_message)
            
            # Verify message was edited
            mock_discord_message.edit.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_on_message_todo_trigger(self, mock_discord_message, mock_discord_channel):
        """Test on_message event with todo trigger"""
        mock_discord_message.content = "✅"
        mock_discord_message.channel.id = int(os.getenv("HAUSHALTSPLAN_CHANNEL_ID"))
        mock_discord_message.author = Mock()
        mock_discord_message.author.name = "TestUser"
        
        with patch('daily_todo_bot.send_daily_todos') as mock_send:
            await daily_todo_bot.on_message(mock_discord_message)
            mock_send.assert_called_once_with(mock_discord_message.channel)
    
    @pytest.mark.asyncio
    async def test_on_reaction_add_toggle_todo(self, mock_discord_reaction, mock_discord_user, temp_json_file):
        """Test toggling todo completion via reaction"""
        # Setup mock reaction for number emoji
        mock_discord_reaction.emoji = "1️⃣"
        mock_discord_reaction.message.id = 123456
        
        with patch('daily_todo_bot.active_todo_messages', {123456: True}), \
             patch('daily_todo_bot.COMPLETED_TODOS_FILE', temp_json_file), \
             patch('daily_todo_bot.load_completed_todos') as mock_load, \
             patch('daily_todo_bot.save_completed_todos') as mock_save, \
             patch('daily_todo_bot.update_todo_message') as mock_update:
            
            mock_load.return_value = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "completed": []
            }
            
            await daily_todo_bot.on_reaction_add(mock_discord_reaction, mock_discord_user)
            
            # Verify save was called
            mock_save.assert_called_once()
            mock_update.assert_called_once()
    
    def test_default_todos_exist(self):
        """Test that default todos are defined"""
        assert hasattr(daily_todo_bot, 'DEFAULT_TODOS')
        assert isinstance(daily_todo_bot.DEFAULT_TODOS, list)
        assert len(daily_todo_bot.DEFAULT_TODOS) > 0
        
        # Check for expected todo items
        todos = daily_todo_bot.DEFAULT_TODOS
        assert "Clean bathroom" in todos
        assert "Make bed" in todos
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_discord_channel):
        """Test help command functionality"""
        # Create a mock context
        ctx = Mock()
        ctx.channel.id = int(os.getenv("HAUSHALTSPLAN_CHANNEL_ID"))
        ctx.send = AsyncMock()
        
        await daily_todo_bot.help_todo(ctx)
        
        # Verify help message was sent
        ctx.send.assert_called_once()
        help_text = ctx.send.call_args[0][0]
        assert "Daily Todo Bot Help" in help_text
        assert ":white_check_mark:" in help_text

if __name__ == "__main__":
    pytest.main([__file__]) 