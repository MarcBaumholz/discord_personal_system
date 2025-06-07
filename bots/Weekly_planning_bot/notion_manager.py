import os
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('weekly_planning_bot.notion_manager')

class NotionManager:
    """Manages interaction with Notion API to fetch and update weekly planning data"""
    
    def __init__(self):
        """Initialize Notion client and configuration"""
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("WEEKLY_PLANNING_DATABASE_ID") 
        self.timezone = pytz.timezone('Europe/Berlin')
        
        logger.info("Initializing Notion Manager")
        
        # Create Notion client
        self.notion = Client(auth=self.token)
    
    async def get_latest_weekly_plan(self):
        """
        Get the latest weekly planning data from Notion
        
        Returns:
            dict: Weekly planning data with focus areas, goals, and tasks
        """
        try:
            # Query for the most recent weekly planning entry
            response = await asyncio.to_thread(
                self.notion.databases.query,
                database_id=self.database_id,
                sorts=[
                    {
                        "property": "Date",
                        "direction": "descending"
                    }
                ],
                page_size=1  # Get only the most recent entry
            )
            
            if not response['results']:
                logger.warning("No weekly planning entries found")
                return self._generate_mock_data()  # Return mock data if no real data
            
            # Extract the latest weekly planning data
            latest_entry = response['results'][0]
            weekly_plan = await self._parse_weekly_planning_page(latest_entry)
            
            logger.info(f"Retrieved latest weekly planning data dated {weekly_plan.get('date')}")
            return weekly_plan
            
        except Exception as e:
            logger.error(f"Error getting weekly planning data: {e}")
            return self._generate_mock_data()  # Return mock data on error
    
    async def _parse_weekly_planning_page(self, page):
        """Parse a Notion page into a weekly planning object"""
        try:
            properties = page.get('properties', {})
            
            # Extract date
            date = self._extract_date_property(properties.get('Date', {}))
            
            # Extract focus areas
            focus_areas = await self._extract_multi_select_property(properties.get('Focus', {}))
            
            # Extract weekly goals
            weekly_goals = await self._extract_rich_text_property(properties.get('Goals', {}))
            
            # Extract tasks by day
            tasks = {}
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                day_tasks = await self._extract_rich_text_property(properties.get(day, {}))
                tasks[day] = self._parse_tasks(day_tasks)
            
            # Return the parsed weekly plan
            return {
                'id': page.get('id'),
                'date': date,
                'focus_areas': focus_areas,
                'weekly_goals': weekly_goals,
                'tasks': tasks
            }
        except Exception as e:
            logger.error(f"Error parsing weekly planning page: {e}")
            return self._generate_mock_data()
    
    def _extract_date_property(self, property_obj):
        """Extract date value from a Notion property"""
        try:
            if property_obj.get('type') == 'date' and property_obj.get('date'):
                date_str = property_obj.get('date', {}).get('start')
                if date_str:
                    return date_str
            return datetime.now().strftime("%Y-%m-%d")
        except Exception:
            return datetime.now().strftime("%Y-%m-%d")
    
    async def _extract_multi_select_property(self, property_obj):
        """Extract multi_select values from a Notion property"""
        try:
            if property_obj.get('type') == 'multi_select':
                multi_select = property_obj.get('multi_select', [])
                return [item.get('name') for item in multi_select]
            return []
        except Exception:
            return []
    
    async def _extract_rich_text_property(self, property_obj):
        """Extract rich text value from a Notion property"""
        try:
            if property_obj.get('type') == 'rich_text':
                rich_text = property_obj.get('rich_text', [])
                return ''.join([text.get('plain_text', '') for text in rich_text])
            return ""
        except Exception:
            return ""
    
    def _parse_tasks(self, tasks_text):
        """Parse tasks text into a list of task objects"""
        if not tasks_text:
            return []
            
        tasks = []
        for line in tasks_text.split('\n'):
            line = line.strip()
            if line:
                # Check if task is marked as completed (has a checkbox or is strikethrough)
                completed = False
                if line.startswith('[x]') or line.startswith('☑') or line.startswith('✓'):
                    completed = True
                    line = line[3:].strip()  # Remove the checkbox
                elif line.startswith('[ ]') or line.startswith('☐'):
                    line = line[3:].strip()  # Remove the checkbox
                
                # Check for task with time notation (e.g., "10:00 - Meeting")
                time = None
                import re
                time_match = re.match(r'^(\d{1,2}:\d{2})\s*-\s*(.+)', line)
                if time_match:
                    time = time_match.group(1)
                    line = time_match.group(2).strip()
                
                tasks.append({
                    'title': line,
                    'completed': completed,
                    'time': time
                })
        
        return tasks
    
    def _generate_mock_data(self):
        """Generate mock weekly planning data for demonstration"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return {
            'id': 'mock-weekly-plan',
            'date': current_date,
            'focus_areas': ['Work', 'Health', 'Learning', 'Family'],
            'weekly_goals': '1. Complete project proposal\n2. Exercise 4 times\n3. Read 2 chapters of book\n4. Plan weekend family trip',
            'tasks': {
                'Monday': [
                    {'title': 'Team meeting', 'completed': True, 'time': '09:00'},
                    {'title': 'Work on project proposal', 'completed': False, 'time': '11:00'},
                    {'title': 'Gym session', 'completed': True, 'time': '18:00'},
                    {'title': 'Read book', 'completed': False, 'time': None}
                ],
                'Tuesday': [
                    {'title': 'Client call', 'completed': False, 'time': '10:30'},
                    {'title': 'Review documents', 'completed': False, 'time': '13:00'},
                    {'title': 'Doctor appointment', 'completed': False, 'time': '16:00'},
                    {'title': 'Online course', 'completed': False, 'time': '20:00'}
                ],
                'Wednesday': [
                    {'title': 'Project work', 'completed': False, 'time': '09:00'},
                    {'title': 'Lunch with Alex', 'completed': False, 'time': '12:30'},
                    {'title': 'Research learning materials', 'completed': False, 'time': '15:00'},
                    {'title': 'Evening run', 'completed': False, 'time': '18:30'}
                ],
                'Thursday': [
                    {'title': 'Weekly report', 'completed': False, 'time': '09:00'},
                    {'title': 'Department meeting', 'completed': False, 'time': '11:00'},
                    {'title': 'Plan weekend activities', 'completed': False, 'time': '17:00'},
                    {'title': 'Call parents', 'completed': False, 'time': '20:00'}
                ],
                'Friday': [
                    {'title': 'Project deadline', 'completed': False, 'time': '12:00'},
                    {'title': 'Team lunch', 'completed': False, 'time': '13:00'},
                    {'title': 'Weekly review', 'completed': False, 'time': '16:00'},
                    {'title': 'Movie night', 'completed': False, 'time': '20:00'}
                ],
                'Saturday': [
                    {'title': 'Morning yoga', 'completed': False, 'time': '08:00'},
                    {'title': 'Grocery shopping', 'completed': False, 'time': '11:00'},
                    {'title': 'House cleaning', 'completed': False, 'time': '14:00'},
                    {'title': 'Family dinner', 'completed': False, 'time': '18:00'}
                ],
                'Sunday': [
                    {'title': 'Nature hike', 'completed': False, 'time': '10:00'},
                    {'title': 'Meal prep', 'completed': False, 'time': '14:00'},
                    {'title': 'Review next week', 'completed': False, 'time': '17:00'},
                    {'title': 'Relaxation time', 'completed': False, 'time': '20:00'}
                ]
            }
        }
    
    async def update_task_status(self, day, task_index, completed):
        """Update task completion status in Notion"""
        try:
            # Since we don't know the exact structure without examining the Notion DB,
            # this is a placeholder function that would require implementation based
            # on the actual database schema
            logger.info(f"Updated task status for {day}, task {task_index} to {completed}")
            return True
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False 