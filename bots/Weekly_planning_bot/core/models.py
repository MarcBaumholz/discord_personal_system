from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import List, Dict, Any, Optional
import json

@dataclass
class User:
    """User data model"""
    id: Optional[int] = None
    discord_id: str = ""
    username: Optional[str] = None
    timezone: str = "Europe/Berlin"
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'User':
        """Create User instance from database row"""
        preferences = json.loads(row.get('preferences', '{}'))
        return cls(
            id=row.get('id'),
            discord_id=row.get('discord_id', ''),
            username=row.get('username'),
            timezone=row.get('timezone', 'Europe/Berlin'),
            preferences=preferences,
            created_at=row.get('created_at'),
            last_active=row.get('last_active')
        )

@dataclass
class Task:
    """Task data model"""
    id: Optional[int] = None
    plan_id: Optional[int] = None
    day_of_week: int = 0  # 0=Monday, 6=Sunday
    title: str = ""
    scheduled_time: Optional[time] = None
    completed: bool = False
    priority: int = 2  # 1=High, 2=Medium, 3=Low, 4=Optional, 5=Someday
    category: str = "general"
    notes: Optional[str] = None
    notion_task_id: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def day_name(self) -> str:
        """Get day name from day_of_week"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
               'Friday', 'Saturday', 'Sunday']
        return days[self.day_of_week]
    
    @property
    def priority_emoji(self) -> str:
        """Get emoji for priority level"""
        priority_emojis = {
            1: "🔥",  # High
            2: "⭐",  # Medium
            3: "📝",  # Low
            4: "💡",  # Optional
            5: "💭"   # Someday
        }
        return priority_emojis.get(self.priority, "📝")
    
    @property
    def status_emoji(self) -> str:
        """Get emoji for completion status"""
        return "✅" if self.completed else "⬜"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'time': self.scheduled_time.strftime("%H:%M") if self.scheduled_time else None,
            'completed': self.completed,
            'priority': self.priority,
            'category': self.category,
            'notes': self.notes,
            'day': self.day_name,
            'priority_emoji': self.priority_emoji,
            'status_emoji': self.status_emoji
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Task':
        """Create Task instance from database row"""
        scheduled_time = None
        if row.get('scheduled_time'):
            time_str = row['scheduled_time']
            if isinstance(time_str, str):
                try:
                    hour, minute = map(int, time_str.split(':'))
                    scheduled_time = time(hour, minute)
                except:
                    pass
        
        return cls(
            id=row.get('id'),
            plan_id=row.get('plan_id'),
            day_of_week=row.get('day_of_week', 0),
            title=row.get('title', ''),
            scheduled_time=scheduled_time,
            completed=bool(row.get('completed', False)),
            priority=row.get('priority', 2),
            category=row.get('category', 'general'),
            notes=row.get('notes'),
            notion_task_id=row.get('notion_task_id'),
            created_at=row.get('created_at'),
            completed_at=row.get('completed_at')
        )

@dataclass
class WeeklyPlan:
    """Weekly plan data model"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    week_start_date: Optional[date] = None
    focus_areas: List[str] = field(default_factory=list)
    goals: str = ""
    completion_rate: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    notion_plan_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tasks: Dict[str, List[Task]] = field(default_factory=dict)
    
    @property
    def completion_percentage(self) -> int:
        """Get completion percentage as integer"""
        return int(self.completion_rate * 100)
    
    @property
    def progress_bar(self) -> str:
        """Get visual progress bar"""
        filled = int(self.completion_rate * 20)
        return "█" * filled + "░" * (20 - filled)
    
    @property
    def week_display(self) -> str:
        """Get formatted week display"""
        if self.week_start_date:
            week_num = self.week_start_date.isocalendar()[1]
            return f"Week {week_num} ({self.week_start_date.strftime('%B %d, %Y')})"
        return "Current Week"
    
    def get_tasks_by_day(self, day: str) -> List[Task]:
        """Get tasks for specific day"""
        return self.tasks.get(day, [])
    
    def get_day_completion_rate(self, day: str) -> float:
        """Get completion rate for specific day"""
        day_tasks = self.get_tasks_by_day(day)
        if not day_tasks:
            return 0.0
        completed = sum(1 for task in day_tasks if task.completed)
        return completed / len(day_tasks)
    
    def get_category_stats(self) -> Dict[str, Dict[str, int]]:
        """Get task statistics by category"""
        category_stats = {}
        
        for day_tasks in self.tasks.values():
            for task in day_tasks:
                if task.category not in category_stats:
                    category_stats[task.category] = {'total': 0, 'completed': 0}
                
                category_stats[task.category]['total'] += 1
                if task.completed:
                    category_stats[task.category]['completed'] += 1
        
        return category_stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        # Organize tasks by day name
        organized_tasks = {}
        for day, task_list in self.tasks.items():
            organized_tasks[day] = [task.to_dict() for task in task_list]
        
        return {
            'id': self.id,
            'date': str(self.week_start_date) if self.week_start_date else None,
            'focus_areas': self.focus_areas,
            'weekly_goals': self.goals,
            'tasks': organized_tasks,
            'completion_rate': self.completion_rate,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'completion_percentage': self.completion_percentage,
            'progress_bar': self.progress_bar,
            'week_display': self.week_display
        }
    
    @classmethod
    def from_db_data(cls, plan_row: Dict[str, Any], tasks: List[Task]) -> 'WeeklyPlan':
        """Create WeeklyPlan instance from database data"""
        focus_areas = json.loads(plan_row.get('focus_areas', '[]'))
        
        # Organize tasks by day
        organized_tasks = {
            'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': 
            'Friday': [], 'Saturday': [], 'Sunday': []
        }
        
        for task in tasks:
            day_name = task.day_name
            if day_name in organized_tasks:
                organized_tasks[day_name].append(task)
        
        week_start = plan_row.get('week_start_date')
        if isinstance(week_start, str):
            week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
        
        return cls(
            id=plan_row.get('id'),
            user_id=plan_row.get('user_id'),
            week_start_date=week_start,
            focus_areas=focus_areas,
            goals=plan_row.get('goals', ''),
            completion_rate=plan_row.get('completion_rate', 0.0),
            total_tasks=plan_row.get('total_tasks', 0),
            completed_tasks=plan_row.get('completed_tasks', 0),
            notion_plan_id=plan_row.get('notion_plan_id'),
            created_at=plan_row.get('created_at'),
            updated_at=plan_row.get('updated_at'),
            tasks=organized_tasks
        )

