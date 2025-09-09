#!/usr/bin/env python3
"""
Test Script für Todo Bot
Testet die Todoist API Integration
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path to import todo_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from todo_agent import TodoistAPI

def test_todoist_connection():
    """Test Todoist API connection"""
    load_dotenv('/home/pi/Documents/discord/bots/00_production/.env')
    
    api_key = os.getenv('TODOIST_API_KEY')
    if not api_key:
        print("❌ TODOIST_API_KEY not found!")
        return False
    
    print(f"🔑 Using API Key: {api_key[:10]}...")
    
    # Initialize API
    todoist = TodoistAPI(api_key)
    
    # Test connection by getting active tasks
    print("📝 Testing connection...")
    tasks = todoist.get_active_tasks()
    
    if tasks is None:
        print("❌ Failed to connect to Todoist API")
        return False
    
    print(f"✅ Successfully connected! Found {len(tasks)} active tasks")
    
    # Show first few tasks
    for i, task in enumerate(tasks[:3]):
        print(f"  {i+1}. {task.content}")
        if task.due_date:
            print(f"     📅 Due: {task.due_date}")
        if task.labels:
            print(f"     🏷️ Labels: {', '.join(task.labels)}")
    
    # Test creating a task
    print("\n🧪 Testing task creation...")
    test_task = todoist.create_task(
        content="Test Task from Discord Bot",
        description="This is a test task created by the Todo Bot",
        priority=2,
        labels=["Test"]
    )
    
    if test_task:
        print(f"✅ Created test task: {test_task.content} (ID: {test_task.id})")
        
        # Test completing the task
        print("🧪 Testing task completion...")
        if todoist.complete_task(test_task.id):
            print("✅ Successfully completed test task")
        else:
            print("❌ Failed to complete test task")
    else:
        print("❌ Failed to create test task")
    
    return True

def test_message_parsing():
    """Test message parsing logic"""
    print("\n🧪 Testing message parsing...")
    
    # Mock message class
    class MockMessage:
        def __init__(self, content, author_name="TestUser"):
            self.content = content
            self.author = MockAuthor(author_name)
    
    class MockAuthor:
        def __init__(self, name):
            self.display_name = name
    
    # Import bot (but don't start it)
    from todo_agent import TodoBot
    bot = TodoBot()
    
    # Test cases
    test_messages = [
        "Wichtig: Einkaufen heute",
        "Marc soll Müll rausbringen morgen",
        "Gemeinsam: Urlaub planen nächste Woche",
        "Dringend: Arzttermin vereinbaren am Montag",
        "Niedrig: Buch lesen später"
    ]
    
    for msg_text in test_messages:
        mock_msg = MockMessage(msg_text)
        parsed = bot.parse_message_for_todo(mock_msg)
        
        print(f"\n📝 Message: '{msg_text}'")
        print(f"   Content: {parsed['content']}")
        priority_emoji = ["", "🟢", "🟡", "🟠", "🔴"]
        print(f"   Priority: {parsed['priority']} {priority_emoji[parsed['priority']]}")
        print(f"   Due Date: {parsed['due_date']}")
        print(f"   Labels: {parsed['labels']}")

def main():
    """Run all tests"""
    print("🚀 Starting Todo Bot Tests\n")
    
    # Test Todoist connection
    if not test_todoist_connection():
        return
    
    # Test message parsing
    test_message_parsing()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
