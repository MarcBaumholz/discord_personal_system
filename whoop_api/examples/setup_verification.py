#!/usr/bin/env python3
"""
WHOOP API Setup Verification Script
Checks if your configuration is correct and guides you through setup.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth


def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking Prerequisites...")
    print("=" * 40)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python {python_version.major}.{python_version.minor} - OK")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} - Need Python 3.8+")
        return False
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found - OK")
    else:
        print("❌ .env file not found")
        print("   Run: cp config.env.example .env")
        return False
    
    # Check if requirements are installed
    try:
        import requests
        import pydantic
        print("✅ Required packages installed - OK")
    except ImportError as e:
        print(f"❌ Missing packages: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def check_configuration():
    """Check if configuration is properly set up."""
    print("\n🔧 Checking Configuration...")
    print("=" * 40)
    
    try:
        config = WhoopConfig.from_env()
        print("✅ Configuration loaded successfully")
        
        # Check individual settings
        if config.client_id and config.client_id != "your_client_id_here":
            print(f"✅ Client ID set: {config.client_id[:10]}...")
        else:
            print("❌ Client ID not set or using placeholder")
            print("   Edit .env file and set WHOOP_CLIENT_ID")
            return False
        
        if config.client_secret and config.client_secret != "your_client_secret_here":
            print(f"✅ Client Secret set: {config.client_secret[:10]}...")
        else:
            print("❌ Client Secret not set or using placeholder")
            print("   Edit .env file and set WHOOP_CLIENT_SECRET")
            return False
        
        if config.redirect_uri:
            print(f"✅ Redirect URI: {config.redirect_uri}")
        else:
            print("❌ Redirect URI not set")
            return False
        
        # Validate configuration
        try:
            config.validate()
            print("✅ Configuration validation passed")
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_oauth_flow():
    """Test OAuth flow setup."""
    print("\n🔐 Testing OAuth Flow...")
    print("=" * 40)
    
    try:
        config = WhoopConfig.from_env()
        oauth = WhoopOAuth(config)
        
        # Test authorization URL generation
        auth_url = oauth.get_authorization_url()
        if auth_url and "response_type=code" in auth_url:
            print("✅ Authorization URL generation - OK")
            print(f"   Sample URL: {auth_url[:100]}...")
        else:
            print("❌ Authorization URL generation failed")
            return False
        
        # Test token info (should be empty initially)
        token_info = oauth.get_token_info()
        if not token_info["has_access_token"]:
            print("✅ Token state (no tokens yet) - OK")
        else:
            print("ℹ️  Tokens already present - OK")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth setup error: {e}")
        return False


def test_api_endpoints():
    """Test API endpoint accessibility."""
    print("\n🌐 Testing API Endpoints...")
    print("=" * 40)
    
    try:
        import requests
        
        # Test WHOOP API base URL
        try:
            response = requests.get("https://api.prod.whoop.com", timeout=10)
            print("✅ WHOOP API base URL accessible")
        except requests.exceptions.RequestException as e:
            print(f"❌ WHOOP API base URL not accessible: {e}")
            return False
        
        # Test OAuth endpoints
        try:
            response = requests.get("https://api.prod.whoop.com/oauth/oauth2/auth", timeout=10)
            print("✅ OAuth authorization endpoint accessible")
        except requests.exceptions.RequestException as e:
            print(f"❌ OAuth authorization endpoint not accessible: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test error: {e}")
        return False


def provide_next_steps():
    """Provide next steps for the user."""
    print("\n🚀 Next Steps...")
    print("=" * 40)
    
    print("1. Run the basic example:")
    print("   python examples/basic_usage.py")
    print()
    print("2. Export your data:")
    print("   python examples/data_export.py")
    print()
    print("3. Set up webhooks (optional):")
    print("   python examples/webhook_server.py")
    print()
    print("4. Read the documentation:")
    print("   cat README.md")
    print()
    print("5. Check setup guide:")
    print("   cat setup_guide.md")


def main():
    """Main verification function."""
    print("WHOOP API Setup Verification")
    print("=" * 50)
    print()
    
    all_checks_passed = True
    
    # Run all checks
    if not check_prerequisites():
        all_checks_passed = False
    
    if not check_configuration():
        all_checks_passed = False
    
    if not test_oauth_flow():
        all_checks_passed = False
    
    if not test_api_endpoints():
        all_checks_passed = False
    
    # Summary
    print("\n📋 Summary")
    print("=" * 40)
    
    if all_checks_passed:
        print("🎉 All checks passed! Your WHOOP API setup is ready.")
        print()
        provide_next_steps()
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("- Copy config.env.example to .env")
        print("- Edit .env with your WHOOP credentials")
        print("- Run: pip install -r requirements.txt")
        print("- Check your internet connection")
        print()
        print("For detailed setup instructions, see setup_guide.md")


if __name__ == "__main__":
    main()
