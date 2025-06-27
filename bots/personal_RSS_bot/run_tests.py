#!/usr/bin/env python3
"""
Test script for Personal RSS News Bot.
Tests individual components and full workflow.
"""

import asyncio
import os
import sys
from pathlib import Path
import logging
from datetime import datetime, timezone

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from database import DatabaseManager
from rss_manager import RSSFeedManager, load_rss_feeds_from_config
from llm_processor import LLMProcessor
from discord_publisher import DiscordPublisher
from main import RSSNewsBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RSSBotTester:
    """Test harness for RSS Bot components."""
    
    def __init__(self):
        self.results = {}
        
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        self.results[test_name] = {"success": success, "message": message}
    
    async def test_database_operations(self) -> bool:
        """Test database initialization and basic operations."""
        try:
            logger.info("Testing database operations...")
            
            # Initialize database
            db_path = "data/test_rss_bot.db"
            db = DatabaseManager(db_path)
            
            # Test feed source addition
            feed_id = db.add_feed_source("Test Feed", "https://example.com/rss", "TEST", 1)
            if not feed_id:
                self.log_test_result("Database - Add Feed", False, "Failed to add feed source")
                return False
            
            # Test article addition
            article_id = db.add_article(
                title="Test Article",
                url="https://example.com/article",
                source="Test Feed",
                category="TEST",
                published_date=datetime.now(timezone.utc),
                content_summary="Test summary",
                relevance_score=0.8
            )
            
            if not article_id:
                self.log_test_result("Database - Add Article", False, "Failed to add article")
                return False
            
            # Test data retrieval
            feeds = db.get_active_feeds()
            articles = db.get_recent_articles(days=7, min_relevance=0.5, limit=10)
            
            self.log_test_result("Database Operations", True, 
                               f"Added feed and article, retrieved {len(feeds)} feeds and {len(articles)} articles")
            return True
            
        except Exception as e:
            self.log_test_result("Database Operations", False, str(e))
            return False
    
    async def test_rss_feeds(self) -> bool:
        """Test RSS feed fetching and parsing."""
        try:
            logger.info("Testing RSS feed operations...")
            
            # Load RSS feeds configuration
            feeds_config_path = "config/rss_feeds.json"
            if not Path(feeds_config_path).exists():
                self.log_test_result("RSS Feeds", False, "RSS feeds config file not found")
                return False
            
            feeds = load_rss_feeds_from_config(feeds_config_path)
            if not feeds:
                self.log_test_result("RSS Feeds", False, "No RSS feeds loaded from config")
                return False
            
            # Test RSS manager with first 3 feeds
            rss_manager = RSSFeedManager(max_concurrent_feeds=3)
            test_feeds = feeds[:3]
            
            async with rss_manager:
                results = await rss_manager.fetch_multiple_feeds_async(test_feeds)
            
            successful_feeds = sum(1 for result in results if result['success'])
            total_articles = sum(len(result.get('articles', [])) for result in results if result['success'])
            
            self.log_test_result("RSS Feeds", successful_feeds > 0, 
                               f"Fetched from {successful_feeds}/{len(test_feeds)} feeds, got {total_articles} articles")
            return successful_feeds > 0
            
        except Exception as e:
            self.log_test_result("RSS Feeds", False, str(e))
            return False
    
    async def test_environment_config(self) -> bool:
        """Test environment configuration."""
        try:
            logger.info("Testing environment configuration...")
            
            required_vars = {
                'DISCORD_TOKEN': 'Discord bot token',
                'DISCORD_CHANNEL_ID': 'Discord channel ID',
                'OPENROUTER_API_KEY': 'OpenRouter API key'
            }
            
            missing_vars = []
            for var, description in required_vars.items():
                value = os.getenv(var)
                if not value or value.startswith('your_'):
                    missing_vars.append(f"{var} ({description})")
            
            if missing_vars:
                self.log_test_result("Environment Config", False, 
                                   f"Missing or placeholder values: {', '.join(missing_vars)}")
                return False
            else:
                self.log_test_result("Environment Config", True, "All required environment variables configured")
                return True
                
        except Exception as e:
            self.log_test_result("Environment Config", False, str(e))
            return False
    
    def print_test_summary(self):
        """Print summary of all test results."""
        logger.info("\n" + "="*60)
        logger.info("RSS BOT TESTING SUMMARY")
        logger.info("="*60)
        
        passed = sum(1 for result in self.results.values() if result['success'])
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            message = f" - {result['message']}" if result['message'] else ""
            logger.info(f"{status} {test_name}{message}")
        
        logger.info("="*60)
        logger.info(f"OVERALL: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Bot is ready for deployment.")
            logger.info("Run: python src/main.py")
        else:
            logger.info("⚠️  Some tests failed. Please fix the issues above.")
            logger.info("1. Copy config.example to .env")
            logger.info("2. Fill in your Discord token and OpenRouter API key")
            logger.info("3. Run tests again")
        
        return passed == total


async def main():
    """Run all tests."""
    tester = RSSBotTester()
    
    logger.info("Starting RSS Bot component testing...")
    logger.info("This will test database, RSS feeds, and configuration...")
    
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Run basic tests
    await tester.test_environment_config()
    await tester.test_database_operations()
    await tester.test_rss_feeds()
    
    # Print summary
    all_passed = tester.print_test_summary()
    
    return all_passed


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv not installed. Make sure environment variables are set.")
    
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 