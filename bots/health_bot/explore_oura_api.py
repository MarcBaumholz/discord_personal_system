#!/usr/bin/env python3
"""Comprehensive Oura API Explorer - Discover all available data from yesterday."""

import requests
import json
from datetime import datetime, timedelta
from pprint import pprint

def explore_oura_api():
    """Explore all Oura API endpoints and show available data."""
    
    access_token = "UAQU4QB5IG324NECOOZNFRD43RW6TY2Y"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://api.ouraring.com/v2/usercollection"
    
    # Test yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print("🔍 COMPREHENSIVE OURA API EXPLORATION")
    print("=" * 60)
    print(f"📅 Testing data for: {yesterday}")
    print()
    
    # All known Oura API endpoints
    endpoints = [
        "daily_activity",
        "daily_sleep", 
        "daily_readiness",
        "daily_spo2",
        "daily_stress",
        "sessions",
        "tags",
        "workouts",
        "daily_cardiovascular_age",
        "daily_cycle_phases",
        "sleep_time",
        "rest_mode_periods",
        "ring_configuration",
        "daily_resilience"
    ]
    
    available_data = {}
    
    for endpoint in endpoints:
        print(f"🔍 Testing endpoint: {endpoint}")
        print("-" * 40)
        
        url = f"{base_url}/{endpoint}"
        
        # Try with date parameters
        params = {
            "start_date": yesterday,
            "end_date": yesterday
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("data") and len(data["data"]) > 0:
                    print(f"   ✅ DATA AVAILABLE: {len(data['data'])} records")
                    
                    # Store the first record for detailed analysis
                    record = data["data"][0]
                    available_data[endpoint] = record
                    
                    # Show key data points
                    print(f"   📊 Sample keys: {list(record.keys())[:8]}")
                    
                    # Show specific interesting values
                    interesting_keys = ['score', 'total_calories', 'active_calories', 'steps', 
                                      'total_sleep_duration', 'deep_sleep_duration', 'rem_sleep_duration',
                                      'sleep_efficiency', 'temperature_deviation', 'activity_balance',
                                      'body_battery', 'recovery_index', 'spo2_average']
                    
                    for key in interesting_keys:
                        if key in record:
                            print(f"   🔹 {key}: {record[key]}")
                            
                elif data.get("data") is not None:
                    print(f"   ⚠️  NO DATA for this date")
                else:
                    print(f"   ❓ Empty response")
                    
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found (404)")
            elif response.status_code == 401:
                print(f"   🔑 Unauthorized (401)")
            elif response.status_code == 403:
                print(f"   🚫 Forbidden (403)")
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)[:100]}")
            
        print()
    
    # Summary of available data
    print("📋 SUMMARY OF AVAILABLE DATA")
    print("=" * 60)
    
    if available_data:
        for endpoint, data in available_data.items():
            print(f"\n🟢 {endpoint.upper()}:")
            
            # Show all available fields for each endpoint
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"   📁 {key}: {list(value.keys())[:5]} (dict)")
                elif isinstance(value, list):
                    print(f"   📋 {key}: [{len(value)} items]")
                else:
                    print(f"   🔹 {key}: {value}")
    else:
        print("❌ No data available for yesterday")
    
    # Test personal info (doesn't need date)
    print("\n👤 PERSONAL INFO (Account Data)")
    print("-" * 40)
    
    try:
        url = f"https://api.ouraring.com/v2/usercollection/personal_info"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            personal_data = response.json()
            print("✅ Personal info available:")
            for key, value in personal_data.items():
                print(f"   🔹 {key}: {value}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")
    
    return available_data

def analyze_data_structure(data_dict):
    """Analyze the structure of retrieved data."""
    
    print("\n🔬 DETAILED DATA STRUCTURE ANALYSIS")
    print("=" * 60)
    
    for endpoint, data in data_dict.items():
        print(f"\n📊 {endpoint.upper()} - Complete Structure:")
        print("-" * 50)
        pprint(data, depth=3, width=80)
        print()

if __name__ == "__main__":
    available_data = explore_oura_api()
    
    if available_data:
        analyze_data_structure(available_data)
    
    print("\n🎯 CONCLUSION:")
    print("=" * 60)
    if available_data:
        print(f"✅ Found data from {len(available_data)} endpoints")
        print("📈 Use this information to enhance your health bot!")
    else:
        print("❌ No data found - check your Oura Ring sync status") 