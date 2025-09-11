#!/usr/bin/env python3
"""
Display all WHOOP data in a structured, well-visualized way
"""

import sys
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth, extract_code_from_url
from src.client import WhoopClient

def format_duration(seconds):
    """Format seconds into hours and minutes"""
    if not seconds:
        return "N/A"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def format_score(score):
    """Format score with color coding"""
    if not score:
        return "N/A"
    if isinstance(score, dict):
        return f"{score.get('score', 'N/A')}"
    return f"{score:.1f}"

def get_score_color(score):
    """Get color based on score value"""
    if not score:
        return "white"
    if isinstance(score, dict):
        score_val = score.get('score', 0)
    else:
        score_val = score
    
    if score_val >= 80:
        return "green"
    elif score_val >= 60:
        return "yellow"
    else:
        return "red"

def main():
    console = Console()
    
    # Your callback URL (you'll need to provide a fresh one)
    callback_url = input("Enter your fresh WHOOP callback URL: ").strip()
    
    if not callback_url:
        console.print("❌ No callback URL provided", style="red")
        return
    
    console.print(Panel.fit("🏃‍♂️ WHOOP Data Dashboard - Marc Baumholz", style="bold blue"))
    
    try:
        # Load configuration and authenticate
        config = WhoopConfig.from_env()
        oauth = WhoopOAuth(config)
        code, state = extract_code_from_url(callback_url)
        token_response = oauth.exchange_code_for_token(code)
        client = WhoopClient(config, oauth)
        
        console.print("✅ [green]Connected to WHOOP API[/green]")
        
        # Get profile
        profile = client.get_user_profile()
        
        # Display profile
        profile_table = Table(title="👤 Profile Information", show_header=True, header_style="bold magenta")
        profile_table.add_column("Field", style="cyan")
        profile_table.add_column("Value", style="white")
        
        profile_table.add_row("User ID", str(profile.user_id))
        profile_table.add_row("Email", profile.email)
        profile_table.add_row("Name", f"{profile.first_name} {profile.last_name or ''}")
        
        console.print(profile_table)
        console.print()
        
        # Get all data without date filters
        console.print("📊 [bold]Retrieving all your WHOOP data...[/bold]")
        
        # Cycles
        cycles = client.get_cycles(limit=25)
        console.print(f"📈 [green]Found {len(cycles.records)} cycles[/green]")
        
        if cycles.records:
            cycles_table = Table(title="📈 Daily Cycles (Physiological Days)", show_header=True, header_style="bold blue")
            cycles_table.add_column("Date", style="cyan")
            cycles_table.add_column("Strain", style="white", justify="center")
            cycles_table.add_column("Avg HR", style="white", justify="center")
            cycles_table.add_column("Max HR", style="white", justify="center")
            cycles_table.add_column("Energy (kJ)", style="white", justify="center")
            
            for cycle_data in cycles.records[:10]:  # Show first 10
                try:
                    cycle = client.get_cycle(cycle_data['id'])
                    strain = cycle.score.strain if cycle.score and cycle.score.strain else "N/A"
                    avg_hr = cycle.score.average_heart_rate if cycle.score and cycle.score.average_heart_rate else "N/A"
                    max_hr = cycle.score.max_heart_rate if cycle.score and cycle.score.max_heart_rate else "N/A"
                    energy = cycle.score.kilojoules if cycle.score and cycle.score.kilojoules else "N/A"
                    
                    cycles_table.add_row(
                        str(cycle.start.date()),
                        f"[{get_score_color(strain)}]{strain}[/{get_score_color(strain)}]",
                        str(avg_hr),
                        str(max_hr),
                        f"{energy:.0f}" if isinstance(energy, (int, float)) else str(energy)
                    )
                except Exception as e:
                    cycles_table.add_row(str(cycle_data.get('start', 'N/A')), "Error", "Error", "Error", "Error")
            
            console.print(cycles_table)
            console.print()
        
        # Sleep
        sleep_data = client.get_sleep_data(limit=25)
        console.print(f"😴 [green]Found {len(sleep_data.records)} sleep records[/green]")
        
        if sleep_data.records:
            sleep_table = Table(title="😴 Sleep Analysis", show_header=True, header_style="bold purple")
            sleep_table.add_column("Date", style="cyan")
            sleep_table.add_column("Score", style="white", justify="center")
            sleep_table.add_column("Total Sleep", style="white", justify="center")
            sleep_table.add_column("Light Sleep", style="white", justify="center")
            sleep_table.add_column("Deep Sleep", style="white", justify="center")
            sleep_table.add_column("REM Sleep", style="white", justify="center")
            sleep_table.add_column("Resp Rate", style="white", justify="center")
            
            for sleep_record in sleep_data.records[:10]:  # Show first 10
                try:
                    sleep = client.get_sleep(sleep_record['id'])
                    
                    # Extract sleep score
                    sleep_score = "N/A"
                    if sleep.score:
                        if isinstance(sleep.score, dict):
                            sleep_score = sleep.score.get('score', 'N/A')
                        else:
                            sleep_score = sleep.score
                    
                    # Calculate total sleep time
                    total_sleep = 0
                    light_sleep = 0
                    deep_sleep = 0
                    rem_sleep = 0
                    
                    if sleep.stage_summary:
                        light_sleep = sleep.stage_summary.light_sleep_time_seconds or 0
                        deep_sleep = sleep.stage_summary.slow_wave_sleep_time_seconds or 0
                        rem_sleep = sleep.stage_summary.rem_sleep_time_seconds or 0
                        total_sleep = light_sleep + deep_sleep + rem_sleep
                    
                    sleep_table.add_row(
                        str(sleep.start.date()),
                        f"[{get_score_color(sleep_score)}]{sleep_score}[/{get_score_color(sleep_score)}]",
                        format_duration(total_sleep),
                        format_duration(light_sleep),
                        format_duration(deep_sleep),
                        format_duration(rem_sleep),
                        f"{sleep.respiratory_rate:.1f}" if sleep.respiratory_rate else "N/A"
                    )
                except Exception as e:
                    sleep_table.add_row(str(sleep_record.get('start', 'N/A')), "Error", "Error", "Error", "Error", "Error", "Error")
            
            console.print(sleep_table)
            console.print()
        
        # Recovery
        recovery_data = client.get_recovery_data(limit=25)
        console.print(f"💪 [green]Found {len(recovery_data.records)} recovery records[/green]")
        
        if recovery_data.records:
            recovery_table = Table(title="💪 Recovery Metrics", show_header=True, header_style="bold green")
            recovery_table.add_column("Date", style="cyan")
            recovery_table.add_column("Score", style="white", justify="center")
            recovery_table.add_column("Resting HR", style="white", justify="center")
            recovery_table.add_column("HRV (ms)", style="white", justify="center")
            recovery_table.add_column("SpO2 (%)", style="white", justify="center")
            recovery_table.add_column("Skin Temp (°C)", style="white", justify="center")
            
            for recovery_record in recovery_data.records[:10]:  # Show first 10
                try:
                    recovery = client.get_recovery(recovery_record['id'])
                    
                    recovery_table.add_row(
                        str(recovery.start.date()),
                        f"[{get_score_color(recovery.score)}]{recovery.score or 'N/A'}[/{get_score_color(recovery.score)}]",
                        str(recovery.resting_heart_rate or "N/A"),
                        f"{recovery.hrv_rmssd_milli_seconds:.1f}" if recovery.hrv_rmssd_milli_seconds else "N/A",
                        f"{recovery.spo2_percentage:.1f}" if recovery.spo2_percentage else "N/A",
                        f"{recovery.skin_temp_celsius:.1f}" if recovery.skin_temp_celsius else "N/A"
                    )
                except Exception as e:
                    recovery_table.add_row(str(recovery_record.get('start', 'N/A')), "Error", "Error", "Error", "Error", "Error")
            
            console.print(recovery_table)
            console.print()
        
        # Workouts
        workouts = client.get_workouts(limit=25)
        console.print(f"🏃 [green]Found {len(workouts.records)} workouts[/green]")
        
        if workouts.records:
            workout_table = Table(title="🏃 Workout Activities", show_header=True, header_style="bold red")
            workout_table.add_column("Date", style="cyan")
            workout_table.add_column("Sport", style="white")
            workout_table.add_column("Strain", style="white", justify="center")
            workout_table.add_column("Avg HR", style="white", justify="center")
            workout_table.add_column("Max HR", style="white", justify="center")
            workout_table.add_column("Energy (kJ)", style="white", justify="center")
            workout_table.add_column("Distance (km)", style="white", justify="center")
            
            for workout_record in workouts.records[:10]:  # Show first 10
                try:
                    workout = client.get_workout(workout_record['id'])
                    
                    strain = workout.score.strain if workout.score and workout.score.strain else "N/A"
                    avg_hr = workout.score.average_heart_rate if workout.score and workout.score.average_heart_rate else "N/A"
                    max_hr = workout.score.max_heart_rate if workout.score and workout.score.max_heart_rate else "N/A"
                    energy = workout.score.kilojoules if workout.score and workout.score.kilojoules else "N/A"
                    distance = f"{workout.distance_meter/1000:.2f}" if workout.distance_meter else "N/A"
                    
                    workout_table.add_row(
                        str(workout.start.date()),
                        workout.sport_name,
                        f"[{get_score_color(strain)}]{strain}[/{get_score_color(strain)}]",
                        str(avg_hr),
                        str(max_hr),
                        f"{energy:.0f}" if isinstance(energy, (int, float)) else str(energy),
                        distance
                    )
                except Exception as e:
                    workout_table.add_row(str(workout_record.get('start', 'N/A')), "Error", "Error", "Error", "Error", "Error", "Error")
            
            console.print(workout_table)
            console.print()
        
        # Summary statistics
        console.print(Panel.fit("📊 Data Summary", style="bold yellow"))
        
        summary_data = [
            f"👤 Profile: {profile.first_name} {profile.last_name or ''}",
            f"📈 Cycles: {len(cycles.records)} records",
            f"😴 Sleep: {len(sleep_data.records)} records", 
            f"💪 Recovery: {len(recovery_data.records)} records",
            f"🏃 Workouts: {len(workouts.records)} records"
        ]
        
        for item in summary_data:
            console.print(f"  {item}")
        
        console.print()
        console.print("🎉 [bold green]All your WHOOP data has been successfully retrieved and displayed![/bold green]")
        
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        console.print("Please provide a fresh callback URL from the OAuth flow")

if __name__ == "__main__":
    main()
