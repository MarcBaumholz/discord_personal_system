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
            
            # Test RSS manager
            rss_manager = RSSFeedManager(max_concurrent_feeds=3)
            
            # Test with first 3 feeds to avoid overwhelming servers
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
    
    async def test_llm_processor(self) -> bool:
        """Test LLM processing functionality."""
        try:
            logger.info("Testing LLM processor...")
            
            # Check if API key is available
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key or api_key == 'your_openrouter_api_key_here':
                self.log_test_result("LLM Processor", False, "OpenRouter API key not configured")
                return False
            
            # Initialize LLM processor
            llm = LLMProcessor(
                api_key=api_key,
                primary_model="meta-llama/llama-3.1-8b-instruct:free",
                fallback_model="meta-llama/llama-3.1-8b-instruct:free"
            )
            
            # Test relevance scoring
            test_article = {
                'title': 'New AI Model Achieves Breakthrough in Language Understanding',
                'content_summary': 'Researchers have developed a new AI model that shows significant improvements in natural language understanding tasks.',
                'category': 'AI_LLM'
            }
            
            relevance_score = await llm.calculate_relevance_score(test_article)
            
            if relevance_score is None:
                self.log_test_result("LLM Processor", False, "Failed to calculate relevance score")
                return False
            
            # Test summary generation
            test_articles = [test_article]
            summary = await llm.generate_summary(test_articles, summary_type="test")
            
            if not summary:
                self.log_test_result("LLM Processor", False, "Failed to generate summary")
                return False
            
            self.log_test_result("LLM Processor", True, 
                               f"Relevance: {relevance_score:.2f}, Summary: {len(summary)} chars")
            return True
            
        except Exception as e:
            self.log_test_result("LLM Processor", False, str(e))
            return False
    
    async def test_discord_connection(self) -> bool:
        """Test Discord bot connection (without posting)."""
        try:
            logger.info("Testing Discord connection...")
            
            # Check if Discord token is available
            token = os.getenv('DISCORD_TOKEN')
            channel_id = os.getenv('DISCORD_CHANNEL_ID')
            
            if not token or token == 'your_discord_bot_token_here':
                self.log_test_result("Discord Connection", False, "Discord token not configured")
                return False
            
            if not channel_id or channel_id == '0':
                self.log_test_result("Discord Connection", False, "Discord channel ID not configured")
                return False
            
            # Initialize Discord publisher
            discord_pub = DiscordPublisher(
                bot_token=token,
                target_channel_id=int(channel_id)
            )
            
            # Start bot and wait for connection
            bot_task = asyncio.create_task(discord_pub.start_bot())
            await asyncio.sleep(5)  # Give it time to connect
            
            if discord_pub.is_ready:
                self.log_test_result("Discord Connection", True, 
                                   f"Connected to channel: {discord_pub.target_channel.name}")
                await discord_pub.stop_bot()
                return True
            else:
                self.log_test_result("Discord Connection", False, "Failed to connect or find channel")
                await discord_pub.stop_bot()
                return False
            
        except Exception as e:
            self.log_test_result("Discord Connection", False, str(e))
            return False
    
    async def test_full_workflow(self) -> bool:
        """Test the complete RSS bot workflow."""
        try:
            logger.info("Testing full workflow...")
            
            # Check environment
            required_env = ['DISCORD_TOKEN', 'OPENROUTER_API_KEY', 'DISCORD_CHANNEL_ID']
            missing_env = [var for var in required_env if not os.getenv(var) or os.getenv(var).startswith('your_')]
            
            if missing_env:
                self.log_test_result("Full Workflow", False, f"Missing environment variables: {missing_env}")
                return False
            
            # Initialize bot
            bot = RSSNewsBot()
            await bot.initialize_components()
            
            # Test manual news generation (like !news command)
            new_articles = await bot.fetch_and_process_articles()
            analyzed_articles = await bot.analyze_article_relevance()
            
            if new_articles > 0 and analyzed_articles > 0:
                summary = await bot.generate_daily_summary()
                
                if summary:
                    self.log_test_result("Full Workflow", True, 
                                       f"Processed {new_articles} articles, analyzed {analyzed_articles}, generated summary")
                    return True
                else:
                    self.log_test_result("Full Workflow", False, "Failed to generate summary")
                    return False
            else:
                self.log_test_result("Full Workflow", False, f"No articles processed: new={new_articles}, analyzed={analyzed_articles}")
                return False
            
        except Exception as e:
            self.log_test_result("Full Workflow", False, str(e))
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
        else:
            logger.info("⚠️  Some tests failed. Check configuration and dependencies.")
        
        return passed == total


async def main():
    """Run all tests."""
    tester = RSSBotTester()
    
    logger.info("Starting RSS Bot component testing...")
    
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Run tests in order
    await tester.test_database_operations()
    await tester.test_rss_feeds()
    await tester.test_llm_processor()
    await tester.test_discord_connection()
    await tester.test_full_workflow()
    
    # Print summary
    all_passed = tester.print_test_summary()
    
    if all_passed:
        logger.info("\n🚀 Ready to run the bot with: python src/main.py")
    else:
        logger.info("\n🔧 Fix the issues above before running the bot.")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main()) 