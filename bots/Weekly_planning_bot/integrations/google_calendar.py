import os
import logging
import asyncio
import json
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Any, Optional, Tuple
import pickle

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google Calendar libraries not available. Install with: pip install google-auth google-auth-oauthlib google-api-python-client")

from core.database import get_database
from core.models import Task, WeeklyPlan

logger = logging.getLogger('weekly_planning_bot.google_calendar')

class GoogleCalendarIntegration:
    """Google Calendar integration for task and event synchronization"""
    
    def __init__(self):
        self.db = get_database()
        self.credentials_file = "data/google_credentials.json"
        self.token_file = "data/google_token.pickle"
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.calendar_id = 'primary'  # Use primary calendar
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
        
        if not GOOGLE_AVAILABLE:
            logger.warning("Google Calendar integration disabled - missing dependencies")
    
    def is_available(self) -> bool:
        """Check if Google Calendar integration is available"""
        return GOOGLE_AVAILABLE and os.path.exists(self.credentials_file)
    
    async def setup_oauth_flow(self, redirect_uri: str = "http://localhost:8080") -> Optional[str]:
        """Set up OAuth flow for Google Calendar authentication"""
        if not GOOGLE_AVAILABLE:
            return None
        
        try:
            if not os.path.exists(self.credentials_file):
                logger.error("Google credentials file not found. Please set up OAuth2 credentials.")
                return None
            
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            return auth_url
            
        except Exception as e:
            logger.error(f"Error setting up OAuth flow: {e}")
            return None
    
    async def complete_oauth_flow(self, auth_code: str, redirect_uri: str = "http://localhost:8080") -> bool:
        """Complete OAuth flow with authorization code"""
        if not GOOGLE_AVAILABLE:
            return False
        
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            # Save credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(credentials, token)
            
            logger.info("Google Calendar authentication completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error completing OAuth flow: {e}")
            return False
    
    def _get_credentials(self) -> Optional[Credentials]:
        """Get valid Google Calendar credentials"""
        creds = None
        
        # Load existing credentials
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh credentials if needed
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                return None
        
        return creds if creds and creds.valid else None
    
    async def get_calendar_service(self):
        """Get authenticated Google Calendar service"""
        if not GOOGLE_AVAILABLE:
            return None
        
        creds = self._get_credentials()
        if not creds:
            return None
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Error building calendar service: {e}")
            return None
    
    async def sync_weekly_plan_to_calendar(self, user_id: int, week_start_date: str = None) -> Dict[str, Any]:
        """Sync weekly plan tasks to Google Calendar"""
        try:
            if not self.is_available():
                return {'error': 'Google Calendar integration not available'}
            
            service = await self.get_calendar_service()
            if not service:
                return {'error': 'Authentication required. Please connect your Google Calendar first.'}
            
            # Get weekly plan
            plan_data = await self.db.get_weekly_plan(user_id, week_start_date)
            if not plan_data:
                return {'error': 'No weekly plan found'}
            
            week_start = datetime.strptime(plan_data['date'], '%Y-%m-%d').date()
            
            # Track sync results
            synced_events = 0
            errors = []
            
            # Sync tasks day by day
            for day_name, day_tasks in plan_data['tasks'].items():
                if not day_tasks:
                    continue
                
                # Calculate day date
                day_offset = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                             'Friday', 'Saturday', 'Sunday'].index(day_name)
                task_date = week_start + timedelta(days=day_offset)
                
                for task in day_tasks:
                    try:
                        event_result = await self._create_calendar_event(
                            service, task, task_date
                        )
                        
                        if event_result:
                            synced_events += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing task {task.get('title', '')}: {e}")
                        errors.append(f"Task '{task.get('title', '')}': {str(e)}")
            
            return {
                'success': True,
                'synced_events': synced_events,
                'errors': errors,
                'week_start': str(week_start)
            }
            
        except Exception as e:
            logger.error(f"Error syncing weekly plan to calendar: {e}")
            return {'error': str(e)}
    
    async def _create_calendar_event(self, service, task: Dict[str, Any], task_date: date) -> Optional[str]:
        """Create a single calendar event for a task"""
        try:
            # Determine event time
            if task.get('time'):
                try:
                    task_time = datetime.strptime(task['time'], '%H:%M').time()
                    start_datetime = datetime.combine(task_date, task_time)
                    end_datetime = start_datetime + timedelta(hours=1)  # Default 1 hour duration
                except:
                    # If time parsing fails, create all-day event
                    start_datetime = task_date
                    end_datetime = task_date + timedelta(days=1)
            else:
                # All-day event
                start_datetime = task_date
                end_datetime = task_date + timedelta(days=1)
            
            # Prepare event data
            event = {
                'summary': f"📋 {task['title']}",
                'description': f"Weekly Planning Task\nCategory: {task.get('category', 'general')}\nPriority: {task.get('priority', 2)}",
                'colorId': self._get_color_for_category(task.get('category', 'general')),
            }
            
            # Set time format based on whether it's all-day
            if isinstance(start_datetime, datetime):
                event['start'] = {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/Berlin',
                }
                event['end'] = {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/Berlin',
                }
            else:
                event['start'] = {'date': start_datetime.isoformat()}
                event['end'] = {'date': end_datetime.isoformat()}
            
            # Add reminders based on priority
            if task.get('priority', 2) <= 2:  # High or medium priority
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15},
                    ],
                }
            
            # Create event
            created_event = service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            return created_event.get('id')
            
        except HttpError as e:
            logger.error(f"HTTP error creating calendar event: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return None
    
    def _get_color_for_category(self, category: str) -> str:
        """Get Google Calendar color ID for task category"""
        category_colors = {
            'work': '9',      # Blue
            'health': '10',   # Green
            'learning': '5',  # Yellow
            'personal': '7',  # Cyan
            'family': '4',    # Red
            'social': '6',    # Orange
            'chores': '8',    # Gray
            'finance': '3',   # Purple
            'general': '1',   # Default blue
        }
        return category_colors.get(category, '1')
    
    async def import_calendar_events(self, user_id: int, week_start_date: str = None, days: int = 7) -> Dict[str, Any]:
        """Import events from Google Calendar to weekly plan"""
        try:
            if not self.is_available():
                return {'error': 'Google Calendar integration not available'}
            
            service = await self.get_calendar_service()
            if not service:
                return {'error': 'Authentication required'}
            
            # Calculate date range
            if week_start_date:
                start_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
            else:
                today = date.today()
                start_date = today - timedelta(days=today.weekday())
            
            end_date = start_date + timedelta(days=days)
            
            # Get events from calendar
            time_min = datetime.combine(start_date, time.min).isoformat() + 'Z'
            time_max = datetime.combine(end_date, time.min).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Process events
            imported_tasks = []
            
            for event in events:
                # Skip events created by our bot
                if event.get('summary', '').startswith('📋'):
                    continue
                
                task_data = await self._convert_event_to_task(event, start_date)
                if task_data:
                    imported_tasks.append(task_data)
            
            return {
                'success': True,
                'imported_events': len(imported_tasks),
                'tasks': imported_tasks,
                'date_range': f"{start_date} to {end_date}"
            }
            
        except HttpError as e:
            logger.error(f"HTTP error importing calendar events: {e}")
            return {'error': f'Calendar API error: {e}'}
        except Exception as e:
            logger.error(f"Error importing calendar events: {e}")
            return {'error': str(e)}
    
    async def _convert_event_to_task(self, event: Dict[str, Any], week_start: date) -> Optional[Dict[str, Any]]:
        """Convert Google Calendar event to task format"""
        try:
            title = event.get('summary', 'Untitled Event')
            description = event.get('description', '')
            
            # Determine task date and time
            start = event.get('start', {})
            
            if 'dateTime' in start:
                # Timed event
                event_datetime = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                task_date = event_datetime.date()
                task_time = event_datetime.time()
            elif 'date' in start:
                # All-day event
                task_date = datetime.strptime(start['date'], '%Y-%m-%d').date()
                task_time = None
            else:
                return None
            
            # Calculate day of week
            day_offset = (task_date - week_start).days
            if day_offset < 0 or day_offset > 6:
                return None  # Outside current week
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                        'Friday', 'Saturday', 'Sunday']
            day_name = day_names[day_offset]
            
            # Determine category from event details
            category = self._categorize_event(title, description)
            
            return {
                'title': title,
                'day': day_name,
                'time': task_time.strftime('%H:%M') if task_time else None,
                'category': category,
                'priority': 2,  # Default medium priority
                'completed': False,
                'notes': description[:100] if description else None,
                'source': 'google_calendar'
            }
            
        except Exception as e:
            logger.error(f"Error converting event to task: {e}")
            return None
    
    def _categorize_event(self, title: str, description: str) -> str:
        """Automatically categorize event based on title and description"""
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""
        
        # Work-related keywords
        if any(word in title_lower for word in ['meeting', 'work', 'office', 'project', 'client', 'call', 'conference']):
            return 'work'
        
        # Health-related keywords
        if any(word in title_lower for word in ['gym', 'workout', 'doctor', 'health', 'medical', 'exercise']):
            return 'health'
        
        # Learning keywords
        if any(word in title_lower for word in ['class', 'course', 'study', 'learn', 'training', 'workshop']):
            return 'learning'
        
        # Family keywords
        if any(word in title_lower for word in ['family', 'kids', 'school', 'parent', 'birthday']):
            return 'family'
        
        # Social keywords
        if any(word in title_lower for word in ['dinner', 'party', 'friends', 'social', 'date', 'event']):
            return 'social'
        
        return 'general'
    
    async def check_calendar_conflicts(self, user_id: int, task_date: date, task_time: time, duration_hours: int = 1) -> Dict[str, Any]:
        """Check for calendar conflicts when scheduling a task"""
        try:
            if not self.is_available():
                return {'conflicts': [], 'message': 'Calendar integration not available'}
            
            service = await self.get_calendar_service()
            if not service:
                return {'conflicts': [], 'message': 'Authentication required'}
            
            # Calculate time range
            start_datetime = datetime.combine(task_date, task_time)
            end_datetime = start_datetime + timedelta(hours=duration_hours)
            
            time_min = start_datetime.isoformat() + 'Z'
            time_max = end_datetime.isoformat() + 'Z'
            
            # Get events in time range
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            conflicts = []
            for event in events:
                event_start = event.get('start', {})
                event_end = event.get('end', {})
                
                # Check for time overlap
                if 'dateTime' in event_start and 'dateTime' in event_end:
                    event_start_dt = datetime.fromisoformat(event_start['dateTime'].replace('Z', '+00:00'))
                    event_end_dt = datetime.fromisoformat(event_end['dateTime'].replace('Z', '+00:00'))
                    
                    # Check overlap
                    if (start_datetime < event_end_dt and end_datetime > event_start_dt):
                        conflicts.append({
                            'title': event.get('summary', 'Untitled'),
                            'start': event_start_dt.strftime('%H:%M'),
                            'end': event_end_dt.strftime('%H:%M')
                        })
            
            return {
                'conflicts': conflicts,
                'message': f"Found {len(conflicts)} potential conflicts" if conflicts else "No conflicts found"
            }
            
        except Exception as e:
            logger.error(f"Error checking calendar conflicts: {e}")
            return {'conflicts': [], 'message': f'Error checking conflicts: {str(e)}'}
    
    async def get_calendar_summary(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get summary of upcoming calendar events"""
        try:
            if not self.is_available():
                return {'error': 'Calendar integration not available'}
            
            service = await self.get_calendar_service()
            if not service:
                return {'error': 'Authentication required'}
            
            # Get events for next week
            start_date = date.today()
            end_date = start_date + timedelta(days=days)
            
            time_min = datetime.combine(start_date, time.min).isoformat() + 'Z'
            time_max = datetime.combine(end_date, time.min).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Organize events by day
            daily_events = {}
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                        'Friday', 'Saturday', 'Sunday']
            
            for event in events:
                start = event.get('start', {})
                
                if 'dateTime' in start:
                    event_date = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00')).date()
                elif 'date' in start:
                    event_date = datetime.strptime(start['date'], '%Y-%m-%d').date()
                else:
                    continue
                
                # Get day name
                day_offset = (event_date - start_date).days
                if 0 <= day_offset < len(day_names):
                    day_name = day_names[day_offset]
                    
                    if day_name not in daily_events:
                        daily_events[day_name] = []
                    
                    daily_events[day_name].append({
                        'title': event.get('summary', 'Untitled'),
                        'time': start.get('dateTime', start.get('date')),
                        'date': str(event_date)
                    })
            
            return {
                'success': True,
                'daily_events': daily_events,
                'total_events': len(events),
                'date_range': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar summary: {e}")
            return {'error': str(e)}

# Global calendar integration instance
calendar_integration = None

def get_calendar_integration() -> GoogleCalendarIntegration:
    """Get global calendar integration instance"""
    global calendar_integration
    if calendar_integration is None:
        calendar_integration = GoogleCalendarIntegration()
    return calendar_integration 