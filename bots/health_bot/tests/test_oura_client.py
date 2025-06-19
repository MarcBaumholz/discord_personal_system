"""Unit tests for Oura API client."""
import pytest
from unittest.mock import Mock, patch
import requests
from datetime import datetime, timedelta

from oura_client import OuraClient, HealthData


class TestOuraClient:
    """Test cases for OuraClient."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = OuraClient("test_token")
    
    def test_initialization(self):
        """Test OuraClient initialization."""
        assert self.client.access_token == "test_token"
        assert "Authorization" in self.client.session.headers
        assert self.client.session.headers["Authorization"] == "Bearer test_token"
    
    @patch('oura_client.requests.Session.get')
    def test_get_daily_activity_success(self, mock_get):
        """Test successful daily activity data retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{
                "total_calories": 2300,
                "active_calories": 480,
                "inactive_calories": 1820,
                "steps": 9500,
                "score": 87
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.client.get_daily_activity("2024-01-15")
        
        # Verify the result
        assert result is not None
        assert isinstance(result, HealthData)
        assert result.date == "2024-01-15"
        assert result.total_calories == 2300
        assert result.active_calories == 480
        assert result.steps == 9500
        assert result.activity_score == 87
        
        # Verify API call was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "daily_activity" in args[0]
        assert kwargs["params"]["start_date"] == "2024-01-15"
        assert kwargs["params"]["end_date"] == "2024-01-15"
    
    @patch('oura_client.requests.Session.get')
    def test_get_daily_activity_no_data(self, mock_get):
        """Test API response with no data."""
        # Mock API response with empty data
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.get_daily_activity("2024-01-15")
        
        assert result is None
    
    @patch('oura_client.requests.Session.get')
    def test_get_daily_activity_api_error(self, mock_get):
        """Test API error handling."""
        # Mock API error
        mock_get.side_effect = requests.RequestException("API Error")
        
        result = self.client.get_daily_activity("2024-01-15")
        
        assert result is None
    
    @patch('oura_client.requests.Session.get')
    def test_get_daily_activity_http_error(self, mock_get):
        """Test HTTP error handling."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response
        
        result = self.client.get_daily_activity("2024-01-15")
        
        assert result is None
    
    @patch('oura_client.requests.Session.get')
    def test_get_daily_activity_partial_data(self, mock_get):
        """Test handling of partial data from API."""
        # Mock API response with missing fields
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{
                "total_calories": 2000,
                # Missing some fields
                "steps": 7500
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.get_daily_activity("2024-01-15")
        
        assert result is not None
        assert result.total_calories == 2000
        assert result.active_calories == 0  # Should default to 0
        assert result.steps == 7500
        assert result.activity_score is None  # Should default to None
    
    @patch('oura_client.requests.Session.get')
    def test_get_yesterday_data(self, mock_get):
        """Test getting yesterday's data."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{
                "total_calories": 2100,
                "active_calories": 420,
                "inactive_calories": 1680,
                "steps": 8200,
                "score": 75
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.get_yesterday_data()
        
        # Verify result
        assert result is not None
        assert isinstance(result, HealthData)
        
        # Verify the date is yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result.date == yesterday
        
        # Verify API was called with yesterday's date
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["start_date"] == yesterday
        assert kwargs["params"]["end_date"] == yesterday
    
    @patch('oura_client.requests.Session.get')
    def test_get_daily_activity_malformed_response(self, mock_get):
        """Test handling of malformed API response."""
        # Mock malformed response
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.get_daily_activity("2024-01-15")
        
        assert result is None 