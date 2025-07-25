#!/usr/bin/env python3
"""
LinkedIn Bot Test Suite
Tests the functionality of the LinkedIn Network Analyzer Bot
"""

import unittest
import asyncio
import os
import sys
import tempfile
import csv
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directory to sys.path to import the bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from linkedin_bot import LinkedInContact, LinkedInAnalyzer, NotionLinkedInHandler

class TestLinkedInContact(unittest.TestCase):
    """Test the LinkedInContact class"""
    
    def test_contact_creation(self):
        """Test creating a LinkedIn contact"""
        contact = LinkedInContact(
            name="John Doe",
            position="Software Engineer", 
            company="Tech Corp",
            email="john@example.com"
        )
        
        self.assertEqual(contact.name, "John Doe")
        self.assertEqual(contact.position, "Software Engineer")
        self.assertEqual(contact.company, "Tech Corp")
        self.assertEqual(contact.email, "john@example.com")
        self.assertEqual(contact.follower_count, 0)
        self.assertEqual(contact.topic_category, "Other")
        self.assertEqual(contact.importance_score, 0)
    
    def test_contact_to_dict(self):
        """Test converting contact to dictionary"""
        contact = LinkedInContact(
            name="Jane Smith",
            position="Data Scientist",
            company="AI Startup"
        )
        contact.follower_count = 2500
        contact.topic_category = "Data Science & Analytics"
        contact.importance_score = 9
        
        contact_dict = contact.to_dict()
        
        self.assertEqual(contact_dict["name"], "Jane Smith")
        self.assertEqual(contact_dict["follower_count"], 2500)
        self.assertEqual(contact_dict["topic_category"], "Data Science & Analytics")
        self.assertEqual(contact_dict["importance_score"], 9)

class TestLinkedInAnalyzer(unittest.TestCase):
    """Test the LinkedInAnalyzer class"""
    
    def setUp(self):
        """Create a temporary CSV file for testing"""
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        
        # Write test data
        writer = csv.writer(self.temp_csv)
        writer.writerow(['First Name', 'Last Name', 'Email Address', 'Company', 'Position'])
        writer.writerow(['John', 'Doe', 'john@example.com', 'Tech Corp', 'Software Engineer'])
        writer.writerow(['Jane', 'Smith', 'jane@ai.com', 'AI Startup', 'Data Scientist'])
        writer.writerow(['Bob', 'Johnson', 'bob@consulting.com', 'Consulting LLC', 'Senior Consultant'])
        
        self.temp_csv.close()
    
    def tearDown(self):
        """Clean up temporary file"""
        os.unlink(self.temp_csv.name)
    
    def test_parse_linkedin_csv(self):
        """Test parsing LinkedIn CSV file"""
        contacts = LinkedInAnalyzer.parse_linkedin_csv(self.temp_csv.name)
        
        self.assertEqual(len(contacts), 3)
        
        # Check first contact
        self.assertEqual(contacts[0].name, "John Doe")
        self.assertEqual(contacts[0].position, "Software Engineer")
        self.assertEqual(contacts[0].company, "Tech Corp")
        self.assertEqual(contacts[0].email, "john@example.com")
        
        # Check second contact
        self.assertEqual(contacts[1].name, "Jane Smith")
        self.assertEqual(contacts[1].position, "Data Scientist")
        self.assertEqual(contacts[1].company, "AI Startup")
    
    def test_parse_nonexistent_csv(self):
        """Test parsing non-existent CSV file"""
        contacts = LinkedInAnalyzer.parse_linkedin_csv("nonexistent.csv")
        self.assertEqual(len(contacts), 0)
    
    def test_rank_contacts_by_category(self):
        """Test ranking contacts by category"""
        contacts = [
            LinkedInContact("Alice", "Engineer", "Tech1"),
            LinkedInContact("Bob", "Engineer", "Tech2"),
            LinkedInContact("Charlie", "Manager", "Corp1")
        ]
        
        # Set categories and scores
        contacts[0].topic_category = "Software Development & Engineering"
        contacts[0].importance_score = 8
        contacts[0].follower_count = 1000
        
        contacts[1].topic_category = "Software Development & Engineering"
        contacts[1].importance_score = 9
        contacts[1].follower_count = 500
        
        contacts[2].topic_category = "Product Management"
        contacts[2].importance_score = 7
        contacts[2].follower_count = 2000
        
        categorized = LinkedInAnalyzer.rank_contacts_by_category(contacts)
        
        # Check categories exist
        self.assertIn("Software Development & Engineering", categorized)
        self.assertIn("Product Management", categorized)
        
        # Check ranking (Bob should be first due to higher importance score)
        eng_contacts = categorized["Software Development & Engineering"]
        self.assertEqual(len(eng_contacts), 2)
        self.assertEqual(eng_contacts[0].name, "Bob")
        self.assertEqual(eng_contacts[1].name, "Alice")

