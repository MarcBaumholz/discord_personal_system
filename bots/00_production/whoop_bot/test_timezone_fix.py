#!/usr/bin/env python3
"""
Test timezone fix for WHOOP data
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth
from src.client import WhoopClient
from src.token_manager import TokenManager

def main():
    print("🕐 Testing Timezone Fix...")
    
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
        
        # Test both local time and UTC
        yesterday_local = datetime.now() - timedelta(days=1)
        yesterday_utc = datetime.utcnow() - timedelta(days=1)
        
        print(f"📅 Yesterday (local): {yesterday_local.strftime('%Y-%m-%d')}")
        print(f"📅 Yesterday (UTC): {yesterday_utc.strftime('%Y-%m-%d')}")
        
        # Get cycles and check dates
        print("\n📈 Checking cycles with UTC comparison...")
        cycles = client.get_cycles(limit=5)
        print(f"Found {len(cycles.records)} cycles")
        
        found_cycle = False
        for i, cycle_data in enumerate(cycles.records):
            try:
                cycle = client.get_cycle(cycle_data['id'])
                cycle_date = cycle.start.date()
                matches_local = cycle_date == yesterday_local.date()
                matches_utc = cycle_date == yesterday_utc.date()
                
                print(f"  Cycle {i+1}: {cycle_date}")
                print(f"    Matches local: {matches_local}")
                print(f"    Matches UTC: {matches_utc}")
                
                if matches_utc:
                    found_cycle = True
                    print(f"    ✅ Found yesterday's cycle!")
                    
            except Exception as e:
                print(f"  Cycle {i+1}: Error - {e}")
        
        if not found_cycle:
            print("❌ No cycle found for yesterday with UTC comparison")
        
        # Get sleep and check dates
        print("\n😴 Checking sleep with UTC comparison...")
        sleep_data = client.get_sleep_data(limit=5)
        print(f"Found {len(sleep_data.records)} sleep records")
        
        found_sleep = False
        for i, sleep_record in enumerate(sleep_data.records):
            try:
                sleep = client.get_sleep(sleep_record['id'])
                sleep_date = sleep.start.date()
                matches_local = sleep_date == yesterday_local.date()
                matches_utc = sleep_date == yesterday_utc.date()
                
                print(f"  Sleep {i+1}: {sleep_date}")
                print(f"    Matches local: {matches_local}")
                print(f"    Matches UTC: {matches_utc}")
                
                if matches_utc:
                    found_sleep = True
                    print(f"    ✅ Found yesterday's sleep!")
                    
            except Exception as e:
                print(f"  Sleep {i+1}: Error - {e}")
        
        if not found_sleep:
            print("❌ No sleep found for yesterday with UTC comparison")
        
        print(f"\n📊 Summary:")
        print(f"  Cycle found: {'✅' if found_cycle else '❌'}")
        print(f"  Sleep found: {'✅' if found_sleep else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
