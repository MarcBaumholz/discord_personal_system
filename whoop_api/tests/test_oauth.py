"""
Tests for OAuth 2.0 implementation.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import requests

from src.config import WhoopConfig
from src.oauth import WhoopOAuth, WhoopOAuthError, extract_code_from_url
from src.models import WhoopTokenResponse


class TestWhoopOAuth:
    """Test cases for WhoopOAuth class."""
    
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
        """Create OAuth client."""
        return WhoopOAuth(config)
    
    def test_oauth_initialization(self, oauth, config):
        """Test OAuth client initialization."""
        assert oauth.config == config
        assert oauth._access_token is None
        assert oauth._refresh_token is None
        assert oauth._token_expires_at is None
    
    def test_get_authorization_url(self, oauth):
        """Test generating authorization URL."""
        url = oauth.get_authorization_url()
        
        assert "response_type=code" in url
        assert "client_id=test_client" in url
        assert "redirect_uri=http://localhost:8080/callback" in url
        assert "scope=" in url
        assert "state=" in url
    
    def test_get_authorization_url_with_state(self, oauth):
        """Test generating authorization URL with custom state."""
        state = "custom_state_123"
        url = oauth.get_authorization_url(state=state)
        
        assert f"state={state}" in url
    
    def test_get_authorization_url_with_scopes(self, oauth):
        """Test generating authorization URL with custom scopes."""
        scopes = ["read:profile", "read:sleep"]
        url = oauth.get_authorization_url(scopes=scopes)
        
        assert "scope=read:profile" in url
        assert "scope=read:sleep" in url
    
    @patch('requests.post')
    def test_exchange_code_for_token_success(self, mock_post, oauth):
        """Test successful code exchange for token."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "test_refresh_token",
            "scope": "read:profile"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = oauth.exchange_code_for_token("test_code")
        
        assert isinstance(result, WhoopTokenResponse)
        assert result.access_token == "test_access_token"
        assert result.refresh_token == "test_refresh_token"
        assert oauth._access_token == "test_access_token"
        assert oauth._refresh_token == "test_refresh_token"
        assert oauth._token_expires_at is not None
    
    @patch('requests.post')
    def test_exchange_code_for_token_request_error(self, mock_post, oauth):
        """Test code exchange with request error."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        with pytest.raises(WhoopOAuthError, match="Failed to exchange code for token"):
            oauth.exchange_code_for_token("test_code")
    
    @patch('requests.post')
    def test_exchange_code_for_token_invalid_response(self, mock_post, oauth):
        """Test code exchange with invalid response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        with pytest.raises(WhoopOAuthError, match="Invalid token response"):
            oauth.exchange_code_for_token("test_code")
    
    @patch('requests.post')
    def test_refresh_access_token_success(self, oauth):
        """Test successful token refresh."""
        # Set up initial tokens
        oauth._refresh_token = "test_refresh_token"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "new_refresh_token"
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            result = oauth.refresh_access_token()
            
            assert result.access_token == "new_access_token"
            assert result.refresh_token == "new_refresh_token"
            assert oauth._access_token == "new_access_token"
            assert oauth._refresh_token == "new_refresh_token"
    
    def test_refresh_access_token_no_refresh_token(self, oauth):
        """Test token refresh without refresh token."""
        with pytest.raises(WhoopOAuthError, match="No refresh token available"):
            oauth.refresh_access_token()
    
    def test_get_valid_access_token_no_token(self, oauth):
        """Test getting valid access token without any token."""
        with pytest.raises(WhoopOAuthError, match="No access token available"):
            oauth.get_valid_access_token()
    
    def test_get_valid_access_token_valid_token(self, oauth):
        """Test getting valid access token with valid token."""
        oauth._access_token = "test_token"
        oauth._token_expires_at = datetime.now() + timedelta(hours=1)
        
        token = oauth.get_valid_access_token()
        assert token == "test_token"
    
    def test_get_valid_access_token_expired_token(self, oauth):
        """Test getting valid access token with expired token."""
        oauth._access_token = "expired_token"
        oauth._refresh_token = "refresh_token"
        oauth._token_expires_at = datetime.now() - timedelta(hours=1)
        
        with patch.object(oauth, 'refresh_access_token') as mock_refresh:
            mock_refresh.return_value = WhoopTokenResponse(
                access_token="new_token",
                token_type="Bearer",
                expires_in=3600
            )
            
            token = oauth.get_valid_access_token()
            assert token == "new_token"
            mock_refresh.assert_called_once()
    
    def test_set_tokens(self, oauth):
        """Test manually setting tokens."""
        oauth.set_tokens("access_token", "refresh_token", 3600)
        
        assert oauth._access_token == "access_token"
        assert oauth._refresh_token == "refresh_token"
        assert oauth._token_expires_at is not None
    
    def test_get_token_info(self, oauth):
        """Test getting token information."""
        info = oauth.get_token_info()
        
        assert info["has_access_token"] is False
        assert info["has_refresh_token"] is False
        assert info["expires_at"] is None
        assert info["is_expired"] is False
        
        # Set tokens and test again
        oauth.set_tokens("access_token", "refresh_token", 3600)
        info = oauth.get_token_info()
        
        assert info["has_access_token"] is True
        assert info["has_refresh_token"] is True
        assert info["expires_at"] is not None
        assert info["is_expired"] is False
    
    def test_revoke_tokens(self, oauth):
        """Test revoking tokens."""
        oauth.set_tokens("access_token", "refresh_token", 3600)
        oauth.revoke_tokens()
        
        assert oauth._access_token is None
        assert oauth._refresh_token is None
        assert oauth._token_expires_at is None


class TestExtractCodeFromUrl:
    """Test cases for URL code extraction."""
    
    def test_extract_code_success(self):
        """Test successful code extraction."""
        url = "http://localhost:8080/callback?code=test_code&state=test_state"
        code, state = extract_code_from_url(url)
        
        assert code == "test_code"
        assert state == "test_state"
    
    def test_extract_code_no_state(self):
        """Test code extraction without state."""
        url = "http://localhost:8080/callback?code=test_code"
        code, state = extract_code_from_url(url)
        
        assert code == "test_code"
        assert state is None
    
    def test_extract_code_no_code(self):
        """Test code extraction without code."""
        url = "http://localhost:8080/callback?state=test_state"
        
        with pytest.raises(ValueError, match="No authorization code found in URL"):
            extract_code_from_url(url)
