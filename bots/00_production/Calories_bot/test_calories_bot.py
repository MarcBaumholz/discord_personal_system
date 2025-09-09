#!/usr/bin/env python3
"""
Comprehensive test suite for Calories Bot
Tests all major functionality including logging, food analysis, and error handling
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from logger_config import CaloriesBotLogger
from calories_bot import GroundTruthHandler, AITextHandler, FoodAnalysisResult

class TestCaloriesBotLogger(unittest.TestCase):
    """Test the logging system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_log_dir = tempfile.mkdtemp()
        self.logger = CaloriesBotLogger(log_dir=self.test_log_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_log_dir)
    
    def test_logger_initialization(self):
        """Test logger initializes correctly"""
        self.assertIsNotNone(self.logger.main_logger)
        self.assertIsNotNone(self.logger.food_logger)
        self.assertIsNotNone(self.logger.error_logger)
        self.assertIsNotNone(self.logger.activity_logger)
        self.assertIsNotNone(self.logger.reports_logger)
    
    def test_log_error(self):
        """Test error logging functionality"""
        error_type = "Test Error"
        error_message = "This is a test error"
        context = {"test": "data"}
        
        # This should not raise an exception
        self.logger.log_error(error_type, error_message, context)
        
        # Check if error log file was created
        error_files = os.listdir(os.path.join(self.test_log_dir, "errors"))
        self.assertTrue(any("errors_" in f for f in error_files))
    
    def test_log_warning(self):
        """Test warning logging functionality"""
        warning_type = "Test Warning"
        warning_message = "This is a test warning"
        context = {"test": "data"}
        
        # This should not raise an exception
        self.logger.log_warning(warning_type, warning_message, context)
        
        # Check if error log file was created (warnings go to error log)
        error_files = os.listdir(os.path.join(self.test_log_dir, "errors"))
        self.assertTrue(any("errors_" in f for f in error_files))
    
    def test_log_food_analysis(self):
        """Test food analysis logging"""
        analysis_data = {
            'user': 'TestUser',
            'food_name': 'Test Food',
            'calories': 300,
            'confidence': 85.0,
            'protein': 20.0,
            'carbohydrates': 30.0,
            'fat': 10.0
        }
        
        # This should not raise an exception
        self.logger.log_food_analysis(analysis_data)
        
        # Check if food analysis log file was created
        food_files = os.listdir(os.path.join(self.test_log_dir, "food_analysis"))
        self.assertTrue(any("analysis_" in f for f in food_files))
    
    def test_log_user_command(self):
        """Test user command logging"""
        user = "TestUser"
        command = "test_command"
        channel = "test_channel"
        
        # This should not raise an exception
        self.logger.log_user_command(user, command, channel)
        
        # Check if user activity log file was created
        activity_files = os.listdir(os.path.join(self.test_log_dir, "user_activity"))
        self.assertTrue(any("commands_" in f for f in activity_files))

