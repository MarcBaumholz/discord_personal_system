#!/usr/bin/env python3
"""
WHOOP data export example.
Exports all available data to CSV files for analysis.
"""

import os
import sys
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth, extract_code_from_url
from src.client import WhoopClient


def export_cycles_to_csv(cycles, filename):
    """Export cycles data to CSV."""
    if not cycles:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'id', 'user_id', 'start', 'end', 'timezone_offset',
            'strain', 'kilojoules', 'average_heart_rate', 'max_heart_rate'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for cycle in cycles:
            row = {
                'id': cycle.id,
                'user_id': cycle.user_id,
                'start': cycle.start.isoformat(),
                'end': cycle.end.isoformat(),
                'timezone_offset': cycle.timezone_offset,
                'strain': cycle.score.strain if cycle.score and cycle.score.strain else None,
                'kilojoules': cycle.score.kilojoules if cycle.score and cycle.score.kilojoules else None,
                'average_heart_rate': cycle.score.average_heart_rate if cycle.score and cycle.score.average_heart_rate else None,
                'max_heart_rate': cycle.score.max_heart_rate if cycle.score and cycle.score.max_heart_rate else None,
            }
            writer.writerow(row)


def export_sleep_to_csv(sleep_records, filename):
    """Export sleep data to CSV."""
    if not sleep_records:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'id', 'user_id', 'start', 'end', 'timezone_offset', 'nap', 'score',
            'time_in_bed_seconds', 'awake_time_seconds', 'light_sleep_time_seconds',
            'slow_wave_sleep_time_seconds', 'rem_sleep_time_seconds', 'number_of_disturbances',
            'respiratory_rate', 'sleep_performance_percentage', 'sleep_consistency_percentage',
            'sleep_efficiency_percentage'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for sleep in sleep_records:
            row = {
                'id': sleep.id,
                'user_id': sleep.user_id,
                'start': sleep.start.isoformat(),
                'end': sleep.end.isoformat(),
                'timezone_offset': sleep.timezone_offset,
                'nap': sleep.nap,
                'score': sleep.score,
                'time_in_bed_seconds': sleep.stage_summary.time_in_bed_seconds if sleep.stage_summary else None,
                'awake_time_seconds': sleep.stage_summary.awake_time_seconds if sleep.stage_summary else None,
                'light_sleep_time_seconds': sleep.stage_summary.light_sleep_time_seconds if sleep.stage_summary else None,
                'slow_wave_sleep_time_seconds': sleep.stage_summary.slow_wave_sleep_time_seconds if sleep.stage_summary else None,
                'rem_sleep_time_seconds': sleep.stage_summary.rem_sleep_time_seconds if sleep.stage_summary else None,
                'number_of_disturbances': sleep.stage_summary.number_of_disturbances if sleep.stage_summary else None,
                'respiratory_rate': sleep.respiratory_rate,
                'sleep_performance_percentage': sleep.sleep_performance_percentage,
                'sleep_consistency_percentage': sleep.sleep_consistency_percentage,
                'sleep_efficiency_percentage': sleep.sleep_efficiency_percentage,
            }
            writer.writerow(row)


def export_recovery_to_csv(recovery_records, filename):
    """Export recovery data to CSV."""
    if not recovery_records:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'id', 'user_id', 'cycle_id', 'start', 'end', 'timezone_offset',
            'score', 'resting_heart_rate', 'hrv_rmssd_milli_seconds',
            'spo2_percentage', 'skin_temp_celsius'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for recovery in recovery_records:
            row = {
                'id': recovery.id,
                'user_id': recovery.user_id,
                'cycle_id': recovery.cycle_id,
                'start': recovery.start.isoformat(),
                'end': recovery.end.isoformat(),
                'timezone_offset': recovery.timezone_offset,
                'score': recovery.score,
                'resting_heart_rate': recovery.resting_heart_rate,
                'hrv_rmssd_milli_seconds': recovery.hrv_rmssd_milli_seconds,
                'spo2_percentage': recovery.spo2_percentage,
                'skin_temp_celsius': recovery.skin_temp_celsius,
            }
            writer.writerow(row)


