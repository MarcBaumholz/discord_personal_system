"""
Main application for Personal RSS News Bot.
Orchestrates all components and manages the weekly processing workflow.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import signal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from rss_manager import RSSFeedManager, load_rss_feeds_from_config
from llm_processor import LLMProcessor, load_llm_config
from discord_publisher import DiscordPublisher, load_discord_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rss_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RSSNewsBot:
    """Main RSS News Bot application."""
    
    def __init__(self, config_path: str = "config.example"):
        """Initialize the RSS News Bot with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.db_manager = None
        self.rss_manager = None
        self.llm_processor = None
        self.discord_publisher = None
        self.scheduler = None
        
        # State management
        self.is_running = False
        self.last_processing_time = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict:
        """Load configuration from environment variables and config file."""
        config = {
            # Database configuration
            'db_path': os.getenv('DATABASE_PATH', 'data/rss_bot.db'),
            
            # Discord configuration
            'discord_token': os.getenv('DISCORD_TOKEN'),
            'discord_channel_id': int(os.getenv('DISCORD_CHANNEL_ID', '0')),
            'discord_command_prefix': os.getenv('DISCORD_COMMAND_PREFIX', '!'),
            
            # OpenRouter/LLM configuration
            'openrouter_api_key': os.getenv('OPENROUTER_API_KEY'),
            'llm_primary_model': os.getenv('PRIMARY_MODEL', 'meta-llama/llama-3.1-8b-instruct:free'),
            'llm_fallback_model': os.getenv('FALLBACK_MODEL', 'meta-llama/llama-3.1-8b-instruct:free'),
            'llm_max_tokens': int(os.getenv('MAX_TOKENS', '1000')),
            'llm_temperature': float(os.getenv('TEMPERATURE', '0.3')),
            
            # RSS processing configuration
            'rss_feeds_config': os.getenv('RSS_FEEDS_CONFIG', 'config/rss_feeds.json'),
            'max_concurrent_feeds': int(os.getenv('MAX_CONCURRENT_FEEDS', '5')),
            'min_relevance_score': float(os.getenv('MIN_RELEVANCE_SCORE', '0.7')),
            'max_articles_per_week': int(os.getenv('MAX_ARTICLES_PER_WEEK', '25')),
            
            # Scheduling configuration  
            'schedule_day': int(os.getenv('SCHEDULE_DAY', '6')),  # 6 = Sunday (0=Monday)
            'schedule_hour': int(os.getenv('SCHEDULE_HOUR', '9')),
            'schedule_minute': int(os.getenv('SCHEDULE_MINUTE', '0')),
            
            # Processing configuration
            'days_to_process': int(os.getenv('DAYS_TO_FETCH', '7')),
            'cleanup_days': int(os.getenv('CLEANUP_DAYS', '30')),
        }
        
        return config
    
    async def initialize_components(self):
        """Initialize all bot components."""
        try:
            logger.info("Initializing RSS News Bot components...")
            
            # Initialize database
            self.db_manager = DatabaseManager(self.config['db_path'])
            logger.info("Database manager initialized")
            
            # Initialize RSS manager
            self.rss_manager = RSSFeedManager(
                max_concurrent_feeds=self.config['max_concurrent_feeds']
            )
            logger.info("RSS manager initialized")
            
            # Initialize LLM processor
            self.llm_processor = LLMProcessor(
                api_key=self.config['openrouter_api_key'],
                primary_model=self.config['llm_primary_model'],
                fallback_model=self.config['llm_fallback_model'],
                max_tokens=self.config['llm_max_tokens'],
                temperature=self.config['llm_temperature']
            )
            logger.info("LLM processor initialized")
            
            # Initialize Discord publisher
            if self.config['discord_token'] and self.config['discord_channel_id']:
                self.discord_publisher = DiscordPublisher(
                    bot_token=self.config['discord_token'],
                    target_channel_id=self.config['discord_channel_id'],
                    command_prefix=self.config['discord_command_prefix']
                )
                # Link the bot instance to the Discord publisher for command access
                self.discord_publisher._rss_bot_instance = self
                logger.info("Discord publisher initialized")
            else:
                logger.warning("Discord configuration missing. Bot will run without Discord integration.")
            
            # Initialize scheduler
            self.scheduler = AsyncIOScheduler()
            logger.info("Scheduler initialized")
            
            # Load feed sources from config
            if Path(self.config['rss_feeds_config']).exists():
                feeds = load_rss_feeds_from_config(self.config['rss_feeds_config'])
                for feed in feeds:
                    self.db_manager.add_feed_source(
                        feed['name'], feed['url'], feed['category'], feed.get('priority', 2)
                    )
                logger.info(f"Loaded {len(feeds)} RSS feeds from configuration")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    async def fetch_and_process_articles(self) -> int:
        """Fetch new articles from RSS feeds and process them."""
        try:
            logger.info("Starting RSS feed processing...")
            
            # Get active feeds from database
            feeds = self.db_manager.get_active_feeds()
            if not feeds:
                logger.warning("No active RSS feeds found")
                return 0
            
            logger.info(f"Processing {len(feeds)} RSS feeds")
            
            # Fetch articles from all feeds
            async with self.rss_manager:
                feed_results = await self.rss_manager.fetch_multiple_feeds_async(feeds)
            
            total_articles = 0
            new_articles = 0
            
            # Process each feed result
            for result in feed_results:
                feed_info = result['feed_info']
                feed_id = feed_info.get('id')
                
                if result['success']:
                    articles = result['articles']
                    total_articles += len(articles)
                    
                    # Add articles to database
                    for article in articles:
                        if self.db_manager.add_article(
                            title=article['title'],
                            url=article['url'],
                            source=article['source'],
                            category=article['category'],
                            published_date=article['published_date'],
                            content_summary=article.get('content_summary', ''),
                            relevance_score=0.0  # Will be calculated later
                        ):
                            new_articles += 1
                    
                    # Update feed statistics
                    if feed_id:
                        self.db_manager.update_feed_stats(feed_id, True)
                    
                    logger.info(f"Processed {len(articles)} articles from {feed_info['name']}")
                else:
                    logger.error(f"Failed to fetch {feed_info['name']}: {result['error_message']}")
                    if feed_id:
                        self.db_manager.update_feed_stats(feed_id, False, result['error_message'])
            
            logger.info(f"RSS processing complete: {total_articles} total articles, {new_articles} new articles")
            return new_articles
            
        except Exception as e:
            logger.error(f"Error in RSS processing: {e}")
            return 0
    
    async def analyze_article_relevance(self) -> int:
        """Analyze relevance of unprocessed articles using LLM."""
        try:
            logger.info("Starting article relevance analysis...")
            
            # Get unprocessed articles
            articles = self.db_manager.get_unprocessed_articles(50)  # Process in batches
            if not articles:
                logger.info("No unprocessed articles found")
                return 0
            
            logger.info(f"Analyzing relevance for {len(articles)} articles")
            
            processed_count = 0
            
            # Analyze articles in smaller batches to avoid rate limits
            batch_size = 10
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i + batch_size]
                
                for article in batch:
                    try:
                        # Analyze relevance
                        relevance_score = await self.llm_processor.analyze_article_relevance(article)
                        
                        # Update database
                        self.db_manager.update_article_relevance(article['id'], relevance_score)
                        self.db_manager.mark_article_processed(article['id'])
                        
                        processed_count += 1
                        
                        logger.debug(f"Analyzed: {article['title']} - Relevance: {relevance_score:.2f}")
                        
                    except Exception as e:
                        logger.error(f"Error analyzing article {article['id']}: {e}")
                        # Mark as processed even if analysis failed
                        self.db_manager.mark_article_processed(article['id'])
                
                # Small delay between batches
                await asyncio.sleep(2)
            
            logger.info(f"Relevance analysis complete: {processed_count} articles processed")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error in relevance analysis: {e}")
            return 0
    
    async def generate_weekly_summary(self) -> Optional[str]:
        """Generate weekly summary from high-relevance articles."""
        try:
            logger.info("Generating weekly summary...")
            
            # Get high-relevance articles from the past week
            articles = self.db_manager.get_recent_articles(
                days=self.config['days_to_process'],
                min_relevance=self.config['min_relevance_score'],
                limit=self.config['max_articles_per_week']
            )
            
            if not articles:
                logger.warning("No relevant articles found for weekly summary")
                return None
            
            logger.info(f"Generating summary from {len(articles)} high-relevance articles")
            
            # Generate summary using LLM
            summary = await self.llm_processor.generate_weekly_summary(articles)
            
            if summary:
                # Store summary in database
                week_start = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
                week_end = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                categories = list(set(article['category'] for article in articles))
                
                summary_id = self.db_manager.add_weekly_summary(
                    week_start=week_start,
                    week_end=week_end,
                    summary_content=summary,
                    article_count=len(articles),
                    categories_covered=categories
                )
                
                logger.info(f"Weekly summary generated and stored (ID: {summary_id})")
                return summary
            else:
                logger.error("Failed to generate weekly summary")
                return None
                
        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
            return None
    
    async def publish_weekly_summary(self, summary: str) -> bool:
        """Publish weekly summary to Discord."""
        try:
            if not self.discord_publisher:
                logger.warning("Discord publisher not available")
                return False
            
            logger.info("Publishing weekly summary to Discord...")
            
            # Get metadata for the summary
            week_start = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
            articles = self.db_manager.get_recent_articles(
                days=self.config['days_to_process'],
                min_relevance=self.config['min_relevance_score'],
                limit=self.config['max_articles_per_week']
            )
            categories = list(set(article['category'] for article in articles))
            
            # Publish to Discord
            message_ids = await self.discord_publisher.publish_long_summary(
                summary_content=summary,
                title="Weekly RSS Summary",
                article_count=len(articles),
                categories=categories
            )
            
            if message_ids:
                logger.info(f"Weekly summary published successfully. Message IDs: {message_ids}")
                return True
            else:
                logger.error("Failed to publish weekly summary")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing weekly summary: {e}")
            return False
    
    async def run_weekly_processing(self):
        """Run the complete weekly processing workflow."""
        try:
            logger.info("=" * 50)
            logger.info("STARTING WEEKLY RSS PROCESSING")
            logger.info("=" * 50)
            
            start_time = datetime.now(timezone.utc)
            
            # Step 1: Fetch new articles
            new_articles = await self.fetch_and_process_articles()
            
            # Step 2: Analyze article relevance
            analyzed_articles = await self.analyze_article_relevance()
            
            # Step 3: Generate weekly summary
            summary = await self.generate_weekly_summary()
            
            # Step 4: Publish to Discord
            published = False
            if summary:
                published = await self.publish_weekly_summary(summary)
            
            # Step 5: Cleanup old articles
            cleaned_articles = self.db_manager.cleanup_old_articles(self.config['cleanup_days'])
            
            # Log processing statistics
            end_time = datetime.now(timezone.utc)
            processing_time = (end_time - start_time).total_seconds()
            
            stats = self.db_manager.get_stats()
            
            logger.info("=" * 50)
            logger.info("WEEKLY PROCESSING COMPLETE")
            logger.info(f"Processing time: {processing_time:.1f} seconds")
            logger.info(f"New articles fetched: {new_articles}")
            logger.info(f"Articles analyzed: {analyzed_articles}")
            logger.info(f"Summary generated: {'Yes' if summary else 'No'}")
            logger.info(f"Published to Discord: {'Yes' if published else 'No'}")
            logger.info(f"Old articles cleaned: {cleaned_articles}")
            logger.info(f"Total articles in database: {stats.get('total_articles', 0)}")
            logger.info("=" * 50)
            
            self.last_processing_time = end_time
            
            # Send notification about processing completion
            if self.discord_publisher:
                await self.discord_publisher.send_notification(
                    "Weekly Processing Complete",
                    f"Processed {new_articles} new articles, analyzed {analyzed_articles} articles. "
                    f"Summary {'published' if published else 'generation failed'}."
                )
            
        except Exception as e:
            logger.error(f"Error in weekly processing: {e}")
            
            # Send error notification
            if self.discord_publisher:
                await self.discord_publisher.send_notification(
                    "Weekly Processing Error",
                    f"An error occurred during weekly processing: {str(e)}",
                    color=0xff0000  # Red color for errors
                )
    
    async def start_scheduler(self):
        """Start the scheduled weekly processing."""
        try:
            # Schedule weekly processing
            trigger = CronTrigger(
                day_of_week=self.config['schedule_day'],
                hour=self.config['schedule_hour'],
                minute=self.config['schedule_minute']
            )
            
            self.scheduler.add_job(
                self.run_weekly_processing,
                trigger=trigger,
                id='weekly_processing',
                name='Weekly RSS Processing',
                replace_existing=True,
                misfire_grace_time=3600  # 1 hour grace period
            )
            
            self.scheduler.start()
            
            next_run = self.scheduler.get_job('weekly_processing').next_run_time
            logger.info(f"Scheduler started. Next weekly processing: {next_run}")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    async def run(self):
        """Main run method for the bot."""
        try:
            logger.info("Starting RSS News Bot...")
            
            # Initialize all components
            await self.initialize_components()
            
            # Start Discord bot if configured
            if self.discord_publisher:
                asyncio.create_task(self.discord_publisher.start_bot())
                # Wait a moment for Discord bot to connect
                await asyncio.sleep(3)
            
            # Start scheduler for weekly processing
            await self.start_scheduler()
            
            # Send startup notification
            if self.discord_publisher:
                await self.discord_publisher.send_notification(
                    "RSS News Bot Started",
                    f"Bot is now running and scheduled for weekly processing every "
                    f"{self.config['schedule_day']} at {self.config['schedule_hour']:02d}:{self.config['schedule_minute']:02d}",
                    color=0x00ff00  # Green color
                )
            
            self.is_running = True
            logger.info("RSS News Bot is running. Press Ctrl+C to stop.")
            
            # Keep the bot running
            while self.is_running:
                await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Error in main run loop: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the bot."""
        logger.info("Shutting down RSS News Bot...")
        
        self.is_running = False
        
        # Stop scheduler
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
        
        # Stop Discord bot
        if self.discord_publisher:
            await self.discord_publisher.stop_bot()
            logger.info("Discord bot stopped")
        
        logger.info("RSS News Bot shutdown complete")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}. Initiating shutdown...")
        self.is_running = False


async def main():
    """Main entry point."""
    try:
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
        
        # Initialize and run the bot
        bot = RSSNewsBot()
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 