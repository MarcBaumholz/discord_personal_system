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
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
print(f"🔍 Loading .env from: {env_path}")
load_dotenv(env_path)

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
FOODIATE_DB_ID = os.getenv("FOODIATE_DB_ID", "20ed42a1faf5807497c2f350ff84ea8d")

print(f"🔍 NOTION_TOKEN loaded: {'✅ Yes' if NOTION_TOKEN else '❌ No'}")
print(f"🔍 FOODIATE_DB_ID: {FOODIATE_DB_ID}")

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
                    
                    # Extract macronutrient data
                    protein = 0.0
                    if "Protein" in properties and properties["Protein"]["number"]:
                        protein = properties["Protein"]["number"]
                    
                    carbohydrates = 0.0
                    if "Carbs" in properties and properties["Carbs"]["number"]:
                        carbohydrates = properties["Carbs"]["number"]
                    
                    fat = 0.0
                    if "Fat" in properties and properties["Fat"]["number"]:
                        fat = properties["Fat"]["number"]
                    
                    # Extract meal hash for similarity detection
                    meal_hash = ""
                    if "meal_hash" in properties and properties["meal_hash"]["rich_text"]:
                        meal_hash = properties["meal_hash"]["rich_text"][0]["text"]["content"]
                    
                    # Process the data
                    calories = self.extract_calories_from_text(calories_raw)
                    
                    # Only include entries with valid data
                    if date_str and person and calories > 0:
                        processed_data.append({
                            "date": datetime.fromisoformat(date_str).date(),
                            "food_name": food_name,
                            "calories": calories,
                            "protein": protein,
                            "carbohydrates": carbohydrates,
                            "fat": fat,
                            "person": person,
                            "confidence": confidence,
                            "calories_raw": calories_raw,
                            "meal_hash": meal_hash
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
    
    def get_meal_frequency_analysis(self, data: List[Dict[str, Any]], username: str) -> Dict[str, Any]:
        """
        Analyze meal frequency and repetition patterns
        
        Args:
            data: List of food entries
            username: Target username
            
        Returns:
            Dictionary with meal frequency analysis
        """
        try:
            # Filter data for the specific user
            user_data = [entry for entry in data if entry.get("person") == username]
            
            if not user_data:
                return {"error": "No data found for user"}
            
            # Count meal frequencies by name and hash
            meal_counts = {}
            meal_hashes = {}
            
            for entry in user_data:
                food_name = entry.get("food_name", "Unknown")
                meal_hash = entry.get("meal_hash", "")
                
                # Count by food name
                if food_name in meal_counts:
                    meal_counts[food_name] += 1
                else:
                    meal_counts[food_name] = 1
                
                # Count by meal hash (for similar meals)
                if meal_hash and meal_hash in meal_hashes:
                    meal_hashes[meal_hash]["count"] += 1
                    meal_hashes[meal_hash]["names"].append(food_name)
                elif meal_hash:
                    meal_hashes[meal_hash] = {
                        "count": 1,
                        "names": [food_name],
                        "representative_name": food_name
                    }
            
            # Get top 10 most frequent meals
            top_meals = sorted(meal_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Get similar meal groups (meals with same hash appearing more than once)
            similar_meals = {
                hash_val: data for hash_val, data in meal_hashes.items() 
                if data["count"] > 1
            }
            
            # Calculate variety metrics
            total_meals = len(user_data)
            unique_foods = len(meal_counts)
            variety_score = (unique_foods / total_meals * 100) if total_meals > 0 else 0
            
            return {
                "total_meals": total_meals,
                "unique_foods": unique_foods,
                "variety_score": round(variety_score, 1),
                "top_meals": top_meals,
                "similar_meal_groups": similar_meals,
                "most_repeated_meal": top_meals[0] if top_meals else ("None", 0)
            }
            
        except Exception as e:
            print(f"❌ Error in meal frequency analysis: {e}")
            return {"error": str(e)}
    
    def get_macronutrient_analysis(self, data: List[Dict[str, Any]], username: str) -> Dict[str, Any]:
        """
        Analyze macronutrient distribution and patterns
        
        Args:
            data: List of food entries
            username: Target username
            
        Returns:
            Dictionary with macronutrient analysis
        """
        try:
            # Filter data for the specific user
            user_data = [entry for entry in data if entry.get("person") == username]
            
            if not user_data:
                return {"error": "No data found for user"}
            
            # Calculate totals
            total_protein = sum(entry.get("protein", 0) for entry in user_data)
            total_carbs = sum(entry.get("carbohydrates", 0) for entry in user_data)
            total_fat = sum(entry.get("fat", 0) for entry in user_data)
            total_calories = sum(entry.get("calories", 0) for entry in user_data)
            
            # Calculate averages per day
            unique_dates = len(set(entry.get("date") for entry in user_data))
            avg_protein = total_protein / unique_dates if unique_dates > 0 else 0
            avg_carbs = total_carbs / unique_dates if unique_dates > 0 else 0
            avg_fat = total_fat / unique_dates if unique_dates > 0 else 0
            avg_calories = total_calories / unique_dates if unique_dates > 0 else 0
            
            # Calculate macronutrient distribution percentages
            total_macros = total_protein + total_carbs + total_fat
            protein_pct = (total_protein / total_macros * 100) if total_macros > 0 else 0
            carbs_pct = (total_carbs / total_macros * 100) if total_macros > 0 else 0
            fat_pct = (total_fat / total_macros * 100) if total_macros > 0 else 0
            
            # Daily breakdowns
            daily_macros = {}
            for entry in user_data:
                date = entry.get("date")
                if date not in daily_macros:
                    daily_macros[date] = {
                        "protein": 0, "carbs": 0, "fat": 0, "calories": 0
                    }
                daily_macros[date]["protein"] += entry.get("protein", 0)
                daily_macros[date]["carbs"] += entry.get("carbohydrates", 0)
                daily_macros[date]["fat"] += entry.get("fat", 0)
                daily_macros[date]["calories"] += entry.get("calories", 0)
            
            return {
                "total_protein": round(total_protein, 1),
                "total_carbs": round(total_carbs, 1),
                "total_fat": round(total_fat, 1),
                "total_calories": total_calories,
                "avg_daily_protein": round(avg_protein, 1),
                "avg_daily_carbs": round(avg_carbs, 1),
                "avg_daily_fat": round(avg_fat, 1),
                "avg_daily_calories": round(avg_calories, 1),
                "protein_percentage": round(protein_pct, 1),
                "carbs_percentage": round(carbs_pct, 1),
                "fat_percentage": round(fat_pct, 1),
                "days_tracked": unique_dates,
                "daily_breakdown": daily_macros
            }
            
        except Exception as e:
            print(f"❌ Error in macronutrient analysis: {e}")
            return {"error": str(e)}

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