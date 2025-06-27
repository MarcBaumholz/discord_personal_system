"""Configuration management for Health Bot."""
import os
from typing import Optional
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)


class Config:
    """Configuration settings for the Health Bot."""
    
    # Discord settings
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    HEALTH_CHANNEL_ID: int = int(os.getenv("HEALTH_CHANNEL_ID", "0"))
    
    # Oura API settings
    OURA_ACCESS_TOKEN: str = os.getenv("OURA_ACCESS_TOKEN", "")
    
    # Health bot settings
    DAILY_SCHEDULE_TIME: str = os.getenv("DAILY_SCHEDULE_TIME", "08:00")
    TARGET_CALORIES: int = int(os.getenv("TARGET_CALORIES", "2200"))
    TARGET_ACTIVE_CALORIES: int = int(os.getenv("TARGET_ACTIVE_CALORIES", "450"))
    TARGET_STEPS: int = int(os.getenv("TARGET_STEPS", "8000"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        required_fields = [
            (cls.DISCORD_TOKEN, "DISCORD_TOKEN"),
            (cls.HEALTH_CHANNEL_ID, "HEALTH_CHANNEL_ID"),
            (cls.OURA_ACCESS_TOKEN, "OURA_ACCESS_TOKEN")
        ]
        
        for value, name in required_fields:
            if not value or (isinstance(value, int) and value == 0):
                print(f"Missing required configuration: {name}")
                return False
        
        return True 