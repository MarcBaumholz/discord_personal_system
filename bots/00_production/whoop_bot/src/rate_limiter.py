"""
Rate limiting implementation for WHOOP API.
Handles requests per minute and per day limits.
"""

import time
from datetime import datetime, timedelta
from typing import Optional
from collections import deque
import threading


class WhoopRateLimiter:
    """Rate limiter for WHOOP API requests."""
    
    def __init__(self, rpm: int = 100, rpd: int = 10000):
        """Initialize rate limiter with requests per minute and per day limits."""
        self.rpm = rpm
        self.rpd = rpd
        
        # Thread-safe request tracking
        self._lock = threading.Lock()
        self._minute_requests = deque()
        self._day_requests = deque()
        
        # Cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_old_requests, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_old_requests(self):
        """Background thread to clean up old request timestamps."""
        while True:
            time.sleep(60)  # Run every minute
            with self._lock:
                now = time.time()
                
                # Remove requests older than 1 minute
                while self._minute_requests and self._minute_requests[0] < now - 60:
                    self._minute_requests.popleft()
                
                # Remove requests older than 1 day
                while self._day_requests and self._day_requests[0] < now - 86400:
                    self._day_requests.popleft()
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limits."""
        with self._lock:
            now = time.time()
            
            # Check minute limit
            minute_requests = len([t for t in self._minute_requests if t > now - 60])
            if minute_requests >= self.rpm:
                return False
            
            # Check day limit
            day_requests = len([t for t in self._day_requests if t > now - 86400])
            if day_requests >= self.rpd:
                return False
            
            return True
    
    def wait_if_needed(self) -> float:
        """Wait if necessary to respect rate limits. Returns wait time in seconds."""
        with self._lock:
            now = time.time()
            
            # Check minute limit
            minute_requests = [t for t in self._minute_requests if t > now - 60]
            if len(minute_requests) >= self.rpm:
                # Wait until oldest request in current minute expires
                wait_time = 60 - (now - minute_requests[0])
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = time.time()
            
            # Check day limit
            day_requests = [t for t in self._day_requests if t > now - 86400]
            if len(day_requests) >= self.rpd:
                # Wait until oldest request in current day expires
                wait_time = 86400 - (now - day_requests[0])
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = time.time()
            
            # Record this request
            self._minute_requests.append(now)
            self._day_requests.append(now)
            
            return 0
    
    def get_status(self) -> dict:
        """Get current rate limiting status."""
        with self._lock:
            now = time.time()
            
            minute_requests = len([t for t in self._minute_requests if t > now - 60])
            day_requests = len([t for t in self._day_requests if t > now - 86400])
            
            return {
                "minute_requests": minute_requests,
                "minute_limit": self.rpm,
                "day_requests": day_requests,
                "day_limit": self.rpd,
                "can_make_request": minute_requests < self.rpm and day_requests < self.rpd,
            }
