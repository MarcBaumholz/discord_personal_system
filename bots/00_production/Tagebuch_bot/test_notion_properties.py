#!/usr/bin/env python3
"""
Test script to check Notion database properties
This helps debug property name mismatches.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

def test_notion_properties():
    """Test and display Notion database properties"""
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("TAGEBUCH_DATABASE_ID")
    
    if not token or not database_id:
        print("❌ Missing NOTION_TOKEN or TAGEBUCH_DATABASE_ID")
        return
    
    try:
        notion = Client(auth=token)
        
        # Get database info
        print("🔍 Checking Notion database...")
        database = notion.databases.retrieve(database_id=database_id)
        
        print(f"✅ Connected to database: {database.get('title', [{}])[0].get('plain_text', 'Untitled')}")
        
        # Display properties
        properties = database.get('properties', {})
        print(f"\n📊 Available properties ({len(properties)}):")
        
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type', 'unknown')
            print(f"  • {prop_name} ({prop_type})")
        
        # Check for expected properties
        expected_props = ['Title', 'Date', 'Text']
        german_props = ['Titel', 'Datum', 'Text']
        
        print(f"\n🔍 Checking for expected properties:")
        
        for prop in expected_props:
            status = "✅" if prop in properties else "❌"
            print(f"  {status} {prop}")
        
        print(f"\n🔍 Checking for German properties:")
        for prop in german_props:
            status = "✅" if prop in properties else "❌"
            print(f"  {status} {prop}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if 'Title' in properties and 'Date' in properties and 'Text' in properties:
            print("  ✅ Database uses English property names - current bot config should work")
        elif 'Titel' in properties and 'Datum' in properties and 'Text' in properties:
            print("  ⚠️  Database uses German property names - bot needs German config")
        else:
            print("  ❌ Database properties don't match expected names")
            print("     Please ensure your database has: Title, Date, Text properties")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_notion_properties() 