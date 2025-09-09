#!/usr/bin/env python3
"""
WHOOP API Command Line Interface
Provides easy access to WHOOP data from the command line.
"""

import click
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import WhoopConfig
from .oauth import WhoopOAuth, extract_code_from_url
from .client import WhoopClient


@click.group()
@click.option('--config-file', '-c', help='Path to configuration file')
@click.pass_context
def cli(ctx, config_file):
    """WHOOP API Command Line Interface."""
    ctx.ensure_object(dict)
    
    # Load configuration
    try:
        if config_file:
            config = WhoopConfig.from_env(config_file)
        else:
            config = WhoopConfig.from_env()
        ctx.obj['config'] = config
    except Exception as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        click.echo("Run 'whoop setup' to configure your credentials", err=True)
        ctx.exit(1)


@cli.command()
def setup():
    """Set up WHOOP API credentials."""
    click.echo("🔧 WHOOP API Setup")
    click.echo("=" * 30)
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        click.echo("Creating .env file from template...")
        try:
            import shutil
            shutil.copy("config.env.example", ".env")
            click.echo("✅ Created .env file")
        except Exception as e:
            click.echo(f"❌ Failed to create .env file: {e}")
            return
    
    click.echo("\nPlease provide your WHOOP API credentials:")
    click.echo("(Get these from https://developer.whoop.com)")
    
    client_id = click.prompt("Client ID")
    client_secret = click.prompt("Client Secret", hide_input=True)
    redirect_uri = click.prompt("Redirect URI", default="http://localhost:8080/callback")
    
    # Update .env file
    env_content = f"""WHOOP_CLIENT_ID={client_id}
WHOOP_CLIENT_SECRET={client_secret}
WHOOP_REDIRECT_URI={redirect_uri}
WHOOP_API_BASE_URL=https://api.prod.whoop.com
WHOOP_AUTH_URL=https://api.prod.whoop.com/oauth/oauth2/auth
WHOOP_TOKEN_URL=https://api.prod.whoop.com/oauth/oauth2/token
WHOOP_RATE_LIMIT_RPM=100
WHOOP_RATE_LIMIT_RPD=10000
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    click.echo("✅ Configuration saved to .env")
    click.echo("\nNext steps:")
    click.echo("1. Run 'whoop auth' to authenticate")
    click.echo("2. Run 'whoop profile' to test your setup")


@cli.command()
@click.pass_context
def auth(ctx):
    """Authenticate with WHOOP API."""
    config = ctx.obj['config']
    oauth = WhoopOAuth(config)
    
    # Generate authorization URL
    auth_url = oauth.get_authorization_url()
    
    click.echo("🔐 WHOOP Authentication")
    click.echo("=" * 30)
    click.echo(f"Please visit this URL to authorize the application:")
    click.echo(f"\n{auth_url}\n")
    
    # Open URL in browser if possible
    try:
        import webbrowser
        webbrowser.open(auth_url)
        click.echo("🌐 Opened URL in your default browser")
    except:
        click.echo("💡 Copy the URL above and open it in your browser")
    
    click.echo("\nAfter authorization, you'll be redirected to a URL like:")
    click.echo("http://localhost:8080/callback?code=YOUR_CODE&state=STATE")
    click.echo("\nPlease paste the full URL here:")
    
    callback_url = click.prompt("Callback URL")
    
    try:
        code, state = extract_code_from_url(callback_url)
        token_response = oauth.exchange_code_for_token(code)
        
        click.echo("✅ Authentication successful!")
        click.echo(f"Token expires in: {token_response.expires_in} seconds")
        
    except Exception as e:
        click.echo(f"❌ Authentication failed: {e}")
        ctx.exit(1)


@cli.command()
@click.pass_context
def profile(ctx):
    """Get user profile information."""
    config = ctx.obj['config']
    oauth = WhoopOAuth(config)
    client = WhoopClient(config, oauth)
    
    try:
        profile = client.get_user_profile()
        
        click.echo("👤 User Profile")
        click.echo("=" * 20)
        click.echo(f"User ID: {profile.user_id}")
        click.echo(f"Email: {profile.email}")
        if profile.first_name:
            click.echo(f"Name: {profile.first_name} {profile.last_name or ''}")
        
        # Get body measurements
        try:
            body = client.get_body_measurements()
            click.echo("\n📏 Body Measurements")
            click.echo("-" * 20)
            if body.height_meter:
                click.echo(f"Height: {body.height_meter:.2f} meters")
            if body.weight_kilogram:
                click.echo(f"Weight: {body.weight_kilogram:.1f} kg")
            if body.max_heart_rate:
                click.echo(f"Max HR: {body.max_heart_rate} bpm")
        except Exception as e:
            click.echo(f"⚠️  Could not fetch body measurements: {e}")
        
    except Exception as e:
        click.echo(f"❌ Failed to get profile: {e}")
        click.echo("Run 'whoop auth' to authenticate first")
        ctx.exit(1)


@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to fetch')
@click.option('--output', '-o', help='Output file (JSON or CSV)')
@click.pass_context
def cycles(ctx, days, output):
    """Get cycle data."""
    config = ctx.obj['config']
    oauth = WhoopOAuth(config)
    client = WhoopClient(config, oauth)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cycles = client.get_cycles(start=start_date, end=end_date)
        
        if output:
            if output.endswith('.csv'):
                export_cycles_csv(cycles.records, output)
                click.echo(f"✅ Exported {len(cycles.records)} cycles to {output}")
            else:
                export_cycles_json(cycles.records, output)
                click.echo(f"✅ Exported {len(cycles.records)} cycles to {output}")
        else:
            click.echo(f"📊 Cycles (Last {days} days)")
            click.echo("=" * 30)
            click.echo(f"Found {len(cycles.records)} cycles")
            
            for i, cycle_data in enumerate(cycles.records[:5]):  # Show first 5
                cycle = client.get_cycle(cycle_data['id'])
                click.echo(f"\nCycle {i+1}: {cycle.start.date()}")
                if cycle.score and cycle.score.strain:
                    click.echo(f"  Strain: {cycle.score.strain:.1f}")
                if cycle.score and cycle.score.average_heart_rate:
                    click.echo(f"  Avg HR: {cycle.score.average_heart_rate} bpm")
                if cycle.score and cycle.score.kilojoules:
                    click.echo(f"  Energy: {cycle.score.kilojoules:.0f} kJ")
    
    except Exception as e:
        click.echo(f"❌ Failed to get cycles: {e}")
        ctx.exit(1)


@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to fetch')
@click.option('--output', '-o', help='Output file (JSON or CSV)')
@click.pass_context
def sleep(ctx, days, output):
    """Get sleep data."""
    config = ctx.obj['config']
    oauth = WhoopOAuth(config)
    client = WhoopClient(config, oauth)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sleep_data = client.get_sleep_data(start=start_date, end=end_date)
        
        if output:
            if output.endswith('.csv'):
                export_sleep_csv(sleep_data.records, output)
                click.echo(f"✅ Exported {len(sleep_data.records)} sleep records to {output}")
            else:
                export_sleep_json(sleep_data.records, output)
                click.echo(f"✅ Exported {len(sleep_data.records)} sleep records to {output}")
        else:
            click.echo(f"😴 Sleep Data (Last {days} days)")
            click.echo("=" * 30)
            click.echo(f"Found {len(sleep_data.records)} sleep records")
            
            for i, sleep_record in enumerate(sleep_data.records[:3]):  # Show first 3
                sleep = client.get_sleep(sleep_record['id'])
                click.echo(f"\nSleep {i+1}: {sleep.start.date()}")
                if sleep.score:
                    click.echo(f"  Score: {sleep.score:.1f}")
                if sleep.stage_summary:
                    total_sleep = (sleep.stage_summary.light_sleep_time_seconds or 0) + \
                                 (sleep.stage_summary.slow_wave_sleep_time_seconds or 0) + \
                                 (sleep.stage_summary.rem_sleep_time_seconds or 0)
                    click.echo(f"  Total Sleep: {total_sleep // 3600}h {(total_sleep % 3600) // 60}m")
                if sleep.respiratory_rate:
                    click.echo(f"  Respiratory Rate: {sleep.respiratory_rate:.1f} breaths/min")
    
    except Exception as e:
        click.echo(f"❌ Failed to get sleep data: {e}")
        ctx.exit(1)


@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to fetch')
@click.option('--output', '-o', help='Output file (JSON or CSV)')
@click.pass_context
def recovery(ctx, days, output):
    """Get recovery data."""
    config = ctx.obj['config']
    oauth = WhoopOAuth(config)
    client = WhoopClient(config, oauth)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        recovery_data = client.get_recovery_data(start=start_date, end=end_date)
        
        if output:
            if output.endswith('.csv'):
                export_recovery_csv(recovery_data.records, output)
                click.echo(f"✅ Exported {len(recovery_data.records)} recovery records to {output}")
            else:
                export_recovery_json(recovery_data.records, output)
                click.echo(f"✅ Exported {len(recovery_data.records)} recovery records to {output}")
        else:
            click.echo(f"💪 Recovery Data (Last {days} days)")
            click.echo("=" * 30)
            click.echo(f"Found {len(recovery_data.records)} recovery records")
            
            for i, recovery_record in enumerate(recovery_data.records[:3]):  # Show first 3
                recovery = client.get_recovery(recovery_record['id'])
                click.echo(f"\nRecovery {i+1}: {recovery.start.date()}")
                if recovery.score:
                    click.echo(f"  Score: {recovery.score:.1f}")
                if recovery.resting_heart_rate:
                    click.echo(f"  Resting HR: {recovery.resting_heart_rate} bpm")
                if recovery.hrv_rmssd_milli_seconds:
                    click.echo(f"  HRV: {recovery.hrv_rmssd_milli_seconds:.1f} ms")
                if recovery.spo2_percentage:
                    click.echo(f"  SpO2: {recovery.spo2_percentage:.1f}%")
    
    except Exception as e:
        click.echo(f"❌ Failed to get recovery data: {e}")
        ctx.exit(1)


@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to fetch')
@click.option('--output', '-o', help='Output file (JSON or CSV)')
@click.pass_context
def workouts(ctx, days, output):
    """Get workout data."""
    config = ctx.obj['config']
    oauth = WhoopOAuth(config)
    client = WhoopClient(config, oauth)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        workouts = client.get_workouts(start=start_date, end=end_date)
        
        if output:
            if output.endswith('.csv'):
                export_workouts_csv(workouts.records, output)
                click.echo(f"✅ Exported {len(workouts.records)} workouts to {output}")
            else:
                export_workouts_json(workouts.records, output)
                click.echo(f"✅ Exported {len(workouts.records)} workouts to {output}")
        else:
            click.echo(f"🏃 Workouts (Last {days} days)")
            click.echo("=" * 30)
            click.echo(f"Found {len(workouts.records)} workouts")
            
            for i, workout_record in enumerate(workouts.records[:3]):  # Show first 3
                workout = client.get_workout(workout_record['id'])
                click.echo(f"\nWorkout {i+1}: {workout.start.date()}")
                click.echo(f"  Sport: {workout.sport_name}")
                if workout.score and workout.score.strain:
                    click.echo(f"  Strain: {workout.score.strain:.1f}")
                if workout.score and workout.score.kilojoules:
                    click.echo(f"  Energy: {workout.score.kilojoules:.0f} kJ")
                if workout.distance_meter:
                    click.echo(f"  Distance: {workout.distance_meter/1000:.2f} km")
    
    except Exception as e:
        click.echo(f"❌ Failed to get workouts: {e}")
        ctx.exit(1)


@cli.command()
@click.option('--days', '-d', default=30, help='Number of days to export')
@click.option('--output-dir', '-o', default='whoop_export', help='Output directory')
@click.pass_context
def export(ctx, days, output_dir):
    """Export all data to CSV files."""
    config = ctx.obj['config']
    oauth = WhoopOAuth(config)
    client = WhoopClient(config, oauth)
    
    try:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        click.echo(f"📊 Exporting WHOOP data (Last {days} days)")
        click.echo("=" * 40)
        click.echo(f"Output directory: {output_path.absolute()}")
        
        # Export cycles
        click.echo("\n1. Exporting cycles...")
        cycles = client.get_all_cycles(start=start_date, end=end_date)
        export_cycles_csv(cycles, output_path / "cycles.csv")
        click.echo(f"   ✅ {len(cycles)} cycles")
        
        # Export sleep
        click.echo("2. Exporting sleep data...")
        sleep_records = client.get_all_sleep_data(start=start_date, end=end_date)
        export_sleep_csv(sleep_records, output_path / "sleep.csv")
        click.echo(f"   ✅ {len(sleep_records)} sleep records")
        
        # Export recovery
        click.echo("3. Exporting recovery data...")
        recovery_records = client.get_all_recovery_data(start=start_date, end=end_date)
        export_recovery_csv(recovery_records, output_path / "recovery.csv")
        click.echo(f"   ✅ {len(recovery_records)} recovery records")
        
        # Export workouts
        click.echo("4. Exporting workouts...")
        workouts = client.get_all_workouts(start=start_date, end=end_date)
        export_workouts_csv(workouts, output_path / "workouts.csv")
        click.echo(f"   ✅ {len(workouts)} workouts")
        
        # Export metadata
        click.echo("5. Exporting metadata...")
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
            }
        }
        
        with open(output_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        click.echo("   ✅ metadata.json")
        
        click.echo(f"\n🎉 Export completed! Check {output_path.absolute()}")
        
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")
        ctx.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show API status and rate limiting information."""
    config = ctx.obj['config']
    oauth = WhoopOAuth(config)
    client = WhoopClient(config, oauth)
    
    try:
        # Test connection
        if client.test_connection():
            click.echo("✅ API Connection: OK")
        else:
            click.echo("❌ API Connection: Failed")
            return
        
        # Get rate limit status
        status = client.get_rate_limit_status()
        click.echo(f"📊 Rate Limiting:")
        click.echo(f"   Minute: {status['minute_requests']}/{status['minute_limit']}")
        click.echo(f"   Day: {status['day_requests']}/{status['day_limit']}")
        click.echo(f"   Can make request: {'Yes' if status['can_make_request'] else 'No'}")
        
        # Get token info
        token_info = oauth.get_token_info()
        click.echo(f"🔐 Authentication:")
        click.echo(f"   Has access token: {'Yes' if token_info['has_access_token'] else 'No'}")
        click.echo(f"   Has refresh token: {'Yes' if token_info['has_refresh_token'] else 'No'}")
        if token_info['expires_at']:
            click.echo(f"   Expires at: {token_info['expires_at']}")
        click.echo(f"   Is expired: {'Yes' if token_info['is_expired'] else 'No'}")
        
    except Exception as e:
        click.echo(f"❌ Status check failed: {e}")


