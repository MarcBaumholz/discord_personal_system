#!/usr/bin/env python3
"""
Open WHOOP login page and generate fresh URL
"""

import sys
import os
import webbrowser

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth

def main():
    print("🚀 WHOOP Data Test - Fresh URL Generated!")
    print("=" * 50)
    
    # Load configuration
    config = WhoopConfig.from_env()
    oauth = WhoopOAuth(config)
    
    # Generate authorization URL
    auth_url = oauth.get_authorization_url()
    
    print("\n📱 STEP 1: Opening WHOOP login page...")
    try:
        webbrowser.open(auth_url)
        print("✅ Browser should open automatically!")
    except:
        print("❌ Could not open browser automatically")
    
    print("\n📋 STEP 2: Complete these steps:")
    print("   1. Sign in to your WHOOP account")
    print("   2. Grant all permissions to 'Morgenroutine'")
    print("   3. You will be redirected to: http://localhost:8080/callback?code=...")
    print("   4. Copy the ENTIRE URL from your browser")
    
    print(f"\n🔗 If browser did not open, manually visit:")
    print(auth_url)
    
    print("\n⏰ You have 10 minutes to complete this...")
    
    print("\n📝 After you get the callback URL, run:")
    print("   python quick_test.py")
    print("   Then paste the URL when prompted")

if __name__ == "__main__":
    main()
