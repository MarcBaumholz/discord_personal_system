"""
Configuration management for WHOOP API integration.
Handles environment variables, OAuth settings, and API configuration.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class WhoopConfig:
    """Configuration class for WHOOP API integration."""
    
    # OAuth 2.0 Credentials
    client_id: str
    client_secret: str
    redirect_uri: str
    
    # API URLs
    api_base_url: str = "https://api.prod.whoop.com"
    auth_url: str = "https://api.prod.whoop.com/oauth/oauth2/auth"
    token_url: str = "https://api.prod.whoop.com/oauth/oauth2/token"
    
    # Rate Limiting
    rate_limit_rpm: int = 100
    rate_limit_rpd: int = 10000
    
    # Database
    database_url: str = "sqlite:///whoop_data.db"
    
    # Webhook
    webhook_secret: Optional[str] = None
    webhook_port: int = 8080
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Cache
    cache_ttl_seconds: int = 300
    redis_url: Optional[str] = None
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "WhoopConfig":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        return cls(
            client_id=os.getenv("WHOOP_CLIENT_ID", ""),
            client_secret=os.getenv("WHOOP_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8080/callback"),
            api_base_url=os.getenv("WHOOP_API_BASE_URL", "https://api.prod.whoop.com"),
            auth_url=os.getenv("WHOOP_AUTH_URL", "https://api.prod.whoop.com/oauth/oauth2/auth"),
            token_url=os.getenv("WHOOP_TOKEN_URL", "https://api.prod.whoop.com/oauth/oauth2/token"),
            rate_limit_rpm=int(os.getenv("WHOOP_RATE_LIMIT_RPM", "100")),
            rate_limit_rpd=int(os.getenv("WHOOP_RATE_LIMIT_RPD", "10000")),
            database_url=os.getenv("DATABASE_URL", "sqlite:///whoop_data.db"),
            webhook_secret=os.getenv("WEBHOOK_SECRET"),
            webhook_port=int(os.getenv("WEBHOOK_PORT", "8080")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
            redis_url=os.getenv("REDIS_URL"),
        )
    
    def validate(self) -> None:
        """Validate configuration parameters."""
        if not self.client_id:
            raise ValueError("WHOOP_CLIENT_ID is required")
        if not self.client_secret:
            raise ValueError("WHOOP_CLIENT_SECRET is required")
        if not self.redirect_uri:
            raise ValueError("WHOOP_REDIRECT_URI is required")
        
        if self.rate_limit_rpm <= 0:
            raise ValueError("WHOOP_RATE_LIMIT_RPM must be positive")
        if self.rate_limit_rpd <= 0:
            raise ValueError("WHOOP_RATE_LIMIT_RPD must be positive")
        if self.cache_ttl_seconds <= 0:
            raise ValueError("CACHE_TTL_SECONDS must be positive")
    
    def get_auth_url(self, state: Optional[str] = None, scopes: Optional[list] = None) -> str:
        """Generate OAuth authorization URL."""
        if scopes is None:
            scopes = [
                "read:profile",
                "read:body_measurement", 
                "read:cycles",
                "read:sleep",
                "read:recovery",
                "read:workout",
                "offline"
            ]
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
