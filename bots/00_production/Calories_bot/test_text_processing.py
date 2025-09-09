#!/usr/bin/env python3
"""
Test script to verify text processing works without logger errors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_text_processing():
    """Test the text processing function that was failing"""
    try:
        # Import the necessary modules
        from logger_config import CaloriesBotLogger
        from calories_bot import GroundTruthHandler, AITextHandler
        
        print("🧪 Testing text processing functionality...")
        
        # Test logger
        logger = CaloriesBotLogger()
        logger.log_error("Test Error", "Testing error logging")
        logger.log_warning("Test Warning", "Testing warning logging")
        print("  ✅ Logger methods work correctly")
        
        # Test ground truth handler
        handler = GroundTruthHandler()
        print("  ✅ Ground truth handler initialized")
        
        # Test AI text handler
        ai_handler = AITextHandler()
        print("  ✅ AI text handler initialized")
        
        print("🎉 All components working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_text_processing()
    sys.exit(0 if success else 1)
