#!/usr/bin/env python3
"""
Quick authentication and data display with token persistence
"""

import sys
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth
from src.client import WhoopClient
from src.token_manager import TokenManager

def main():
    console = Console()
    
    console.print(Panel.fit("🏃‍♂️ WHOOP Quick Auth & Data Display", style="bold blue"))
    
    try:
        # Load configuration
        config = WhoopConfig.from_env()
        oauth = WhoopOAuth(config)
        token_manager = TokenManager()
        client = WhoopClient(config, oauth, token_manager)
        
        # Check if we have saved tokens
        if client.is_authenticated():
            console.print("✅ [green]Using saved authentication tokens[/green]")
        else:
            console.print("🔐 [yellow]No saved tokens found. Need to authenticate...[/yellow]")
            
            # Generate fresh authorization URL
            auth_url = oauth.get_authorization_url()
            console.print(f"\n🔗 [bold]Click this URL to authorize:[/bold]")
            console.print(f"[cyan]{auth_url}[/cyan]")
            console.print("\n⏰ You have 10 minutes to complete this...")
            
            callback_url = input("\n📋 Paste the callback URL here: ").strip()
            
            if not callback_url:
                console.print("❌ No callback URL provided", style="red")
                return
            
            if client.authenticate_with_callback(callback_url):
                console.print("✅ [green]Authentication successful! Tokens saved for future use.[/green]")
            else:
                console.print("❌ [red]Authentication failed[/red]")
                return
        
        # Get profile
        console.print("\n📊 [bold]Retrieving your WHOOP data...[/bold]")
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
        
        # Get cycles
        cycles = client.get_cycles(limit=10)
        console.print(f"📈 [green]Found {len(cycles.records)} cycles[/green]")
        
        if cycles.records:
            cycles_table = Table(title="📈 Recent Daily Cycles", show_header=True, header_style="bold blue")
            cycles_table.add_column("Date", style="cyan")
            cycles_table.add_column("Strain", style="white", justify="center")
            cycles_table.add_column("Avg HR", style="white", justify="center")
            cycles_table.add_column("Max HR", style="white", justify="center")
            cycles_table.add_column("Energy (kJ)", style="white", justify="center")
            
            for cycle_data in cycles.records[:5]:  # Show first 5
                try:
                    cycle = client.get_cycle(cycle_data['id'])
                    strain = cycle.score.strain if cycle.score and cycle.score.strain else "N/A"
                    avg_hr = cycle.score.average_heart_rate if cycle.score and cycle.score.average_heart_rate else "N/A"
                    max_hr = cycle.score.max_heart_rate if cycle.score and cycle.score.max_heart_rate else "N/A"
                    energy = cycle.score.kilojoules if cycle.score and cycle.score.kilojoules else "N/A"
                    
                    cycles_table.add_row(
                        str(cycle.start.date()),
                        str(strain),
                        str(avg_hr),
                        str(max_hr),
                        f"{energy:.0f}" if isinstance(energy, (int, float)) else str(energy)
                    )
                except Exception as e:
                    cycles_table.add_row(str(cycle_data.get('start', 'N/A')), "Error", "Error", "Error", "Error")
            
            console.print(cycles_table)
            console.print()
        
        # Get sleep data
        sleep_data = client.get_sleep_data(limit=10)
        console.print(f"😴 [green]Found {len(sleep_data.records)} sleep records[/green]")
        
        if sleep_data.records:
            sleep_table = Table(title="😴 Recent Sleep Analysis", show_header=True, header_style="bold purple")
            sleep_table.add_column("Date", style="cyan")
            sleep_table.add_column("Score", style="white", justify="center")
            sleep_table.add_column("Total Sleep", style="white", justify="center")
            sleep_table.add_column("Light Sleep", style="white", justify="center")
            sleep_table.add_column("Deep Sleep", style="white", justify="center")
            sleep_table.add_column("REM Sleep", style="white", justify="center")
            
            for sleep_record in sleep_data.records[:5]:  # Show first 5
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
                    
                    def format_duration(seconds):
                        if not seconds:
                            return "N/A"
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        return f"{hours}h {minutes}m"
                    
                    sleep_table.add_row(
                        str(sleep.start.date()),
                        str(sleep_score),
                        format_duration(total_sleep),
                        format_duration(light_sleep),
                        format_duration(deep_sleep),
                        format_duration(rem_sleep)
                    )
                except Exception as e:
                    sleep_table.add_row(str(sleep_record.get('start', 'N/A')), "Error", "Error", "Error", "Error", "Error")
            
            console.print(sleep_table)
            console.print()
        
        # Get recovery data
        recovery_data = client.get_recovery_data(limit=10)
        console.print(f"💪 [green]Found {len(recovery_data.records)} recovery records[/green]")
        
        if recovery_data.records:
            recovery_table = Table(title="💪 Recent Recovery Metrics", show_header=True, header_style="bold green")
            recovery_table.add_column("Date", style="cyan")
            recovery_table.add_column("Score", style="white", justify="center")
            recovery_table.add_column("Resting HR", style="white", justify="center")
            recovery_table.add_column("HRV (ms)", style="white", justify="center")
            recovery_table.add_column("SpO2 (%)", style="white", justify="center")
            
            for recovery_record in recovery_data.records[:5]:  # Show first 5
                try:
                    recovery = client.get_recovery(recovery_record['id'])
                    
                    recovery_table.add_row(
                        str(recovery.start.date()),
                        str(recovery.score or 'N/A'),
                        str(recovery.resting_heart_rate or "N/A"),
                        f"{recovery.hrv_rmssd_milli_seconds:.1f}" if recovery.hrv_rmssd_milli_seconds else "N/A",
                        f"{recovery.spo2_percentage:.1f}" if recovery.spo2_percentage else "N/A"
                    )
                except Exception as e:
                    recovery_table.add_row(str(recovery_record.get('start', 'N/A')), "Error", "Error", "Error", "Error")
            
            console.print(recovery_table)
            console.print()
        
        # Get workouts
        workouts = client.get_workouts(limit=10)
        console.print(f"🏃 [green]Found {len(workouts.records)} workouts[/green]")
        
        if workouts.records:
            workout_table = Table(title="🏃 Recent Workout Activities", show_header=True, header_style="bold red")
            workout_table.add_column("Date", style="cyan")
            workout_table.add_column("Sport", style="white")
            workout_table.add_column("Strain", style="white", justify="center")
            workout_table.add_column("Avg HR", style="white", justify="center")
            workout_table.add_column("Max HR", style="white", justify="center")
            workout_table.add_column("Energy (kJ)", style="white", justify="center")
            
            for workout_record in workouts.records[:5]:  # Show first 5
                try:
                    workout = client.get_workout(workout_record['id'])
                    
                    strain = workout.score.strain if workout.score and workout.score.strain else "N/A"
                    avg_hr = workout.score.average_heart_rate if workout.score and workout.score.average_heart_rate else "N/A"
                    max_hr = workout.score.max_heart_rate if workout.score and workout.score.max_heart_rate else "N/A"
                    energy = workout.score.kilojoules if workout.score and workout.score.kilojoules else "N/A"
                    
                    workout_table.add_row(
                        str(workout.start.date()),
                        workout.sport_name,
                        str(strain),
                        str(avg_hr),
                        str(max_hr),
                        f"{energy:.0f}" if isinstance(energy, (int, float)) else str(energy)
                    )
                except Exception as e:
                    workout_table.add_row(str(workout_record.get('start', 'N/A')), "Error", "Error", "Error", "Error", "Error")
            
            console.print(workout_table)
            console.print()
        
        # Summary
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
        console.print("🎉 [bold green]All your WHOOP data has been successfully retrieved![/bold green]")
        console.print("💾 [blue]Your tokens have been saved - run this script again anytime![/blue]")
        
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
