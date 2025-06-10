import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add path for importing bot modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bots', 'routine_bot'))

# Import bot modules
from notion_manager import NotionManager
from openrouter_service import OpenRouterService
from routine_scheduler import RoutineScheduler

class TestRoutineBot:
    """Test suite for Routine Bot"""
    
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
    def routine_scheduler(self, mock_discord_bot, notion_manager, openrouter_service):
        """Create RoutineScheduler instance"""
        scheduler = RoutineScheduler(mock_discord_bot, notion_manager, openrouter_service, 123456789)
        yield scheduler
    
    def test_notion_manager_find_routine_database(self, notion_manager, mock_requests):
        """Test finding routine database in Notion"""
        # Mock search response
        mock_requests['post'].return_value.json.return_value = {
            'results': [
                {
                    'id': 'test-db-id',
                    'title': [
                        {'plain_text': 'Routinen'}
                    ]
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        with patch.object(notion_manager.notion.search, return_value=mock_requests['post'].return_value.json.return_value):
            result = notion_manager.find_routine_database()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_notion_manager_get_routines_for_day(self, notion_manager, sample_routines):
        """Test getting routines for a specific day"""
        # Mock Notion database query response
        mock_response = {
            'results': [
                {
                    'id': 'routine1',
                    'properties': {
                        'Name': {
                            'title': [{'plain_text': 'Morgenroutine'}]
                        },
                        'Time': {
                            'rich_text': [{'plain_text': '07:00'}]
                        },
                        'Notes': {
                            'rich_text': [{'plain_text': 'Aufstehen, Duschen, Anziehen'}]
                        },
                        'Day of Week': {
                            'multi_select': [
                                {'name': 'Monday'},
                                {'name': 'Tuesday'}
                            ]
                        }
                    }
                }
            ]
        }
        
        with patch.object(notion_manager.notion.databases, 'query', return_value=mock_response):
            routines = await notion_manager.get_routines_for_day()
            
            assert len(routines) == 1
            assert routines[0]['name'] == 'Morgenroutine'
            assert routines[0]['time'] == '07:00'
            assert 'Aufstehen' in routines[0]['notes']
    
    @pytest.mark.asyncio
    async def test_openrouter_service_generate_structured_routine_steps(self, openrouter_service, mock_requests):
        """Test generating structured routine steps"""
        routine = {
            'name': 'Morgenroutine',
            'notes': 'Aufstehen, Duschen, Anziehen, Frühstück'
        }
        
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '''# 🌅 Morgenroutine

## Schritte:
1. ⏰ Aufstehen (5 min)
2. 🚿 Duschen (15 min)
3. 👔 Anziehen (10 min)
4. 🍳 Frühstück (20 min)

**Gesamtzeit:** 50 Minuten'''
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = await openrouter_service.generate_structured_routine_steps(routine)
        
        assert 'Morgenroutine' in result
        assert 'Aufstehen' in result
        assert 'Duschen' in result
        assert 'Gesamtzeit' in result
    
    @pytest.mark.asyncio
    async def test_openrouter_service_format_routine_message(self, openrouter_service, sample_routines, mock_requests):
        """Test formatting routine message"""
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '''📋 **Deine Routinen für heute**

🌅 **Morgenroutine** (07:00)
• Aufstehen, Duschen, Anziehen, Frühstück

🌙 **Abendroutine** (21:00)  
• Zähne putzen, Lesen, Schlafen'''
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = await openrouter_service.format_routine_message(sample_routines)
        
        assert 'Deine Routinen' in result
        assert 'Morgenroutine' in result
        assert 'Abendroutine' in result
    
    def test_openrouter_service_parse_fallback_steps(self, openrouter_service):
        """Test parsing fallback steps from notes"""
        notes = "Aufstehen, Duschen und anziehen, Frühstück machen"
        
        steps = openrouter_service._parse_fallback_steps(notes)
        
        assert len(steps) == 3
        assert "Aufstehen" in steps[0]
        assert "Duschen" in steps[1]
        assert "Frühstück" in steps[2]
    
    def test_openrouter_service_create_fallback_routine_message(self, openrouter_service, sample_routines):
        """Test creating fallback routine message"""
        result = openrouter_service._create_fallback_routine_message(sample_routines)
        
        assert "📋 Deine Routinen" in result
        assert "Morgenroutine" in result
        assert "07:00" in result
        assert "Abendroutine" in result
        assert "21:00" in result
    
    @pytest.mark.asyncio
    async def test_routine_scheduler_check_and_post_routines(self, routine_scheduler, mock_discord_channel):
        """Test checking and posting routines"""
        routine_scheduler.bot.get_channel.return_value = mock_discord_channel
        
        with patch.object(routine_scheduler.notion_manager, 'get_routines_by_time') as mock_get_routines, \
             patch.object(routine_scheduler.openrouter_service, 'format_routine_message') as mock_format:
            
            mock_get_routines.return_value = []  # No routines for this time
            
            await routine_scheduler.check_and_post_routines()
            
            mock_get_routines.assert_called()
    
    @pytest.mark.asyncio
    async def test_routine_scheduler_post_morning_routine(self, routine_scheduler, mock_discord_channel, sample_routines):
        """Test posting morning routine"""
        routine_scheduler.bot.get_channel.return_value = mock_discord_channel
        
        with patch.object(routine_scheduler.notion_manager, 'get_routines_by_time') as mock_get_routines, \
             patch.object(routine_scheduler.openrouter_service, 'format_routine_message') as mock_format:
            
            mock_get_routines.return_value = [sample_routines[0]]  # Morning routine
            mock_format.return_value = "📋 **Morgenroutine**\n• Aufstehen\n• Duschen"
            
            await routine_scheduler.post_morning_routine()
            
            mock_discord_channel.send.assert_called()
            mock_get_routines.assert_called_with(time_of_day="morning")
    
    @pytest.mark.asyncio
    async def test_routine_scheduler_post_evening_routine(self, routine_scheduler, mock_discord_channel, sample_routines):
        """Test posting evening routine"""
        routine_scheduler.bot.get_channel.return_value = mock_discord_channel
        
        with patch.object(routine_scheduler.notion_manager, 'get_routines_by_time') as mock_get_routines, \
             patch.object(routine_scheduler.openrouter_service, 'format_routine_message') as mock_format:
            
            mock_get_routines.return_value = [sample_routines[1]]  # Evening routine
            mock_format.return_value = "📋 **Abendroutine**\n• Zähne putzen\n• Lesen"
            
            await routine_scheduler.post_evening_routine()
            
            mock_discord_channel.send.assert_called()
            mock_get_routines.assert_called_with(time_of_day="evening")
    
    @pytest.mark.asyncio
    async def test_routine_scheduler_handle_emoji_trigger(self, routine_scheduler, mock_discord_message):
        """Test handling emoji triggers"""
        mock_discord_message.content = "📢"
        
        with patch.object(routine_scheduler, 'post_todays_routines') as mock_post_today:
            await routine_scheduler.handle_emoji_trigger(mock_discord_message)
            
            mock_post_today.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_routine_scheduler_process_emoji_reaction(self, routine_scheduler, mock_discord_message, mock_discord_user):
        """Test processing emoji reactions"""
        with patch.object(routine_scheduler, 'post_morning_routine') as mock_morning, \
             patch.object(routine_scheduler, 'post_evening_routine') as mock_evening:
            
            # Test morning routine emoji
            await routine_scheduler.process_emoji_reaction(mock_discord_message, "1️⃣", mock_discord_user)
            mock_morning.assert_called_once()
            
            # Test evening routine emoji
            await routine_scheduler.process_emoji_reaction(mock_discord_message, "2️⃣", mock_discord_user)
            mock_evening.assert_called_once()
    
    def test_notion_manager_extract_properties(self, notion_manager):
        """Test extracting different property types from Notion"""
        # Test text property
        text_prop = {
            'type': 'title',
            'title': [{'plain_text': 'Test Routine'}]
        }
        result = notion_manager._extract_text_property(text_prop)
        assert result == 'Test Routine'
        
        # Test select property
        select_prop = {
            'type': 'select',
            'select': {'name': 'Morning'}
        }
        result = notion_manager._extract_select_property(select_prop)
        assert result == 'Morning'
        
        # Test rich text property
        rich_text_prop = {
            'type': 'rich_text',
            'rich_text': [
                {'plain_text': 'First part '},
                {'plain_text': 'second part'}
            ]
        }
        result = notion_manager._extract_rich_text_property(rich_text_prop)
        assert result == 'First part second part'
    
    @pytest.mark.asyncio
    async def test_notion_manager_get_routines_by_name_contains(self, notion_manager):
        """Test getting routines by name keyword"""
        with patch.object(notion_manager, 'get_routines_for_day') as mock_get_routines:
            mock_get_routines.return_value = [
                {'name': 'Morgenroutine', 'time': '07:00'},
                {'name': 'Abendroutine', 'time': '21:00'},
                {'name': 'Sportroutine', 'time': '18:00'}
            ]
            
            routines = await notion_manager.get_routines_by_name_contains("Morgen")
            
            assert len(routines) == 1
            assert routines[0]['name'] == 'Morgenroutine'

if __name__ == "__main__":
    pytest.main([__file__]) 