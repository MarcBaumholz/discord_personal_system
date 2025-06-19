import os
import logging
import asyncio
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('weekly_planning_bot.openrouter_service')

class OpenRouterService:
    """Service to interact with OpenRouter LLM API for weekly planning formatting and visualization"""
    
    def __init__(self):
        """Initialize OpenRouter service"""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        logger.info("Initializing OpenRouter Service")
    
    async def format_weekly_plan(self, weekly_data):
        """
        Generate a formatted, visually appealing weekly plan for Discord
        
        Args:
            weekly_data: Dict containing weekly planning data
            
        Returns:
            str: Formatted weekly plan as a Discord message
        """
        try:
            # Extract data from weekly_data
            date = weekly_data.get('date', datetime.now().strftime("%Y-%m-%d"))
            focus_areas = weekly_data.get('focus_areas', [])
            weekly_goals = weekly_data.get('weekly_goals', '')
            tasks = weekly_data.get('tasks', {})
            
            # Format the data for the prompt
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%B %d, %Y")
            week_number = date_obj.isocalendar()[1]
            
            # Calculate task completion statistics
            total_tasks = 0
            completed_tasks = 0
            for day, day_tasks in tasks.items():
                total_tasks += len(day_tasks)
                completed_tasks += sum(1 for task in day_tasks if task.get('completed', False))
            
            completion_percentage = 0
            if total_tasks > 0:
                completion_percentage = int((completed_tasks / total_tasks) * 100)
            
            # Prepare the prompt for the LLM
            prompt = f"""Create a visually stunning Discord message for a weekly planning overview. Here's the data:

Week: Week {week_number}, {date_formatted}
Focus Areas: {', '.join(focus_areas)}
Weekly Goals:
{weekly_goals}

Daily Tasks:
{json.dumps(tasks, indent=2)}

Task Completion: {completed_tasks}/{total_tasks} tasks completed ({completion_percentage}%)

Please format this into a beautiful Discord message that:
1. Uses Discord markdown formatting (bold, italics, code blocks, etc.)
2. Includes visual elements like emojis and dividers
3. Organizes the weekly view in a clean, scannable format
4. Color-codes or visually distinguishes between days
5. Clearly shows completed vs. pending tasks (using ✅ and ⬜)
6. Shows task times when available
7. Includes progress bars for task completion
8. Has a motivational element based on current progress
9. Keeps the output concise but comprehensive

The format should be visually engaging and easy to read in Discord.
"""

            # Call the LLM via OpenRouter
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",  # Using free DeepSeek model for formatting
                "messages": [
                    {"role": "system", "content": "You are a weekly planning visualization expert who creates beautiful Discord-formatted planning views."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            }
            
            # Make the API call asynchronously
            response = await self._async_post_request(self.api_url, headers, payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    formatted_plan = result['choices'][0]['message']['content']
                    return formatted_plan
            
            logger.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
            return self._create_fallback_weekly_plan(weekly_data)
            
        except Exception as e:
            logger.error(f"Error formatting weekly plan: {e}")
            return self._create_fallback_weekly_plan(weekly_data)
    
    async def generate_family_plan(self):
        """
        Generate a family weekly plan focused on a father and two children
        with meals, groceries, events, and chores details
        
        Returns:
            str: Formatted family plan as a Discord message
        """
        try:
            # Current date info
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            date_formatted = week_start.strftime("%B %d, %Y")
            week_number = today.isocalendar()[1]
            
            # Stuttgart trash calendar reference (typical German trash schedule)
            trash_schedule = {
                'Monday': 'Paper/Cardboard (Blue Bin)',
                'Tuesday': None,
                'Wednesday': 'General Waste (Black Bin)',
                'Thursday': 'Recyclables (Yellow Bin)',
                'Friday': None,
                'Saturday': None,
                'Sunday': None
            }
            
            # Prepare the prompt for the LLM to generate a family plan
            prompt = f"""Create a detailed, visually engaging family weekly plan for Discord. This is for a family with:
- Father
- Two children

The plan needs to show for Week {week_number} ({date_formatted}):

1. Who is present at home each day of the week (Father, Child 1, Child 2)
2. Meal plans for each person (breakfast, lunch, dinner)
3. Who is responsible for buying groceries and when
4. Detailed evening activities and weekend plans
5. Important events for each family member on different days
6. Trash schedule for Stuttgart, Germany (who takes out which bin on which day)

For the trash schedule, use this information for Stuttgart:
{json.dumps(trash_schedule, indent=2)}

Please format this into a beautiful Discord message that:
1. Has a calendar-like view with all days of the week
2. Uses Discord markdown formatting (bold, italics, code blocks, etc.)
3. Uses emojis effectively to visually distinguish different types of information
4. Color-codes or visually distinguishes between family members
5. Organizes information in a clear, scannable format that shows the entire week at a glance
6. Adds visual dividers between sections
7. Uses a consistent and visually appealing layout

The format should be concise, information-dense, but very easy to scan in Discord to see the entire family's week at once.
"""

            # Call the LLM via OpenRouter
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",  # Using free DeepSeek model for formatting
                "messages": [
                    {"role": "system", "content": "You are a family planning expert who creates beautiful, detailed Discord-formatted family weekly plans."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            # Make the API call asynchronously
            response = await self._async_post_request(self.api_url, headers, payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    formatted_plan = result['choices'][0]['message']['content']
                    return formatted_plan
            
            logger.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
            return self._create_fallback_family_plan()
            
        except Exception as e:
            logger.error(f"Error generating family plan: {e}")
            return self._create_fallback_family_plan()
    
    def _create_fallback_family_plan(self):
        """Create a fallback family plan when API fails"""
        try:
            # Current date info
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            date_formatted = week_start.strftime("%B %d, %Y")
            week_number = today.isocalendar()[1]
            
            # Build a simple fallback family plan
            plan = f"""# 👨‍👧‍👦 Family Weekly Plan - Week {week_number} ({date_formatted})

## 🗓️ Weekly Overview

### 👨 Dad | 👧 Child 1 | 👦 Child 2

## Monday
- **Present**: 👨 👧 👦
- **Meals**: 
  - 🍳 Breakfast: Cereal and fruits
  - 🍱 Lunch: Packed sandwiches
  - 🍽️ Dinner: Pasta with vegetables
- **Evening**: Homework time (6-7 PM)
- **Events**: 👧 Ballet class (5 PM)
- **Chores**: 👨 Take out Paper/Cardboard bin (Blue)

## Tuesday
- **Present**: 👨 👧 👦
- **Meals**: 
  - 🍳 Breakfast: Toast and eggs
  - 🍱 Lunch: School cafeteria
  - 🍽️ Dinner: Grilled chicken and rice
- **Evening**: Family game night (7-8 PM)
- **Events**: 👦 Football practice (4 PM)
- **Groceries**: 👨 Evening shopping

## Wednesday
- **Present**: 👨 👧 👦
- **Meals**: 
  - 🍳 Breakfast: Yogurt and granola
  - 🍱 Lunch: Packed wraps
  - 🍽️ Dinner: Vegetable stir-fry
- **Evening**: Reading time (7-8 PM)
- **Events**: 👨 Work meeting (6 PM - online)
- **Chores**: 👦 Take out General Waste bin (Black)

## Thursday
- **Present**: 👨 👧 👦
- **Meals**: 
  - 🍳 Breakfast: Pancakes
  - 🍱 Lunch: School cafeteria
  - 🍽️ Dinner: Soup and sandwiches
- **Evening**: TV time (7-8 PM)
- **Events**: 👧 Piano lesson (5 PM)
- **Chores**: 👧 Take out Recyclables bin (Yellow)

## Friday
- **Present**: 👨 👧 👦
- **Meals**: 
  - 🍳 Breakfast: Fruit smoothies
  - 🍱 Lunch: School cafeteria
  - 🍽️ Dinner: Pizza night
- **Evening**: Movie night (7-9 PM)
- **Events**: None
- **Groceries**: 👨 Evening shopping for weekend

## Weekend Plans
### Saturday
- **Present**: 👨 👧 👦
- **Morning**: Farmer's market trip (9-11 AM)
- **Afternoon**: Park visit (2-4 PM)
- **Meals**: Brunch at 11 AM, Barbecue dinner
- **Events**: 👦 Friend's birthday party (4-6 PM)

### Sunday
- **Present**: 👨 👧 👦
- **Morning**: Family breakfast (9 AM)
- **Afternoon**: Homework and chores (2-4 PM)
- **Evening**: Family planning for next week (6 PM)
- **Meals**: Special family lunch, Light dinner
- **Groceries**: 👨 Morning shopping for the week

> 💡 **Remember**: Get prepared for the next week on Sunday evening!

"""
            return plan
        except Exception as e:
            logger.error(f"Error creating fallback family plan: {e}")
            return "Error generating family plan. Please try again later."
    
    async def _async_post_request(self, url, headers, json_data):
        """Make an async POST request"""
        return await asyncio.to_thread(
            lambda: requests.post(url, headers=headers, json=json_data)
        )
    
    def _create_fallback_weekly_plan(self, weekly_data):
        """Create a basic formatted weekly plan when the API fails"""
        try:
            date = weekly_data.get('date', datetime.now().strftime("%Y-%m-%d"))
            focus_areas = weekly_data.get('focus_areas', [])
            weekly_goals = weekly_data.get('weekly_goals', '')
            tasks = weekly_data.get('tasks', {})
            
            # Format the data
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%B %d, %Y")
            week_number = date_obj.isocalendar()[1]
            
            # Calculate task completion
            total_tasks = 0
            completed_tasks = 0
            for day, day_tasks in tasks.items():
                total_tasks += len(day_tasks)
                completed_tasks += sum(1 for task in day_tasks if task.get('completed', False))
            
            completion_percentage = 0
            if total_tasks > 0:
                completion_percentage = int((completed_tasks / total_tasks) * 100)
            
            # Build the message
            message = f"""# 📅 Weekly Plan: Week {week_number} ({date_formatted})

## 🎯 Focus Areas
{', '.join([f'`{area}`' for area in focus_areas])}

## 🏆 Weekly Goals
{weekly_goals}

## 📋 Weekly Overview
Progress: {completed_tasks}/{total_tasks} tasks completed ({completion_percentage}%)
{'█' * (completion_percentage // 10)}{'░' * (10 - (completion_percentage // 10))} {completion_percentage}%

"""
            
            # Add daily tasks
            for day, day_tasks in tasks.items():
                day_emoji = "🔵"
                if day == "Saturday" or day == "Sunday":
                    day_emoji = "🟢"
                
                message += f"\n### {day_emoji} {day}\n"
                
                if not day_tasks:
                    message += "No tasks scheduled.\n"
                    continue
                
                for task in day_tasks:
                    status = "✅" if task.get('completed', False) else "⬜"
                    title = task.get('title', 'Task')
                    time = task.get('time')
                    
                    if time:
                        message += f"{status} `{time}` {title}\n"
                    else:
                        message += f"{status} {title}\n"
            
            # Add motivational message
            if completion_percentage < 30:
                message += "\n> 💪 You've got this! Keep pushing forward."
            elif completion_percentage < 70:
                message += "\n> 🌟 Great progress! Keep up the momentum."
            else:
                message += "\n> 🎉 Awesome job! You're crushing your goals this week."
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating fallback weekly plan: {e}")
            return "Error generating weekly plan. Please try again later."
    
    async def generate_sample_weekly_plan(self):
        """Generate a sample weekly plan for demonstration"""
        try:
            # Create a sample weekly data structure
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            
            sample_data = {
                'id': 'sample-weekly-plan',
                'date': week_start.strftime("%Y-%m-%d"),
                'focus_areas': ['Career Growth', 'Health', 'Learning', 'Social'],
                'weekly_goals': '1. Complete project milestone\n2. Exercise 3 times\n3. Finish online course\n4. Connect with 2 friends',
                'tasks': {
                    'Monday': [
                        {'title': 'Morning standup', 'completed': True, 'time': '09:30'},
                        {'title': 'Project planning', 'completed': True, 'time': '11:00'},
                        {'title': 'Lunch walk', 'completed': True, 'time': '12:30'},
                        {'title': 'Code review', 'completed': True, 'time': '14:00'}
                    ],
                    'Tuesday': [
                        {'title': 'Team meeting', 'completed': True, 'time': '10:00'},
                        {'title': 'Work on feature X', 'completed': True, 'time': '11:30'},
                        {'title': 'Gym session', 'completed': True, 'time': '18:00'},
                        {'title': 'Reading', 'completed': False, 'time': '21:00'}
                    ],
                    'Wednesday': [
                        {'title': 'Client presentation', 'completed': False, 'time': '10:00'},
                        {'title': 'Lunch with mentor', 'completed': False, 'time': '12:30'},
                        {'title': 'Online course - Module 3', 'completed': False, 'time': '19:00'},
                        {'title': 'Call with friend', 'completed': False, 'time': '20:30'}
                    ],
                    'Thursday': [
                        {'title': 'Project work', 'completed': False, 'time': '09:00'},
                        {'title': 'API documentation', 'completed': False, 'time': '14:00'},
                        {'title': 'Running session', 'completed': False, 'time': '18:30'},
                        {'title': 'Plan weekend', 'completed': False, 'time': '20:00'}
                    ],
                    'Friday': [
                        {'title': 'Weekly review', 'completed': False, 'time': '09:00'},
                        {'title': 'Team retrospective', 'completed': False, 'time': '11:00'},
                        {'title': 'Submit timesheet', 'completed': False, 'time': '16:30'},
                        {'title': 'Social dinner', 'completed': False, 'time': '19:00'}
                    ],
                    'Saturday': [
                        {'title': 'Farmers market', 'completed': False, 'time': '10:00'},
                        {'title': 'Home project', 'completed': False, 'time': '13:00'},
                        {'title': 'Online course - Module 4', 'completed': False, 'time': '16:00'},
                        {'title': 'Movie night', 'completed': False, 'time': '20:00'}
                    ],
                    'Sunday': [
                        {'title': 'Morning hike', 'completed': False, 'time': '09:00'},
                        {'title': 'Meal prep', 'completed': False, 'time': '14:00'},
                        {'title': 'Weekly planning', 'completed': False, 'time': '17:00'},
                        {'title': 'Relaxation time', 'completed': False, 'time': '20:00'}
                    ]
                }
            }
            
            # Format the sample plan
            return await self.format_weekly_plan(sample_data)
        except Exception as e:
            logger.error(f"Error generating sample plan: {e}")
            return self._create_fallback_weekly_plan({
                'date': datetime.now().strftime("%Y-%m-%d"),
                'focus_areas': ['Sample Focus 1', 'Sample Focus 2'],
                'weekly_goals': 'Sample goals would appear here',
                'tasks': {}
            })
    
    async def generate_weekly_stats(self):
        """Generate detailed weekly statistics"""
        try:
            # This would normally pull from actual data, but for demo we'll create mock stats
            stats = """
📊 **Weekly Statistics**

**Task Completion by Category:**
- Work: 8/12 (67%)
- Health: 3/5 (60%)
- Learning: 2/4 (50%)
- Personal: 4/7 (57%)

**Most Productive Day:** Tuesday (85% completion)
**Least Productive Day:** Friday (40% completion)

**Time Distribution:**
- Work Tasks: 24 hours
- Health Activities: 5 hours
- Learning: 6 hours
- Personal/Social: 8 hours

**Improvement vs Last Week:**
- Tasks Completed: +15%
- Focus Time: +2 hours
- Exercise Time: +30 minutes

**Looking Ahead:**
Based on your patterns, consider:
- Scheduling more focused work in the morning
- Adding buffer time between meetings
- Dedicating more time to learning goals
            """
            return stats
        except Exception as e:
            logger.error(f"Error generating weekly stats: {e}")
            return "Error generating weekly statistics. Please try again later." 