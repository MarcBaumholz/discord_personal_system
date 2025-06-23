#!/usr/bin/env python3
"""
Test script for monthly calorie report functionality
Tests all components together with real data
"""

import asyncio
from datetime import datetime
from notion_data_reader import CalorieDataExtractor
from chart_generator import CalorieChartGenerator
from monthly_report import MonthlyReportGenerator

async def test_complete_workflow():
    """Test the complete monthly report workflow"""
    try:
        print("🧪 Testing Complete Monthly Report Workflow")
        print("=" * 50)
        
        # Use current month data (June 2025) since we found data there
        test_year = 2025
        test_month = 6
        
        print(f"📅 Testing with {test_month}/{test_year}")
        
        # 1. Test Data Extraction
        print("\n1️⃣ Testing Data Extraction...")
        extractor = CalorieDataExtractor()
        
        users = extractor.get_all_users(test_year, test_month)
        print(f"👥 Users found: {users}")
        
        if not users:
            print("❌ No users found - cannot continue test")
            return False
        
        test_user = users[0]
        print(f"🔍 Testing with user: {test_user}")
        
        # Get user data
        df = extractor.get_user_monthly_data(test_year, test_month, test_user)
        stats = extractor.get_monthly_stats(test_year, test_month, test_user)
        
        print(f"📊 Data points: {len(df)}")
        print(f"📈 Stats: {stats}")
        
        # 2. Test Chart Generation
        print("\n2️⃣ Testing Chart Generation...")
        chart_generator = CalorieChartGenerator()
        
        chart_path = f"test_monthly_chart_{test_user}_{test_year}_{test_month}.png"
        chart_success = chart_generator.create_monthly_chart(df, stats, chart_path)
        
        if chart_success:
            print(f"✅ Chart created successfully: {chart_path}")
        else:
            print("❌ Chart creation failed")
            return False
        
        # 3. Test Report Generation (without Discord)
        print("\n3️⃣ Testing Report Generation...")
        report_generator = MonthlyReportGenerator()
        
        report_data = await report_generator.generate_monthly_report(test_year, test_month, test_user)
        
        if report_data.get('success'):
            print("✅ Monthly report generated successfully")
            print(f"📊 Report data: {report_data}")
        else:
            print(f"❌ Report generation failed: {report_data.get('message')}")
            return False
        
        # 4. Test Discord Embed Creation
        print("\n4️⃣ Testing Discord Embed Creation...")
        embed = report_generator.create_report_embed(report_data)
        
        print(f"✅ Discord embed created: {embed.title}")
        print(f"📝 Embed description: {embed.description}")
        print(f"🎨 Embed color: {embed.color}")
        print(f"📊 Fields count: {len(embed.fields)}")
        
        # 5. Clean up test files
        print("\n5️⃣ Cleaning up test files...")
        import os
        try:
            if os.path.exists(chart_path):
                os.remove(chart_path)
                print(f"🧹 Removed: {chart_path}")
            
            if os.path.exists("test_chart.png"):
                os.remove("test_chart.png")
                print("🧹 Removed: test_chart.png")
                
        except OSError as e:
            print(f"⚠️ Cleanup warning: {e}")
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED! Monthly functionality is working correctly.")
        print("🎉 Ready for production use!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scheduler_functionality():
    """Test scheduler functionality without actually running it"""
    try:
        print("\n🧪 Testing Scheduler Functionality")
        print("=" * 50)
        
        from scheduler import MonthlyReportScheduler
        
        scheduler = MonthlyReportScheduler()
        
        # Test status
        status = scheduler.get_scheduler_status()
        print(f"📊 Scheduler status: {status}")
        
        print("✅ Scheduler functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🍽️ Monthly Calorie Report - Comprehensive Test Suite")
    print("=" * 60)
    
    # Run async workflow test
    workflow_success = asyncio.run(test_complete_workflow())
    
    # Run scheduler test
    scheduler_success = asyncio.run(test_scheduler_functionality())
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    print(f"🔧 Workflow Test: {'✅ PASSED' if workflow_success else '❌ FAILED'}")
    print(f"⏰ Scheduler Test: {'✅ PASSED' if scheduler_success else '❌ FAILED'}")
    
    if workflow_success and scheduler_success:
        print("\n🎉 ALL SYSTEMS GO! Monthly calorie reports are ready for deployment!")
        print("\n📝 Next Steps:")
        print("   1. Set up environment variables (.env file)")
        print("   2. Start the scheduler: python scheduler.py start")
        print("   3. Test manually: python scheduler.py manual")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 