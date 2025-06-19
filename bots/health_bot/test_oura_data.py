#!/usr/bin/env python3
"""Test script to debug Oura API data retrieval."""

import requests
import json
from datetime import datetime, timedelta
from config import Config

def test_oura_api():
    """Test Oura API with multiple date ranges."""
    config = Config()
    
    # Use the new token provided by user
    access_token = "UAQU4QB5IG324NECOOZNFRD43RW6TY2Y"
    
    print("🔍 Testing Oura API Connection...")
    print(f"Token (first 10 chars): {access_token[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test last 7 days
    print("\n📅 Testing last 7 days...")
    for days_back in range(0, 8):
        date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        print(f"\n🗓️  Testing date: {date}")
        
        # Test daily activity endpoint
        url = "https://api.ouraring.com/v2/usercollection/daily_activity"
        params = {
            "start_date": date,
            "end_date": date
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    activity = data["data"][0]
                    print(f"   ✅ DATA FOUND!")
                    print(f"   📊 Total Calories: {activity.get('total_calories', 'N/A')}")
                    print(f"   🔥 Active Calories: {activity.get('active_calories', 'N/A')}")
                    print(f"   👟 Steps: {activity.get('steps', 'N/A')}")
                    print(f"   📈 Score: {activity.get('score', 'N/A')}")
                    print(f"   🕐 Day: {activity.get('day', 'N/A')}")
                    
                    # Show raw data for debugging
                    print(f"   📝 Raw data keys: {list(activity.keys())}")
                    
                    # Return first found data
                    return {
                        "date": date,
                        "total_calories": activity.get('total_calories', 0),
                        "active_calories": activity.get('active_calories', 0),
                        "steps": activity.get('steps', 0),
                        "score": activity.get('score', None),
                        "raw_data": activity
                    }
                else:
                    print(f"   ❌ No data available")
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                if response.status_code == 401:
                    print("   🔑 Invalid access token!")
                    break
                    
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    print("\n❌ No data found in the last 7 days")
    return None

def test_personal_info():
    """Test personal info endpoint to verify token."""
    access_token = "UAQU4QB5IG324NECOOZNFRD43RW6TY2Y"
    
    print("\n👤 Testing Personal Info endpoint...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        url = "https://api.ouraring.com/v2/usercollection/personal_info"
        response = requests.get(url, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Token is valid!")
            print(f"User ID: {data.get('id', 'N/A')}")
            print(f"Age: {data.get('age', 'N/A')}")
            print(f"Weight: {data.get('weight', 'N/A')}")
            print(f"Height: {data.get('height', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_all_endpoints():
    """Test various Oura API endpoints."""
    access_token = "UAQU4QB5IG324NECOOZNFRD43RW6TY2Y"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        "daily_activity",
        "daily_sleep", 
        "daily_readiness",
        "sessions",
        "tags"
    ]
    
    print("\n🔍 Testing all available endpoints...")
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    for endpoint in endpoints:
        print(f"\n📡 Testing endpoint: {endpoint}")
        
        url = f"https://api.ouraring.com/v2/usercollection/{endpoint}"
        params = {
            "start_date": yesterday,
            "end_date": yesterday
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    print(f"   ✅ Data available: {len(data['data'])} records")
                    if endpoint == "daily_activity" and data["data"]:
                        activity = data["data"][0]
                        print(f"   📊 Sample data: {dict(list(activity.items())[:3])}")
                else:
                    print(f"   ❌ No data")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    print("🏥 Oura API Test Script")
    print("=" * 50)
    
    # Test token validity
    test_personal_info()
    
    # Test all endpoints
    test_all_endpoints()
    
    # Test data retrieval
    data = test_oura_api()
    
    if data:
        print(f"\n🎉 SUCCESS! Found data for {data['date']}")
        print("\n📋 Summary:")
        print(f"   Date: {data['date']}")
        print(f"   Total Calories: {data['total_calories']}")
        print(f"   Active Calories: {data['active_calories']}")
        print(f"   Steps: {data['steps']}")
        print(f"   Score: {data['score']}")
    else:
        print("\n❌ No recent data found. Please check:")
        print("   1. Your Oura ring is worn and synced")
        print("   2. Your access token is valid")
        print("   3. Data might take 1-2 days to appear in API") 