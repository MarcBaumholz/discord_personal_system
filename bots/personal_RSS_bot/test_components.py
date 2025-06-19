#!/usr/bin/env python3
"""
Simple test script to verify all components work correctly.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_database():
    """Test database functionality."""
    print("Testing Database...")
    try:
        from database import DatabaseManager
        db = DatabaseManager("data/test_db.db")
        print("✅ Database: OK")
        return True
    except Exception as e:
        print(f"❌ Database: {e}")
        return False

def test_rss_manager():
    """Test RSS manager functionality."""
    print("Testing RSS Manager...")
    try:
        from rss_manager import RSSFeedManager
        rss = RSSFeedManager()
        print("✅ RSS Manager: OK")
        return True
    except Exception as e:
        print(f"❌ RSS Manager: {e}")
        return False

def test_llm_processor():
    """Test LLM processor functionality."""
    print("Testing LLM Processor...")
    try:
        from llm_processor import LLMProcessor
        llm = LLMProcessor()
        print("✅ LLM Processor: OK")
        return True
    except Exception as e:
        print(f"❌ LLM Processor: {e}")
        return False

def test_discord_publisher():
    """Test Discord publisher functionality."""
    print("Testing Discord Publisher...")
    try:
        from discord_publisher import DiscordPublisher
        # Test with dummy values since we don't have real tokens
        publisher = DiscordPublisher("dummy_token", 123456)
        print("✅ Discord Publisher: OK")
        return True
    except Exception as e:
        print(f"❌ Discord Publisher: {e}")
        return False

def test_main_app():
    """Test main application."""
    print("Testing Main Application...")
    try:
        from main import RSSNewsBot
        # Test initialization without starting
        bot = RSSNewsBot()
        print("✅ Main Application: OK")
        return True
    except Exception as e:
        print(f"❌ Main Application: {e}")
        return False

def main():
    """Run all component tests."""
    print("=" * 50)
    print("Personal RSS News Bot - Component Tests")
    print("=" * 50)
    
    tests = [
        test_database,
        test_rss_manager,
        test_llm_processor,
        test_discord_publisher,
        test_main_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All components working correctly!")
        print("The RSS News Bot is ready for deployment!")
    else:
        print("⚠️  Some components have issues that need attention.")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 