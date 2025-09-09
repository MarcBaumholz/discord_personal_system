#!/usr/bin/env python3
"""
Easy WHOOP API test - step by step guide
"""

import sys
import os
import webbrowser
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth, extract_code_from_url
from src.client import WhoopClient


def main():
    print("🚀 Easy WHOOP Data Test")
    print("=" * 30)
    
    # Load configuration
    config = WhoopConfig.from_env()
    oauth = WhoopOAuth(config)
    
    # Generate authorization URL
    auth_url = oauth.get_authorization_url()
    
    print(f"\n📱 STEP 1: I'll open the WHOOP login page for you...")
    
    try:
        # Try to open the URL automatically
        webbrowser.open(auth_url)
        print("✅ Browser opened with WHOOP login page!")
    except:
        print("❌ Could not open browser automatically")
        print(f"   Please manually open: {auth_url}")
    
    print(f"\n📋 STEP 2: Complete these steps in your browser:")
    print(f"   1. Sign in to your WHOOP account")
    print(f"   2. Grant all permissions to 'Morgenroutine'")
    print(f"   3. You'll be redirected to: http://localhost:8080/callback?code=...")
    print(f"   4. Copy the ENTIRE URL from your browser")
    
    print(f"\n⏰ You have 10 minutes to complete this...")
    
    # Wait for user input
    callback_url = input(f"\n🔗 Paste the complete callback URL here: ").strip()
    
    if not callback_url:
        print("❌ No URL provided. Test cancelled.")
        return
    
    print(f"\n🔄 Processing your authorization...")
    
    try:
        # Extract code and get tokens
        code, state = extract_code_from_url(callback_url)
        print(f"✅ Authorization code received: {code[:10]}...")
        
        token_response = oauth.exchange_code_for_token(code)
        print("✅ Access token obtained!")
        print(f"   Token expires in: {token_response.expires_in} seconds")
        
        # Initialize client
        client = WhoopClient(config, oauth)
        
        print("\n🔍 Testing API connection...")
        if client.test_connection():
            print("✅ API connection successful!")
        else:
            print("❌ API connection failed")
            return
        
        print("\n📊 Fetching your WHOOP data...")
        
        # Get profile
        try:
            profile = client.get_user_profile()
            print(f"\n👤 Profile:")
            print(f"   User ID: {profile.user_id}")
            print(f"   Email: {profile.email}")
            if profile.first_name:
                print(f"   Name: {profile.first_name} {profile.last_name or ''}")
        except Exception as e:
            print(f"❌ Profile error: {e}")
        
        # Get body measurements
        try:
            body = client.get_body_measurements()
            print(f"\n📏 Body Measurements:")
            if body.height_meter:
                print(f"   Height: {body.height_meter:.2f} meters")
            if body.weight_kilogram:
                print(f"   Weight: {body.weight_kilogram:.1f} kg")
            if body.max_heart_rate:
                print(f"   Max HR: {body.max_heart_rate} bpm")
        except Exception as e:
            print(f"❌ Body measurements error: {e}")
        
        # Get recent data (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Cycles
        try:
            cycles = client.get_cycles(start=start_date, end=end_date, limit=5)
            print(f"\n📈 Recent Cycles (last 7 days):")
            print(f"   Found {len(cycles.records)} cycles")
            
            for i, cycle_data in enumerate(cycles.records[:3]):
                cycle = client.get_cycle(cycle_data['id'])
                print(f"   Cycle {i+1}: {cycle.start.date()}")
                if cycle.score and cycle.score.strain:
                    print(f"     Strain: {cycle.score.strain:.1f}")
                if cycle.score and cycle.score.average_heart_rate:
                    print(f"     Avg HR: {cycle.score.average_heart_rate} bpm")
        except Exception as e:
            print(f"❌ Cycles error: {e}")
        
        # Sleep
        try:
            sleep_data = client.get_sleep_data(start=start_date, end=end_date, limit=5)
            print(f"\n😴 Recent Sleep (last 7 days):")
            print(f"   Found {len(sleep_data.records)} sleep records")
            
            for i, sleep_record in enumerate(sleep_data.records[:3]):
                sleep = client.get_sleep(sleep_record['id'])
                print(f"   Sleep {i+1}: {sleep.start.date()}")
                if sleep.score:
                    print(f"     Score: {sleep.score:.1f}")
                if sleep.stage_summary:
                    total_sleep = (sleep.stage_summary.light_sleep_time_seconds or 0) + \
                                 (sleep.stage_summary.slow_wave_sleep_time_seconds or 0) + \
                                 (sleep.stage_summary.rem_sleep_time_seconds or 0)
                    print(f"     Total Sleep: {total_sleep // 3600}h {(total_sleep % 3600) // 60}m")
        except Exception as e:
            print(f"❌ Sleep error: {e}")
        
        # Recovery
        try:
            recovery_data = client.get_recovery_data(start=start_date, end=end_date, limit=5)
            print(f"\n💪 Recent Recovery (last 7 days):")
            print(f"   Found {len(recovery_data.records)} recovery records")
            
            for i, recovery_record in enumerate(recovery_data.records[:3]):
                recovery = client.get_recovery(recovery_record['id'])
                print(f"   Recovery {i+1}: {recovery.start.date()}")
                if recovery.score:
                    print(f"     Score: {recovery.score:.1f}")
                if recovery.resting_heart_rate:
                    print(f"     Resting HR: {recovery.resting_heart_rate} bpm")
                if recovery.hrv_rmssd_milli_seconds:
                    print(f"     HRV: {recovery.hrv_rmssd_milli_seconds:.1f} ms")
        except Exception as e:
            print(f"❌ Recovery error: {e}")
        
        # Workouts
        try:
            workouts = client.get_workouts(start=start_date, end=end_date, limit=5)
            print(f"\n🏃 Recent Workouts (last 7 days):")
            print(f"   Found {len(workouts.records)} workouts")
            
            for i, workout_record in enumerate(workouts.records[:3]):
                workout = client.get_workout(workout_record['id'])
                print(f"   Workout {i+1}: {workout.start.date()}")
                print(f"     Sport: {workout.sport_name}")
                if workout.score and workout.score.strain:
                    print(f"     Strain: {workout.score.strain:.1f}")
                if workout.score and workout.score.kilojoules:
                    print(f"     Energy: {workout.score.kilojoules:.0f} kJ")
        except Exception as e:
            print(f"❌ Workouts error: {e}")
        
        print(f"\n🎉 SUCCESS! Your WHOOP data has been retrieved!")
        print(f"\nNext steps:")
        print(f"- Run 'python examples/data_export.py' to export all data to CSV")
        print(f"- Run 'python examples/webhook_server.py' for real-time updates")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"- Make sure you copied the ENTIRE callback URL")
        print(f"- Check that you granted all permissions to the app")
        print(f"- Verify your WHOOP account is active")
        print(f"- Try again with a fresh URL")


if __name__ == "__main__":
    main()
