#!/usr/bin/env python3
"""
Test WHOOP API without date filters
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth, extract_code_from_url
from src.client import WhoopClient

def main():
    # Your callback URL
    callback_url = 'http://localhost:8080/callback?code=TKsKFSgN1ksOWEOLtVK07cplNnSGiv-sbAILQa-Ncjg.mG1uE-6h5HG_7WUSk9hirdaiYLpCsgcI59SqKPzOIgQ&scope=read%3Aprofile%20read%3Abody_measurement%20read%3Acycles%20read%3Asleep%20read%3Arecovery%20read%3Aworkout%20offline&state=7FQlK51ghkRVxkscIupzOh4g6D3DvHFDfVU8BkBcUDs'

    print('🔍 Testing WHOOP API without date filters...')
    print('=' * 50)

    try:
        config = WhoopConfig.from_env()
        oauth = WhoopOAuth(config)
        code, state = extract_code_from_url(callback_url)
        token_response = oauth.exchange_code_for_token(code)
        client = WhoopClient(config, oauth)
        
        print('✅ Connected to WHOOP API')
        
        # Try cycles without date filter
        print('\n📈 Testing cycles (no date filter)...')
        try:
            cycles = client.get_cycles(limit=5)
            print(f'   Found {len(cycles.records)} cycles')
            if cycles.records:
                for i, cycle_data in enumerate(cycles.records[:2]):
                    cycle = client.get_cycle(cycle_data['id'])
                    print(f'   Cycle {i+1}: {cycle.start.date()}')
                    if cycle.score and cycle.score.strain:
                        print(f'     Strain: {cycle.score.strain:.1f}')
                    if cycle.score and cycle.score.average_heart_rate:
                        print(f'     Avg HR: {cycle.score.average_heart_rate} bpm')
            else:
                print('   No cycles found')
        except Exception as e:
            print(f'   Error: {e}')
        
        # Try sleep without date filter
        print('\n😴 Testing sleep (no date filter)...')
        try:
            sleep_data = client.get_sleep_data(limit=5)
            print(f'   Found {len(sleep_data.records)} sleep records')
            if sleep_data.records:
                for i, sleep_record in enumerate(sleep_data.records[:2]):
                    sleep = client.get_sleep(sleep_record['id'])
                    print(f'   Sleep {i+1}: {sleep.start.date()}')
                    if sleep.score:
                        print(f'     Score: {sleep.score:.1f}')
                    if sleep.stage_summary:
                        total_sleep = (sleep.stage_summary.light_sleep_time_seconds or 0) + (sleep.stage_summary.slow_wave_sleep_time_seconds or 0) + (sleep.stage_summary.rem_sleep_time_seconds or 0)
                        print(f'     Total Sleep: {total_sleep // 3600}h {(total_sleep % 3600) // 60}m')
            else:
                print('   No sleep records found')
        except Exception as e:
            print(f'   Error: {e}')
        
        # Try recovery without date filter
        print('\n💪 Testing recovery (no date filter)...')
        try:
            recovery_data = client.get_recovery_data(limit=5)
            print(f'   Found {len(recovery_data.records)} recovery records')
            if recovery_data.records:
                for i, recovery_record in enumerate(recovery_data.records[:2]):
                    recovery = client.get_recovery(recovery_record['id'])
                    print(f'   Recovery {i+1}: {recovery.start.date()}')
                    if recovery.score:
                        print(f'     Score: {recovery.score:.1f}')
                    if recovery.resting_heart_rate:
                        print(f'     Resting HR: {recovery.resting_heart_rate} bpm')
                    if recovery.hrv_rmssd_milli_seconds:
                        print(f'     HRV: {recovery.hrv_rmssd_milli_seconds:.1f} ms')
            else:
                print('   No recovery records found')
        except Exception as e:
            print(f'   Error: {e}')
        
        # Try workouts without date filter
        print('\n🏃 Testing workouts (no date filter)...')
        try:
            workouts = client.get_workouts(limit=5)
            print(f'   Found {len(workouts.records)} workouts')
            if workouts.records:
                for i, workout_record in enumerate(workouts.records[:2]):
                    workout = client.get_workout(workout_record['id'])
                    print(f'   Workout {i+1}: {workout.start.date()}')
                    print(f'     Sport: {workout.sport_name}')
                    if workout.score and workout.score.strain:
                        print(f'     Strain: {workout.score.strain:.1f}')
                    if workout.score and workout.score.kilojoules:
                        print(f'     Energy: {workout.score.kilojoules:.0f} kJ')
            else:
                print('   No workouts found')
        except Exception as e:
            print(f'   Error: {e}')
        
        print('\n🎉 Test completed!')
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    main()