# Export helper functions
def export_cycles_csv(cycles, filename):
    """Export cycles to CSV."""
    if not cycles:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'user_id', 'start', 'end', 'timezone_offset', 'strain', 'kilojoules', 'average_heart_rate', 'max_heart_rate']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for cycle in cycles:
            writer.writerow({
                'id': cycle.id,
                'user_id': cycle.user_id,
                'start': cycle.start.isoformat(),
                'end': cycle.end.isoformat(),
                'timezone_offset': cycle.timezone_offset,
                'strain': cycle.score.strain if cycle.score and cycle.score.strain else None,
                'kilojoules': cycle.score.kilojoules if cycle.score and cycle.score.kilojoules else None,
                'average_heart_rate': cycle.score.average_heart_rate if cycle.score and cycle.score.average_heart_rate else None,
                'max_heart_rate': cycle.score.max_heart_rate if cycle.score and cycle.score.max_heart_rate else None,
            })


def export_sleep_csv(sleep_records, filename):
    """Export sleep records to CSV."""
    if not sleep_records:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'user_id', 'start', 'end', 'timezone_offset', 'nap', 'score', 'time_in_bed_seconds', 'awake_time_seconds', 'light_sleep_time_seconds', 'slow_wave_sleep_time_seconds', 'rem_sleep_time_seconds', 'number_of_disturbances', 'respiratory_rate']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for sleep in sleep_records:
            writer.writerow({
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
            })


