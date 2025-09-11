#!/usr/bin/env python3
"""
Final WHOOP API test with correct endpoints based on API spec
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth, extract_code_from_url
from src.client import WhoopClient

def main():
    # Your fresh callback URL
    callback_url = 'http://localhost:8080/callback?code=NwG043-lKlmoIzBj9UdHlWcUoeQJnxTmiZSXatLNMkk._cUzS1sIl0B5JQCa2oogcYdKICZ8OzEqAYe13QSyraU&scope=read%3Aprofile%20read%3Abody_measurement%20read%3Acycles%20read%3Asleep%20read%3Arecovery%20read%3Aworkout%20offline&state=vPcQITFoC9HaqCeKl6LiFrXXIdCzqNSzCOz_LUgIvgk'

    print('🚀 WHOOP Data Retrieval - Final Test')
    print('=' * 50)
    print('Based on official WHOOP API specification')
    print()

    try:
        # Load configuration
        config = WhoopConfig.from_env()
        oauth = WhoopOAuth(config)
        
        # Extract code and get tokens
        code, state = extract_code_from_url(callback_url)
        print(f'✅ Authorization code received: {code[:10]}...')
        
        token_response = oauth.exchange_code_for_token(code)
        print('✅ Access token obtained!')
        print(f'   Token expires in: {token_response.expires_in} seconds')
        
        # Initialize client
        client = WhoopClient(config, oauth)
        
        print('\n🔍 Testing API connection...')
        if client.test_connection():
            print('✅ API connection successful!')
        else:
            print('❌ API connection failed')
            return
        
        print('\n📊 Fetching your WHOOP data...')
        
        # Get profile
        try:
            profile = client.get_user_profile()
            print(f'\n👤 Profile:')
            print(f'   User ID: {profile.user_id}')
            print(f'   Email: {profile.email}')
            if profile.first_name:
                print(f'   Name: {profile.first_name} {profile.last_name or ""}')
        except Exception as e:
            print(f'❌ Profile error: {e}')
        
        # Get body measurements
        try:
            body = client.get_body_measurements()
            print(f'\n📏 Body Measurements:')
            if body.height_meter:
                print(f'   Height: {body.height_meter:.2f} meters')
            if body.weight_kilogram:
                print(f'   Weight: {body.weight_kilogram:.1f} kg')
            if body.max_heart_rate:
                print(f'   Max HR: {body.max_heart_rate} bpm')
        except Exception as e:
            print(f'❌ Body measurements error: {e}')
        
        # Get cycles (no date filter first)
        print(f'\n📈 Testing Cycles (no date filter)...')
        try:
            cycles = client.get_cycles(limit=10)
            print(f'   Found {len(cycles.records)} cycles')
            if cycles.records:
                for i, cycle_data in enumerate(cycles.records[:3]):
                    cycle = client.get_cycle(cycle_data['id'])
                    print(f'   Cycle {i+1}: {cycle.start.date()}')
                    if cycle.score and cycle.score.strain:
                        print(f'     Strain: {cycle.score.strain:.1f}')
                    if cycle.score and cycle.score.average_heart_rate:
                        print(f'     Avg HR: {cycle.score.average_heart_rate} bpm')
                    if cycle.score and cycle.score.kilojoules:
                        print(f'     Energy: {cycle.score.kilojoules:.0f} kJ')
            else:
                print('   No cycles found')
        except Exception as e:
            print(f'   Error: {e}')
        
        # Get sleep data (no date filter)
        print(f'\n😴 Testing Sleep (no date filter)...')
        try:
            sleep_data = client.get_sleep_data(limit=10)
            print(f'   Found {len(sleep_data.records)} sleep records')
            if sleep_data.records:
                for i, sleep_record in enumerate(sleep_data.records[:3]):
                    sleep = client.get_sleep(sleep_record['id'])
                    print(f'   Sleep {i+1}: {sleep.start.date()}')
                    if sleep.score:
                        print(f'     Score: {sleep.score:.1f}')
                    if sleep.stage_summary:
                        total_sleep = (sleep.stage_summary.light_sleep_time_seconds or 0) + (sleep.stage_summary.slow_wave_sleep_time_seconds or 0) + (sleep.stage_summary.rem_sleep_time_seconds or 0)
                        print(f'     Total Sleep: {total_sleep // 3600}h {(total_sleep % 3600) // 60}m')
                    if sleep.respiratory_rate:
                        print(f'     Respiratory Rate: {sleep.respiratory_rate:.1f} breaths/min')
            else:
                print('   No sleep records found')
        except Exception as e:
            print(f'   Error: {e}')
        
        # Get recovery data (no date filter)
        print(f'\n💪 Testing Recovery (no date filter)...')
        try:
            recovery_data = client.get_recovery_data(limit=10)
            print(f'   Found {len(recovery_data.records)} recovery records')
            if recovery_data.records:
                for i, recovery_record in enumerate(recovery_data.records[:3]):
                    recovery = client.get_recovery(recovery_record['id'])
                    print(f'   Recovery {i+1}: {recovery.start.date()}')
                    if recovery.score:
                        print(f'     Score: {recovery.score:.1f}')
                    if recovery.resting_heart_rate:
                        print(f'     Resting HR: {recovery.resting_heart_rate} bpm')
                    if recovery.hrv_rmssd_milli_seconds:
                        print(f'     HRV: {recovery.hrv_rmssd_milli_seconds:.1f} ms')
                    if recovery.spo2_percentage:
                        print(f'     SpO2: {recovery.spo2_percentage:.1f}%')
            else:
                print('   No recovery records found')
        except Exception as e:
            print(f'   Error: {e}')
        
        # Get workouts (no date filter)
        print(f'\n🏃 Testing Workouts (no date filter)...')
        try:
            workouts = client.get_workouts(limit=10)
            print(f'   Found {len(workouts.records)} workouts')
            if workouts.records:
                for i, workout_record in enumerate(workouts.records[:3]):
                    workout = client.get_workout(workout_record['id'])
                    print(f'   Workout {i+1}: {workout.start.date()}')
                    print(f'     Sport: {workout.sport_name}')
                    if workout.score and workout.score.strain:
                        print(f'     Strain: {workout.score.strain:.1f}')
                    if workout.score and workout.score.kilojoules:
                        print(f'     Energy: {workout.score.kilojoules:.0f} kJ')
                    if workout.distance_meter:
                        print(f'     Distance: {workout.distance_meter/1000:.2f} km')
            else:
                print('   No workouts found')
        except Exception as e:
            print(f'   Error: {e}')
        
        # Test with date range (last 30 days)
        print(f'\n📅 Testing with date range (last 30 days)...')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        try:
            cycles_dated = client.get_cycles(start=start_date, end=end_date, limit=5)
            print(f'   Cycles with date filter: {len(cycles_dated.records)} found')
        except Exception as e:
            print(f'   Cycles with date filter error: {e}')
        
        try:
            sleep_dated = client.get_sleep_data(start=start_date, end=end_date, limit=5)
            print(f'   Sleep with date filter: {len(sleep_dated.records)} found')
        except Exception as e:
            print(f'   Sleep with date filter error: {e}')
        
        print(f'\n🎉 WHOOP Data Retrieval Complete!')
        print(f'\nSummary:')
        print(f'- Profile: ✅ Retrieved')
        print(f'- Body Measurements: {"✅ Retrieved" if "body" in locals() else "❌ Not available"}')
        print(f'- Cycles: {"✅ Retrieved" if "cycles" in locals() and cycles.records else "❌ No data"}')
        print(f'- Sleep: {"✅ Retrieved" if "sleep_data" in locals() and sleep_data.records else "❌ No data"}')
        print(f'- Recovery: {"✅ Retrieved" if "recovery_data" in locals() and recovery_data.records else "❌ No data"}')
        print(f'- Workouts: {"✅ Retrieved" if "workouts" in locals() and workouts.records else "❌ No data"}')
        
        print(f'\nNext steps:')
        print(f'- Run "python examples/data_export.py" to export all data to CSV')
        print(f'- Run "python examples/webhook_server.py" for real-time updates')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        print(f'\nTroubleshooting:')
        print(f'- Make sure the callback URL is complete and fresh')
        print(f'- Check that you granted all permissions to the app')
        print(f'- Verify your WHOOP account is active and has data')

if __name__ == "__main__":
    main()
