"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock
from src.config import WhoopConfig
from src.oauth import WhoopOAuth


@pytest.fixture
def temp_env_file():
    """Create temporary environment file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
WHOOP_CLIENT_ID=test_client_id
WHOOP_CLIENT_SECRET=test_client_secret
WHOOP_REDIRECT_URI=http://localhost:8080/callback
WHOOP_RATE_LIMIT_RPM=100
WHOOP_RATE_LIMIT_RPD=10000
        """)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)


@pytest.fixture
def sample_config():
    """Create sample configuration for testing."""
    return WhoopConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8080/callback",
        rate_limit_rpm=100,
        rate_limit_rpd=10000
    )


@pytest.fixture
def sample_oauth(sample_config):
    """Create sample OAuth client for testing."""
    return WhoopOAuth(sample_config)


@pytest.fixture
def mock_oauth():
    """Create mock OAuth client for testing."""
    oauth = Mock(spec=WhoopOAuth)
    oauth.get_valid_access_token.return_value = "test_access_token"
    oauth.get_token_info.return_value = {
        "has_access_token": True,
        "has_refresh_token": True,
        "expires_at": "2024-12-31T23:59:59",
        "is_expired": False
    }
    return oauth
