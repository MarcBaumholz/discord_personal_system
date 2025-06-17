import unittest
import os
import json
from pathlib import Path
from learning_bot import LearningBot

class TestLearningBot(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.bot = LearningBot()
        self.test_doc = {
            'title': 'Test Document',
            'content': 'This is a test document content.',
            'filename': 'test.txt',
            'upload_date': '2024-03-20T10:00:00'
        }

    def test_document_management(self):
        """Test document management functionality"""
        # Test saving document
        self.bot.documents['1'] = self.test_doc
        self.bot.save_documents()
        
        # Verify file exists
        metadata_file = Path('data/metadata/documents.json')
        self.assertTrue(metadata_file.exists())
        
        # Test loading document
        self.bot.documents = {}
        self.bot.load_documents()
        self.assertEqual(self.bot.documents['1']['title'], 'Test Document')

    def test_daily_learning_generation(self):
        """Test daily learning generation"""
        # Add test document
        self.bot.documents['1'] = self.test_doc
        
        # Test learning generation
        learning = self.bot.generate_daily_learning()
        self.assertIsNotNone(learning)
        self.assertIsInstance(learning, str)

    def tearDown(self):
        """Clean up test environment"""
        # Remove test files
        metadata_file = Path('data/metadata/documents.json')
        if metadata_file.exists():
            metadata_file.unlink()

if __name__ == '__main__':
    unittest.main() 