class TestGroundTruthHandler(unittest.TestCase):
    """Test the ground truth food database handler"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_data = {
            "apple": {
                "calories": 95,
                "protein": 0.5,
                "carbohydrates": 25.0,
                "fat": 0.3,
                "fiber": 4.0,
                "sugar": 19.0,
                "vitamins": {"C": 14.0},
                "minerals": {"potassium": 195.0}
            },
            "banana": {
                "calories": 105,
                "protein": 1.3,
                "carbohydrates": 27.0,
                "fat": 0.4,
                "fiber": 3.1,
                "sugar": 14.0,
                "vitamins": {"B6": 0.4, "C": 17.0},
                "minerals": {"potassium": 422.0}
            }
        }
        
        # Create temporary ground truth file
        self.test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_data, self.test_file)
        self.test_file.close()
        
        # Mock the file path
        with patch.object(GroundTruthHandler, '__init__', self._mock_init):
            self.handler = GroundTruthHandler()
    
    def _mock_init(self, instance):
        """Mock initialization"""
        instance.ground_truth_file = self.test_file.name
        instance.foods_db = self.test_data
    
    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.test_file.name)
    
    def test_search_ground_truth_exact_match(self):
        """Test exact match in ground truth database"""
        result = self.handler.search_ground_truth("apple")
        self.assertIsNotNone(result)
        self.assertEqual(result.food_name, "apple")
        self.assertEqual(result.calories, 95)
        self.assertEqual(result.analysis_source, "ground_truth")
    
    def test_search_ground_truth_partial_match(self):
        """Test partial match in ground truth database"""
        result = self.handler.search_ground_truth("banana bread")
        self.assertIsNotNone(result)
        self.assertEqual(result.food_name, "banana")
        self.assertEqual(result.calories, 105)
    
    def test_search_ground_truth_no_match(self):
        """Test no match in ground truth database"""
        result = self.handler.search_ground_truth("pizza")
        self.assertIsNone(result)
    
    def test_search_ground_truth_case_insensitive(self):
        """Test case insensitive search"""
        result = self.handler.search_ground_truth("APPLE")
        self.assertIsNotNone(result)
        self.assertEqual(result.food_name, "apple")

class TestAITextHandler(unittest.TestCase):
    """Test the AI text analysis handler"""
    
    def setUp(self):
        """Set up test environment"""
        self.handler = AITextHandler()
    
    @patch('calories_bot.openai_client')
    def test_analyze_food_text_success(self, mock_client):
        """Test successful AI text analysis"""
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "food_name": "Grilled Chicken Breast",
            "calories": 250,
            "confidence": 85.0,
            "description": "A healthy grilled chicken breast",
            "protein": 45.0,
            "carbohydrates": 0.0,
            "fat": 8.0,
            "fiber": 0.0,
            "sugar": 0.0,
            "saturated_fat": 2.0,
            "cholesterol": 120.0,
            "vitamins": {"B6": 0.8, "B12": 0.3},
            "minerals": {"iron": 1.2, "zinc": 1.8}
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        result = self.handler.analyze_food_text("grilled chicken breast")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.food_name, "Grilled Chicken Breast")
        self.assertEqual(result.calories, 250)
        self.assertEqual(result.confidence, 85.0)
        self.assertEqual(result.analysis_source, "ai")
    
    @patch('calories_bot.openai_client')
    def test_analyze_food_text_invalid_json(self, mock_client):
        """Test AI analysis with invalid JSON response"""
        # Mock the OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = self.handler.analyze_food_text("test food")
        
        self.assertIsNone(result)
    
    @patch('calories_bot.openai_client')
    def test_analyze_food_text_api_error(self, mock_client):
        """Test AI analysis with API error"""
        # Mock API error
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = self.handler.analyze_food_text("test food")
        
        self.assertIsNone(result)

class TestFoodAnalysisResult(unittest.TestCase):
    """Test the FoodAnalysisResult class"""
    
    def test_food_analysis_result_creation(self):
        """Test creating a FoodAnalysisResult object"""
        result = FoodAnalysisResult(
            food_name="Test Food",
            calories=300,
            confidence=85.0,
            description="A test food item",
            protein=20.0,
            carbohydrates=30.0,
            fat=10.0,
            fiber=5.0,
            sugar=15.0,
            saturated_fat=3.0,
            cholesterol=50.0,
            vitamins={"C": 100.0},
            minerals={"iron": 2.0},
            analysis_source="test"
        )
        
        self.assertEqual(result.food_name, "Test Food")
        self.assertEqual(result.calories, 300)
        self.assertEqual(result.confidence, 85.0)
        self.assertEqual(result.protein, 20.0)
        self.assertEqual(result.carbohydrates, 30.0)
        self.assertEqual(result.fat, 10.0)
        self.assertEqual(result.fiber, 5.0)
        self.assertEqual(result.sugar, 15.0)
        self.assertEqual(result.saturated_fat, 3.0)
        self.assertEqual(result.cholesterol, 50.0)
        self.assertEqual(result.vitamins, {"C": 100.0})
        self.assertEqual(result.minerals, {"iron": 2.0})
        self.assertEqual(result.analysis_source, "test")
        self.assertIsNotNone(result.timestamp)
    
    def test_get_meal_hash(self):
        """Test meal hash generation"""
        result1 = FoodAnalysisResult("Apple", 95, 80.0)
        result2 = FoodAnalysisResult("apple", 95, 80.0)
        result3 = FoodAnalysisResult("Banana", 105, 80.0)
        
        # Same food (case insensitive) should have same hash
        self.assertEqual(result1.get_meal_hash(), result2.get_meal_hash())
        
        # Different foods should have different hashes
        self.assertNotEqual(result1.get_meal_hash(), result3.get_meal_hash())
        
        # Hash should be consistent
        self.assertEqual(result1.get_meal_hash(), result1.get_meal_hash())

class TestCaloriesBotIntegration(unittest.TestCase):
    """Integration tests for the Calories Bot"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_log_dir = tempfile.mkdtemp()
        self.logger = CaloriesBotLogger(log_dir=self.test_log_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_log_dir)
    
    def test_logger_error_handling(self):
        """Test that logger methods don't raise AttributeError"""
        # These should not raise AttributeError
        try:
            self.logger.log_error("Test Error", "Test message")
            self.logger.log_warning("Test Warning", "Test message")
            self.logger.log_food_analysis({
                'user': 'TestUser',
                'food_name': 'Test Food',
                'calories': 300,
                'confidence': 85.0
            })
            self.logger.log_user_command("TestUser", "test_command", "test_channel")
        except AttributeError as e:
            self.fail(f"Logger raised AttributeError: {e}")
    
    def test_ground_truth_integration(self):
        """Test ground truth handler integration"""
        test_data = {
            "test_food": {
                "calories": 200,
                "protein": 10.0,
                "carbohydrates": 20.0,
                "fat": 5.0,
                "fiber": 3.0,
                "sugar": 8.0,
                "vitamins": {"A": 50.0},
                "minerals": {"calcium": 100.0}
            }
        }
        
        # Create temporary ground truth file
        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(test_data, test_file)
        test_file.close()
        
        try:
            with patch.object(GroundTruthHandler, '__init__', lambda self: setattr(self, 'ground_truth_file', test_file.name) or setattr(self, 'foods_db', test_data)):
                handler = GroundTruthHandler()
                result = handler.search_ground_truth("test_food")
                
                self.assertIsNotNone(result)
                self.assertEqual(result.food_name, "test_food")
                self.assertEqual(result.calories, 200)
        finally:
            os.unlink(test_file.name)

def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestCaloriesBotLogger))
    test_suite.addTest(unittest.makeSuite(TestGroundTruthHandler))
    test_suite.addTest(unittest.makeSuite(TestAITextHandler))
    test_suite.addTest(unittest.makeSuite(TestFoodAnalysisResult))
    test_suite.addTest(unittest.makeSuite(TestCaloriesBotIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🧪 Running Calories Bot Test Suite...")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
