"""
Tests for configuration management.
"""

import pytest
import os
from unittest.mock import patch
from src.config import WhoopConfig


class TestWhoopConfig:
    """Test cases for WhoopConfig class."""
    
    def test_config_creation(self):
        """Test basic config creation."""
        config = WhoopConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback"
        )
        
        assert config.client_id == "test_client"
        assert config.client_secret == "test_secret"
        assert config.redirect_uri == "http://localhost:8080/callback"
        assert config.api_base_url == "https://api.prod.whoop.com"
        assert config.rate_limit_rpm == 100
        assert config.rate_limit_rpd == 10000
    
    def test_config_from_env(self):
        """Test loading config from environment variables."""
        env_vars = {
            "WHOOP_CLIENT_ID": "env_client",
            "WHOOP_CLIENT_SECRET": "env_secret",
            "WHOOP_REDIRECT_URI": "http://localhost:9090/callback",
            "WHOOP_RATE_LIMIT_RPM": "150",
            "WHOOP_RATE_LIMIT_RPD": "15000",
        }
        
        with patch.dict(os.environ, env_vars):
            config = WhoopConfig.from_env()
            
            assert config.client_id == "env_client"
            assert config.client_secret == "env_secret"
            assert config.redirect_uri == "http://localhost:9090/callback"
            assert config.rate_limit_rpm == 150
            assert config.rate_limit_rpd == 15000
    
    def test_config_validation_success(self):
        """Test successful config validation."""
        config = WhoopConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback"
        )
        
        # Should not raise any exception
        config.validate()
    
    def test_config_validation_missing_client_id(self):
        """Test config validation with missing client ID."""
        config = WhoopConfig(
            client_id="",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback"
        )
        
        with pytest.raises(ValueError, match="WHOOP_CLIENT_ID is required"):
            config.validate()
    
    def test_config_validation_missing_client_secret(self):
        """Test config validation with missing client secret."""
        config = WhoopConfig(
            client_id="test_client",
            client_secret="",
            redirect_uri="http://localhost:8080/callback"
        )
        
        with pytest.raises(ValueError, match="WHOOP_CLIENT_SECRET is required"):
            config.validate()
    
    def test_config_validation_missing_redirect_uri(self):
        """Test config validation with missing redirect URI."""
        config = WhoopConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri=""
        )
        
        with pytest.raises(ValueError, match="WHOOP_REDIRECT_URI is required"):
            config.validate()
    
    def test_config_validation_invalid_rate_limits(self):
        """Test config validation with invalid rate limits."""
        config = WhoopConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback",
            rate_limit_rpm=0,
            rate_limit_rpd=-1
        )
        
        with pytest.raises(ValueError, match="WHOOP_RATE_LIMIT_RPM must be positive"):
            config.validate()
    
    def test_get_auth_url_default_scopes(self):
        """Test generating auth URL with default scopes."""
        config = WhoopConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback"
        )
        
        url = config.get_auth_url()
        
        assert "response_type=code" in url
        assert "client_id=test_client" in url
        assert "redirect_uri=http://localhost:8080/callback" in url
        assert "scope=read:profile" in url
        assert "scope=read:body_measurement" in url
        assert "scope=read:cycles" in url
        assert "scope=read:sleep" in url
        assert "scope=read:recovery" in url
        assert "scope=read:workout" in url
        assert "scope=offline" in url
    
    def test_get_auth_url_custom_scopes(self):
        """Test generating auth URL with custom scopes."""
        config = WhoopConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback"
        )
        
        custom_scopes = ["read:profile", "read:sleep"]
        url = config.get_auth_url(scopes=custom_scopes)
        
        assert "scope=read:profile" in url
        assert "scope=read:sleep" in url
        assert "scope=read:body_measurement" not in url
    
    def test_get_auth_url_with_state(self):
        """Test generating auth URL with state parameter."""
        config = WhoopConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback"
        )
        
        state = "test_state_123"
        url = config.get_auth_url(state=state)
        
        assert f"state={state}" in url
