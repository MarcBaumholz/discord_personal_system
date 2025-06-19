"""
Database management for Personal RSS News Bot.
Handles SQLite database operations for storing articles, feeds, and summaries.
"""

import sqlite3
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for the RSS bot."""
    
    def __init__(self, db_path: str = "data/rss_bot.db"):
        """Initialize database manager with path to database file."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create articles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        source TEXT NOT NULL,
                        category TEXT NOT NULL,
                        published_date TEXT NOT NULL,
                        fetched_date TEXT NOT NULL,
                        content_summary TEXT,
                        content_hash TEXT UNIQUE NOT NULL,
                        relevance_score REAL DEFAULT 0.0,
                        processed BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create feed_sources table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feed_sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        category TEXT NOT NULL,
                        priority INTEGER DEFAULT 2,
                        active BOOLEAN DEFAULT TRUE,
                        last_fetched TEXT,
                        fetch_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        last_error TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create weekly_summaries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weekly_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        week_start_date TEXT NOT NULL,
                        week_end_date TEXT NOT NULL,
                        summary_content TEXT NOT NULL,
                        article_count INTEGER NOT NULL,
                        categories_covered TEXT NOT NULL,
                        posted_to_discord BOOLEAN DEFAULT FALSE,
                        discord_message_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_published_date ON articles(published_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_relevance ON articles(relevance_score)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_feed_sources_category ON feed_sources(category)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_feed_source(self, name: str, url: str, category: str, priority: int = 2) -> bool:
        """Add a new feed source to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO feed_sources 
                    (name, url, category, priority, active)
                    VALUES (?, ?, ?, ?, TRUE)
                """, (name, url, category, priority))
                conn.commit()
                logger.info(f"Added feed source: {name}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error adding feed source {name}: {e}")
            return False
    
    def get_active_feeds(self) -> List[Dict]:
        """Get all active RSS feed sources."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, url, category, priority, last_fetched
                    FROM feed_sources 
                    WHERE active = TRUE
                    ORDER BY priority ASC, category
                """)
                
                columns = [description[0] for description in cursor.description]
                feeds = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return feeds
        except sqlite3.Error as e:
            logger.error(f"Error getting active feeds: {e}")
            return []
    
    def add_article(self, title: str, url: str, source: str, category: str, 
                   published_date: str, content_summary: str = "", 
                   relevance_score: float = 0.0) -> bool:
        """Add a new article to the database."""
        try:
            # Create content hash from title + url for deduplication
            content_hash = hashlib.md5(f"{title}{url}".encode()).hexdigest()
            fetched_date = datetime.now(timezone.utc).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO articles 
                    (title, url, source, category, published_date, fetched_date,
                     content_summary, content_hash, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, url, source, category, published_date, fetched_date,
                      content_summary, content_hash, relevance_score))
                
                rows_affected = cursor.rowcount
                conn.commit()
                
                if rows_affected > 0:
                    logger.debug(f"Added article: {title}")
                    return True
                else:
                    logger.debug(f"Article already exists: {title}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error adding article {title}: {e}")
            return False
    
    def get_unprocessed_articles(self, limit: int = 50) -> List[Dict]:
        """Get articles that haven't been processed yet."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, url, source, category, published_date,
                           content_summary, relevance_score
                    FROM articles 
                    WHERE processed = FALSE
                    ORDER BY published_date DESC, relevance_score DESC
                    LIMIT ?
                """, (limit,))
                
                columns = [description[0] for description in cursor.description]
                articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return articles
        except sqlite3.Error as e:
            logger.error(f"Error getting unprocessed articles: {e}")
            return []
    
    def get_recent_articles(self, days: int = 7, min_relevance: float = 0.7, 
                          limit: int = 25) -> List[Dict]:
        """Get recent articles above relevance threshold for weekly summary."""
        try:
            cutoff_date = datetime.now(timezone.utc)
            cutoff_date = cutoff_date.replace(
                day=cutoff_date.day - days
            ).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, url, source, category, published_date,
                           content_summary, relevance_score
                    FROM articles 
                    WHERE published_date >= ? AND relevance_score >= ? AND processed = TRUE
                    ORDER BY relevance_score DESC, published_date DESC
                    LIMIT ?
                """, (cutoff_date, min_relevance, limit))
                
                columns = [description[0] for description in cursor.description]
                articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return articles
        except sqlite3.Error as e:
            logger.error(f"Error getting recent articles: {e}")
            return []
    
    def mark_article_processed(self, article_id: int) -> bool:
        """Mark an article as processed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE articles SET processed = TRUE 
                    WHERE id = ?
                """, (article_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error marking article {article_id} as processed: {e}")
            return False
    
    def update_article_relevance(self, article_id: int, relevance_score: float) -> bool:
        """Update the relevance score for an article."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE articles SET relevance_score = ? 
                    WHERE id = ?
                """, (relevance_score, article_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating relevance for article {article_id}: {e}")
            return False
    
    def add_weekly_summary(self, week_start: str, week_end: str, 
                          summary_content: str, article_count: int,
                          categories_covered: List[str]) -> int:
        """Add a weekly summary to the database."""
        try:
            categories_json = json.dumps(categories_covered)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO weekly_summaries 
                    (week_start_date, week_end_date, summary_content, 
                     article_count, categories_covered)
                    VALUES (?, ?, ?, ?, ?)
                """, (week_start, week_end, summary_content, 
                      article_count, categories_json))
                
                summary_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Added weekly summary with ID: {summary_id}")
                return summary_id
        except sqlite3.Error as e:
            logger.error(f"Error adding weekly summary: {e}")
            return 0
    
    def update_feed_stats(self, feed_id: int, success: bool, error_msg: str = "") -> bool:
        """Update feed statistics after fetch attempt."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                current_time = datetime.now(timezone.utc).isoformat()
                
                if success:
                    cursor.execute("""
                        UPDATE feed_sources 
                        SET last_fetched = ?, fetch_count = fetch_count + 1
                        WHERE id = ?
                    """, (current_time, feed_id))
                else:
                    cursor.execute("""
                        UPDATE feed_sources 
                        SET error_count = error_count + 1, last_error = ?
                        WHERE id = ?
                    """, (error_msg, feed_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating feed stats for feed {feed_id}: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get database statistics for monitoring."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total articles
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_articles = cursor.fetchone()[0]
                
                # Articles by category
                cursor.execute("""
                    SELECT category, COUNT(*) 
                    FROM articles 
                    GROUP BY category
                """)
                articles_by_category = dict(cursor.fetchall())
                
                # Recent articles (last 7 days)
                week_ago = datetime.now(timezone.utc)
                week_ago = week_ago.replace(day=week_ago.day - 7).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE published_date >= ?
                """, (week_ago,))
                recent_articles = cursor.fetchone()[0]
                
                # Feed statistics
                cursor.execute("SELECT COUNT(*) FROM feed_sources WHERE active = TRUE")
                active_feeds = cursor.fetchone()[0]
                
                # Weekly summaries
                cursor.execute("SELECT COUNT(*) FROM weekly_summaries")
                total_summaries = cursor.fetchone()[0]
                
                return {
                    "total_articles": total_articles,
                    "recent_articles": recent_articles,
                    "articles_by_category": articles_by_category,
                    "active_feeds": active_feeds,
                    "total_summaries": total_summaries
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_articles(self, days: int = 30) -> int:
        """Clean up articles older than specified days."""
        try:
            cutoff_date = datetime.now(timezone.utc)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM articles 
                    WHERE published_date < ?
                """, (cutoff_date,))
                
                rows_deleted = cursor.rowcount
                conn.commit()
                
                if rows_deleted > 0:
                    logger.info(f"Cleaned up {rows_deleted} old articles")
                
                return rows_deleted
                
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old articles: {e}")
            return 0


if __name__ == "__main__":
    # Test database operations
    logging.basicConfig(level=logging.INFO)
    
    db = DatabaseManager("data/test_rss_bot.db")
    
    # Test adding a feed source
    db.add_feed_source("Test Feed", "https://example.com/feed.xml", "TEST", 1)
    
    # Test getting active feeds
    feeds = db.get_active_feeds()
    print(f"Active feeds: {len(feeds)}")
    
    # Test adding an article
    db.add_article(
        "Test Article", 
        "https://example.com/article1", 
        "Test Feed",
        "TEST",
        datetime.now(timezone.utc).isoformat(),
        "This is a test article summary",
        0.8
    )
    
    # Test getting statistics
    stats = db.get_stats()
    print(f"Database stats: {stats}")

    print("Database test completed successfully!") 