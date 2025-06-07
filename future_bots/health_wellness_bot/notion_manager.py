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
        self.health_db_id = os.getenv("NOTION_HEALTH_DATABASE_ID")
        self.medication_db_id = os.getenv("NOTION_MEDICATION_DATABASE_ID", "")
        
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
            # Check health database
            if self.health_db_id:
                self.client.databases.retrieve(self.health_db_id)
                logger.info(f"Health database validated: {self.health_db_id}")
            else:
                logger.warning("Health database ID not provided")
            
            # Check medication database
            if self.medication_db_id:
                self.client.databases.retrieve(self.medication_db_id)
                logger.info(f"Medication database validated: {self.medication_db_id}")
        except Exception as e:
            logger.error(f"Error validating Notion databases: {str(e)}")
    
    def get_or_create_daily_entry(self, date):
        """Get today's entry or create it if it doesn't exist"""
        if not self.client or not self.health_db_id:
            logger.error("Notion client or health database ID not available")
            return None
        
        try:
            # Format date for Notion
            formatted_date = date.strftime("%Y-%m-%d")
            
            # Query for existing entry
            query_params = {
                "database_id": self.health_db_id,
                "filter": {
                    "property": "Datum",
                    "date": {
                        "equals": formatted_date
                    }
                }
            }
            
            response = self.client.databases.query(**query_params)
            results = response.get("results", [])
            
            # Return existing entry if found
            if results:
                entry = results[0]
                properties = entry.get("properties", {})
                
                # Extract relevant data
                return {
                    "id": entry["id"],
                    "date": formatted_date,
                    "waterAmount": self._extract_number_property(properties, "Wasserkonsum"),
                    "sleepHours": self._extract_number_property(properties, "Schlafstunden"),
                    "moodRating": self._extract_number_property(properties, "Stimmungswert"),
                    "meditationMinutes": self._extract_number_property(properties, "Achtsamkeitsminuten"),
                    "activityLevel": self._extract_select_property(properties, "Aktivitätslevel"),
                    "medications": self._extract_multiselect_property(properties, "Medikamente"),
                    "notes": self._extract_text_property(properties, "Notizen")
                }
            
            # Create new entry if not found
            new_page = {
                "parent": {"database_id": self.health_db_id},
                "properties": {
                    "Datum": {
                        "date": {
                            "start": formatted_date
                        }
                    },
                    "Wasserkonsum": {
                        "number": 0
                    },
                    "Schlafstunden": {
                        "number": 0
                    },
                    "Stimmungswert": {
                        "number": 0
                    },
                    "Achtsamkeitsminuten": {
                        "number": 0
                    },
                    "Aktivitätslevel": {
                        "select": {
                            "name": "Mittel"
                        }
                    },
                    "Medikamente": {
                        "multi_select": []
                    },
                    "Notizen": {
                        "rich_text": [{
                            "text": {
                                "content": ""
                            }
                        }]
                    }
                }
            }
            
            response = self.client.pages.create(**new_page)
            logger.info(f"Created new daily entry for {formatted_date}")
            
            return {
                "id": response["id"],
                "date": formatted_date,
                "waterAmount": 0,
                "sleepHours": 0,
                "moodRating": 0,
                "meditationMinutes": 0,
                "activityLevel": "Mittel",
                "medications": [],
                "notes": ""
            }
            
        except Exception as e:
            logger.error(f"Error getting/creating daily entry: {str(e)}")
            return None
    
    def update_daily_entry(self, page_id, data):
        """Update a daily entry with new data"""
        if not self.client:
            logger.error("Notion client not available")
            return False
        
        try:
            properties = {}
            
            # Add properties based on provided data
            if "waterAmount" in data:
                properties["Wasserkonsum"] = {"number": data["waterAmount"]}
            
            if "sleepHours" in data:
                properties["Schlafstunden"] = {"number": data["sleepHours"]}
            
            if "moodRating" in data:
                properties["Stimmungswert"] = {"number": data["moodRating"]}
            
            if "meditationMinutes" in data:
                properties["Achtsamkeitsminuten"] = {"number": data["meditationMinutes"]}
            
            if "activityLevel" in data:
                properties["Aktivitätslevel"] = {"select": {"name": data["activityLevel"]}}
            
            if "medications" in data:
                multi_select = [{"name": med} for med in data["medications"]]
                properties["Medikamente"] = {"multi_select": multi_select}
            
            if "notes" in data:
                properties["Notizen"] = {
                    "rich_text": [{
                        "text": {
                            "content": data["notes"]
                        }
                    }]
                }
            
            # Update the page
            self.client.pages.update(page_id=page_id, properties=properties)
            logger.info(f"Updated daily entry {page_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating daily entry: {str(e)}")
            return False
    
    def get_water_data(self, days=7):
        """Get water consumption data for the specified number of days"""
        if not self.client or not self.health_db_id:
            return {}
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # Format dates for Notion
            formatted_start = start_date.strftime("%Y-%m-%d")
            formatted_end = end_date.strftime("%Y-%m-%d")
            
            # Query for entries in date range
            query_params = {
                "database_id": self.health_db_id,
                "filter": {
                    "property": "Datum",
                    "date": {
                        "on_or_after": formatted_start,
                        "on_or_before": formatted_end
                    }
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
            
            # Extract water data
            water_data = {}
            for entry in results:
                properties = entry.get("properties", {})
                date_prop = properties.get("Datum", {}).get("date", {})
                
                if date_prop and date_prop.get("start"):
                    date_str = date_prop.get("start")
                    # Format the date for display
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    display_date = date_obj.strftime("%d.%m")
                    
                    # Get water amount
                    water_amount = self._extract_number_property(properties, "Wasserkonsum")
                    water_data[display_date] = water_amount
            
            return water_data
            
        except Exception as e:
            logger.error(f"Error getting water data: {str(e)}")
            return {}
    
    def get_user_health_data(self, days=7):
        """Get aggregated health data for analytics"""
        if not self.client or not self.health_db_id:
            return {}
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # Format dates for Notion
            formatted_start = start_date.strftime("%Y-%m-%d")
            formatted_end = end_date.strftime("%Y-%m-%d")
            
            # Query for entries in date range
            query_params = {
                "database_id": self.health_db_id,
                "filter": {
                    "property": "Datum",
                    "date": {
                        "on_or_after": formatted_start,
                        "on_or_before": formatted_end
                    }
                }
            }
            
            response = self.client.databases.query(**query_params)
            results = response.get("results", [])
            
            # Calculate aggregates
            total_water = 0
            total_sleep = 0
            total_mood = 0
            total_meditation = 0
            activity_counts = {"Niedrig": 0, "Mittel": 0, "Hoch": 0}
            
            for entry in results:
                properties = entry.get("properties", {})
                
                # Sum up values
                total_water += self._extract_number_property(properties, "Wasserkonsum")
                total_sleep += self._extract_number_property(properties, "Schlafstunden")
                total_mood += self._extract_number_property(properties, "Stimmungswert")
                total_meditation += self._extract_number_property(properties, "Achtsamkeitsminuten")
                
                # Count activity levels
                activity = self._extract_select_property(properties, "Aktivitätslevel")
                if activity in activity_counts:
                    activity_counts[activity] += 1
            
            # Calculate averages
            count = len(results) or 1  # Avoid division by zero
            avg_water = round(total_water / count, 1)
            avg_sleep = round(total_sleep / count, 1)
            avg_mood = round(total_mood / count, 1)
            avg_meditation = round(total_meditation / count, 1)
            
            # Determine most common activity level
            activity_level = max(activity_counts, key=activity_counts.get)
            
            return {
                "avg_water": avg_water,
                "avg_sleep": avg_sleep,
                "avg_mood": avg_mood,
                "avg_meditation": avg_meditation,
                "activity_level": activity_level,
                "days_tracked": count
            }
            
        except Exception as e:
            logger.error(f"Error getting user health data: {str(e)}")
            return {}
    
    def _extract_number_property(self, properties, property_name):
        """Extract a number property from Notion properties"""
        prop = properties.get(property_name, {})
        return prop.get("number", 0) or 0
    
    def _extract_select_property(self, properties, property_name):
        """Extract a select property from Notion properties"""
        prop = properties.get(property_name, {})
        select = prop.get("select", {})
        return select.get("name", "") if select else ""
    
    def _extract_multiselect_property(self, properties, property_name):
        """Extract a multi_select property from Notion properties"""
        prop = properties.get(property_name, {})
        multi_select = prop.get("multi_select", [])
        return [item.get("name", "") for item in multi_select]
    
    def _extract_text_property(self, properties, property_name):
        """Extract a rich_text property from Notion properties"""
        prop = properties.get(property_name, {})
        rich_text = prop.get("rich_text", [])
        
        if rich_text:
            return rich_text[0].get("text", {}).get("content", "")
        return "" 