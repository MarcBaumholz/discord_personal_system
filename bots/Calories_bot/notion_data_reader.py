#!/usr/bin/env python3
"""
Notion Data Reader for Monthly Calorie Reports
Extracts and processes calorie data from Notion database for analysis
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
from notion_client import Client as NotionClient
from dotenv import load_dotenv
import re

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
FOODIATE_DB_ID = os.getenv("FOODIATE_DB_ID", "20ed42a1faf5807497c2f350ff84ea8d")

# Initialize Notion client
notion = NotionClient(auth=NOTION_TOKEN)

class CalorieDataExtractor:
    """Handles extraction and processing of calorie data from Notion database"""
    
    def __init__(self):
        self.notion = notion
        self.db_id = FOODIATE_DB_ID
    
    def extract_calories_from_text(self, calories_text: str) -> int:
        """Extract numeric calorie value from text field"""
        try:
            if not calories_text:
                return 0
            
            # Remove 'kcal' and other units, extract numbers
            numeric_text = re.sub(r'[^\d.]', '', str(calories_text))
            if numeric_text:
                return int(float(numeric_text))
            return 0
        except (ValueError, TypeError):
            return 0
    
    def get_monthly_data(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Extract all calorie data for a specific month
        
        Args:
            year: Target year (e.g., 2024)
            month: Target month (1-12)
            
        Returns:
            List of dictionaries with calorie data
        """
        try:
            # Calculate date range for the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            print(f"🔍 Extracting data for {start_date.strftime('%B %Y')}")
            print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
            
            # Query Notion database with date filter
            query_filter = {
                "and": [
                    {
                        "property": "date",
                        "date": {
                            "on_or_after": start_date.isoformat()
                        }
                    },
                    {
                        "property": "date", 
                        "date": {
                            "on_or_before": end_date.isoformat()
                        }
                    }
                ]
            }
            
            # Query the database
            response = notion.databases.query(
                database_id=self.db_id,
                filter=query_filter,
                sorts=[
                    {
                        "property": "date",
                        "direction": "ascending"
                    }
                ]
            )
            
            processed_data = []
            
            for page in response["results"]:
                try:
                    properties = page["properties"]
                    
                    # Extract data from Notion properties
                    food_name = ""
                    if "Food" in properties and properties["Food"]["title"]:
                        food_name = properties["Food"]["title"][0]["text"]["content"]
                    
                    calories_raw = ""
                    if "Calories" in properties:
                        if properties["Calories"]["rich_text"]:
                            calories_raw = properties["Calories"]["rich_text"][0]["text"]["content"]
                    
                    date_str = ""
                    if "date" in properties and properties["date"]["date"]:
                        date_str = properties["date"]["date"]["start"]
                    
                    person = ""
                    if "person" in properties and properties["person"]["select"]:
                        person = properties["person"]["select"]["name"]
                    
                    confidence = 0
                    if "confidence" in properties and properties["confidence"]["number"]:
                        confidence = properties["confidence"]["number"]
                    
                    # Process the data
                    calories = self.extract_calories_from_text(calories_raw)
                    
                    # Only include entries with valid data
                    if date_str and person and calories > 0:
                        processed_data.append({
                            "date": datetime.fromisoformat(date_str).date(),
                            "food_name": food_name,
                            "calories": calories,
                            "person": person,
                            "confidence": confidence,
                            "calories_raw": calories_raw
                        })
                    
                except Exception as e:
                    print(f"⚠️ Error processing page: {e}")
                    continue
            
            print(f"✅ Extracted {len(processed_data)} valid entries")
            return processed_data
            
        except Exception as e:
            print(f"❌ Error querying Notion database: {e}")
            return []
    
    def get_user_monthly_data(self, year: int, month: int, username: str) -> pd.DataFrame:
        """
        Get monthly calorie data for a specific user as DataFrame
        
        Args:
            year: Target year
            month: Target month  
            username: Username to filter by
            
        Returns:
            DataFrame with daily calorie data for the user
        """
        try:
            # Get all monthly data
            all_data = self.get_monthly_data(year, month)
            
            # Filter by user
            user_data = [entry for entry in all_data if entry["person"].lower() == username.lower()]
            
            if not user_data:
                print(f"⚠️ No data found for user '{username}' in {month}/{year}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(user_data)
            
            # Group by date and sum calories
            daily_calories = df.groupby('date')['calories'].sum().reset_index()
            daily_calories = daily_calories.sort_values('date')
            
            print(f"✅ Processed {len(daily_calories)} days of data for {username}")
            return daily_calories
            
        except Exception as e:
            print(f"❌ Error processing user data: {e}")
            return pd.DataFrame()
    
    def get_all_users(self, year: int, month: int) -> List[str]:
        """
        Get list of all users with data in the specified month
        
        Args:
            year: Target year
            month: Target month
            
        Returns:
            List of unique usernames
        """
        try:
            all_data = self.get_monthly_data(year, month)
            users = list(set([entry["person"] for entry in all_data if entry["person"]]))
            print(f"👥 Found users: {users}")
            return users
        except Exception as e:
            print(f"❌ Error getting users: {e}")
            return []
    
    def get_monthly_stats(self, year: int, month: int, username: str) -> Dict[str, Any]:
        """
        Calculate monthly statistics for a user
        
        Args:
            year: Target year
            month: Target month
            username: Username to analyze
            
        Returns:
            Dictionary with monthly statistics
        """
        try:
            df = self.get_user_monthly_data(year, month, username)
            
            if df.empty:
                return {
                    "username": username,
                    "month": month,
                    "year": year,
                    "total_calories": 0,
                    "average_daily": 0,
                    "max_daily": 0,
                    "min_daily": 0,
                    "days_tracked": 0
                }
            
            stats = {
                "username": username,
                "month": month,
                "year": year,
                "total_calories": int(df['calories'].sum()),
                "average_daily": int(df['calories'].mean()),
                "max_daily": int(df['calories'].max()),
                "min_daily": int(df['calories'].min()),
                "days_tracked": len(df)
            }
            
            print(f"📊 Stats for {username}: {stats['total_calories']} total kcal over {stats['days_tracked']} days")
            return stats
            
        except Exception as e:
            print(f"❌ Error calculating stats: {e}")
            return {}

# Test function
async def test_data_extraction():
    """Test function for data extraction"""
    try:
        extractor = CalorieDataExtractor()
        
        # Test with current month
        now = datetime.now()
        year = now.year
        month = now.month
        
        print(f"\n🧪 Testing data extraction for {month}/{year}")
        
        # Get all users
        users = extractor.get_all_users(year, month)
        print(f"Users found: {users}")
        
        # Get data for each user
        for user in users[:2]:  # Test with first 2 users
            print(f"\n👤 Testing user: {user}")
            df = extractor.get_user_monthly_data(year, month, user)
            if not df.empty:
                print(f"Data shape: {df.shape}")
                print(df.head())
            
            stats = extractor.get_monthly_stats(year, month, user)
            print(f"Stats: {stats}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_data_extraction()) 