def export_recovery_csv(recovery_records, filename):
    """Export recovery records to CSV."""
    if not recovery_records:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'user_id', 'cycle_id', 'start', 'end', 'timezone_offset', 'score', 'resting_heart_rate', 'hrv_rmssd_milli_seconds', 'spo2_percentage', 'skin_temp_celsius']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for recovery in recovery_records:
            writer.writerow({
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
            })


def export_workouts_csv(workouts, filename):
    """Export workouts to CSV."""
    if not workouts:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'user_id', 'start', 'end', 'timezone_offset', 'sport_id', 'sport_name', 'strain', 'average_heart_rate', 'max_heart_rate', 'kilojoules', 'percent_recorded', 'distance_meter', 'altitude_gain_meter', 'altitude_change_meter']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for workout in workouts:
            writer.writerow({
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
            })


# JSON export functions
def export_cycles_json(cycles, filename):
    """Export cycles to JSON."""
    data = [cycle.dict() for cycle in cycles]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def export_sleep_json(sleep_records, filename):
    """Export sleep records to JSON."""
    data = [sleep.dict() for sleep in sleep_records]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def export_recovery_json(recovery_records, filename):
    """Export recovery records to JSON."""
    data = [recovery.dict() for recovery in recovery_records]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def export_workouts_json(workouts, filename):
    """Export workouts to JSON."""
    data = [workout.dict() for workout in workouts]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)


if __name__ == '__main__':
    cli()
