"""
Tests for WHOOP API client.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import requests

from src.config import WhoopConfig
from src.oauth import WhoopOAuth
from src.client import WhoopClient, WhoopAPIError, WhoopRateLimitError, WhoopAuthenticationError
from src.models import WhoopUser, WhoopCycle, WhoopSleep, WhoopRecovery, WhoopWorkout


class TestWhoopClient:
    """Test cases for WhoopClient class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return WhoopConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback"
        )
    
    @pytest.fixture
    def oauth(self, config):
        """Create mock OAuth client."""
        oauth = Mock(spec=WhoopOAuth)
        oauth.get_valid_access_token.return_value = "test_access_token"
        return oauth
    
    @pytest.fixture
    def client(self, config, oauth):
        """Create WHOOP client."""
        return WhoopClient(config, oauth)
    
    def test_client_initialization(self, config, oauth):
        """Test client initialization."""
        client = WhoopClient(config, oauth)
        
        assert client.config == config
        assert client.oauth == oauth
        assert client.rate_limiter is not None
        assert client.session is not None
    
    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request, client):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"user_id": 123, "email": "test@example.com"}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        result = client._make_request("GET", "/test")
        
        assert result == {"user_id": 123, "email": "test@example.com"}
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_make_request_rate_limit(self, mock_request, client):
        """Test API request with rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_request.return_value = mock_response
        
        with pytest.raises(WhoopRateLimitError, match="Rate limit exceeded"):
            client._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_make_request_authentication_error(self, mock_request, client):
        """Test API request with authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        with pytest.raises(WhoopAuthenticationError, match="Invalid or expired access token"):
            client._make_request("GET", "/test")
    
    @patch('requests.Session.request')
    def test_make_request_network_error(self, mock_request, client):
        """Test API request with network error."""
        mock_request.side_effect = requests.exceptions.RequestException("Network error")
        
        with pytest.raises(WhoopAPIError, match="Request failed"):
            client._make_request("GET", "/test")
    
    @patch.object(WhoopClient, '_make_request')
    def test_get_user_profile(self, mock_request, client):
        """Test getting user profile."""
        mock_request.return_value = {
            "user_id": 123,
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        result = client.get_user_profile()
        
        assert isinstance(result, WhoopUser)
        assert result.user_id == 123
        assert result.email == "test@example.com"
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        mock_request.assert_called_once_with("GET", "/developer/v2/user/profile/basic")
    
    @patch.object(WhoopClient, '_make_request')
    def test_get_cycles(self, mock_request, client):
        """Test getting cycles."""
        mock_request.return_value = {
            "records": [
                {
                    "id": 1,
                    "user_id": 123,
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-01T23:59:59Z",
                    "timezone_offset": "+00:00"
                }
            ],
            "next_token": None
        }
        
        result = client.get_cycles()
        
        assert isinstance(result.records, list)
        assert len(result.records) == 1
        assert result.next_token is None
        mock_request.assert_called_once()
    
    @patch.object(WhoopClient, '_make_request')
    def test_get_cycles_with_params(self, mock_request, client):
        """Test getting cycles with parameters."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        
        mock_request.return_value = {"records": [], "next_token": None}
        
        client.get_cycles(start=start, end=end, limit=50, next_token="token123")
        
        mock_request.assert_called_once_with(
            "GET", 
            "/developer/v2/cycle",
            params={
                "start": "2024-01-01T00:00:00",
                "end": "2024-01-31T00:00:00",
                "limit": 50,
                "next_token": "token123"
            }
        )
    
    @patch.object(WhoopClient, '_make_request')
    def test_get_cycle_by_id(self, mock_request, client):
        """Test getting specific cycle by ID."""
        mock_request.return_value = {
            "id": 1,
            "user_id": 123,
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-01T23:59:59Z",
            "timezone_offset": "+00:00"
        }
        
        result = client.get_cycle(1)
        
        assert isinstance(result, WhoopCycle)
        assert result.id == 1
        mock_request.assert_called_once_with("GET", "/developer/v2/cycle/1")
    
    @patch.object(WhoopClient, '_make_request')
    def test_get_sleep_data(self, mock_request, client):
        """Test getting sleep data."""
        mock_request.return_value = {
            "records": [
                {
                    "id": 1,
                    "user_id": 123,
                    "start": "2024-01-01T22:00:00Z",
                    "end": "2024-01-02T06:00:00Z",
                    "timezone_offset": "+00:00",
                    "nap": False
                }
            ],
            "next_token": None
        }
        
        result = client.get_sleep_data()
        
        assert isinstance(result.records, list)
        assert len(result.records) == 1
        mock_request.assert_called_once()
    
    @patch.object(WhoopClient, '_make_request')
    def test_get_recovery_data(self, mock_request, client):
        """Test getting recovery data."""
        mock_request.return_value = {
            "records": [
                {
                    "id": 1,
                    "user_id": 123,
                    "cycle_id": 1,
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-01T23:59:59Z",
                    "timezone_offset": "+00:00",
                    "score": 75.0
                }
            ],
            "next_token": None
        }
        
        result = client.get_recovery_data()
        
        assert isinstance(result.records, list)
        assert len(result.records) == 1
        mock_request.assert_called_once()
    
    @patch.object(WhoopClient, '_make_request')
    def test_get_workouts(self, mock_request, client):
        """Test getting workouts."""
        mock_request.return_value = {
            "records": [
                {
                    "id": 1,
                    "user_id": 123,
                    "start": "2024-01-01T10:00:00Z",
                    "end": "2024-01-01T11:00:00Z",
                    "timezone_offset": "+00:00",
                    "sport_id": 1,
                    "sport_name": "Running"
                }
            ],
            "next_token": None
        }
        
        result = client.get_workouts()
        
        assert isinstance(result.records, list)
        assert len(result.records) == 1
        mock_request.assert_called_once()
    
    @patch.object(WhoopClient, 'get_cycles')
    def test_get_all_cycles(self, mock_get_cycles, client):
        """Test getting all cycles with pagination."""
        # Mock first page
        mock_get_cycles.side_effect = [
            type('Response', (), {
                'records': [{'id': 1, 'user_id': 123, 'start': '2024-01-01T00:00:00Z', 
                           'end': '2024-01-01T23:59:59Z', 'timezone_offset': '+00:00'}],
                'next_token': 'token123'
            })(),
            type('Response', (), {
                'records': [{'id': 2, 'user_id': 123, 'start': '2024-01-02T00:00:00Z', 
                           'end': '2024-01-02T23:59:59Z', 'timezone_offset': '+00:00'}],
                'next_token': None
            })()
        ]
        
        result = client.get_all_cycles()
        
        assert len(result) == 2
        assert all(isinstance(cycle, WhoopCycle) for cycle in result)
        assert mock_get_cycles.call_count == 2
    
    def test_get_rate_limit_status(self, client):
        """Test getting rate limit status."""
        status = client.get_rate_limit_status()
        
        assert "minute_requests" in status
        assert "minute_limit" in status
        assert "day_requests" in status
        assert "day_limit" in status
        assert "can_make_request" in status
    
    @patch.object(WhoopClient, 'get_user_profile')
    def test_test_connection_success(self, mock_get_profile, client):
        """Test successful connection test."""
        mock_get_profile.return_value = WhoopUser(user_id=123, email="test@example.com")
        
        result = client.test_connection()
        
        assert result is True
        mock_get_profile.assert_called_once()
    
    @patch.object(WhoopClient, 'get_user_profile')
    def test_test_connection_failure(self, mock_get_profile, client):
        """Test failed connection test."""
        mock_get_profile.side_effect = Exception("Connection failed")
        
        result = client.test_connection()
        
        assert result is False
        mock_get_profile.assert_called_once()
