#!/usr/bin/env python3
"""
Test script for Tagebuch Bot components
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_text_processor():
    """Test the text processor component"""
    print("🧪 Testing Text Processor...")
    
    from text_processor import TextProcessor
    
    processor = TextProcessor()
    
    # Test cases
    test_texts = [
        "Heute war ein wunderschöner Tag! Ich habe viel gelernt und bin dankbar.",
        "Ich bin heute sehr müde. Es war ein anstrengender Tag bei der Arbeit.",
        "Kurzer Text",
        "Ein sehr langer Text ohne Satzzeichen der trotzdem verarbeitet werden sollte und einen sinnvollen Titel bekommen soll",
        ""
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Input: '{text}'")
        
        if text:
            title = processor.generate_title(text)
            is_valid = processor.validate_text(text)
            formatted = processor.format_text_for_notion(text)
            
            print(f"Title: '{title}'")
            print(f"Valid: {is_valid}")
            print(f"Formatted length: {len(formatted)}")
        else:
            print("Empty text - skipping processing")
    
    print("✅ Text Processor tests completed")

def test_notion_connection():
    """Test Notion connection (without creating entries)"""
    print("\n🧪 Testing Notion Connection...")
    
    try:
        from notion_manager import NotionManager
        
        # This will test the connection during initialization
        notion = NotionManager()
        print("✅ Notion connection successful")
        
    except Exception as e:
        print(f"❌ Notion connection failed: {e}")
        return False
    
    return True

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("\n🧪 Testing Environment Variables...")
    
    required_vars = [
        "DISCORD_TOKEN",
        "NOTION_TOKEN", 
        "TAGEBUCH_DATABASE_ID",
        "TAGEBUCH_CHANNEL_ID"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
        else:
            # Don't print actual tokens for security
            if "TOKEN" in var:
                print(f"✅ {var}: Set (length: {len(value)})")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False
    
    print("✅ All environment variables are set")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Tagebuch Bot Component Tests\n")
    
    # Test environment variables first
    if not test_environment_variables():
        print("\n❌ Environment variable tests failed. Cannot continue.")
        sys.exit(1)
    
    # Test text processor
    test_text_processor()
    
    # Test Notion connection
    notion_ok = test_notion_connection()
    
    print("\n" + "="*50)
    print("📊 Test Summary:")
    print("✅ Environment Variables: OK")
    print("✅ Text Processor: OK")
    print(f"{'✅' if notion_ok else '❌'} Notion Connection: {'OK' if notion_ok else 'FAILED'}")
    
    if notion_ok:
        print("\n🎉 All tests passed! The bot should work correctly.")
        print("\n💡 Next steps:")
        print("1. Make sure Discord bot has proper permissions")
        print("2. Run: python tagebuch_bot.py")
        print("3. Test with !tagebuch_help command in Discord")
    else:
        print("\n⚠️  Notion connection failed. Check your NOTION_TOKEN and database settings.")

if __name__ == "__main__":
    main() 