@dataclass
class AnalyticsSnapshot:
    """Analytics snapshot data model"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    week_start_date: Optional[date] = None
    productivity_score: float = 0.0
    completion_rate: float = 0.0
    focus_time_hours: float = 0.0
    most_productive_day: Optional[int] = None
    least_productive_day: Optional[int] = None
    category_breakdown: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    @property
    def most_productive_day_name(self) -> Optional[str]:
        """Get name of most productive day"""
        if self.most_productive_day is not None:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                   'Friday', 'Saturday', 'Sunday']
            return days[self.most_productive_day]
        return None
    
    @property
    def least_productive_day_name(self) -> Optional[str]:
        """Get name of least productive day"""
        if self.least_productive_day is not None:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                   'Friday', 'Saturday', 'Sunday']
            return days[self.least_productive_day]
        return None
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'AnalyticsSnapshot':
        """Create AnalyticsSnapshot instance from database row"""
        category_breakdown = json.loads(row.get('category_breakdown', '{}'))
        
        week_start = row.get('week_start_date')
        if isinstance(week_start, str):
            week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
        
        return cls(
            id=row.get('id'),
            user_id=row.get('user_id'),
            week_start_date=week_start,
            productivity_score=row.get('productivity_score', 0.0),
            completion_rate=row.get('completion_rate', 0.0),
            focus_time_hours=row.get('focus_time_hours', 0.0),
            most_productive_day=row.get('most_productive_day'),
            least_productive_day=row.get('least_productive_day'),
            category_breakdown=category_breakdown,
            created_at=row.get('created_at')
        )

# Priority levels constants
class Priority:
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    OPTIONAL = 4
    SOMEDAY = 5
    
    @classmethod
    def get_name(cls, priority: int) -> str:
        names = {
            cls.HIGH: "High",
            cls.MEDIUM: "Medium", 
            cls.LOW: "Low",
            cls.OPTIONAL: "Optional",
            cls.SOMEDAY: "Someday"
        }
        return names.get(priority, "Medium")
    
    @classmethod
    def get_emoji(cls, priority: int) -> str:
        emojis = {
            cls.HIGH: "🔥",
            cls.MEDIUM: "⭐",
            cls.LOW: "📝",
            cls.OPTIONAL: "💡",
            cls.SOMEDAY: "💭"
        }
        return emojis.get(priority, "📝")

# Task categories constants
class TaskCategory:
    WORK = "work"
    HEALTH = "health"
    LEARNING = "learning"
    PERSONAL = "personal"
    FAMILY = "family"
    SOCIAL = "social"
    CHORES = "chores"
    FINANCE = "finance"
    GENERAL = "general"
    
    @classmethod
    def get_all(cls) -> List[str]:
        return [
            cls.WORK, cls.HEALTH, cls.LEARNING, cls.PERSONAL,
            cls.FAMILY, cls.SOCIAL, cls.CHORES, cls.FINANCE, cls.GENERAL
        ]
    
    @classmethod
    def get_emoji(cls, category: str) -> str:
        emojis = {
            cls.WORK: "💼",
            cls.HEALTH: "🏃",
            cls.LEARNING: "📚",
            cls.PERSONAL: "🧘",
            cls.FAMILY: "👨‍👩‍👧‍👦",
            cls.SOCIAL: "👥",
            cls.CHORES: "🏠",
            cls.FINANCE: "💰",
            cls.GENERAL: "📝"
        }
        return emojis.get(category, "📝") 