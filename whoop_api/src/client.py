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
    
    def __init__(self, config: WhoopConfig, oauth: Optional[WhoopOAuth] = None):
        """Initialize WHOOP API client."""
        self.config = config
        self.oauth = oauth or WhoopOAuth(config)
        self.rate_limiter = WhoopRateLimiter(
            rpm=config.rate_limit_rpm,
            rpd=config.rate_limit_rpd
        )
        
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
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to WHOOP API with rate limiting."""
        # Wait for rate limit if needed
        self.rate_limiter.wait_if_needed()
        
        # Get valid access token
        try:
            access_token = self.oauth.get_valid_access_token()
        except WhoopOAuthError as e:
            raise WhoopAuthenticationError(f"Authentication failed: {e}")
        
        # Prepare request
        url = f"{self.config.api_base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
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
