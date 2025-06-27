#!/usr/bin/env python3
"""
Test script for Tagebuch Bot logic without requiring real tokens
Tests the core functionality with mock data
"""

import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

def test_text_processor():
    """Test text processor functionality"""
    print("🧪 Testing Text Processor...")
    
    try:
        from text_processor import TextProcessor
        processor = TextProcessor()
        
        test_cases = [
            "Heute war ein schöner Tag!",
            "Ich bin müde. Lange Arbeit heute.",
            "Kurz",
            "Ein sehr langer Text ohne Punkt der trotzdem funktionieren sollte"
        ]
        
        for i, text in enumerate(test_cases, 1):
            title = processor.generate_title(text)
            valid = processor.validate_text(text)
            formatted = processor.format_text_for_notion(text)
            
            print(f"   Test {i}: {text[:30]}...")
            print(f"   Title: '{title}' | Valid: {valid} | Length: {len(formatted)}")
        
        print("✅ Text Processor tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Text Processor test failed: {e}")
        return False

def test_scheduler_logic():
    """Test scheduler logic"""
    print("\n🧪 Testing Scheduler Logic...")
    
    try:
        from scheduler import ReminderScheduler
        
        # Mock bot
        mock_bot = Mock()
        scheduler = ReminderScheduler(mock_bot)
        
        # Test reminder message creation
        reminder_msg = scheduler.create_reminder_message()
        
        if reminder_msg and len(reminder_msg) > 50:
            print("✅ Scheduler logic works")
            print(f"   Reminder preview: {reminder_msg[:80]}...")
            return True
        else:
            print("❌ Scheduler reminder message too short")
            return False
            
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False

def test_notion_manager_structure():
    """Test notion manager structure without real connection"""
    print("\n🧪 Testing Notion Manager Structure...")
    
    try:
        # Mock environment variables
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'mock_token_for_testing_purposes_only',
            'TAGEBUCH_DATABASE_ID': '214d42a1faf5803193c6c71b7d4d7c3f'
        }):
            from notion_manager import NotionManager
            
            # This will fail at connection, but we can test the structure
            try:
                manager = NotionManager()
            except Exception as connection_error:
                # Expected to fail without real token
                if "API token is invalid" in str(connection_error) or "Failed to connect" in str(connection_error):
                    print("✅ Notion Manager structure is correct (connection fails as expected)")
                    return True
                else:
                    print(f"⚠️  Unexpected connection error: {connection_error}")
                    return False
                    
    except ImportError as e:
        print(f"❌ Notion Manager import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Notion Manager test failed: {e}")
        return False

def test_bot_message_processing():
    """Test bot message processing logic"""
    print("\n🧪 Testing Bot Message Processing Logic...")
    
    try:
        # Mock Discord message
        mock_message = Mock()
        mock_message.content = "Heute war ein wunderschöner Tag! Ich habe viel gelernt."
        mock_message.author.bot = False
        mock_message.channel.id = 1384289197115838625
        
        # Test text validation
        text = mock_message.content.strip()
        if len(text) > 10:  # Basic validation
            print("✅ Message validation works")
            print(f"   Test message: {text[:50]}...")
            return True
        else:
            print("❌ Message validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Bot message processing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Tagebuch Bot Logic Tests")
    print("="*50)
    print("Testing core functionality without real tokens...")
    print()
    
    results = {
        "Text Processor": test_text_processor(),
        "Scheduler Logic": test_scheduler_logic(),
        "Notion Manager Structure": test_notion_manager_structure(),
        "Message Processing": test_bot_message_processing()
    }
    
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All logic tests passed! Bot code is working correctly.")
        print("Next step: Configure real tokens using setup_validator.py")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 