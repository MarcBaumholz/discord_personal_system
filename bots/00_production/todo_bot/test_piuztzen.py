#!/usr/bin/env python3
"""
Test Script specifically for testing 'piuztzen' message functionality
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path to import todo_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from todo_agent import TodoistAPI, TodoBot

def test_piuztzen_message():
    """Test that 'piuztzen' message creates a todo successfully"""
    print("🧪 Testing 'piuztzen' message functionality...")
    
    # Load environment variables
    load_dotenv('/home/pi/Documents/discord/bots/00_production/.env')
    
    # Initialize API
    api_key = os.getenv('TODOIST_API_KEY')
    if not api_key:
        print("❌ TODOIST_API_KEY not found!")
        return False
    
    todoist = TodoistAPI(api_key)
    
    # Mock message class
    class MockMessage:
        def __init__(self, content, author_name="TestUser"):
            self.content = content
            self.author = MockAuthor(author_name)
    
    class MockAuthor:
        def __init__(self, name):
            self.display_name = name
    
    # Import bot (but don't start it)
    bot = TodoBot()
    
    # Test the specific 'piuztzen' message
    test_message = "piuztzen"
    mock_msg = MockMessage(test_message)
    
    print(f"📝 Testing message: '{test_message}'")
    
    # Parse the message
    parsed = bot.parse_message_for_todo(mock_msg)
    
    print(f"   Content: {parsed['content']}")
    print(f"   Priority: {parsed['priority']}")
    print(f"   Due Date: {parsed['due_date']}")
    print(f"   Labels: {parsed['labels']}")
    
    # Create the todo in Todoist
    print("\n🧪 Creating todo in Todoist...")
    todo = todoist.create_task(**parsed)
    
    if todo:
        print(f"✅ Successfully created todo: '{todo.content}' (ID: {todo.id})")
        print(f"   Priority: {todo.priority}")
        print(f"   Due Date: {todo.due_date}")
        print(f"   Labels: {todo.labels}")
        
        # Clean up - complete the test task
        print("\n🧹 Cleaning up test task...")
        if todoist.complete_task(todo.id):
            print("✅ Test task completed and cleaned up")
        else:
            print("❌ Failed to clean up test task")
        
        return True
    else:
        print("❌ Failed to create todo from 'piuztzen' message")
        return False

def test_various_messages():
    """Test various message formats to ensure they work"""
    print("\n🧪 Testing various message formats...")
    
    # Load environment variables
    load_dotenv('/home/pi/Documents/discord/bots/00_production/.env')
    
    # Initialize API
    api_key = os.getenv('TODOIST_API_KEY')
    if not api_key:
        print("❌ TODOIST_API_KEY not found!")
        return False
    
    todoist = TodoistAPI(api_key)
    
    # Mock message class
    class MockMessage:
        def __init__(self, content, author_name="TestUser"):
            self.content = content
            self.author = MockAuthor(author_name)
    
    class MockAuthor:
        def __init__(self, name):
            self.display_name = name
    
    # Import bot (but don't start it)
    bot = TodoBot()
    
    # Test cases
    test_messages = [
        "piuztzen",
        "Wichtig: piuztzen heute",
        "Marc soll piuztzen morgen",
        "Gemeinsam: piuztzen nächste Woche",
        "Dringend: piuztzen am Montag",
        "Einfach nur piuztzen",
        "piuztzen für Maggie",
        "piuztzen mit hoher Priorität"
    ]
    
    created_todos = []
    
    for msg_text in test_messages:
        mock_msg = MockMessage(msg_text)
        parsed = bot.parse_message_for_todo(mock_msg)
        
        print(f"\n📝 Message: '{msg_text}'")
        print(f"   Content: {parsed['content']}")
        print(f"   Priority: {parsed['priority']}")
        print(f"   Due Date: {parsed['due_date']}")
        print(f"   Labels: {parsed['labels']}")
        
        # Create the todo in Todoist
        todo = todoist.create_task(**parsed)
        
        if todo:
            print(f"   ✅ Created: {todo.content} (ID: {todo.id})")
            created_todos.append(todo)
        else:
            print(f"   ❌ Failed to create todo")
    
    # Clean up all created todos
    print(f"\n🧹 Cleaning up {len(created_todos)} test todos...")
    for todo in created_todos:
        if todoist.complete_task(todo.id):
            print(f"   ✅ Cleaned up: {todo.content}")
        else:
            print(f"   ❌ Failed to clean up: {todo.content}")
    
    return len(created_todos) > 0

def main():
    """Run all tests"""
    print("🚀 Starting Piuztzen Message Tests\n")
    
    # Test the specific 'piuztzen' message
    if not test_piuztzen_message():
        print("\n❌ 'piuztzen' message test failed!")
        return
    
    # Test various message formats
    if not test_various_messages():
        print("\n❌ Various message formats test failed!")
        return
    
    print("\n✅ All piuztzen tests completed successfully!")
    print("🎉 The todo bot should now work with 'piuztzen' messages!")

if __name__ == "__main__":
    main()
