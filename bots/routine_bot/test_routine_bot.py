import os
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('routine_bot_test')

# Load environment variables
load_dotenv()

# Import modules to test
from notion_manager import NotionManager
from openrouter_service import OpenRouterService

def test_notion_manager():
    """Test the Notion integration"""
    logger.info("Testing NotionManager...")
    
    notion_manager = NotionManager()
    
    # Check if database was found
    if not notion_manager.database_id:
        logger.error("No database ID found. Tests cannot continue.")
        return False
    
    logger.info(f"Using database ID: {notion_manager.database_id}")
    
    # Get today's routines
    today = datetime.now(pytz.timezone('Europe/Berlin')).date()
    routines = notion_manager.get_routines_for_day(today)
    
    logger.info(f"Found {len(routines)} routines for today:")
    for routine in routines:
        logger.info(f"  - {routine.get('name')} ({routine.get('time_of_day')}, {routine.get('duration')} min)")
    
    # Get routines by time of day
    for time_of_day in ['Morning', 'Afternoon', 'Evening']:
        time_routines = notion_manager.get_routines_by_time(time_of_day)
        logger.info(f"Found {len(time_routines)} routines for {time_of_day}")
    
    logger.info("NotionManager test complete")
    return True

def test_openrouter_service():
    """Test the OpenRouter integration"""
    logger.info("Testing OpenRouterService...")
    
    openrouter_service = OpenRouterService()
    
    # Create some sample routines
    sample_routines = [
        {
            'name': 'Morning Exercise',
            'time_of_day': 'Morning',
            'duration': 30,
            'status': 'Not Started'
        },
        {
            'name': 'Meditation',
            'time_of_day': 'Morning',
            'duration': 15,
            'status': 'Not Started'
        },
        {
            'name': 'Work Planning',
            'time_of_day': 'Morning',
            'duration': 20,
            'status': 'Not Started'
        }
    ]
    
    # Test formatting a routine message
    message = openrouter_service.format_routine_message(sample_routines, 'Morning')
    
    logger.info("OpenRouter generated the following message:")
    logger.info(message)
    
    logger.info("OpenRouterService test complete")
    return True

def run_tests():
    """Run all tests"""
    logger.info("Starting routine bot tests")
    
    # Test Notion integration
    notion_result = test_notion_manager()
    
    # Only test OpenRouter if Notion test passed
    if notion_result:
        openrouter_result = test_openrouter_service()
    else:
        logger.warning("Skipping OpenRouter tests due to Notion test failure")
        openrouter_result = False
    
    # Summarize results
    if notion_result and openrouter_result:
        logger.info("All tests completed successfully")
    else:
        logger.warning("Some tests failed")

if __name__ == "__main__":
    run_tests() 