"""
Database management for Deutsche Bahn Discord Bot.
"""
import aiosqlite
import structlog
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from config import config

logger = structlog.get_logger()

@dataclass
class TrainConnection:
    """Represents a saved train connection."""
    id: Optional[int] = None
    user_id: int = 0
    from_station: str = ""
    to_station: str = ""
    alias: Optional[str] = None
    created_at: Optional[datetime] = None

class DatabaseManager:
    """Manages all database operations for the bot."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_URL
        
    async def initialize(self) -> bool:
        """Initialize the database with required tables."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await self._create_tables(db)
                await db.commit()
                logger.info("Database initialized successfully", db_path=self.db_path)
                return True
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            return False
    
    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        """Create required database tables."""
        
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                discord_username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Train connections table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS train_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                from_station TEXT NOT NULL,
                to_station TEXT NOT NULL,
                alias TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, from_station, to_station)
            )
        """)
        
        # Create indexes for better performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_connections_user ON train_connections(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)")
    
    async def add_user(self, user_id: int, username: str = None) -> bool:
        """Add or update a user in the database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO users (user_id, discord_username, last_active)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, username))
                await db.commit()
                logger.info("User added/updated", user_id=user_id, username=username)
                return True
        except Exception as e:
            logger.error("Failed to add user", user_id=user_id, error=str(e))
            return False
    
    async def add_connection(self, user_id: int, from_station: str, to_station: str, alias: str = None) -> bool:
        """Add a train connection for a user."""
        try:
            # Check if user has reached max connections
            connections = await self.get_user_connections(user_id)
            if len(connections) >= config.MAX_CONNECTIONS_PER_USER:
                logger.warning("User has reached max connections", 
                             user_id=user_id, 
                             current_count=len(connections),
                             max_allowed=config.MAX_CONNECTIONS_PER_USER)
                return False
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO train_connections (user_id, from_station, to_station, alias)
                    VALUES (?, ?, ?, ?)
                """, (user_id, from_station, to_station, alias))
                await db.commit()
                logger.info("Connection added", 
                          user_id=user_id, 
                          from_station=from_station, 
                          to_station=to_station)
                return True
                
        except aiosqlite.IntegrityError:
            logger.warning("Connection already exists", 
                         user_id=user_id, 
                         from_station=from_station, 
                         to_station=to_station)
            return False
        except Exception as e:
            logger.error("Failed to add connection", user_id=user_id, error=str(e))
            return False
    
    async def get_user_connections(self, user_id: int) -> List[TrainConnection]:
        """Get all saved connections for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT id, user_id, from_station, to_station, alias, created_at
                    FROM train_connections
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                rows = await cursor.fetchall()
                
                connections = []
                for row in rows:
                    connections.append(TrainConnection(
                        id=row['id'],
                        user_id=row['user_id'],
                        from_station=row['from_station'],
                        to_station=row['to_station'],
                        alias=row['alias'],
                        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                    ))
                
                return connections
                
        except Exception as e:
            logger.error("Failed to get user connections", user_id=user_id, error=str(e))
            return []
    
    async def remove_connection(self, user_id: int, connection_id: int) -> bool:
        """Remove a specific connection for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    DELETE FROM train_connections
                    WHERE id = ? AND user_id = ?
                """, (connection_id, user_id))
                await db.commit()
                
                if cursor.rowcount > 0:
                    logger.info("Connection removed", user_id=user_id, connection_id=connection_id)
                    return True
                else:
                    logger.warning("Connection not found or not owned by user", 
                                 user_id=user_id, connection_id=connection_id)
                    return False
                    
        except Exception as e:
            logger.error("Failed to remove connection", 
                        user_id=user_id, connection_id=connection_id, error=str(e))
            return False
    
    async def get_connection_by_id(self, connection_id: int, user_id: int) -> Optional[TrainConnection]:
        """Get a specific connection by ID for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT id, user_id, from_station, to_station, alias, created_at
                    FROM train_connections
                    WHERE id = ? AND user_id = ?
                """, (connection_id, user_id))
                row = await cursor.fetchone()
                
                if row:
                    return TrainConnection(
                        id=row['id'],
                        user_id=row['user_id'],
                        from_station=row['from_station'],
                        to_station=row['to_station'],
                        alias=row['alias'],
                        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                    )
                return None
                
        except Exception as e:
            logger.error("Failed to get connection by ID", 
                        connection_id=connection_id, user_id=user_id, error=str(e))
            return None
    
    async def update_user_activity(self, user_id: int) -> bool:
        """Update the last activity timestamp for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE users 
                    SET last_active = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                """, (user_id,))
                await db.commit()
                return True
        except Exception as e:
            logger.error("Failed to update user activity", user_id=user_id, error=str(e))
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Count users
                cursor = await db.execute("SELECT COUNT(*) FROM users")
                user_count = (await cursor.fetchone())[0]
                
                # Count connections
                cursor = await db.execute("SELECT COUNT(*) FROM train_connections")
                connection_count = (await cursor.fetchone())[0]
                
                # Count active users (last 30 days)
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE last_active > datetime('now', '-30 days')
                """)
                active_users = (await cursor.fetchone())[0]
                
                return {
                    "total_users": user_count,
                    "total_connections": connection_count,
                    "active_users_30d": active_users
                }
                
        except Exception as e:
            logger.error("Failed to get database stats", error=str(e))
            return {}

# Create a global database manager instance
db_manager = DatabaseManager()