class TestAIAnalysis(unittest.TestCase):
    """Test AI analysis functionality with mocking"""
    
    @patch('linkedin_bot.openai_client')
    async def test_analyze_contact_with_ai(self, mock_openai):
        """Test AI analysis of a contact"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "estimated_followers": 2500,
            "topic_category": "Software Development & Engineering",
            "importance_score": 8,
            "notes": "Senior engineer with strong open source contributions"
        }
        '''
        
        mock_openai.chat.completions.acreate = AsyncMock(return_value=mock_response)
        
        # Test contact
        contact = LinkedInContact(
            name="Test User",
            position="Senior Software Engineer",
            company="Tech Company"
        )
        
        # Analyze
        analyzed_contact = await LinkedInAnalyzer.analyze_contact_with_ai(contact)
        
        # Verify results
        self.assertEqual(analyzed_contact.follower_count, 2500)
        self.assertEqual(analyzed_contact.topic_category, "Software Development & Engineering")
        self.assertEqual(analyzed_contact.importance_score, 8)
        self.assertIn("open source", analyzed_contact.notes)

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_end_to_end_workflow(self):
        """Test the complete workflow without external APIs"""
        # Create test data
        contacts = [
            LinkedInContact("Alice AI", "ML Engineer", "AI Corp"),
            LinkedInContact("Bob Dev", "Software Engineer", "Tech Inc"),
            LinkedInContact("Charlie PM", "Product Manager", "Startup LLC")
        ]
        
        # Manually set analysis results (simulating AI analysis)
        contacts[0].topic_category = "Artificial Intelligence & Machine Learning"
        contacts[0].importance_score = 9
        contacts[0].follower_count = 3000
        
        contacts[1].topic_category = "Software Development & Engineering"
        contacts[1].importance_score = 7
        contacts[1].follower_count = 1500
        
        contacts[2].topic_category = "Product Management"
        contacts[2].importance_score = 8
        contacts[2].follower_count = 2000
        
        # Rank contacts
        categorized = LinkedInAnalyzer.rank_contacts_by_category(contacts)
        
        # Verify categorization
        self.assertEqual(len(categorized), 3)
        self.assertEqual(len(categorized["Artificial Intelligence & Machine Learning"]), 1)
        self.assertEqual(len(categorized["Software Development & Engineering"]), 1)
        self.assertEqual(len(categorized["Product Management"]), 1)
        
        # Verify ranking (highest scores first)
        ai_contacts = categorized["Artificial Intelligence & Machine Learning"]
        self.assertEqual(ai_contacts[0].name, "Alice AI")
        self.assertEqual(ai_contacts[0].importance_score, 9)

def run_async_test(coro):
    """Helper to run async tests"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

if __name__ == '__main__':
    print("🧪 Running LinkedIn Bot Tests")
    print("=" * 40)
    
    # Run tests
    unittest.main(verbosity=2)
