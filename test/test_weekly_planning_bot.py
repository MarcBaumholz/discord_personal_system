import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add path for importing bot modules  
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bots', 'Weekly_planning_bot'))

# Import bot modules
from notion_manager import NotionManager
from openrouter_service import OpenRouterService

class TestWeeklyPlanningBot:
    """Test suite for Weekly Planning Bot"""
    
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
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
            service = OpenRouterService()
            yield service
    
    @pytest.mark.asyncio
    async def test_notion_manager_get_latest_weekly_plan(self, notion_manager, sample_weekly_plan):
        """Test getting latest weekly plan from Notion"""
        # Mock the Notion API response
        mock_response = {
            'results': [
                {
                    'id': 'test-id',
                    'properties': {
                        'Date': {
                            'type': 'date',
                            'date': {'start': '2025-01-13'}
                        },
                        'Focus': {
                            'type': 'multi_select',
                            'multi_select': [
                                {'name': 'Work'},
                                {'name': 'Health'}
                            ]
                        },
                        'Goals': {
                            'type': 'rich_text',
                            'rich_text': [
                                {'plain_text': '1. Complete project\n2. Exercise 3 times'}
                            ]
                        },
                        'Monday': {
                            'type': 'rich_text',
                            'rich_text': [
                                {'plain_text': '[x] 09:00 - Team meeting\n[ ] 11:00 - Work on project'}
                            ]
                        }
                    }
                }
            ]
        }
        
        with patch.object(notion_manager.notion.databases, 'query', return_value=mock_response):
            result = await notion_manager.get_latest_weekly_plan()
            
            assert result['date'] == '2025-01-13'
            assert 'Work' in result['focus_areas']
            assert 'Health' in result['focus_areas']
            assert 'Complete project' in result['weekly_goals']
            assert len(result['tasks']['Monday']) == 2
            assert result['tasks']['Monday'][0]['completed'] is True
            assert result['tasks']['Monday'][1]['completed'] is False
    
    def test_notion_manager_parse_tasks(self, notion_manager):
        """Test parsing tasks from text"""
        tasks_text = """[x] 09:00 - Team meeting
[ ] 11:00 - Work on project
Important task without checkbox
[x] 15:00 - Call client"""
        
        tasks = notion_manager._parse_tasks(tasks_text)
        
        assert len(tasks) == 4
        assert tasks[0]['completed'] is True
        assert tasks[0]['time'] == '09:00'
        assert tasks[0]['title'] == 'Team meeting'
        
        assert tasks[1]['completed'] is False
        assert tasks[1]['time'] == '11:00'
        assert tasks[1]['title'] == 'Work on project'
        
        assert tasks[2]['completed'] is False
        assert tasks[2]['time'] is None
        assert tasks[2]['title'] == 'Important task without checkbox'
    
    @pytest.mark.asyncio
    async def test_openrouter_service_format_weekly_plan(self, openrouter_service, sample_weekly_plan, mock_requests):
        """Test formatting weekly plan with OpenRouter"""
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '# 📅 Weekly Plan: Week 3 (January 13, 2025)\n\n## 🎯 Focus Areas\n`Work`, `Health`, `Learning`'
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = await openrouter_service.format_weekly_plan(sample_weekly_plan)
        
        assert '📅 Weekly Plan' in result
        assert 'Focus Areas' in result
        assert mock_requests['post'].called
    
    @pytest.mark.asyncio
    async def test_openrouter_service_generate_family_plan(self, openrouter_service, mock_requests):
        """Test generating family plan"""
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '# 👨‍👧‍👦 Family Weekly Plan\n\n## Monday\n- **Present**: 👨 👧 👦'
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = await openrouter_service.generate_family_plan()
        
        assert '👨‍👧‍👦 Family Weekly Plan' in result
        assert 'Monday' in result
        assert mock_requests['post'].called
    
    def test_openrouter_service_create_fallback_weekly_plan(self, openrouter_service, sample_weekly_plan):
        """Test fallback weekly plan creation"""
        result = openrouter_service._create_fallback_weekly_plan(sample_weekly_plan)
        
        assert '📅 Weekly Plan' in result
        assert 'Focus Areas' in result
        assert 'Weekly Goals' in result
        assert 'Work' in result
        assert 'Health' in result
        assert 'Learning' in result
        assert 'Team meeting' in result
    
    @pytest.mark.asyncio
    async def test_openrouter_service_generate_weekly_stats(self, openrouter_service):
        """Test generating weekly statistics"""
        result = await openrouter_service.generate_weekly_stats()
        
        assert 'Weekly Statistics' in result
        assert 'Task Completion by Category' in result
        assert 'Most Productive Day' in result
        assert 'Time Distribution' in result
    
    @pytest.mark.asyncio
    async def test_openrouter_service_generate_sample_weekly_plan(self, openrouter_service, mock_requests):
        """Test generating sample weekly plan"""
        # Mock OpenRouter response
        mock_requests['post'].return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '# 📅 Sample Weekly Plan\n\n## Monday\n✅ Morning standup'
                    }
                }
            ]
        }
        mock_requests['post'].return_value.status_code = 200
        
        result = await openrouter_service.generate_sample_weekly_plan()
        
        assert '📅' in result
        assert 'Monday' in result
    
    def test_notion_manager_generate_mock_data(self, notion_manager):
        """Test mock data generation"""
        mock_data = notion_manager._generate_mock_data()
        
        assert 'id' in mock_data
        assert 'date' in mock_data
        assert 'focus_areas' in mock_data
        assert 'weekly_goals' in mock_data
        assert 'tasks' in mock_data
        
        # Check all days are present
        expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in expected_days:
            assert day in mock_data['tasks']
            assert isinstance(mock_data['tasks'][day], list)
    
    @pytest.mark.asyncio
    async def test_notion_manager_extract_properties(self, notion_manager):
        """Test extracting different property types"""
        # Test date property
        date_prop = {
            'type': 'date',
            'date': {'start': '2025-01-13'}
        }
        result = notion_manager._extract_date_property(date_prop)
        assert result == '2025-01-13'
        
        # Test multi-select property
        multi_select_prop = {
            'type': 'multi_select',
            'multi_select': [
                {'name': 'Work'},
                {'name': 'Health'}
            ]
        }
        result = await notion_manager._extract_multi_select_property(multi_select_prop)
        assert result == ['Work', 'Health']
        
        # Test rich text property
        rich_text_prop = {
            'type': 'rich_text',
            'rich_text': [
                {'plain_text': 'Test goal 1'},
                {'plain_text': '\nTest goal 2'}
            ]
        }
        result = await notion_manager._extract_rich_text_property(rich_text_prop)
        assert result == 'Test goal 1\nTest goal 2'
    
    @pytest.mark.asyncio
    async def test_openrouter_service_async_post_request(self, openrouter_service, mock_requests):
        """Test async POST request functionality"""
        mock_requests['post'].return_value.status_code = 200
        mock_requests['post'].return_value.json.return_value = {"test": "response"}
        
        url = "https://test.example.com"
        headers = {"Content-Type": "application/json"}
        json_data = {"test": "data"}
        
        result = await openrouter_service._async_post_request(url, headers, json_data)
        
        assert result.status_code == 200
        assert result.json() == {"test": "response"}
        mock_requests['post'].assert_called_once_with(url, headers=headers, json=json_data)

if __name__ == "__main__":
    pytest.main([__file__]) 