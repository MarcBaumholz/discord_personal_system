#!/usr/bin/env python3
"""
Debug script to check WHOOP API response structure
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth
from src.client import WhoopClient
from src.token_manager import TokenManager

def main():
    print("🔍 Debugging WHOOP API Response Structure...")
    
    try:
        # Load configuration
        config = WhoopConfig.from_env()
        oauth = WhoopOAuth(config)
        token_manager = TokenManager()
        client = WhoopClient(config, oauth, token_manager)
        
        if not client.is_authenticated():
            print("❌ No valid WHOOP tokens found")
            return
        
        print("✅ WHOOP authentication successful")
        
        # Get recovery data and inspect structure
        print("\n📊 Checking recovery data structure...")
        recovery_data = client.get_recovery_data(limit=3)
        print(f"Found {len(recovery_data.records)} recovery records")
        
        if recovery_data.records:
            print("\nFirst recovery record structure:")
            print(json.dumps(recovery_data.records[0], indent=2, default=str))
        
        # Get sleep data and inspect structure
        print("\n📊 Checking sleep data structure...")
        sleep_data = client.get_sleep_data(limit=3)
        print(f"Found {len(sleep_data.records)} sleep records")
        
        if sleep_data.records:
            print("\nFirst sleep record structure:")
            print(json.dumps(sleep_data.records[0], indent=2, default=str))
        
        # Get cycle data and inspect structure
        print("\n📊 Checking cycle data structure...")
        cycles = client.get_cycles(limit=3)
        print(f"Found {len(cycles.records)} cycle records")
        
        if cycles.records:
            print("\nFirst cycle record structure:")
            print(json.dumps(cycles.records[0], indent=2, default=str))
        
        # Get workout data and inspect structure
        print("\n📊 Checking workout data structure...")
        workouts = client.get_workouts(limit=3)
        print(f"Found {len(workouts.records)} workout records")
        
        if workouts.records:
            print("\nFirst workout record structure:")
            print(json.dumps(workouts.records[0], indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