def export_workouts_to_csv(workouts, filename):
    """Export workouts data to CSV."""
    if not workouts:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'id', 'user_id', 'start', 'end', 'timezone_offset', 'sport_id', 'sport_name',
            'strain', 'average_heart_rate', 'max_heart_rate', 'kilojoules', 'percent_recorded',
            'distance_meter', 'altitude_gain_meter', 'altitude_change_meter'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for workout in workouts:
            row = {
                'id': workout.id,
                'user_id': workout.user_id,
                'start': workout.start.isoformat(),
                'end': workout.end.isoformat(),
                'timezone_offset': workout.timezone_offset,
                'sport_id': workout.sport_id,
                'sport_name': workout.sport_name,
                'strain': workout.score.strain if workout.score and workout.score.strain else None,
                'average_heart_rate': workout.score.average_heart_rate if workout.score and workout.score.average_heart_rate else None,
                'max_heart_rate': workout.score.max_heart_rate if workout.score and workout.score.max_heart_rate else None,
                'kilojoules': workout.score.kilojoules if workout.score and workout.score.kilojoules else None,
                'percent_recorded': workout.score.percent_recorded if workout.score and workout.score.percent_recorded else None,
                'distance_meter': workout.distance_meter,
                'altitude_gain_meter': workout.altitude_gain_meter,
                'altitude_change_meter': workout.altitude_change_meter,
            }
            writer.writerow(row)


def main():
    """Main export function."""
    print("WHOOP Data Export Example")
    print("=" * 30)
    
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
    
    # Get authorization URL
    auth_url = oauth.get_authorization_url()
    print(f"\n1. Please visit this URL to authorize the application:")
    print(f"   {auth_url}")
    
    # Get authorization code from user
    print("\n2. After authorization, paste the full callback URL here:")
    callback_url = input("Callback URL: ").strip()
    
    try:
        # Extract code and exchange for tokens
        code, state = extract_code_from_url(callback_url)
        token_response = oauth.exchange_code_for_token(code)
        print("✓ Access token obtained successfully")
        
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return
    
    # Initialize API client
    client = WhoopClient(config, oauth)
    print("✓ WHOOP API client initialized")
    
    # Test connection
    if not client.test_connection():
        print("✗ API connection failed")
        return
    
    print("✓ API connection successful")
    
    # Create output directory
    output_dir = Path("whoop_export")
    output_dir.mkdir(exist_ok=True)
    print(f"\n3. Exporting data to: {output_dir.absolute()}")
    
    # Get date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    print(f"   Date range: {start_date.date()} to {end_date.date()}")
    
    # Export cycles
    try:
        print("\n4. Exporting cycles...")
        cycles = client.get_all_cycles(start=start_date, end=end_date)
        export_cycles_to_csv(cycles, output_dir / "cycles.csv")
        print(f"   ✓ Exported {len(cycles)} cycles")
    except Exception as e:
        print(f"   ✗ Failed to export cycles: {e}")
    
    # Export sleep data
    try:
        print("5. Exporting sleep data...")
        sleep_records = client.get_all_sleep_data(start=start_date, end=end_date)
        export_sleep_to_csv(sleep_records, output_dir / "sleep.csv")
        print(f"   ✓ Exported {len(sleep_records)} sleep records")
    except Exception as e:
        print(f"   ✗ Failed to export sleep data: {e}")
    
    # Export recovery data
    try:
        print("6. Exporting recovery data...")
        recovery_records = client.get_all_recovery_data(start=start_date, end=end_date)
        export_recovery_to_csv(recovery_records, output_dir / "recovery.csv")
        print(f"   ✓ Exported {len(recovery_records)} recovery records")
    except Exception as e:
        print(f"   ✗ Failed to export recovery data: {e}")
    
    # Export workouts
    try:
        print("7. Exporting workouts...")
        workouts = client.get_all_workouts(start=start_date, end=end_date)
        export_workouts_to_csv(workouts, output_dir / "workouts.csv")
        print(f"   ✓ Exported {len(workouts)} workouts")
    except Exception as e:
        print(f"   ✗ Failed to export workouts: {e}")
    
    # Export metadata
    try:
        print("8. Exporting metadata...")
        profile = client.get_user_profile()
        body = client.get_body_measurements()
        
        metadata = {
            "export_timestamp": datetime.now().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "user_profile": {
                "user_id": profile.user_id,
                "email": profile.email,
                "first_name": profile.first_name,
                "last_name": profile.last_name
            },
            "body_measurements": {
                "height_meter": body.height_meter,
                "weight_kilogram": body.weight_kilogram,
                "max_heart_rate": body.max_heart_rate
            },
            "rate_limit_status": client.get_rate_limit_status()
        }
        
        with open(output_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        print("   ✓ Exported metadata")
        
    except Exception as e:
        print(f"   ✗ Failed to export metadata: {e}")
    
    print(f"\n✓ Export completed! Check the '{output_dir}' directory for CSV files.")
    print("\nFiles created:")
    for file in output_dir.glob("*.csv"):
        print(f"   - {file.name}")
    print(f"   - metadata.json")


if __name__ == "__main__":
    main()
