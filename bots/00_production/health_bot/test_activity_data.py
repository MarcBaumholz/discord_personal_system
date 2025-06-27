#!/usr/bin/env python3
"""Test script to find available Daily Activity data (calories, steps)."""

import requests
from datetime import datetime, timedelta

def test_activity_data():
    """Test Daily Activity endpoint with different date ranges."""
    
    access_token = "UAQU4QB5IG324NECOOZNFRD43RW6TY2Y"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("🔍 TESTING DAILY ACTIVITY DATA")
    print("=" * 60)
    
    url = "https://api.ouraring.com/v2/usercollection/daily_activity"
    
    # Test last 14 days individually
    print("📅 Testing individual days (last 14 days):")
    found_data = []
    
    for days_back in range(0, 15):
        date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        params = {"start_date": date, "end_date": date}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                activity = data["data"][0]
                found_data.append(activity)
                print(f"   📅 {date}: ✅ DATA FOUND!")
                print(f"      🔥 Active Calories: {activity.get('active_calories', 'N/A')}")
                print(f"      📊 Total Calories: {activity.get('total_calories', 'N/A')}")
                print(f"      👟 Steps: {activity.get('steps', 'N/A')}")
                print(f"      📈 Score: {activity.get('score', 'N/A')}")
                print(f"      🗓️  Day: {activity.get('day', 'N/A')}")
            else:
                print(f"   📅 {date}: ❌ No data")
        else:
            print(f"   📅 {date}: ❌ Error {response.status_code}")
    
    print(f"\n📊 SUMMARY: Found {len(found_data)} days with activity data")
    
    if found_data:
        print("\n🎯 MOST RECENT ACTIVITY DATA:")
        latest = found_data[0]
        print(f"   📅 Date: {latest.get('day', 'N/A')}")
        print(f"   🔥 Active Calories: {latest.get('active_calories', 'N/A')}")
        print(f"   📊 Total Calories: {latest.get('total_calories', 'N/A')}")
        print(f"   👟 Steps: {latest.get('steps', 'N/A')}")
        print(f"   📈 Activity Score: {latest.get('score', 'N/A')}")
        print(f"   🗝️  All available keys: {list(latest.keys())}")
        
        # Show detailed structure
        print("\n🔬 DETAILED STRUCTURE:")
        for key, value in latest.items():
            if isinstance(value, dict):
                print(f"   📁 {key}: {list(value.keys())} (dict)")
            else:
                print(f"   🔹 {key}: {value}")
    
    # Test with wider date range
    print("\n🎯 TESTING WITH WIDE DATE RANGE (last 30 days):")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    params = {"start_date": start_date, "end_date": end_date}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("data"):
            print(f"✅ Found {len(data['data'])} activity records in last 30 days!")
            
            # Show most recent records
            print("\n📈 LAST 5 RECORDS:")
            for record in data["data"][-5:]:
                date = record.get("day", "N/A")
                calories = record.get("total_calories", 0)
                active_cal = record.get("active_calories", 0)
                steps = record.get("steps", 0)
                score = record.get("score", "N/A")
                print(f"   📅 {date}: {calories} cal ({active_cal} active), {steps} steps, Score: {score}")
                
        else:
            print("❌ No activity data in last 30 days")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    
    return found_data

if __name__ == "__main__":
    activity_data = test_activity_data()
    
    if activity_data:
        print(f"\n🎉 SUCCESS: Found activity data from {len(activity_data)} days!")
        print("💡 Your bot CAN access calorie and step data!")
    else:
        print("\n⚠️  No activity data found in last 14 days")
        print("💡 Activity data might have a longer delay or sync issue") 