"""Notion client for fetching calories data from the FoodIate database."""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from notion_client import Client as NotionClient
import logging

logger = logging.getLogger(__name__)


class NotionCaloriesClient:
    """Client for fetching calories data from Notion FoodIate database."""
    
    def __init__(self, notion_token: str, database_id: str):
        """Initialize Notion client with token and database ID."""
        self.notion = NotionClient(auth=notion_token)
        self.database_id = database_id
    
    def get_yesterday_calories(self, person_name: str = "Marc") -> Tuple[int, List[Dict]]:
        """
        Get total calories consumed yesterday from Notion database.
        
        Args:
            person_name: Name of the person to filter by (default: "Marc")
            
        Returns:
            Tuple of (total_calories, list_of_entries)
        """
        try:
            # Calculate yesterday's date
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            
            logger.info(f"Fetching calories for {person_name} on {yesterday_str}")
            
            # Query the Notion database for yesterday's entries
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "and": [
                        {
                            "property": "date",
                            "date": {
                                "equals": yesterday_str
                            }
                        },
                        {
                            "property": "person",
                            "select": {
                                "equals": person_name
                            }
                        }
                    ]
                }
            )
            
            entries = response.get("results", [])
            total_calories = 0
            processed_entries = []
            
            for entry in entries:
                try:
                    # Extract calories from the entry
                    calories_property = entry.get("properties", {}).get("Calories", {})
                    calories_text = ""
                    
                    # Handle different possible structures
                    if "rich_text" in calories_property:
                        rich_text = calories_property["rich_text"]
                        if rich_text and len(rich_text) > 0:
                            calories_text = rich_text[0].get("text", {}).get("content", "")
                    elif "title" in calories_property:
                        title = calories_property["title"]
                        if title and len(title) > 0:
                            calories_text = title[0].get("text", {}).get("content", "")
                    
                    # Extract numeric value from calories text (e.g., "600 kcal" -> 600)
                    import re
                    calories_match = re.search(r'(\d+)', calories_text)
                    if calories_match:
                        calories = int(calories_match.group(1))
                        total_calories += calories
                        
                        # Get food name
                        food_name = "Unknown Food"
                        food_property = entry.get("properties", {}).get("Food", {})
                        if "title" in food_property:
                            title = food_property["title"]
                            if title and len(title) > 0:
                                food_name = title[0].get("text", {}).get("content", "Unknown Food")
                        
                        processed_entries.append({
                            "food_name": food_name,
                            "calories": calories,
                            "date": yesterday_str
                        })
                        
                        logger.info(f"Found entry: {food_name} - {calories} kcal")
                
                except Exception as e:
                    logger.warning(f"Error processing entry: {e}")
                    continue
            
            logger.info(f"Total calories for {person_name} on {yesterday_str}: {total_calories}")
            return total_calories, processed_entries
            
        except Exception as e:
            logger.error(f"Error fetching calories from Notion: {e}")
            return 0, []
    
    def get_calories_for_date(self, date: datetime, person_name: str = "Marc") -> Tuple[int, List[Dict]]:
        """
        Get total calories consumed for a specific date.
        
        Args:
            date: Date to fetch calories for
            person_name: Name of the person to filter by
            
        Returns:
            Tuple of (total_calories, list_of_entries)
        """
        try:
            date_str = date.strftime("%Y-%m-%d")
            logger.info(f"Fetching calories for {person_name} on {date_str}")
            
            # Query the Notion database for the specific date
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "and": [
                        {
                            "property": "date",
                            "date": {
                                "equals": date_str
                            }
                        },
                        {
                            "property": "person",
                            "select": {
                                "equals": person_name
                            }
                        }
                    ]
                }
            )
            
            entries = response.get("results", [])
            total_calories = 0
            processed_entries = []
            
            for entry in entries:
                try:
                    # Extract calories from the entry
                    calories_property = entry.get("properties", {}).get("Calories", {})
                    calories_text = ""
                    
                    # Handle different possible structures
                    if "rich_text" in calories_property:
                        rich_text = calories_property["rich_text"]
                        if rich_text and len(rich_text) > 0:
                            calories_text = rich_text[0].get("text", {}).get("content", "")
                    elif "title" in calories_property:
                        title = calories_property["title"]
                        if title and len(title) > 0:
                            calories_text = title[0].get("text", {}).get("content", "")
                    
                    # Extract numeric value from calories text
                    import re
                    calories_match = re.search(r'(\d+)', calories_text)
                    if calories_match:
                        calories = int(calories_match.group(1))
                        total_calories += calories
                        
                        # Get food name
                        food_name = "Unknown Food"
                        food_property = entry.get("properties", {}).get("Food", {})
                        if "title" in food_property:
                            title = food_property["title"]
                            if title and len(title) > 0:
                                food_name = title[0].get("text", {}).get("content", "Unknown Food")
                        
                        processed_entries.append({
                            "food_name": food_name,
                            "calories": calories,
                            "date": date_str
                        })
                
                except Exception as e:
                    logger.warning(f"Error processing entry: {e}")
                    continue
            
            logger.info(f"Total calories for {person_name} on {date_str}: {total_calories}")
            return total_calories, processed_entries
            
        except Exception as e:
            logger.error(f"Error fetching calories from Notion: {e}")
            return 0, []
    
    def get_weekly_calories_average(self, person_name: str = "Marc", days_back: int = 7) -> Tuple[float, List[Dict]]:
        """
        Get average daily calories for the past week.
        
        Args:
            person_name: Name of the person to filter by
            days_back: Number of days to look back (default: 7)
            
        Returns:
            Tuple of (average_calories, list_of_daily_totals)
        """
        try:
            daily_totals = []
            total_calories = 0
            days_with_data = 0
            
            for i in range(days_back):
                date = datetime.now() - timedelta(days=i+1)
                calories, entries = self.get_calories_for_date(date, person_name)
                
                if calories > 0:
                    daily_totals.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "calories": calories,
                        "entries_count": len(entries)
                    })
                    total_calories += calories
                    days_with_data += 1
            
            average_calories = total_calories / days_with_data if days_with_data > 0 else 0
            
            logger.info(f"Weekly average calories for {person_name}: {average_calories:.1f} kcal/day")
            return average_calories, daily_totals
            
        except Exception as e:
            logger.error(f"Error calculating weekly average: {e}")
            return 0.0, []
    
    def test_connection(self) -> bool:
        """Test the Notion connection and database access."""
        try:
            # Try to query the database
            response = self.notion.databases.query(
                database_id=self.database_id,
                page_size=1
            )
            
            logger.info("Notion connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")
            return False
