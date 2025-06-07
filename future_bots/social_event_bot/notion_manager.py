import os
import logging
from datetime import datetime, timedelta
from notion_client import Client
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger("notion_manager")

class NotionManager:
    def __init__(self):
        """Initialize Notion API client and database IDs"""
        load_dotenv()
        
        self.token = os.getenv("NOTION_TOKEN")
        self.birthday_db_id = os.getenv("NOTION_BIRTHDAY_DATABASE_ID")
        self.events_db_id = os.getenv("NOTION_EVENTS_DATABASE_ID")
        
        # Initialize Notion client
        if self.token:
            self.client = Client(auth=self.token)
            logger.info("Notion client initialized")
        else:
            self.client = None
            logger.error("Notion token not found in environment variables")
        
        # Ensure database IDs are valid
        self._validate_databases()
    
    def _validate_databases(self):
        """Validate that database IDs exist and are accessible"""
        if not self.client:
            return
        
        try:
            # Check birthday database
            if self.birthday_db_id:
                self.client.databases.retrieve(self.birthday_db_id)
                logger.info(f"Birthday database validated: {self.birthday_db_id}")
            else:
                logger.warning("Birthday database ID not provided")
            
            # Check events database
            if self.events_db_id:
                self.client.databases.retrieve(self.events_db_id)
                logger.info(f"Events database validated: {self.events_db_id}")
            else:
                logger.warning("Events database ID not provided")
        
        except Exception as e:
            logger.error(f"Error validating Notion databases: {str(e)}")
    
    # -------------------- Birthday Functions --------------------
    
    def get_birthday(self, name):
        """Get a birthday entry by name"""
        if not self.client or not self.birthday_db_id:
            logger.error("Notion client or birthday database ID not available")
            return None
        
        try:
            # Query for the person
            query_params = {
                "database_id": self.birthday_db_id,
                "filter": {
                    "property": "Name",
                    "title": {
                        "equals": name
                    }
                }
            }
            
            response = self.client.databases.query(**query_params)
            results = response.get("results", [])
            
            # Return the first match if found
            if results:
                return self._parse_birthday_entry(results[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting birthday: {str(e)}")
            return None
    
    def add_birthday(self, name, birth_date, relation=None, notes=None, gift_ideas=None):
        """Add a new birthday entry to the database"""
        if not self.client or not self.birthday_db_id:
            logger.error("Notion client or birthday database ID not available")
            return False
        
        try:
            # Format date for Notion
            formatted_date = birth_date.strftime("%Y-%m-%d")
            
            # Prepare properties
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": name
                            }
                        }
                    ]
                },
                "Datum": {
                    "date": {
                        "start": formatted_date
                    }
                }
            }
            
            # Add relation if provided
            if relation:
                properties["Beziehung"] = {
                    "select": {
                        "name": relation
                    }
                }
            
            # Add notes if provided
            if notes:
                properties["Notizen"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": notes
                            }
                        }
                    ]
                }
            
            # Add gift ideas if provided
            if gift_ideas:
                properties["Geschenkideen"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": gift_ideas
                            }
                        }
                    ]
                }
            
            # Set reminder checkbox
            properties["Erinnerung"] = {
                "checkbox": True
            }
            
            # Create the page
            new_page = {
                "parent": {"database_id": self.birthday_db_id},
                "properties": properties
            }
            
            response = self.client.pages.create(**new_page)
            logger.info(f"Added birthday for {name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding birthday: {str(e)}")
            return False
    
    def update_birthday(self, page_id, data):
        """Update a birthday entry"""
        if not self.client:
            logger.error("Notion client not available")
            return False
        
        try:
            properties = {}
            
            # Name
            if "name" in data:
                properties["Name"] = {
                    "title": [
                        {
                            "text": {
                                "content": data["name"]
                            }
                        }
                    ]
                }
            
            # Date
            if "birth_date" in data:
                formatted_date = data["birth_date"].strftime("%Y-%m-%d")
                properties["Datum"] = {
                    "date": {
                        "start": formatted_date
                    }
                }
            
            # Relation
            if "relation" in data:
                properties["Beziehung"] = {
                    "select": {
                        "name": data["relation"]
                    }
                }
            
            # Notes
            if "notes" in data:
                properties["Notizen"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": data["notes"]
                            }
                        }
                    ]
                }
            
            # Gift ideas
            if "gift_ideas" in data:
                properties["Geschenkideen"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": data["gift_ideas"]
                            }
                        }
                    ]
                }
            
            # Last gift
            if "last_gift" in data:
                properties["Letztes Geschenk"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": data["last_gift"]
                            }
                        }
                    ]
                }
            
            # Reminder setting
            if "reminder" in data:
                properties["Erinnerung"] = {
                    "checkbox": data["reminder"]
                }
            
            # Update the page
            self.client.pages.update(page_id=page_id, properties=properties)
            logger.info(f"Updated birthday entry {page_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating birthday: {str(e)}")
            return False
    
    def remove_birthday(self, name):
        """Remove a birthday entry by name"""
        if not self.client or not self.birthday_db_id:
            logger.error("Notion client or birthday database ID not available")
            return False
        
        try:
            # Find the entry
            birthday = self.get_birthday(name)
            
            if not birthday:
                return False
            
            # Archive the page
            self.client.pages.update(
                page_id=birthday["id"],
                archived=True
            )
            
            logger.info(f"Removed birthday for {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing birthday: {str(e)}")
            return False
    
    def get_birthdays_by_date(self, target_date):
        """Get all birthdays for a specific date (day and month)"""
        if not self.client or not self.birthday_db_id:
            logger.error("Notion client or birthday database ID not available")
            return []
        
        try:
            # Format the target date as MM-DD
            month_day = target_date.strftime("%m-%d")
            
            # Query all birthdays
            response = self.client.databases.query(database_id=self.birthday_db_id)
            results = response.get("results", [])
            
            # Filter for matching day and month
            birthdays = []
            for result in results:
                birthday = self._parse_birthday_entry(result)
                
                if birthday and birthday["date"].strftime("%m-%d") == month_day:
                    birthdays.append(birthday)
            
            return birthdays
            
        except Exception as e:
            logger.error(f"Error getting birthdays by date: {str(e)}")
            return []
    
    def get_upcoming_birthdays(self, days=30):
        """Get all birthdays in the next X days"""
        if not self.client or not self.birthday_db_id:
            logger.error("Notion client or birthday database ID not available")
            return []
        
        try:
            # Calculate date range
            today = datetime.now().date()
            end_date = today + timedelta(days=days)
            
            # Query all birthdays
            response = self.client.databases.query(database_id=self.birthday_db_id)
            results = response.get("results", [])
            
            # Filter for upcoming birthdays in the next X days
            upcoming = []
            for result in results:
                birthday = self._parse_birthday_entry(result)
                
                if not birthday:
                    continue
                
                # Get this year's birthday date
                this_year_bday = datetime(
                    today.year,
                    birthday["date"].month,
                    birthday["date"].day
                ).date()
                
                # If already passed this year, get next year's date
                if this_year_bday < today:
                    this_year_bday = datetime(
                        today.year + 1,
                        birthday["date"].month,
                        birthday["date"].day
                    ).date()
                
                # Check if within range
                if today <= this_year_bday <= end_date:
                    # Add current year's date for easy comparison
                    birthday["current_date"] = this_year_bday
                    upcoming.append(birthday)
            
            # Sort by date
            upcoming.sort(key=lambda x: x["current_date"])
            
            # Remove temporary field
            for b in upcoming:
                del b["current_date"]
            
            return upcoming
            
        except Exception as e:
            logger.error(f"Error getting upcoming birthdays: {str(e)}")
            return []
    
    def _parse_birthday_entry(self, entry):
        """Parse a Notion birthday entry into a standardized format"""
        try:
            properties = entry.get("properties", {})
            
            # Extract name
            name_prop = properties.get("Name", {})
            title = name_prop.get("title", [{}])[0] if name_prop.get("title") else {}
            name = title.get("text", {}).get("content", "") if title else ""
            
            # Extract date
            date_prop = properties.get("Datum", {}).get("date", {})
            if not date_prop or not date_prop.get("start"):
                return None
            
            date_str = date_prop.get("start")
            birth_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Extract other properties
            relation_prop = properties.get("Beziehung", {}).get("select", {})
            relation = relation_prop.get("name", "") if relation_prop else ""
            
            notes_prop = properties.get("Notizen", {}).get("rich_text", [{}])[0] if properties.get("Notizen", {}).get("rich_text") else {}
            notes = notes_prop.get("text", {}).get("content", "") if notes_prop else ""
            
            gift_ideas_prop = properties.get("Geschenkideen", {}).get("rich_text", [{}])[0] if properties.get("Geschenkideen", {}).get("rich_text") else {}
            gift_ideas = gift_ideas_prop.get("text", {}).get("content", "") if gift_ideas_prop else ""
            
            last_gift_prop = properties.get("Letztes Geschenk", {}).get("rich_text", [{}])[0] if properties.get("Letztes Geschenk", {}).get("rich_text") else {}
            last_gift = last_gift_prop.get("text", {}).get("content", "") if last_gift_prop else ""
            
            reminder = properties.get("Erinnerung", {}).get("checkbox", True)
            
            return {
                "id": entry["id"],
                "name": name,
                "date": birth_date,
                "birth_year": birth_date.year,
                "relation": relation,
                "notes": notes,
                "gift_ideas": gift_ideas,
                "last_gift": last_gift,
                "reminder": reminder
            }
            
        except Exception as e:
            logger.error(f"Error parsing birthday entry: {str(e)}")
            return None
    
    # -------------------- Event Functions --------------------
    
    def get_event(self, event_id):
        """Get an event by ID"""
        if not self.client:
            logger.error("Notion client not available")
            return None
        
        try:
            # Retrieve the page
            response = self.client.pages.retrieve(page_id=event_id)
            return self._parse_event_entry(response)
        
        except Exception as e:
            logger.error(f"Error getting event: {str(e)}")
            return None
    
    def add_event(self, name, date, time=None, location=None, description=None, organizer=None):
        """Add a new event to the database"""
        if not self.client or not self.events_db_id:
            logger.error("Notion client or events database ID not available")
            return None
        
        try:
            # Format date for Notion
            formatted_date = date.strftime("%Y-%m-%d")
            
            # Prepare properties
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": name
                            }
                        }
                    ]
                },
                "Datum": {
                    "date": {
                        "start": formatted_date
                    }
                },
                "Status": {
                    "select": {
                        "name": "Geplant"
                    }
                }
            }
            
            # Add optional properties
            if time:
                properties["Uhrzeit"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": time
                            }
                        }
                    ]
                }
            
            if location:
                properties["Ort"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": location
                            }
                        }
                    ]
                }
            
            if description:
                properties["Beschreibung"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": description
                            }
                        }
                    ]
                }
            
            if organizer:
                properties["Organisator"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": organizer
                            }
                        }
                    ]
                }
            
            # Set reminder checkbox
            properties["Erinnerung"] = {
                "checkbox": True
            }
            
            # Create the page
            new_page = {
                "parent": {"database_id": self.events_db_id},
                "properties": properties
            }
            
            response = self.client.pages.create(**new_page)
            logger.info(f"Added event: {name}")
            
            # Return the ID of the new event
            return response["id"]
            
        except Exception as e:
            logger.error(f"Error adding event: {str(e)}")
            return None
    
    def update_event(self, event_id, data):
        """Update an event entry"""
        if not self.client:
            logger.error("Notion client not available")
            return False
        
        try:
            properties = {}
            
            # Name
            if "name" in data:
                properties["Name"] = {
                    "title": [
                        {
                            "text": {
                                "content": data["name"]
                            }
                        }
                    ]
                }
            
            # Date
            if "date" in data:
                formatted_date = data["date"].strftime("%Y-%m-%d")
                properties["Datum"] = {
                    "date": {
                        "start": formatted_date
                    }
                }
            
            # Time
            if "time" in data:
                properties["Uhrzeit"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": data["time"]
                            }
                        }
                    ]
                }
            
            # Location
            if "location" in data:
                properties["Ort"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": data["location"]
                            }
                        }
                    ]
                }
            
            # Description
            if "description" in data:
                properties["Beschreibung"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": data["description"]
                            }
                        }
                    ]
                }
            
            # Organizer
            if "organizer" in data:
                properties["Organisator"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": data["organizer"]
                            }
                        }
                    ]
                }
            
            # Status
            if "status" in data:
                properties["Status"] = {
                    "select": {
                        "name": data["status"]
                    }
                }
            
            # Reminder
            if "reminder" in data:
                properties["Erinnerung"] = {
                    "checkbox": data["reminder"]
                }
            
            # Update the page
            self.client.pages.update(page_id=event_id, properties=properties)
            logger.info(f"Updated event {event_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating event: {str(e)}")
            return False
    
    def cancel_event(self, event_id):
        """Cancel an event (set status to Cancelled)"""
        return self.update_event(event_id, {"status": "Abgesagt"})
    
    def get_events_by_date(self, target_date):
        """Get all events for a specific date"""
        if not self.client or not self.events_db_id:
            logger.error("Notion client or events database ID not available")
            return []
        
        try:
            # Format date for Notion
            formatted_date = target_date.strftime("%Y-%m-%d")
            
            # Query for events on the target date
            query_params = {
                "database_id": self.events_db_id,
                "filter": {
                    "and": [
                        {
                            "property": "Datum",
                            "date": {
                                "equals": formatted_date
                            }
                        },
                        {
                            "property": "Status",
                            "select": {
                                "does_not_equal": "Abgesagt"
                            }
                        }
                    ]
                }
            }
            
            response = self.client.databases.query(**query_params)
            results = response.get("results", [])
            
            # Parse events
            events = []
            for result in results:
                event = self._parse_event_entry(result)
                if event:
                    events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events by date: {str(e)}")
            return []
    
    def get_upcoming_events(self, days=30):
        """Get all events in the next X days"""
        if not self.client or not self.events_db_id:
            logger.error("Notion client or events database ID not available")
            return []
        
        try:
            # Calculate date range
            today = datetime.now().date()
            end_date = today + timedelta(days=days)
            
            # Format dates for Notion
            formatted_start = today.strftime("%Y-%m-%d")
            formatted_end = end_date.strftime("%Y-%m-%d")
            
            # Query for events in the date range
            query_params = {
                "database_id": self.events_db_id,
                "filter": {
                    "and": [
                        {
                            "property": "Datum",
                            "date": {
                                "on_or_after": formatted_start
                            }
                        },
                        {
                            "property": "Datum",
                            "date": {
                                "on_or_before": formatted_end
                            }
                        },
                        {
                            "property": "Status",
                            "select": {
                                "does_not_equal": "Abgesagt"
                            }
                        }
                    ]
                },
                "sorts": [
                    {
                        "property": "Datum",
                        "direction": "ascending"
                    }
                ]
            }
            
            response = self.client.databases.query(**query_params)
            results = response.get("results", [])
            
            # Parse events
            events = []
            for result in results:
                event = self._parse_event_entry(result)
                if event:
                    events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {str(e)}")
            return []
    
    def _parse_event_entry(self, entry):
        """Parse a Notion event entry into a standardized format"""
        try:
            properties = entry.get("properties", {})
            
            # Extract name
            name_prop = properties.get("Name", {})
            title = name_prop.get("title", [{}])[0] if name_prop.get("title") else {}
            name = title.get("text", {}).get("content", "") if title else ""
            
            # Extract date
            date_prop = properties.get("Datum", {}).get("date", {})
            if not date_prop or not date_prop.get("start"):
                return None
            
            date_str = date_prop.get("start")
            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Extract other properties
            time_prop = properties.get("Uhrzeit", {}).get("rich_text", [{}])[0] if properties.get("Uhrzeit", {}).get("rich_text") else {}
            time = time_prop.get("text", {}).get("content", "") if time_prop else ""
            
            location_prop = properties.get("Ort", {}).get("rich_text", [{}])[0] if properties.get("Ort", {}).get("rich_text") else {}
            location = location_prop.get("text", {}).get("content", "") if location_prop else ""
            
            description_prop = properties.get("Beschreibung", {}).get("rich_text", [{}])[0] if properties.get("Beschreibung", {}).get("rich_text") else {}
            description = description_prop.get("text", {}).get("content", "") if description_prop else ""
            
            organizer_prop = properties.get("Organisator", {}).get("rich_text", [{}])[0] if properties.get("Organisator", {}).get("rich_text") else {}
            organizer = organizer_prop.get("text", {}).get("content", "") if organizer_prop else ""
            
            status_prop = properties.get("Status", {}).get("select", {})
            status = status_prop.get("name", "Geplant") if status_prop else "Geplant"
            
            reminder = properties.get("Erinnerung", {}).get("checkbox", True)
            
            # Extract participants (if available)
            participants = []
            participants_prop = properties.get("Teilnehmer", {}).get("relation", [])
            if participants_prop:
                participants = [{"id": p.get("id")} for p in participants_prop]
            
            return {
                "id": entry["id"],
                "name": name,
                "date": event_date,
                "time": time,
                "location": location,
                "description": description,
                "organizer": organizer,
                "status": status,
                "reminder": reminder,
                "participants": participants
            }
            
        except Exception as e:
            logger.error(f"Error parsing event entry: {str(e)}")
            return None 