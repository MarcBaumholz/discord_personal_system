"""
RSS Feed Manager for Personal RSS News Bot.
Handles fetching, parsing, and processing RSS feeds from various sources.
"""

import feedparser
import requests
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
import hashlib
import asyncio
import aiohttp
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class RSSFeedManager:
    """Manages RSS feed fetching and article extraction."""
    
    def __init__(self, max_concurrent_feeds: int = 5, request_timeout: int = 30,
                 rate_limit_delay: float = 1.0):
        """Initialize RSS feed manager with configuration."""
        self.max_concurrent_feeds = max_concurrent_feeds
        self.request_timeout = request_timeout
        self.rate_limit_delay = rate_limit_delay
        self.session = None
        
        # Configure user agent for RSS requests
        self.headers = {
            'User-Agent': 'Personal RSS News Bot/1.0 (Educational Use)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Encoding': 'gzip, deflate'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.request_timeout),
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def fetch_feed_sync(self, feed_url: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Synchronously fetch and parse a single RSS feed.
        Returns: (success, parsed_feed, error_message)
        """
        try:
            logger.debug(f"Fetching RSS feed: {feed_url}")
            
            # Add rate limiting
            time.sleep(self.rate_limit_delay)
            
            # Fetch the feed with proper headers
            response = requests.get(
                feed_url, 
                headers=self.headers, 
                timeout=self.request_timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse the RSS feed
            parsed_feed = feedparser.parse(response.content)
            
            # Check if parsing was successful
            if parsed_feed.bozo:
                logger.warning(f"Feed parsing had issues for {feed_url}: {parsed_feed.bozo_exception}")
            
            if not parsed_feed.entries:
                return False, None, "No entries found in feed"
            
            logger.info(f"Successfully fetched {len(parsed_feed.entries)} articles from {feed_url}")
            return True, parsed_feed, ""
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error for {feed_url}: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error fetching {feed_url}: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    async def fetch_feed_async(self, feed_url: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Asynchronously fetch and parse a single RSS feed.
        Returns: (success, parsed_feed, error_message)
        """
        try:
            logger.debug(f"Async fetching RSS feed: {feed_url}")
            
            # Add rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(feed_url) as response:
                response.raise_for_status()
                content = await response.read()
            
            # Parse the RSS feed
            parsed_feed = feedparser.parse(content)
            
            # Check if parsing was successful
            if parsed_feed.bozo:
                logger.warning(f"Feed parsing had issues for {feed_url}: {parsed_feed.bozo_exception}")
            
            if not parsed_feed.entries:
                return False, None, "No entries found in feed"
            
            logger.info(f"Successfully fetched {len(parsed_feed.entries)} articles from {feed_url}")
            return True, parsed_feed, ""
            
        except aiohttp.ClientError as e:
            error_msg = f"Request error for {feed_url}: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error fetching {feed_url}: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def extract_articles_from_feed(self, parsed_feed: Dict, source_name: str, 
                                  category: str) -> List[Dict]:
        """Extract and normalize articles from a parsed RSS feed."""
        articles = []
        
        for entry in parsed_feed.entries:
            try:
                # Extract basic article information
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                
                if not title or not link:
                    continue
                
                # Extract publication date
                published_date = self._extract_publication_date(entry)
                
                # Extract content/summary
                content_summary = self._extract_content_summary(entry)
                
                # Create article dictionary
                article = {
                    'title': title,
                    'url': link,
                    'source': source_name,
                    'category': category,
                    'published_date': published_date,
                    'content_summary': content_summary,
                    'author': entry.get('author', '').strip(),
                    'tags': self._extract_tags(entry)
                }
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Error extracting article from {source_name}: {e}")
                continue
        
        logger.info(f"Extracted {len(articles)} articles from {source_name}")
        return articles
    
    def _extract_publication_date(self, entry: Dict) -> str:
        """Extract and normalize publication date from RSS entry."""
        # Try different date fields
        date_fields = ['published', 'updated', 'created']
        
        for field in date_fields:
            if field in entry:
                try:
                    # Parse the date and convert to ISO format
                    date_struct = entry[f"{field}_parsed"]
                    if date_struct:
                        dt = datetime(*date_struct[:6], tzinfo=timezone.utc)
                        return dt.isoformat()
                except (ValueError, TypeError, AttributeError):
                    continue
        
        # Fallback to current time if no date found
        return datetime.now(timezone.utc).isoformat()
    
    def _extract_content_summary(self, entry: Dict) -> str:
        """Extract content summary from RSS entry."""
        # Try different content fields
        content_fields = ['summary', 'description', 'content']
        
        for field in content_fields:
            if field in entry:
                content = entry[field]
                if isinstance(content, list) and content:
                    content = content[0].get('value', '')
                elif isinstance(content, dict):
                    content = content.get('value', '')
                
                if content:
                    # Clean HTML tags and normalize whitespace
                    clean_content = self._clean_html_content(content)
                    return clean_content[:500] + "..." if len(clean_content) > 500 else clean_content
        
        return ""
    
    def _extract_tags(self, entry: Dict) -> List[str]:
        """Extract tags/categories from RSS entry."""
        tags = []
        
        # Extract from tags field
        if 'tags' in entry:
            for tag in entry['tags']:
                tag_text = tag.get('term', '').strip()
                if tag_text:
                    tags.append(tag_text)
        
        # Extract from category field
        if 'category' in entry:
            category = entry['category'].strip()
            if category and category not in tags:
                tags.append(category)
        
        return tags
    
    def _clean_html_content(self, content: str) -> str:
        """Clean HTML tags and normalize content."""
        import re
        
        # Remove HTML tags
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # Normalize whitespace
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        return clean_content
    
    async def fetch_multiple_feeds_async(self, feeds: List[Dict]) -> List[Dict]:
        """
        Fetch multiple RSS feeds concurrently.
        Each feed dict should have: {'id', 'name', 'url', 'category', 'priority'}
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_feeds)
        tasks = []
        
        async def fetch_single_feed(feed_info):
            async with semaphore:
                success, parsed_feed, error_msg = await self.fetch_feed_async(feed_info['url'])
                
                result = {
                    'feed_info': feed_info,
                    'success': success,
                    'error_message': error_msg,
                    'articles': []
                }
                
                if success and parsed_feed:
                    result['articles'] = self.extract_articles_from_feed(
                        parsed_feed, 
                        feed_info['name'], 
                        feed_info['category']
                    )
                
                return result
        
        # Create tasks for all feeds
        for feed in feeds:
            task = asyncio.create_task(fetch_single_feed(feed))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def fetch_multiple_feeds_sync(self, feeds: List[Dict]) -> List[Dict]:
        """
        Fetch multiple RSS feeds synchronously.
        Each feed dict should have: {'id', 'name', 'url', 'category', 'priority'}
        """
        results = []
        
        for feed_info in feeds:
            success, parsed_feed, error_msg = self.fetch_feed_sync(feed_info['url'])
            
            result = {
                'feed_info': feed_info,
                'success': success,
                'error_message': error_msg,
                'articles': []
            }
            
            if success and parsed_feed:
                result['articles'] = self.extract_articles_from_feed(
                    parsed_feed, 
                    feed_info['name'], 
                    feed_info['category']
                )
            
            results.append(result)
        
        return results
    
    def validate_feed_url(self, feed_url: str) -> Tuple[bool, str]:
        """Validate if a URL is a valid RSS feed."""
        try:
            success, parsed_feed, error_msg = self.fetch_feed_sync(feed_url)
            
            if not success:
                return False, error_msg
            
            if not parsed_feed or not parsed_feed.entries:
                return False, "Feed has no entries"
            
            return True, "Feed is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"


# Utility functions for RSS management
def load_rss_feeds_from_config(config_path: str) -> List[Dict]:
    """Load RSS feeds from JSON configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        feeds = []
        for feed in config.get('feeds', []):
            feeds.append({
                'name': feed['name'],
                'url': feed['url'],
                'category': feed['category'],
                'priority': feed.get('priority', 2)
            })
        
        logger.info(f"Loaded {len(feeds)} RSS feeds from config")
        return feeds
        
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error loading RSS feeds config: {e}")
        return []


async def test_rss_manager():
    """Test function for RSS manager."""
    logging.basicConfig(level=logging.INFO)
    
    # Test feeds
    test_feeds = [
        {
            'id': 1,
            'name': 'OpenAI Blog',
            'url': 'https://openai.com/blog/rss/',
            'category': 'AI_LLM',
            'priority': 1
        },
        {
            'id': 2,
            'name': 'Harvard Business Review',
            'url': 'https://feeds.hbr.org/harvardbusiness',
            'category': 'PRODUCTIVITY',
            'priority': 1
        }
    ]
    
    async with RSSFeedManager() as rss_manager:
        results = await rss_manager.fetch_multiple_feeds_async(test_feeds)
        
        for result in results:
            feed_name = result['feed_info']['name']
            if result['success']:
                print(f"✅ {feed_name}: {len(result['articles'])} articles")
            else:
                print(f"❌ {feed_name}: {result['error_message']}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_rss_manager()) 