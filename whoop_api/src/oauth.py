"""
OAuth 2.0 implementation for WHOOP API authentication.
Handles authorization code flow, token management, and refresh.
"""

import json
import time
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode, parse_qs, urlparse

from .config import WhoopConfig
from .models import WhoopTokenResponse, WhoopError


class WhoopOAuth:
    """OAuth 2.0 client for WHOOP API authentication."""
    
    def __init__(self, config: WhoopConfig):
        """Initialize OAuth client with configuration."""
        self.config = config
        self.config.validate()
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    def get_authorization_url(self, state: Optional[str] = None, scopes: Optional[list] = None) -> str:
        """Generate OAuth authorization URL."""
        if state is None:
            state = secrets.token_urlsafe(32)
        
        return self.config.get_auth_url(state=state, scopes=scopes)
    
    def exchange_code_for_token(self, authorization_code: str) -> WhoopTokenResponse:
        """Exchange authorization code for access token."""
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "redirect_uri": self.config.redirect_uri,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        try:
            response = requests.post(
                self.config.token_url,
                data=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            token_response = WhoopTokenResponse(**token_data)
            
            # Store tokens for future use
            self._access_token = token_response.access_token
            self._refresh_token = token_response.refresh_token
            self._token_expires_at = datetime.now() + timedelta(seconds=token_response.expires_in)
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            raise WhoopOAuthError(f"Failed to exchange code for token: {e}")
        except Exception as e:
            raise WhoopOAuthError(f"Invalid token response: {e}")
    
    def refresh_access_token(self) -> WhoopTokenResponse:
        """Refresh access token using refresh token."""
        if not self._refresh_token:
            raise WhoopOAuthError("No refresh token available")
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        try:
            response = requests.post(
                self.config.token_url,
                data=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            token_response = WhoopTokenResponse(**token_data)
            
            # Update stored tokens
            self._access_token = token_response.access_token
            if token_response.refresh_token:
                self._refresh_token = token_response.refresh_token
            self._token_expires_at = datetime.now() + timedelta(seconds=token_response.expires_in)
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            raise WhoopOAuthError(f"Failed to refresh token: {e}")
        except Exception as e:
            raise WhoopOAuthError(f"Invalid refresh response: {e}")
    
    def get_valid_access_token(self) -> str:
        """Get valid access token, refreshing if necessary."""
        if not self._access_token:
            raise WhoopOAuthError("No access token available. Please authenticate first.")
        
        # Check if token is expired or will expire soon (within 5 minutes)
        if self._token_expires_at and datetime.now() >= (self._token_expires_at - timedelta(minutes=5)):
            try:
                self.refresh_access_token()
            except WhoopOAuthError:
                # If refresh fails, we need to re-authenticate
                raise WhoopOAuthError("Token expired and refresh failed. Please re-authenticate.")
        
        return self._access_token
    
    def set_tokens(self, access_token: str, refresh_token: Optional[str] = None, expires_in: Optional[int] = None):
        """Manually set tokens (useful for loading from storage)."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        if expires_in:
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get current token information."""
        return {
            "has_access_token": self._access_token is not None,
            "has_refresh_token": self._refresh_token is not None,
            "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
            "is_expired": self._token_expires_at is not None and datetime.now() >= self._token_expires_at,
        }
    
    def revoke_tokens(self):
        """Revoke current tokens."""
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None


class WhoopOAuthError(Exception):
    """OAuth-specific error for WHOOP API."""
    pass


def extract_code_from_url(url: str) -> tuple[str, Optional[str]]:
    """Extract authorization code and state from callback URL."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    code = query_params.get("code", [None])[0]
    state = query_params.get("state", [None])[0]
    
    if not code:
        raise ValueError("No authorization code found in URL")
    
    return code, state
