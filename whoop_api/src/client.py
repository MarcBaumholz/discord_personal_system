"""
Main WHOOP API client with rate limiting and error handling.
Provides access to all WHOOP v2 endpoints.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import WhoopConfig
from .oauth import WhoopOAuth, WhoopOAuthError
from .rate_limiter import WhoopRateLimiter
from .token_manager import TokenManager
from .models import (
    WhoopUser, WhoopBodyMeasurement, WhoopCycle, WhoopSleep, 
    WhoopRecovery, WhoopWorkout, WhoopPaginatedResponse, WhoopError
)


class WhoopAPIError(Exception):
    """Base exception for WHOOP API errors."""
    pass


class WhoopRateLimitError(WhoopAPIError):
    """Rate limit exceeded error."""
    pass


class WhoopAuthenticationError(WhoopAPIError):
    """Authentication error."""
    pass


class WhoopClient:
    """Main client for WHOOP API v2."""
    
    def __init__(self, config: WhoopConfig, oauth: Optional[WhoopOAuth] = None, token_manager: Optional[TokenManager] = None):
        """Initialize WHOOP API client."""
        self.config = config
        self.oauth = oauth or WhoopOAuth(config)
        self.token_manager = token_manager or TokenManager()
        self.rate_limiter = WhoopRateLimiter(
            rpm=config.rate_limit_rpm,
            rpd=config.rate_limit_rpd
        )
        self._current_tokens = None
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers, using saved tokens if available."""
        # Try to get valid tokens from token manager
        if not self._current_tokens:
            self._current_tokens = self.token_manager.get_valid_tokens()
        
        if self._current_tokens:
            return {
                'Authorization': f"{self._current_tokens['token_type']} {self._current_tokens['access_token']}"
            }
        
        # If no valid tokens, we need to authenticate
        raise WhoopAuthenticationError("No valid tokens available. Please authenticate first.")
    
    def authenticate_with_callback(self, callback_url: str) -> bool:
        """Authenticate using a callback URL and save tokens."""
        try:
            from .oauth import extract_code_from_url
            code, state = extract_code_from_url(callback_url)
            token_response = self.oauth.exchange_code_for_token(code)
            
            # Convert token response to dictionary for saving
            token_dict = {
                'access_token': token_response.access_token,
                'refresh_token': token_response.refresh_token,
                'expires_in': token_response.expires_in,
                'token_type': token_response.token_type,
                'scope': token_response.scope
            }
            
            # Save tokens for future use
            self.token_manager.save_tokens(token_dict)
            self._current_tokens = {
                'access_token': token_response.access_token,
                'refresh_token': token_response.refresh_token,
                'token_type': token_response.token_type,
                'scope': token_response.scope
            }
            
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication tokens."""
        return self.token_manager.has_tokens()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to WHOOP API with rate limiting."""
        # Wait for rate limit if needed
        self.rate_limiter.wait_if_needed()
        
        # Get authentication headers
        try:
            headers = self._get_auth_headers()
            headers['Accept'] = 'application/json'
            headers['Content-Type'] = 'application/json'
        except WhoopAuthenticationError:
            raise WhoopAuthenticationError("Please authenticate first using authenticate_with_callback()")
        
        # Prepare request
        url = f"{self.config.api_base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                time.sleep(retry_after)
                raise WhoopRateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
            
            # Handle authentication errors
            if response.status_code == 401:
                raise WhoopAuthenticationError("Invalid or expired access token")
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise WhoopAPIError(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            raise WhoopAPIError(f"Invalid JSON response: {e}")
    
    def get_user_profile(self) -> WhoopUser:
        """Get basic user profile."""
        data = self._make_request("GET", "/developer/v2/user/profile/basic")
        return WhoopUser(**data)
    
    def get_body_measurements(self) -> WhoopBodyMeasurement:
        """Get user body measurements."""
        data = self._make_request("GET", "/developer/v2/user/profile/body_measurement")
        return WhoopBodyMeasurement(**data)
    
    def get_cycles(self, start: Optional[datetime] = None, end: Optional[datetime] = None,
                   limit: int = 25, next_token: Optional[str] = None) -> WhoopPaginatedResponse:
        """Get user cycles (physiological days)."""
        params = {"limit": limit}
        
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        if next_token:
            params["next_token"] = next_token
        
        data = self._make_request("GET", "/developer/v2/cycle", params=params)
        return WhoopPaginatedResponse(**data)
    
    def get_cycle(self, cycle_id: int) -> WhoopCycle:
        """Get specific cycle by ID."""
        data = self._make_request("GET", f"/developer/v2/cycle/{cycle_id}")
        return WhoopCycle(**data)
    
    def get_sleep_data(self, start: Optional[datetime] = None, end: Optional[datetime] = None,
                       limit: int = 25, next_token: Optional[str] = None) -> WhoopPaginatedResponse:
        """Get user sleep data."""
        params = {"limit": limit}
        
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        if next_token:
            params["next_token"] = next_token
        
        data = self._make_request("GET", "/developer/v2/activity/sleep", params=params)
        return WhoopPaginatedResponse(**data)
    
    def get_sleep(self, sleep_id: int) -> WhoopSleep:
        """Get specific sleep record by ID."""
        data = self._make_request("GET", f"/developer/v2/activity/sleep/{sleep_id}")
        return WhoopSleep(**data)
    
    def get_recovery_data(self, start: Optional[datetime] = None, end: Optional[datetime] = None,
                          limit: int = 25, next_token: Optional[str] = None) -> WhoopPaginatedResponse:
        """Get user recovery data."""
        params = {"limit": limit}
        
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        if next_token:
            params["next_token"] = next_token
        
        data = self._make_request("GET", "/developer/v2/recovery", params=params)
        return WhoopPaginatedResponse(**data)
    
    def get_recovery(self, recovery_id: int) -> WhoopRecovery:
        """Get specific recovery record by ID."""
        data = self._make_request("GET", f"/developer/v2/recovery/{recovery_id}")
        return WhoopRecovery(**data)
    
    def get_workouts(self, start: Optional[datetime] = None, end: Optional[datetime] = None,
                     limit: int = 25, next_token: Optional[str] = None) -> WhoopPaginatedResponse:
        """Get user workout data."""
        params = {"limit": limit}
        
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        if next_token:
            params["next_token"] = next_token
        
        data = self._make_request("GET", "/developer/v2/activity/workout", params=params)
        return WhoopPaginatedResponse(**data)
    
    def get_workout(self, workout_id: int) -> WhoopWorkout:
        """Get specific workout by ID."""
        data = self._make_request("GET", f"/developer/v2/activity/workout/{workout_id}")
        return WhoopWorkout(**data)
    
    def get_all_cycles(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[WhoopCycle]:
        """Get all cycles with automatic pagination."""
        cycles = []
        next_token = None
        
        while True:
            response = self.get_cycles(start=start, end=end, next_token=next_token)
            cycles.extend([WhoopCycle(**record) for record in response.records])
            
            if not response.next_token:
                break
            next_token = response.next_token
        
        return cycles
    
    def get_all_sleep_data(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[WhoopSleep]:
        """Get all sleep data with automatic pagination."""
        sleep_records = []
        next_token = None
        
        while True:
            response = self.get_sleep_data(start=start, end=end, next_token=next_token)
            sleep_records.extend([WhoopSleep(**record) for record in response.records])
            
            if not response.next_token:
                break
            next_token = response.next_token
        
        return sleep_records
    
    def get_all_recovery_data(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[WhoopRecovery]:
        """Get all recovery data with automatic pagination."""
        recovery_records = []
        next_token = None
        
        while True:
            response = self.get_recovery_data(start=start, end=end, next_token=next_token)
            recovery_records.extend([WhoopRecovery(**record) for record in response.records])
            
            if not response.next_token:
                break
            next_token = response.next_token
        
        return recovery_records
    
    def get_all_workouts(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[WhoopWorkout]:
        """Get all workouts with automatic pagination."""
        workouts = []
        next_token = None
        
        while True:
            response = self.get_workouts(start=start, end=end, next_token=next_token)
            workouts.extend([WhoopWorkout(**record) for record in response.records])
            
            if not response.next_token:
                break
            next_token = response.next_token
        
        return workouts
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limiting status."""
        return self.rate_limiter.get_status()
    
    def test_connection(self) -> bool:
        """Test API connection and authentication."""
        try:
            self.get_user_profile()
            return True
        except Exception:
            return False
