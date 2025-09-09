#!/usr/bin/env python3
"""
Basic WHOOP API usage example.
Demonstrates OAuth flow and basic data retrieval.
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth, extract_code_from_url
from src.client import WhoopClient


def main():
    """Main example function."""
    print("WHOOP API Basic Usage Example")
    print("=" * 40)
    
    # Load configuration
    try:
        config = WhoopConfig.from_env()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        print("Please ensure you have a .env file with WHOOP credentials")
        return
    
    # Initialize OAuth client
    oauth = WhoopOAuth(config)
    print("✓ OAuth client initialized")
    
    # Step 1: Get authorization URL
    auth_url = oauth.get_authorization_url()
    print(f"\n1. Please visit this URL to authorize the application:")
    print(f"   {auth_url}")
    
    # Step 2: Get authorization code from user
    print("\n2. After authorization, you'll be redirected to a URL like:")
    print("   http://localhost:8080/callback?code=YOUR_CODE&state=STATE")
    print("   Please paste the full URL here:")
    
    callback_url = input("Callback URL: ").strip()
    
    try:
        # Extract code from URL
        code, state = extract_code_from_url(callback_url)
        print(f"✓ Authorization code extracted: {code[:10]}...")
        
        # Exchange code for tokens
        token_response = oauth.exchange_code_for_token(code)
        print("✓ Access token obtained successfully")
        print(f"   Token type: {token_response.token_type}")
        print(f"   Expires in: {token_response.expires_in} seconds")
        
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return
    
    # Initialize API client
    client = WhoopClient(config, oauth)
    print("\n✓ WHOOP API client initialized")
    
    # Test connection
    if client.test_connection():
        print("✓ API connection successful")
    else:
        print("✗ API connection failed")
        return
    
    # Get user profile
    try:
        print("\n3. Fetching user profile...")
        profile = client.get_user_profile()
        print(f"   User ID: {profile.user_id}")
        print(f"   Email: {profile.email}")
        if profile.first_name:
            print(f"   Name: {profile.first_name} {profile.last_name or ''}")
    except Exception as e:
        print(f"✗ Failed to get profile: {e}")
        return
    
    # Get body measurements
    try:
        print("\n4. Fetching body measurements...")
        body = client.get_body_measurements()
        if body.height_meter:
            print(f"   Height: {body.height_meter:.2f} meters")
        if body.weight_kilogram:
            print(f"   Weight: {body.weight_kilogram:.1f} kg")
        if body.max_heart_rate:
            print(f"   Max HR: {body.max_heart_rate} bpm")
    except Exception as e:
        print(f"✗ Failed to get body measurements: {e}")
    
    # Get recent cycles (last 7 days)
    try:
        print("\n5. Fetching recent cycles...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        cycles = client.get_cycles(start=start_date, end=end_date, limit=10)
        print(f"   Found {len(cycles.records)} cycles in the last 7 days")
        
        for i, cycle_data in enumerate(cycles.records[:3]):  # Show first 3
            cycle = client.get_cycle(cycle_data['id'])
            print(f"   Cycle {i+1}: {cycle.start.date()} - {cycle.end.date()}")
            if cycle.score and cycle.score.strain:
                print(f"     Strain: {cycle.score.strain:.1f}")
            if cycle.score and cycle.score.average_heart_rate:
                print(f"     Avg HR: {cycle.score.average_heart_rate} bpm")
    
    except Exception as e:
        print(f"✗ Failed to get cycles: {e}")
    
    # Get recent sleep data
    try:
        print("\n6. Fetching recent sleep data...")
        sleep_data = client.get_sleep_data(start=start_date, end=end_date, limit=5)
        print(f"   Found {len(sleep_data.records)} sleep records in the last 7 days")
        
        for i, sleep_record in enumerate(sleep_data.records[:2]):  # Show first 2
            sleep = client.get_sleep(sleep_record['id'])
            print(f"   Sleep {i+1}: {sleep.start.date()} - {sleep.end.date()}")
            if sleep.score:
                print(f"     Sleep Score: {sleep.score:.1f}")
            if sleep.stage_summary:
                total_sleep = sleep.stage_summary.light_sleep_time_seconds or 0
                total_sleep += sleep.stage_summary.slow_wave_sleep_time_seconds or 0
                total_sleep += sleep.stage_summary.rem_sleep_time_seconds or 0
                print(f"     Total Sleep: {total_sleep // 3600}h {(total_sleep % 3600) // 60}m")
    
    except Exception as e:
        print(f"✗ Failed to get sleep data: {e}")
    
    # Get recent recovery data
    try:
        print("\n7. Fetching recent recovery data...")
        recovery_data = client.get_recovery_data(start=start_date, end=end_date, limit=5)
        print(f"   Found {len(recovery_data.records)} recovery records in the last 7 days")
        
        for i, recovery_record in enumerate(recovery_data.records[:2]):  # Show first 2
            recovery = client.get_recovery(recovery_record['id'])
            print(f"   Recovery {i+1}: {recovery.start.date()}")
            if recovery.score:
                print(f"     Recovery Score: {recovery.score:.1f}")
            if recovery.resting_heart_rate:
                print(f"     Resting HR: {recovery.resting_heart_rate} bpm")
            if recovery.hrv_rmssd_milli_seconds:
                print(f"     HRV: {recovery.hrv_rmssd_milli_seconds:.1f} ms")
    
    except Exception as e:
        print(f"✗ Failed to get recovery data: {e}")
    
    # Get recent workouts
    try:
        print("\n8. Fetching recent workouts...")
        workouts = client.get_workouts(start=start_date, end=end_date, limit=5)
        print(f"   Found {len(workouts.records)} workouts in the last 7 days")
        
        for i, workout_record in enumerate(workouts.records[:2]):  # Show first 2
            workout = client.get_workout(workout_record['id'])
            print(f"   Workout {i+1}: {workout.start.date()} - {workout.sport_name}")
            if workout.score and workout.score.strain:
                print(f"     Strain: {workout.score.strain:.1f}")
            if workout.score and workout.score.kilojoules:
                print(f"     Energy: {workout.score.kilojoules:.0f} kJ")
    
    except Exception as e:
        print(f"✗ Failed to get workouts: {e}")
    
    # Show rate limit status
    print("\n9. Rate limiting status:")
    status = client.get_rate_limit_status()
    print(f"   Minute requests: {status['minute_requests']}/{status['minute_limit']}")
    print(f"   Day requests: {status['day_requests']}/{status['day_limit']}")
    print(f"   Can make request: {status['can_make_request']}")
    
    print("\n✓ Example completed successfully!")
    print("\nNext steps:")
    print("- Check the examples/ directory for more advanced usage")
    print("- Implement webhook support for real-time updates")
    print("- Add data persistence for historical analysis")


if __name__ == "__main__":
    main()
