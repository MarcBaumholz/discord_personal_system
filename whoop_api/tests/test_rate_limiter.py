"""
Tests for rate limiting implementation.
"""

import pytest
import time
from unittest.mock import patch
from src.rate_limiter import WhoopRateLimiter


class TestWhoopRateLimiter:
    """Test cases for WhoopRateLimiter class."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = WhoopRateLimiter(rpm=100, rpd=10000)
        
        assert limiter.rpm == 100
        assert limiter.rpd == 10000
        assert len(limiter._minute_requests) == 0
        assert len(limiter._day_requests) == 0
    
    def test_can_make_request_initial(self):
        """Test can make request when no requests made yet."""
        limiter = WhoopRateLimiter(rpm=100, rpd=10000)
        
        assert limiter.can_make_request() is True
    
    def test_can_make_request_within_limits(self):
        """Test can make request within limits."""
        limiter = WhoopRateLimiter(rpm=5, rpd=100)
        
        # Make 4 requests (within limit of 5)
        for _ in range(4):
            limiter.wait_if_needed()
        
        assert limiter.can_make_request() is True
    
    def test_can_make_request_exceeds_minute_limit(self):
        """Test can make request when minute limit exceeded."""
        limiter = WhoopRateLimiter(rpm=3, rpd=100)
        
        # Make 3 requests (at limit)
        for _ in range(3):
            limiter.wait_if_needed()
        
        assert limiter.can_make_request() is False
    
    def test_can_make_request_exceeds_day_limit(self):
        """Test can make request when day limit exceeded."""
        limiter = WhoopRateLimiter(rpm=100, rpd=3)
        
        # Make 3 requests (at day limit)
        for _ in range(3):
            limiter.wait_if_needed()
        
        assert limiter.can_make_request() is False
    
    def test_wait_if_needed_within_limits(self):
        """Test wait if needed when within limits."""
        limiter = WhoopRateLimiter(rpm=100, rpd=10000)
        
        wait_time = limiter.wait_if_needed()
        assert wait_time == 0
    
    @patch('time.sleep')
    def test_wait_if_needed_exceeds_minute_limit(self, mock_sleep):
        """Test wait if needed when minute limit exceeded."""
        limiter = WhoopRateLimiter(rpm=2, rpd=100)
        
        # Make 2 requests to reach limit
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        
        # This should trigger a wait
        limiter.wait_if_needed()
        
        # Should have called sleep
        mock_sleep.assert_called()
    
    def test_get_status_initial(self):
        """Test get status when no requests made."""
        limiter = WhoopRateLimiter(rpm=100, rpd=10000)
        
        status = limiter.get_status()
        
        assert status["minute_requests"] == 0
        assert status["minute_limit"] == 100
        assert status["day_requests"] == 0
        assert status["day_limit"] == 10000
        assert status["can_make_request"] is True
    
    def test_get_status_after_requests(self):
        """Test get status after making requests."""
        limiter = WhoopRateLimiter(rpm=100, rpd=10000)
        
        # Make 5 requests
        for _ in range(5):
            limiter.wait_if_needed()
        
        status = limiter.get_status()
        
        assert status["minute_requests"] == 5
        assert status["day_requests"] == 5
        assert status["can_make_request"] is True
    
    def test_get_status_at_limit(self):
        """Test get status when at limit."""
        limiter = WhoopRateLimiter(rpm=3, rpd=100)
        
        # Make 3 requests (at limit)
        for _ in range(3):
            limiter.wait_if_needed()
        
        status = limiter.get_status()
        
        assert status["minute_requests"] == 3
        assert status["can_make_request"] is False
    
    @patch('time.time')
    def test_cleanup_old_requests(self, mock_time):
        """Test cleanup of old requests."""
        limiter = WhoopRateLimiter(rpm=100, rpd=10000)
        
        # Mock time progression
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Add some old requests
        limiter._minute_requests.extend([900.0, 950.0, 1000.0])  # 100s, 50s, 0s old
        limiter._day_requests.extend([100.0, 500.0, 1000.0])  # 900s, 500s, 0s old
        
        # Mock time to be 70 seconds later (oldest minute request is 100s old)
        mock_time.return_value = current_time + 70
        
        # Trigger cleanup
        limiter._cleanup_old_requests()
        
        # Should have removed the 100s old request from minute_requests
        assert len(limiter._minute_requests) == 2
        assert 900.0 not in limiter._minute_requests
        
        # Day requests should still be there (all less than 1 day old)
        assert len(limiter._day_requests) == 3
