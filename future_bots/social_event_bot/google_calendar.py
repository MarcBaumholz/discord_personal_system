import logging
import os
import datetime
import pytz
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
logger = logging.getLogger("google_calendar")

# Try importing Google API libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_IMPORTS_SUCCESS = True
except ImportError:
    logger.warning("Google API libraries not found. Some calendar features will be disabled.")
    GOOGLE_IMPORTS_SUCCESS = False

class GoogleCalendarIntegration:
    def __init__(self):
        """Initialize Google Calendar integration"""
        load_dotenv()
        
        self.credentials_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS')
        self.token_path = os.getenv('GOOGLE_CALENDAR_TOKEN', 'token.json')
        self.timezone = pytz.timezone('Europe/Berlin')
        self.service = None
        self.calendar_ids = {}
        
        # List of OAuth scopes
        self.SCOPES = [
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        
        # Initialize if possible
        self.initialized = False
        
        if GOOGLE_IMPORTS_SUCCESS and self.credentials_path:
            try:
                self.initialize()
                logger.info("Google Calendar integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Calendar integration: {str(e)}")
    
    def initialize(self):
        """Initialize the Google Calendar API service"""
        if not GOOGLE_IMPORTS_SUCCESS:
            logger.error("Cannot initialize Google Calendar: Required libraries not installed")
            return False
        
        try:
            creds = None
            token_path = Path(self.token_path)
            
            # Check if token file exists
            if token_path.exists():
                creds = Credentials.from_authorized_user_info(
                    eval(token_path.read_text()), # Convert JSON string to dict
                    self.SCOPES
                )
            
            # If no valid credentials available, let user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # This would require user interaction - in a real bot this would need handling
                    logger.warning("No valid credentials. User needs to authenticate.")
                    return False
                
                # Save the credentials for next run
                token_path.write_text(str(creds.to_json()))
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=creds)
            
            # Get user calendars
            self._fetch_calendar_list()
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Google Calendar API: {str(e)}")
            return False
    
    def _fetch_calendar_list(self):
        """Fetch list of user's calendars"""
        if not self.service:
            return
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            
            for calendar in calendar_list.get('items', []):
                self.calendar_ids[calendar['summary']] = calendar['id']
                
                # Set primary calendar
                if calendar.get('primary', False):
                    self.calendar_ids['primary'] = calendar['id']
            
            # If no primary calendar found, use the first one
            if 'primary' not in self.calendar_ids and self.calendar_ids:
                first_calendar = next(iter(self.calendar_ids.items()))
                self.calendar_ids['primary'] = first_calendar[1]
                
        except Exception as e:
            logger.error(f"Error fetching calendar list: {str(e)}")
    
    def get_events(self, days=7, calendar_id=None):
        """Get events for the next X days"""
        if not self.initialized or not self.service:
            logger.warning("Google Calendar not initialized")
            return []
        
        try:
            # Use primary calendar if none specified
            if not calendar_id:
                calendar_id = self.calendar_ids.get('primary', 'primary')
            
            # Calculate time range
            now = datetime.datetime.now(self.timezone)
            end_time = now + datetime.timedelta(days=days)
            
            # Format for Google API
            time_min = now.isoformat()
            time_max = end_time.isoformat()
            
            # Fetch events
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events for easier use
            formatted_events = []
            for event in events:
                # Extract start and end times
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse start time
                if 'T' in start:  # Has time component
                    start_dt = datetime.datetime.fromisoformat(start)
                    start_time = start_dt.strftime('%H:%M')
                    start_date = start_dt.date()
                else:  # All-day event
                    start_time = "ganztägig"
                    start_date = datetime.datetime.strptime(start, "%Y-%m-%d").date()
                
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'Kein Titel'),
                    'date': start_date,
                    'time': start_time,
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'raw_start': start,
                    'raw_end': end
                })
            
            return formatted_events
            
        except Exception as e:
            logger.error(f"Error getting events: {str(e)}")
            return []
    
    def get_free_slots(self, date, min_duration=30):
        """Get free time slots for a specific date"""
        if not self.initialized or not self.service:
            logger.warning("Google Calendar not initialized")
            return []
        
        try:
            # Get all events for the date
            events = self.get_events_for_date(date)
            
            # Define business hours (9:00 to 17:00)
            business_start = datetime.datetime.combine(date, datetime.time(9, 0))
            business_end = datetime.datetime.combine(date, datetime.time(17, 0))
            
            # Add timezone info
            business_start = self.timezone.localize(business_start)
            business_end = self.timezone.localize(business_end)
            
            # Sort events by start time
            events.sort(key=lambda x: x['raw_start'])
            
            # Find free slots
            free_slots = []
            current_time = business_start
            
            for event in events:
                # Skip all-day events or events without time
                if 'T' not in event['raw_start']:
                    continue
                
                event_start = datetime.datetime.fromisoformat(event['raw_start'])
                event_end = datetime.datetime.fromisoformat(event['raw_end'])
                
                # Check if there's a gap before this event
                if event_start > current_time:
                    duration_minutes = (event_start - current_time).total_seconds() / 60
                    
                    if duration_minutes >= min_duration:
                        free_slots.append({
                            'start': current_time.strftime('%H:%M'),
                            'end': event_start.strftime('%H:%M'),
                            'duration': int(duration_minutes)
                        })
                
                # Move current time to end of this event
                if event_end > current_time:
                    current_time = event_end
            
            # Check for free time after the last event
            if current_time < business_end:
                duration_minutes = (business_end - current_time).total_seconds() / 60
                
                if duration_minutes >= min_duration:
                    free_slots.append({
                        'start': current_time.strftime('%H:%M'),
                        'end': business_end.strftime('%H:%M'),
                        'duration': int(duration_minutes)
                    })
            
            return free_slots
            
        except Exception as e:
            logger.error(f"Error getting free slots: {str(e)}")
            return []
    
    def get_events_for_date(self, date):
        """Get all events for a specific date"""
        if not self.initialized or not self.service:
            logger.warning("Google Calendar not initialized")
            return []
        
        try:
            # Calculate time range for the whole day
            start_of_day = datetime.datetime.combine(date, datetime.time.min)
            end_of_day = datetime.datetime.combine(date, datetime.time.max)
            
            # Add timezone info
            start_of_day = self.timezone.localize(start_of_day)
            end_of_day = self.timezone.localize(end_of_day)
            
            # Format for Google API
            time_min = start_of_day.isoformat()
            time_max = end_of_day.isoformat()
            
            # Fetch events
            events_result = self.service.events().list(
                calendarId=self.calendar_ids.get('primary', 'primary'),
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events for easier use
            formatted_events = []
            for event in events:
                # Extract start and end times
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse start time
                if 'T' in start:  # Has time component
                    start_dt = datetime.datetime.fromisoformat(start)
                    start_time = start_dt.strftime('%H:%M')
                else:  # All-day event
                    start_time = "ganztägig"
                
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'Kein Titel'),
                    'time': start_time,
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'raw_start': start,
                    'raw_end': end
                })
            
            return formatted_events
            
        except Exception as e:
            logger.error(f"Error getting events for date: {str(e)}")
            return []
    
    def create_event(self, summary, start_time, end_time, description=None, location=None):
        """Create a new calendar event"""
        if not self.initialized or not self.service:
            logger.warning("Google Calendar not initialized")
            return None
        
        try:
            # Prepare event data
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': self.timezone.zone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.timezone.zone,
                }
            }
            
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            # Add reminders
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'popup', 'minutes': 10}
                ]
            }
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_ids.get('primary', 'primary'),
                body=event
            ).execute()
            
            return created_event.get('id')
            
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            return None
    
    def delete_event(self, event_id):
        """Delete a calendar event"""
        if not self.initialized or not self.service:
            logger.warning("Google Calendar not initialized")
            return False
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_ids.get('primary', 'primary'),
                eventId=event_id
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return False
    
    def update_event(self, event_id, **kwargs):
        """Update a calendar event"""
        if not self.initialized or not self.service:
            logger.warning("Google Calendar not initialized")
            return False
        
        try:
            # First get the existing event
            event = self.service.events().get(
                calendarId=self.calendar_ids.get('primary', 'primary'),
                eventId=event_id
            ).execute()
            
            # Update fields
            if 'summary' in kwargs:
                event['summary'] = kwargs['summary']
            
            if 'start_time' in kwargs:
                event['start']['dateTime'] = kwargs['start_time'].isoformat()
            
            if 'end_time' in kwargs:
                event['end']['dateTime'] = kwargs['end_time'].isoformat()
            
            if 'description' in kwargs:
                event['description'] = kwargs['description']
            
            if 'location' in kwargs:
                event['location'] = kwargs['location']
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_ids.get('primary', 'primary'),
                eventId=event_id,
                body=event
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating event: {str(e)}")
            return False
    
    def is_initialized(self):
        """Check if the integration is initialized"""
        return self.initialized 