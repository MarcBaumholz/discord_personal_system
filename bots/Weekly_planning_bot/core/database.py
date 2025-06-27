import sqlite3
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

logger = logging.getLogger('weekly_planning_bot.database')

class DatabaseManager:
    """SQLite database manager for persistent storage of weekly planning data"""
    
    def __init__(self, db_path: str = "data/weekly_planning.db"):
        """Initialize database manager with SQLite connection"""
        self.db_path = db_path
        self.db_dir = os.path.dirname(db_path)
        
        # Create data directory if it doesn't exist
        os.makedirs(self.db_dir, exist_ok=True)
        
        logger.info(f"Initializing database at {db_path}")
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return conn
    
    def _initialize_database(self):
        """Initialize database schema if not exists"""
        try:
            with self._get_connection() as conn:
                # Create users table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        discord_id TEXT UNIQUE NOT NULL,
                        username TEXT,
                        timezone TEXT DEFAULT 'Europe/Berlin',
                        preferences TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create weekly_plans table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS weekly_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        week_start_date DATE NOT NULL,
                        focus_areas TEXT DEFAULT '[]',
                        goals TEXT,
                        completion_rate REAL DEFAULT 0,
                        total_tasks INTEGER DEFAULT 0,
                        completed_tasks INTEGER DEFAULT 0,
                        notion_plan_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        UNIQUE(user_id, week_start_date)
                    )
                ''')
                
                # Create tasks table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id INTEGER NOT NULL,
                        day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
                        title TEXT NOT NULL,
                        scheduled_time TIME,
                        completed BOOLEAN DEFAULT FALSE,
                        priority INTEGER DEFAULT 2 CHECK (priority >= 1 AND priority <= 5),
                        category TEXT DEFAULT 'general',
                        notes TEXT,
                        notion_task_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        FOREIGN KEY (plan_id) REFERENCES weekly_plans (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create analytics table for performance tracking
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS analytics_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        week_start_date DATE NOT NULL,
                        productivity_score REAL,
                        completion_rate REAL,
                        focus_time_hours REAL,
                        most_productive_day INTEGER,
                        least_productive_day INTEGER,
                        category_breakdown TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create indexes for better performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users (discord_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_date ON weekly_plans (user_id, week_start_date)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_plan_day ON tasks (plan_id, day_of_week)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_analytics_user_date ON analytics_snapshots (user_id, week_start_date)')
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def get_or_create_user(self, discord_id: str, username: str = None) -> Dict[str, Any]:
        """Get existing user or create new one"""
        try:
            with self._get_connection() as conn:
                # Try to get existing user
                cursor = conn.execute(
                    "SELECT * FROM users WHERE discord_id = ?", 
                    (discord_id,)
                )
                user = cursor.fetchone()
                
                if user:
                    # Update last active
                    conn.execute(
                        "UPDATE users SET last_active = CURRENT_TIMESTAMP, username = ? WHERE discord_id = ?",
                        (username or user['username'], discord_id)
                    )
                    conn.commit()
                    return dict(user)
                
                # Create new user
                cursor = conn.execute(
                    """INSERT INTO users (discord_id, username, preferences) 
                       VALUES (?, ?, ?) RETURNING *""",
                    (discord_id, username, '{}')
                )
                new_user = cursor.fetchone()
                conn.commit()
                
                logger.info(f"Created new user: {discord_id}")
                return dict(new_user)
                
        except Exception as e:
            logger.error(f"Error getting/creating user {discord_id}: {e}")
            raise
    
    async def save_weekly_plan(self, user_id: int, weekly_data: Dict[str, Any]) -> int:
        """Save weekly plan data to database"""
        try:
            week_start = datetime.strptime(weekly_data['date'], "%Y-%m-%d").date()
            focus_areas = json.dumps(weekly_data.get('focus_areas', []))
            goals = weekly_data.get('weekly_goals', '')
            
            # Calculate task statistics
            tasks = weekly_data.get('tasks', {})
            total_tasks = sum(len(day_tasks) for day_tasks in tasks.values())
            completed_tasks = sum(
                sum(1 for task in day_tasks if task.get('completed', False))
                for day_tasks in tasks.values()
            )
            completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0
            
            with self._get_connection() as conn:
                # Insert or update weekly plan
                cursor = conn.execute(
                    """INSERT OR REPLACE INTO weekly_plans 
                       (user_id, week_start_date, focus_areas, goals, completion_rate, 
                        total_tasks, completed_tasks, notion_plan_id, updated_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP) 
                       RETURNING id""",
                    (user_id, week_start, focus_areas, goals, completion_rate,
                     total_tasks, completed_tasks, weekly_data.get('id'))
                )
                plan_id = cursor.fetchone()[0]
                
                # Delete existing tasks for this plan
                conn.execute("DELETE FROM tasks WHERE plan_id = ?", (plan_id,))
                
                # Insert tasks
                for day_name, day_tasks in tasks.items():
                    day_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                                  'Friday', 'Saturday', 'Sunday'].index(day_name)
                    
                    for task in day_tasks:
                        conn.execute(
                            """INSERT INTO tasks (plan_id, day_of_week, title, scheduled_time, 
                               completed, priority, category) 
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (plan_id, day_of_week, task.get('title', ''),
                             task.get('time'), task.get('completed', False),
                             task.get('priority', 2), task.get('category', 'general'))
                        )
                
                conn.commit()
                logger.info(f"Saved weekly plan {plan_id} for user {user_id}")
                return plan_id
                
        except Exception as e:
            logger.error(f"Error saving weekly plan for user {user_id}: {e}")
            raise
    
    async def get_weekly_plan(self, user_id: int, week_start_date: str = None) -> Optional[Dict[str, Any]]:
        """Get weekly plan for user (current week if date not specified)"""
        try:
            if not week_start_date:
                # Get current week start (Monday)
                today = datetime.now().date()
                week_start = today - timedelta(days=today.weekday())
            else:
                week_start = datetime.strptime(week_start_date, "%Y-%m-%d").date()
            
            with self._get_connection() as conn:
                # Get weekly plan
                cursor = conn.execute(
                    """SELECT * FROM weekly_plans 
                       WHERE user_id = ? AND week_start_date = ?""",
                    (user_id, week_start)
                )
                plan = cursor.fetchone()
                
                if not plan:
                    return None
                
                # Get tasks for this plan
                cursor = conn.execute(
                    """SELECT * FROM tasks 
                       WHERE plan_id = ? 
                       ORDER BY day_of_week, scheduled_time""",
                    (plan['id'],)
                )
                tasks = cursor.fetchall()
                
                # Organize tasks by day
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                       'Friday', 'Saturday', 'Sunday']
                organized_tasks = {day: [] for day in days}
                
                for task in tasks:
                    day_name = days[task['day_of_week']]
                    organized_tasks[day_name].append({
                        'id': task['id'],
                        'title': task['title'],
                        'time': task['scheduled_time'],
                        'completed': bool(task['completed']),
                        'priority': task['priority'],
                        'category': task['category'],
                        'notes': task['notes']
                    })
                
                return {
                    'id': plan['id'],
                    'date': str(plan['week_start_date']),
                    'focus_areas': json.loads(plan['focus_areas']),
                    'weekly_goals': plan['goals'],
                    'tasks': organized_tasks,
                    'completion_rate': plan['completion_rate'],
                    'total_tasks': plan['total_tasks'],
                    'completed_tasks': plan['completed_tasks']
                }
                
        except Exception as e:
            logger.error(f"Error getting weekly plan for user {user_id}: {e}")
            return None
    
    async def update_task_status(self, task_id: int, completed: bool) -> bool:
        """Update task completion status"""
        try:
            with self._get_connection() as conn:
                # Update task
                completed_at = datetime.now() if completed else None
                conn.execute(
                    """UPDATE tasks 
                       SET completed = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE id = ?""",
                    (completed, completed_at, task_id)
                )
                
                # Update weekly plan completion rate
                cursor = conn.execute(
                    """SELECT plan_id FROM tasks WHERE id = ?""",
                    (task_id,)
                )
                plan_id = cursor.fetchone()[0]
                
                # Recalculate completion rate for the plan
                cursor = conn.execute(
                    """SELECT COUNT(*) as total, 
                       SUM(CASE WHEN completed THEN 1 ELSE 0 END) as completed
                       FROM tasks WHERE plan_id = ?""",
                    (plan_id,)
                )
                stats = cursor.fetchone()
                
                completion_rate = (stats['completed'] / stats['total']) if stats['total'] > 0 else 0
                
                conn.execute(
                    """UPDATE weekly_plans 
                       SET completion_rate = ?, completed_tasks = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (completion_rate, stats['completed'], plan_id)
                )
                
                conn.commit()
                logger.info(f"Updated task {task_id} completion status to {completed}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating task {task_id} status: {e}")
            return False
    
    async def get_user_analytics(self, user_id: int, weeks_back: int = 4) -> Dict[str, Any]:
        """Get analytics data for user over specified weeks"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(weeks=weeks_back)
            
            with self._get_connection() as conn:
                # Get weekly plans in date range
                cursor = conn.execute(
                    """SELECT * FROM weekly_plans 
                       WHERE user_id = ? AND week_start_date >= ? AND week_start_date <= ?
                       ORDER BY week_start_date""",
                    (user_id, start_date, end_date)
                )
                plans = cursor.fetchall()
                
                if not plans:
                    return {'message': 'No data available for analytics'}
                
                # Calculate analytics
                total_completion = sum(plan['completion_rate'] for plan in plans)
                avg_completion = total_completion / len(plans) if plans else 0
                
                # Get task category breakdown
                cursor = conn.execute(
                    """SELECT t.category, COUNT(*) as total,
                       SUM(CASE WHEN t.completed THEN 1 ELSE 0 END) as completed
                       FROM tasks t
                       JOIN weekly_plans wp ON t.plan_id = wp.id
                       WHERE wp.user_id = ? AND wp.week_start_date >= ?
                       GROUP BY t.category""",
                    (user_id, start_date)
                )
                categories = cursor.fetchall()
                
                category_breakdown = {}
                for cat in categories:
                    category_breakdown[cat['category']] = {
                        'total': cat['total'],
                        'completed': cat['completed'],
                        'rate': (cat['completed'] / cat['total']) if cat['total'] > 0 else 0
                    }
                
                # Find most/least productive days
                cursor = conn.execute(
                    """SELECT t.day_of_week, COUNT(*) as total,
                       SUM(CASE WHEN t.completed THEN 1 ELSE 0 END) as completed
                       FROM tasks t
                       JOIN weekly_plans wp ON t.plan_id = wp.id
                       WHERE wp.user_id = ? AND wp.week_start_date >= ?
                       GROUP BY t.day_of_week""",
                    (user_id, start_date)
                )
                day_stats = cursor.fetchall()
                
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                       'Friday', 'Saturday', 'Sunday']
                
                day_completion = {}
                for stat in day_stats:
                    day_name = days[stat['day_of_week']]
                    completion_rate = (stat['completed'] / stat['total']) if stat['total'] > 0 else 0
                    day_completion[day_name] = {
                        'total': stat['total'],
                        'completed': stat['completed'],
                        'rate': completion_rate
                    }
                
                # Find best and worst days
                if day_completion:
                    best_day = max(day_completion.items(), key=lambda x: x[1]['rate'])
                    worst_day = min(day_completion.items(), key=lambda x: x[1]['rate'])
                else:
                    best_day = worst_day = None
                
                return {
                    'weeks_analyzed': len(plans),
                    'average_completion_rate': avg_completion,
                    'total_tasks': sum(plan['total_tasks'] for plan in plans),
                    'total_completed': sum(plan['completed_tasks'] for plan in plans),
                    'category_breakdown': category_breakdown,
                    'day_completion': day_completion,
                    'most_productive_day': best_day[0] if best_day else None,
                    'least_productive_day': worst_day[0] if worst_day else None,
                    'weekly_trends': [
                        {
                            'week': str(plan['week_start_date']),
                            'completion_rate': plan['completion_rate'],
                            'total_tasks': plan['total_tasks']
                        }
                        for plan in plans
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics for user {user_id}: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data beyond specified days"""
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
            
            with self._get_connection() as conn:
                # Delete old weekly plans (tasks will be deleted via cascade)
                cursor = conn.execute(
                    "DELETE FROM weekly_plans WHERE week_start_date < ?",
                    (cutoff_date,)
                )
                deleted_plans = cursor.rowcount
                
                # Delete old analytics snapshots
                cursor = conn.execute(
                    "DELETE FROM analytics_snapshots WHERE week_start_date < ?",
                    (cutoff_date,)
                )
                deleted_snapshots = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_plans} old plans and {deleted_snapshots} old snapshots")
                return deleted_plans + deleted_snapshots
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def close(self):
        """Close database connections"""
        logger.info("Database manager closed")

# Global database instance
db_manager = None

def get_database() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager 