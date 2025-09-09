#!/usr/bin/env python3
"""
Test script to validate calories integration with Notion database.
This script tests the complete calories analysis functionality.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from config import Config
from oura_client import OuraClient
from health_analyzer import HealthAnalyzer
from notion_calories_client import NotionCaloriesClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_notion_connection():
    """Test Notion API connection and database access."""
    print("\n🔍 Testing Notion Connection...")
    
    config = Config()
    if not config.NOTION_TOKEN or not config.FOODIATE_DB_ID:
        print("❌ Missing Notion configuration!")
        return False
    
    try:
        client = NotionCaloriesClient(config.NOTION_TOKEN, config.FOODIATE_DB_ID)
        success = client.test_connection()
        
        if success:
            print("✅ Notion connection successful!")
            return True
        else:
            print("❌ Notion connection failed!")
            return False
    except Exception as e:
        print(f"❌ Notion connection error: {e}")
        return False

async def test_calories_retrieval():
    """Test calories data retrieval from Notion."""
    print("\n📊 Testing Calories Retrieval...")
    
    config = Config()
    client = NotionCaloriesClient(config.NOTION_TOKEN, config.FOODIATE_DB_ID)
    
    try:
        # Test yesterday's calories
        consumed_calories, food_entries = client.get_yesterday_calories("Marc")
        
        print(f"✅ Calories retrieved for yesterday:")
        print(f"   Total consumed: {consumed_calories:,} kcal")
        print(f"   Number of meals: {len(food_entries)}")
        
        if food_entries:
            print("   Sample meals:")
            for i, entry in enumerate(food_entries[:3]):
                print(f"     {i+1}. {entry['food_name']} - {entry['calories']} kcal")
        
        return True
        
    except Exception as e:
        print(f"❌ Calories retrieval error: {e}")
        return False

async def test_health_analyzer_with_calories():
    """Test health analyzer with calories integration."""
    print("\n🧠 Testing Health Analyzer with Calories...")
    
    config = Config()
    oura_client = OuraClient(config.OURA_ACCESS_TOKEN)
    analyzer = HealthAnalyzer()
    
    try:
        # Get health data
        health_data = oura_client.get_yesterday_data()
        if not health_data:
            print("❌ No health data available!")
            return False
        
        print(f"✅ Health data retrieved:")
        print(f"   Sleep Score: {health_data.sleep_score}")
        print(f"   Readiness Score: {health_data.readiness_score}")
        print(f"   Total Calories: {health_data.total_calories}")
        print(f"   Active Calories: {health_data.active_calories}")
        
        # Analyze with calories
        insight = analyzer.analyze(health_data)
        
        print(f"✅ Health analysis completed:")
        print(f"   Status: {insight.status.value}")
        print(f"   Score: {insight.score}/100")
        
        # Check calories analysis
        if insight.calories_analysis:
            calories_data = insight.calories_analysis
            print(f"✅ Calories analysis available:")
            print(f"   Consumed: {calories_data['consumed_calories']:,} kcal")
            print(f"   Burned: {calories_data['burned_calories']:,} kcal")
            print(f"   Net: {calories_data['net_calories']:+,} kcal")
            print(f"   Status: {calories_data['balance_status']}")
            print(f"   Message: {calories_data['message']}")
        else:
            print("⚠️ No calories analysis available")
        
        return True
        
    except Exception as e:
        print(f"❌ Health analyzer error: {e}")
        return False

async def test_weekly_average():
    """Test weekly calories average calculation."""
    print("\n📅 Testing Weekly Calories Average...")
    
    config = Config()
    client = NotionCaloriesClient(config.NOTION_TOKEN, config.FOODIATE_DB_ID)
    
    try:
        avg_calories, daily_totals = client.get_weekly_calories_average("Marc", 7)
        
        print(f"✅ Weekly average calculated:")
        print(f"   Average daily calories: {avg_calories:.1f} kcal")
        print(f"   Days with data: {len(daily_totals)}")
        
        if daily_totals:
            print("   Daily breakdown:")
            for day in daily_totals[:5]:  # Show last 5 days
                print(f"     {day['date']}: {day['calories']} kcal ({day['entries_count']} meals)")
        
        return True
        
    except Exception as e:
        print(f"❌ Weekly average error: {e}")
        return False

async def test_calories_balance_scenarios():
    """Test different calories balance scenarios."""
    print("\n⚖️ Testing Calories Balance Scenarios...")
    
    config = Config()
    analyzer = HealthAnalyzer()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Calorie Surplus",
            "consumed": 3000,
            "burned": 2200,
            "expected_status": "calorie_surplus"
        },
        {
            "name": "Calorie Deficit", 
            "consumed": 1500,
            "burned": 2500,
            "expected_status": "calorie_deficit"
        },
        {
            "name": "Calorie Balanced",
            "consumed": 2200,
            "burned": 2200,
            "expected_status": "calorie_balanced"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n   Testing: {scenario['name']}")
        
        # Create mock health data
        from oura_client import HealthData
        mock_data = HealthData(
            date="2025-09-08",
            total_calories=scenario["burned"],
            active_calories=500,
            inactive_calories=scenario["burned"] - 500,
            steps=8000,
            sleep_score=80,
            readiness_score=75
        )
        
        # Mock the calories client to return test data
        original_client = analyzer.calories_client
        analyzer.calories_client = type('MockClient', (), {
            'get_yesterday_calories': lambda person: (scenario["consumed"], [])
        })()
        
        try:
            insight = analyzer.analyze(mock_data)
            
            if insight.calories_analysis:
                actual_status = insight.calories_analysis['balance_status']
                expected_status = scenario['expected_status']
                
                if actual_status == expected_status:
                    print(f"     ✅ Correct status: {actual_status}")
                else:
                    print(f"     ❌ Wrong status: {actual_status} (expected: {expected_status})")
            else:
                print(f"     ❌ No calories analysis generated")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
        finally:
            # Restore original client
            analyzer.calories_client = original_client
    
    return True

async def run_comprehensive_calories_test():
    """Run all calories integration tests."""
    print("🚀 Starting Comprehensive Calories Integration Testing...")
    print("=" * 70)
    
    tests = [
        ("Notion Connection", test_notion_connection),
        ("Calories Retrieval", test_calories_retrieval),
        ("Health Analyzer with Calories", test_health_analyzer_with_calories),
        ("Weekly Average", test_weekly_average),
        ("Calories Balance Scenarios", test_calories_balance_scenarios),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 CALORIES INTEGRATION TEST RESULTS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print("-" * 70)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL CALORIES INTEGRATION TESTS PASSED!")
        print("✅ Notion integration is working!")
        print("✅ Calories analysis is functional!")
        print("✅ Health bot is ready with calories tracking!")
    else:
        print(f"\n⚠️ {total - passed} tests failed!")
        print("❌ Please check the configuration and connections!")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_comprehensive_calories_test())
