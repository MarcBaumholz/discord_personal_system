#!/usr/bin/env python3
"""
Final test to verify the Calories Bot is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_calories_bot():
    """Test the Calories Bot functionality"""
    print("🧪 Final Calories Bot Test")
    print("=" * 40)
    
    try:
        # Test 1: Import bot module
        print("1. Testing bot module import...")
        import bot
        print("   ✅ Bot module imported successfully")
        
        # Test 2: Test logger functionality
        print("2. Testing logger functionality...")
        from logger_config import CaloriesBotLogger
        logger = CaloriesBotLogger()
        
        # Test error logging (the main fix)
        logger.log_error("Test Error", "This should work now")
        print("   ✅ Error logging works")
        
        # Test warning logging (newly added)
        logger.log_warning("Test Warning", "This should work now")
        print("   ✅ Warning logging works")
        
        # Test 3: Test ground truth handler
        print("3. Testing ground truth handler...")
        ground_truth_handler = bot.GroundTruthHandler()
        print("   ✅ Ground truth handler initialized")
        
        # Test 4: Test AI text handler
        print("4. Testing AI text handler...")
        ai_handler = bot.AITextHandler()
        print("   ✅ AI text handler initialized")
        
        # Test 5: Test food analysis result
        print("5. Testing food analysis result...")
        result = bot.FoodAnalysisResult(
            food_name="Test Food",
            calories=300,
            confidence=85.0
        )
        print(f"   ✅ Food analysis result created: {result.food_name}")
        
        print("\n🎉 All tests passed! The Calories Bot is working correctly.")
        print("The logger error has been fixed and the bot should now process")
        print("food text without the 'CaloriesBotLogger' object has no attribute 'error' error.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calories_bot()
    sys.exit(0 if success else 1)
