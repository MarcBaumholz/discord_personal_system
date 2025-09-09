#!/usr/bin/env python3
"""
Simple test script to verify Calories Bot functionality
Tests the logger fixes and basic bot operations
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from logger_config import CaloriesBotLogger
from calories_bot import GroundTruthHandler, FoodAnalysisResult

def test_logger_fixes():
    """Test that the logger fixes work properly"""
    print("🔧 Testing logger fixes...")
    
    # Create temporary log directory
    test_log_dir = tempfile.mkdtemp()
    
    try:
        # Initialize logger
        logger = CaloriesBotLogger(log_dir=test_log_dir)
        
        # Test error logging (this was the main issue)
        print("  Testing log_error method...")
        logger.log_error("Test Error", "This should not raise AttributeError")
        
        # Test warning logging (newly added)
        print("  Testing log_warning method...")
        logger.log_warning("Test Warning", "This should not raise AttributeError")
        
        # Test food analysis logging
        print("  Testing log_food_analysis method...")
        logger.log_food_analysis({
            'user': 'TestUser',
            'food_name': 'Test Food',
            'calories': 300,
            'confidence': 85.0,
            'protein': 20.0,
            'carbohydrates': 30.0,
            'fat': 10.0
        })
        
        # Test user command logging
        print("  Testing log_user_command method...")
        logger.log_user_command("TestUser", "test_command", "test_channel")
        
        print("  ✅ All logger methods work correctly!")
        return True
        
    except AttributeError as e:
        print(f"  ❌ Logger still has AttributeError: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False
    finally:
        # Clean up
        shutil.rmtree(test_log_dir)

def test_ground_truth_handler():
    """Test ground truth handler functionality"""
    print("\n🍎 Testing Ground Truth Handler...")
    
    # Create test data
    test_data = {
        "apple": {
            "calories": 95,
            "protein": 0.5,
            "carbohydrates": 25.0,
            "fat": 0.3,
            "fiber": 4.0,
            "sugar": 19.0,
            "vitamins": {"C": 14.0},
            "minerals": {"potassium": 195.0}
        },
        "banana": {
            "calories": 105,
            "protein": 1.3,
            "carbohydrates": 27.0,
            "fat": 0.4,
            "fiber": 3.1,
            "sugar": 14.0,
            "vitamins": {"B6": 0.4, "C": 17.0},
            "minerals": {"potassium": 422.0}
        }
    }
    
    # Create temporary ground truth file
    import json
    test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(test_data, test_file)
    test_file.close()
    
    try:
        # Mock the handler initialization
        handler = GroundTruthHandler()
        handler.ground_truth_file = test_file.name
        handler.foods_db = test_data
        
        # Test exact match
        print("  Testing exact match...")
        result = handler.search_ground_truth("apple")
        if result and result.food_name == "apple" and result.calories == 95:
            print("    ✅ Exact match works")
        else:
            print("    ❌ Exact match failed")
            return False
        
        # Test partial match
        print("  Testing partial match...")
        result = handler.search_ground_truth("banana bread")
        if result and result.food_name == "banana":
            print("    ✅ Partial match works")
        else:
            print("    ❌ Partial match failed")
            return False
        
        # Test no match
        print("  Testing no match...")
        result = handler.search_ground_truth("pizza")
        if result is None:
            print("    ✅ No match works")
        else:
            print("    ❌ No match failed")
            return False
        
        print("  ✅ Ground Truth Handler works correctly!")
        return True
        
    except Exception as e:
        print(f"  ❌ Ground Truth Handler error: {e}")
        return False
    finally:
        # Clean up
        os.unlink(test_file.name)

def test_food_analysis_result():
    """Test FoodAnalysisResult class"""
    print("\n🥗 Testing FoodAnalysisResult...")
    
    try:
        # Test basic creation
        result = FoodAnalysisResult(
            food_name="Test Food",
            calories=300,
            confidence=85.0,
            description="A test food item",
            protein=20.0,
            carbohydrates=30.0,
            fat=10.0,
            fiber=5.0,
            sugar=15.0,
            saturated_fat=3.0,
            cholesterol=50.0,
            vitamins={"C": 100.0},
            minerals={"iron": 2.0},
            analysis_source="test"
        )
        
        # Test properties
        assert result.food_name == "Test Food"
        assert result.calories == 300
        assert result.confidence == 85.0
        assert result.protein == 20.0
        assert result.analysis_source == "test"
        
        # Test meal hash generation
        hash1 = result.get_meal_hash()
        hash2 = result.get_meal_hash()
        assert hash1 == hash2  # Should be consistent
        
        print("  ✅ FoodAnalysisResult works correctly!")
        return True
        
    except Exception as e:
        print(f"  ❌ FoodAnalysisResult error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Calories Bot Functionality Test")
    print("=" * 50)
    
    tests = [
        test_logger_fixes,
        test_ground_truth_handler,
        test_food_analysis_result
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Calories Bot should be working correctly now.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
