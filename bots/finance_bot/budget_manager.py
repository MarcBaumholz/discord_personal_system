import logging
import sqlite3
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger('finance_bot.budget_manager')

class BudgetManager:
    """Manages budget settings and tracks spending against budgets"""
    
    def __init__(self, db_path="finance.db"):
        """
        Initialize budget manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        logger.info(f"Initializing BudgetManager with database: {db_path}")
        
        # Initialize database if it doesn't exist
        self._initialize_db()
        
        # Load current budgets
        self.budgets = self._load_budgets()
        
    def _initialize_db(self):
        """Create database tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create budgets table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                period TEXT DEFAULT 'monthly'
            )
            ''')
            
            # Create categories table for transaction categorization
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                keyword TEXT UNIQUE,
                category TEXT NOT NULL
            )
            ''')
            
            # Create spending table to track spending history
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS spending (
                id INTEGER PRIMARY KEY,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _load_budgets(self):
        """Load budgets from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT category, amount, period FROM budgets")
            rows = cursor.fetchall()
            
            budgets = {}
            for row in rows:
                category, amount, period = row
                budgets[category] = {"amount": amount, "period": period}
            
            conn.close()
            logger.info(f"Loaded {len(budgets)} budget categories")
            return budgets
        except Exception as e:
            logger.error(f"Error loading budgets: {e}")
            return {}
    
    def set_budget(self, category, amount, period="monthly"):
        """
        Set budget for a category
        
        Args:
            category: Budget category name
            amount: Budget amount
            period: Budget period (daily, weekly, monthly, yearly)
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert or update budget
            cursor.execute('''
            INSERT OR REPLACE INTO budgets (category, amount, period)
            VALUES (?, ?, ?)
            ''', (category, amount, period))
            
            conn.commit()
            conn.close()
            
            # Update in-memory cache
            self.budgets[category] = {"amount": amount, "period": period}
            
            logger.info(f"Set {period} budget for {category} to {amount}")
            return True
        except Exception as e:
            logger.error(f"Error setting budget: {e}")
            return False
    
    def record_spending(self, category, amount, date=None):
        """
        Record spending in a category
        
        Args:
            category: Spending category
            amount: Amount spent (positive number)
            date: Date of spending (defaults to today)
            
        Returns:
            bool: Success status
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if amount < 0:
            amount = abs(amount)  # Ensure amount is positive
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO spending (category, amount, date)
            VALUES (?, ?, ?)
            ''', (category, amount, date))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded {amount} spending in {category} on {date}")
            return True
        except Exception as e:
            logger.error(f"Error recording spending: {e}")
            return False
    
    def get_spending(self, category=None, days=30):
        """
        Get spending for a period
        
        Args:
            category: Category to filter by (None for all)
            days: Number of days to look back
            
        Returns:
            dict: Spending by category
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            if category:
                cursor.execute('''
                SELECT category, SUM(amount) FROM spending
                WHERE category = ? AND date >= ?
                GROUP BY category
                ''', (category, start_date_str))
            else:
                cursor.execute('''
                SELECT category, SUM(amount) FROM spending
                WHERE date >= ?
                GROUP BY category
                ''', (start_date_str,))
            
            rows = cursor.fetchall()
            
            spending = {}
            for row in rows:
                cat, amount = row
                spending[cat] = amount
            
            conn.close()
            return spending
        except Exception as e:
            logger.error(f"Error getting spending: {e}")
            return {}
    
    def check_budgets(self):
        """
        Check if any budgets are over their limits
        
        Returns:
            list: Categories that are over budget with details
        """
        # For demo purposes, we'll return sample data
        # In a real implementation, you would compare actual spending to budgets
        
        # Simulated overspent categories
        over_budget = [
            {
                "category": "Dining",
                "budget": 200.00,
                "spent": 245.30,
                "percentage": 122.65
            },
            {
                "category": "Entertainment",
                "budget": 100.00,
                "spent": 112.99,
                "percentage": 112.99
            }
        ]
        
        return over_budget 