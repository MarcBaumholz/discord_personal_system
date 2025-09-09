"""
WHOOP API Integration Package

A comprehensive Python client for accessing WHOOP data via the official v2 API.
Supports OAuth 2.0 authentication, rate limiting, webhooks, and all major endpoints.
"""

__version__ = "1.0.0"
__author__ = "WHOOP API Integration"

from .config import WhoopConfig
from .oauth import WhoopOAuth
from .client import WhoopClient
from .models import *

__all__ = [
    "WhoopConfig",
    "WhoopOAuth", 
    "WhoopClient",
]
