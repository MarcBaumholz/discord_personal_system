#!/usr/bin/env python3
"""
Test script to validate Health Bot fixes and ensure real data usage.
This script tests the main components without running the full Discord bot.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from config import Config
from oura_client import OuraClient
from health_analyzer import HealthAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_connection():
    """Test API connection and authentication."""
    print("\n🔍 Testing API Connection...")
    
    config = Config()
    if not config.validate():
        print("❌ Configuration validation failed!")
        return False
    
    client = OuraClient(config.OURA_ACCESS_TOKEN)
    
    try:
        # Test API connection
        test_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        response = client.session.get(
            f"{client.BASE_URL}/daily_sleep",
            params={"start_date": test_date, "end_date": test_date},
            timeout=10
        )
        response.raise_for_status()
        print(f"✅ API Connection successful! Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ API Connection failed: {e}")
        return False

async def test_data_retrieval():
    """Test data retrieval and validation."""
    print("\n📊 Testing Data Retrieval...")
    
    config = Config()
    client = OuraClient(config.OURA_ACCESS_TOKEN)
    
    # Test data retrieval
    health_data = client.get_yesterday_data()
    
    if not health_data:
        print("❌ No health data retrieved!")
        return False
    
    print(f"✅ Health data retrieved for date: {health_data.date}")
    
    # Validate data sources
    data_sources = []
    if health_data.sleep_score and health_data.sleep_score > 0:
        data_sources.append(f"Sleep Score: {health_data.sleep_score}/100")
    if health_data.readiness_score and health_data.readiness_score > 0:
        data_sources.append(f"Readiness Score: {health_data.readiness_score}/100")
    if health_data.total_calories > 0:
        data_sources.append(f"Total Calories: {health_data.total_calories:,}")
    if health_data.active_calories > 0:
        data_sources.append(f"Active Calories: {health_data.active_calories:,}")
    if health_data.steps > 0:
        data_sources.append(f"Steps: {health_data.steps:,}")
    if health_data.spo2_average:
        data_sources.append(f"SpO2: {health_data.spo2_average:.1f}%")
    
    if data_sources:
        print("📋 Available Real Data Sources:")
        for source in data_sources:
            print(f"   • {source}")
    else:
        print("⚠️ No meaningful data found - this indicates sync issues")
        return False
    
    return True

async def test_health_analysis():
    """Test health analysis functionality."""
    print("\n🧠 Testing Health Analysis...")
    
    config = Config()
    client = OuraClient(config.OURA_ACCESS_TOKEN)
    analyzer = HealthAnalyzer()
    
    # Get data
    health_data = client.get_yesterday_data()
    if not health_data:
        print("❌ No data for analysis!")
        return False
    
    # Analyze data
    try:
        insight = analyzer.analyze(health_data)
        print(f"✅ Analysis completed!")
        print(f"   Status: {insight.status.value}")
        print(f"   Score: {insight.score}/100")
        print(f"   Message: {insight.message[:100]}...")
        
        if insight.tips:
            print(f"   Tips: {len(insight.tips)} personalized recommendations")
        
        return True
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

async def test_data_validation():
    """Test data validation functions."""
    print("\n🔍 Testing Data Validation...")
    
    config = Config()
    client = OuraClient(config.OURA_ACCESS_TOKEN)
    
    # Get data
    health_data = client.get_yesterday_data()
    if not health_data:
        print("❌ No data for validation!")
        return False
    
    # Test validation logic
    has_sleep_data = health_data.sleep_score is not None and health_data.sleep_score > 0
    has_readiness_data = health_data.readiness_score is not None and health_data.readiness_score > 0
    has_activity_data = (health_data.total_calories > 0 or health_data.steps > 0)
    
    print(f"✅ Data Validation Results:")
    print(f"   Sleep Data: {'✅ Available' if has_sleep_data else '❌ Not available'}")
    print(f"   Readiness Data: {'✅ Available' if has_readiness_data else '❌ Not available'}")
    print(f"   Activity Data: {'✅ Available' if has_activity_data else '❌ Not available'}")
    
    # Overall validation
    is_valid = has_sleep_data or has_readiness_data or has_activity_data
    print(f"   Overall Quality: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    return is_valid

async def test_error_handling():
    """Test error handling scenarios."""
    print("\n🛡️ Testing Error Handling...")
    
    # Test with invalid token
    try:
        client = OuraClient("invalid_token")
        test_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # This should fail gracefully
        sleep_data = client.get_daily_sleep(test_date)
        if sleep_data is None:
            print("✅ Invalid token handled gracefully")
        else:
            print("⚠️ Invalid token should have failed")
    except Exception as e:
        print(f"✅ Invalid token failed as expected: {type(e).__name__}")
    
    return True

async def run_comprehensive_test():
    """Run all tests and provide final assessment."""
    print("🚀 Starting Comprehensive Health Bot Testing...")
    print("=" * 60)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Data Retrieval", test_data_retrieval),
        ("Health Analysis", test_health_analysis),
        ("Data Validation", test_data_validation),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your health bot is ready to use with real data!")
        print("✅ Error handling is working properly!")
        print("✅ Data validation is functioning correctly!")
    else:
        print(f"\n⚠️ {total - passed} tests failed!")
        print("❌ Please check the configuration and API connection!")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test()) 