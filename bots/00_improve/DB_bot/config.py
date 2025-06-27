"""
S-Bahn Configuration (Schwaikheim ↔ Stuttgart Feuersee)
"""
import os
from dotenv import load_dotenv

# Load environment from parent directory  
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

class Config:
    """S-Bahn monitoring configuration."""
    
    # Discord & API Keys
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
    DB_API_KEY = os.getenv("DB_APICLIENT", "")
    
    # Station IDs
    SCHWAIKHEIM_ID = "8005462"
    FEUERSEE_ID = "8002058"
    
    # Route Names
    ROUTE_1_NAME = "Schwaikheim → Stuttgart Feuersee"
    ROUTE_2_NAME = "Stuttgart Feuersee → Schwaikheim"
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        return bool(cls.DISCORD_TOKEN)
    
    @classmethod
    def get_route_config(cls, route_number):
        """Get route configuration for route 1 or 2."""
        if route_number == 1:
            return {
                "origin": cls.SCHWAIKHEIM_ID,
                "destination": cls.FEUERSEE_ID,
                "name": cls.ROUTE_1_NAME
            }
        elif route_number == 2:
            return {
                "origin": cls.FEUERSEE_ID,
                "destination": cls.SCHWAIKHEIM_ID,
                "name": cls.ROUTE_2_NAME
            }
        else:
            raise ValueError(f"Invalid route number: {route_number}")

# Global config instance
config = Config()

if __name__ == "__main__":
    print(f"Config validation: {config.validate()}")
    print(f"Route 1: {config.get_route_config(1)}")
    print(f"Route 2: {config.get_route_config(2)}") 