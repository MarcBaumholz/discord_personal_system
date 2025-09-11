#!/usr/bin/env python3
"""
Check actual dates in WHOOP data
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
    print("🔍 Checking WHOOP Data Dates...")
    
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
        
        # Check what yesterday should be
        yesterday = datetime.now() - timedelta(days=1)
        print(f"📅 Yesterday should be: {yesterday.strftime('%Y-%m-%d')}")
        print(f"📅 Yesterday date object: {yesterday.date()}")
        
        # Get cycles and check dates
        print("\n📈 Checking cycles...")
        cycles = client.get_cycles(limit=5)
        print(f"Found {len(cycles.records)} cycles")
        
        for i, cycle_data in enumerate(cycles.records):
            try:
                cycle = client.get_cycle(cycle_data['id'])
                cycle_date = cycle.start.date()
                print(f"  Cycle {i+1}: {cycle_date} (matches yesterday: {cycle_date == yesterday.date()})")
            except Exception as e:
                print(f"  Cycle {i+1}: Error - {e}")
        
        # Get sleep and check dates
        print("\n😴 Checking sleep...")
        sleep_data = client.get_sleep_data(limit=5)
        print(f"Found {len(sleep_data.records)} sleep records")
        
        for i, sleep_record in enumerate(sleep_data.records):
            try:
                sleep = client.get_sleep(sleep_record['id'])
                sleep_date = sleep.start.date()
                print(f"  Sleep {i+1}: {sleep_date} (matches yesterday: {sleep_date == yesterday.date()})")
            except Exception as e:
                print(f"  Sleep {i+1}: Error - {e}")
        
        # Get recovery and check dates
        print("\n💪 Checking recovery...")
        recovery_data = client.get_recovery_data(limit=5)
        print(f"Found {len(recovery_data.records)} recovery records")
        
        for i, recovery_record in enumerate(recovery_data.records):
            try:
                cycle = client.get_cycle(recovery_record['cycle_id'])
                recovery_date = cycle.start.date()
                print(f"  Recovery {i+1}: {recovery_date} (matches yesterday: {recovery_date == yesterday.date()})")
            except Exception as e:
                print(f"  Recovery {i+1}: Error - {e}")
        
        # Get workouts and check dates
        print("\n🏃 Checking workouts...")
        workouts = client.get_workouts(limit=5)
        print(f"Found {len(workouts.records)} workouts")
        
        for i, workout_record in enumerate(workouts.records):
            try:
                workout = client.get_workout(workout_record['id'])
                workout_date = workout.start.date()
                print(f"  Workout {i+1}: {workout_date} (matches yesterday: {workout_date == yesterday.date()})")
            except Exception as e:
                print(f"  Workout {i+1}: Error - {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
