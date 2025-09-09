#!/usr/bin/env python3
"""
Comprehensive Test Suite for Todo Bot
Tests all functionality including message parsing, Todoist integration, and Discord bot features
"""
import os
import sys
import asyncio
import unittest
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Add parent directory to path to import todo_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from todo_agent import TodoistAPI, TodoBot, TodoItem

class TestTodoBot(unittest.TestCase):
    """Comprehensive test suite for Todo Bot"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        load_dotenv('/home/pi/Documents/discord/bots/00_production/.env')
        
        cls.api_key = os.getenv('TODOIST_API_KEY')
        if not cls.api_key:
            raise unittest.SkipTest("TODOIST_API_KEY not found in environment")
        
        cls.todoist = TodoistAPI(cls.api_key)
        cls.bot = TodoBot()
    
    def setUp(self):
        """Set up for each test"""
        self.created_todos = []
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up any todos created during tests
        for todo in self.created_todos:
            try:
                self.todoist.complete_task(todo.id)
            except:
                pass  # Ignore cleanup errors
    
    def test_todoist_connection(self):
        """Test Todoist API connection"""
        print("\n🧪 Testing Todoist API connection...")
        tasks = self.todoist.get_active_tasks()
        self.assertIsNotNone(tasks)
        print(f"✅ Connected successfully! Found {len(tasks)} active tasks")
    
    def test_message_parsing_priority(self):
        """Test message parsing for priority detection"""
        print("\n🧪 Testing priority parsing...")
        
        test_cases = [
            ("Wichtig: Einkaufen", 4, "urgent/wichtig should be priority 4"),
            ("Dringend: Arzttermin", 4, "dringend should be priority 4"),
            ("Urgent: Meeting", 4, "urgent should be priority 4"),
            ("Sofort: Feuer löschen", 4, "sofort should be priority 4"),
            ("Hoch: Projekt", 3, "hoch should be priority 3"),
            ("High: Task", 3, "high should be priority 3"),
            ("Normal: Routine", 2, "normal should be priority 2"),
            ("Medium: Work", 2, "medium should be priority 2"),
            ("Niedrig: Lesen", 1, "niedrig should be priority 1"),
            ("Low: Hobby", 1, "low should be priority 1"),
            ("Später: Buch", 1, "später should be priority 1"),
            ("Einfach nur piuztzen", 1, "no priority keywords should default to 1")
        ]
        
        for message, expected_priority, description in test_cases:
            with self.subTest(message=message):
                mock_msg = self._create_mock_message(message)
                parsed = self.bot.parse_message_for_todo(mock_msg)
                self.assertEqual(parsed['priority'], expected_priority, description)
                print(f"   ✅ '{message}' → Priority {expected_priority}")
    
    def test_message_parsing_dates(self):
        """Test message parsing for date detection"""
        print("\n🧪 Testing date parsing...")
        
        test_cases = [
            ("Einkaufen heute", "today", "heute should be today"),
            ("Meeting tomorrow", "tomorrow", "tomorrow should be tomorrow"),
            ("Urlaub übermorgen", "in 2 days", "übermorgen should be in 2 days"),
            ("Projekt nächste Woche", "next week", "nächste woche should be next week"),
            ("Planung nächster Monat", "next month", "nächster monat should be next month"),
            ("Termin am Montag", "monday", "montag should be monday"),
            ("Meeting am Dienstag", "tuesday", "dienstag should be tuesday"),
            ("Arbeit am Mittwoch", "wednesday", "mittwoch should be wednesday"),
            ("Freitag frei", "friday", "freitag should be friday"),
            ("Termin am 15.12", "12/15", "15.12 should be 12/15"),
            ("Meeting am 31.01", "01/31", "31.01 should be 01/31"),
            ("Einfach nur piuztzen", None, "no date keywords should be None")
        ]
        
        for message, expected_date, description in test_cases:
            with self.subTest(message=message):
                mock_msg = self._create_mock_message(message)
                parsed = self.bot.parse_message_for_todo(mock_msg)
                self.assertEqual(parsed['due_date'], expected_date, description)
                print(f"   ✅ '{message}' → Date: {expected_date}")
    
    def test_message_parsing_labels(self):
        """Test message parsing for family member labels"""
        print("\n🧪 Testing label parsing...")
        
        test_cases = [
            ("Marc soll einkaufen", ["Marc"], "marc should create Marc label"),
            ("Papa soll putzen", ["Marc"], "papa should create Marc label"),
            ("Maggie soll kochen", ["Maggie"], "maggie should create Maggie label"),
            ("Mama soll waschen", ["Maggie"], "mama should create Maggie label"),
            ("Gemeinsam: Urlaub planen", ["Familie"], "gemeinsam should create Familie label"),
            ("Together: Project", ["Familie"], "together should create Familie label"),
            ("Alle: Meeting", ["Familie"], "alle should create Familie label"),
            ("Einfach nur piuztzen", ["TestUser"], "no family keywords should use author name")
        ]
        
        for message, expected_labels, description in test_cases:
            with self.subTest(message=message):
                mock_msg = self._create_mock_message(message)
                parsed = self.bot.parse_message_for_todo(mock_msg)
                self.assertEqual(parsed['labels'], expected_labels, description)
                print(f"   ✅ '{message}' → Labels: {expected_labels}")
    
    def test_todo_creation(self):
        """Test todo creation in Todoist"""
        print("\n🧪 Testing todo creation...")
        
        test_todo_data = {
            'content': 'Test Todo from Comprehensive Test',
            'description': 'This is a test todo created by the comprehensive test suite',
            'priority': 2,
            'due_date': 'today',
            'labels': ['Test']
        }
        
        todo = self.todoist.create_task(**test_todo_data)
        self.assertIsNotNone(todo, "Todo creation should succeed")
        self.assertEqual(todo.content, test_todo_data['content'])
        self.assertEqual(todo.priority, test_todo_data['priority'])
        self.assertEqual(todo.labels, test_todo_data['labels'])
        
        self.created_todos.append(todo)
        print(f"   ✅ Created todo: '{todo.content}' (ID: {todo.id})")
    
    def test_piuztzen_functionality(self):
        """Test specific 'piuztzen' functionality"""
        print("\n🧪 Testing 'piuztzen' functionality...")
        
        # Test basic piuztzen
        mock_msg = self._create_mock_message("piuztzen")
        parsed = self.bot.parse_message_for_todo(mock_msg)
        
        self.assertEqual(parsed['content'], "piuztzen")
        self.assertEqual(parsed['priority'], 1)
        self.assertIsNone(parsed['due_date'])
        self.assertEqual(parsed['labels'], ["TestUser"])
        
        # Create todo in Todoist
        todo = self.todoist.create_task(**parsed)
        self.assertIsNotNone(todo)
        self.created_todos.append(todo)
        
        print(f"   ✅ 'piuztzen' → Created: '{todo.content}' (ID: {todo.id})")
        
        # Test piuztzen with modifiers
        test_cases = [
            ("Wichtig: piuztzen heute", 4, "today", ["TestUser"]),
            ("Marc soll piuztzen morgen", 1, "tomorrow", ["Marc"]),
            ("Gemeinsam: piuztzen nächste Woche", 1, "next week", ["Familie"]),
            ("Dringend: piuztzen am Montag", 4, "monday", ["TestUser"])
        ]
        
        for message, expected_priority, expected_date, expected_labels in test_cases:
            with self.subTest(message=message):
                mock_msg = self._create_mock_message(message)
                parsed = self.bot.parse_message_for_todo(mock_msg)
                
                self.assertEqual(parsed['priority'], expected_priority)
                self.assertEqual(parsed['due_date'], expected_date)
                self.assertEqual(parsed['labels'], expected_labels)
                
                # Create todo
                todo = self.todoist.create_task(**parsed)
                self.assertIsNotNone(todo)
                self.created_todos.append(todo)
                
                print(f"   ✅ '{message}' → Created successfully")
    
    def test_todo_completion(self):
        """Test todo completion functionality"""
        print("\n🧪 Testing todo completion...")
        
        # Create a test todo
        test_todo_data = {
            'content': 'Test Todo for Completion',
            'description': 'This todo will be completed',
            'priority': 1,
            'labels': ['Test']
        }
        
        todo = self.todoist.create_task(**test_todo_data)
        self.assertIsNotNone(todo)
        
        # Complete the todo
        success = self.todoist.complete_task(todo.id)
        self.assertTrue(success, "Todo completion should succeed")
        
        print(f"   ✅ Completed todo: '{todo.content}' (ID: {todo.id})")
    
    def test_todo_deletion(self):
        """Test todo deletion functionality"""
        print("\n🧪 Testing todo deletion...")
        
        # Create a test todo
        test_todo_data = {
            'content': 'Test Todo for Deletion',
            'description': 'This todo will be deleted',
            'priority': 1,
            'labels': ['Test']
        }
        
        todo = self.todoist.create_task(**test_todo_data)
        self.assertIsNotNone(todo)
        
        # Delete the todo
        success = self.todoist.delete_task(todo.id)
        self.assertTrue(success, "Todo deletion should succeed")
        
        print(f"   ✅ Deleted todo: '{todo.content}' (ID: {todo.id})")
    
    def test_complex_message_parsing(self):
        """Test complex message parsing with multiple features"""
        print("\n🧪 Testing complex message parsing...")
        
        test_cases = [
            {
                'message': 'Wichtig: Marc soll einkaufen morgen',
                'expected': {
                    'content': 'Wichtig: Marc soll einkaufen morgen',
                    'priority': 4,
                    'due_date': 'tomorrow',
                    'labels': ['Marc']
                }
            },
            {
                'message': 'Dringend: Gemeinsam Urlaub planen nächste Woche',
                'expected': {
                    'content': 'Dringend: Gemeinsam Urlaub planen nächste Woche',
                    'priority': 4,
                    'due_date': 'next week',
                    'labels': ['Familie']
                }
            },
            {
                'message': 'Maggie soll Arzttermin am Montag vereinbaren',
                'expected': {
                    'content': 'Maggie soll Arzttermin am Montag vereinbaren',
                    'priority': 1,
                    'due_date': 'monday',
                    'labels': ['Maggie']
                }
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(message=test_case['message']):
                mock_msg = self._create_mock_message(test_case['message'])
                parsed = self.bot.parse_message_for_todo(mock_msg)
                
                expected = test_case['expected']
                self.assertEqual(parsed['content'], expected['content'])
                self.assertEqual(parsed['priority'], expected['priority'])
                self.assertEqual(parsed['due_date'], expected['due_date'])
                self.assertEqual(parsed['labels'], expected['labels'])
                
                print(f"   ✅ Complex parsing: '{test_case['message']}'")
    
    def _create_mock_message(self, content, author_name="TestUser"):
        """Create a mock Discord message for testing"""
        mock_msg = Mock()
        mock_msg.content = content
        mock_msg.author = Mock()
        mock_msg.author.display_name = author_name
        return mock_msg

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive Todo Bot Test Suite\n")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTodoBot)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print(f"\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if result.wasSuccessful():
        print(f"\n✅ All tests passed! The todo bot is working correctly.")
        print(f"🎉 'piuztzen' and all other functionality is working as expected!")
    else:
        print(f"\n❌ Some tests failed. Please check the issues above.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_comprehensive_tests()
