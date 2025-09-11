#!/usr/bin/env python3
"""
Send manual WHOOP data to Discord with detailed logging
"""

import os
import sys
import asyncio
import discord
from datetime import datetime, timedelta
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth
from src.client import WhoopClient
from src.token_manager import TokenManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_manual_data():
    """Send manual WHOOP data with detailed logging"""
    print("🏃‍♂️ Sending Manual WHOOP Data...")
    
    try:
        # Load WHOOP configuration
        config = WhoopConfig.from_env()
        oauth = WhoopOAuth(config)
        token_manager = TokenManager()
        client = WhoopClient(config, oauth, token_manager)
        
        if not client.is_authenticated():
            print("❌ No valid WHOOP tokens found")
            return False
        
        print("✅ WHOOP authentication successful")
        
        # Get Discord token
        discord_token = os.getenv('DISCORD_TOKEN')
        if not discord_token:
            print("❌ DISCORD_TOKEN not found")
            return False
        
        # Create Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        bot = discord.Client(intents=intents)
        
        @bot.event
        async def on_ready():
            print(f"✅ Discord bot connected as {bot.user}")
            
            # Get target channel
            channel_id = 1415625361106014348
            channel = bot.get_channel(channel_id)
            
            if not channel:
                print(f"❌ Could not find channel {channel_id}")
                await bot.close()
                return
            
            print(f"✅ Found channel: {channel.name}")
            
            # Get yesterday's data with UTC
            yesterday_utc = datetime.utcnow() - timedelta(days=1)
            print(f"📅 Looking for data from: {yesterday_utc.strftime('%Y-%m-%d')} (UTC)")
            
            try:
                # Get profile
                profile = client.get_user_profile()
                print(f"👤 Profile: {profile.first_name} {profile.last_name}")
                
                # Get cycles
                print("\n📈 Getting cycles...")
                cycles = client.get_cycles(limit=10)
                print(f"Found {len(cycles.records)} cycles")
                
                yesterday_cycle = None
                for i, cycle_data in enumerate(cycles.records):
                    cycle = client.get_cycle(cycle_data['id'])
                    cycle_date = cycle.start.date()
                    matches = cycle_date == yesterday_utc.date()
                    print(f"  Cycle {i+1}: {cycle_date} (matches: {matches})")
                    if matches:
                        yesterday_cycle = cycle
                        print(f"  ✅ Found yesterday's cycle!")
                        break
                
                # Get sleep
                print("\n😴 Getting sleep...")
                sleep_data = client.get_sleep_data(limit=10)
                print(f"Found {len(sleep_data.records)} sleep records")
                
                yesterday_sleep = None
                for i, sleep_record in enumerate(sleep_data.records):
                    sleep = client.get_sleep(sleep_record['id'])
                    sleep_date = sleep.start.date()
                    matches = sleep_date == yesterday_utc.date()
                    print(f"  Sleep {i+1}: {sleep_date} (matches: {matches})")
                    if matches:
                        yesterday_sleep = sleep
                        print(f"  ✅ Found yesterday's sleep!")
                        break
                
                # Get recovery
                print("\n💪 Getting recovery...")
                recovery_data = client.get_recovery_data(limit=10)
                print(f"Found {len(recovery_data.records)} recovery records")
                
                yesterday_recovery = None
                for i, recovery_record in enumerate(recovery_data.records):
                    try:
                        cycle = client.get_cycle(recovery_record['cycle_id'])
                        recovery_date = cycle.start.date()
                        matches = recovery_date == yesterday_utc.date()
                        print(f"  Recovery {i+1}: {recovery_date} (matches: {matches})")
                        if matches:
                            yesterday_recovery = recovery_record
                            print(f"  ✅ Found yesterday's recovery!")
                            break
                    except Exception as e:
                        print(f"  Recovery {i+1}: Error - {e}")
                
                # Get workouts
                print("\n🏃 Getting workouts...")
                workouts = client.get_workouts(limit=10)
                print(f"Found {len(workouts.records)} workouts")
                
                yesterday_workouts = []
                for i, workout_record in enumerate(workouts.records):
                    workout = client.get_workout(workout_record['id'])
                    workout_date = workout.start.date()
                    matches = workout_date == yesterday_utc.date()
                    print(f"  Workout {i+1}: {workout_date} (matches: {matches})")
                    if matches:
                        yesterday_workouts.append(workout)
                        print(f"  ✅ Found yesterday's workout: {workout.sport_name}")
                
                # Create summary
                print(f"\n📊 Data Summary:")
                print(f"  Cycle: {'✅' if yesterday_cycle else '❌'}")
                print(f"  Sleep: {'✅' if yesterday_sleep else '❌'}")
                print(f"  Recovery: {'✅' if yesterday_recovery else '❌'}")
                print(f"  Workouts: {len(yesterday_workouts)}")
                
                # Create embed
                embed = discord.Embed(
                    title=f"🏃‍♂️ WHOOP Manual Test - {yesterday_utc.strftime('%Y-%m-%d')}",
                    description=f"**{profile.first_name} {profile.last_name or ''}**'s WHOOP data with detailed logging",
                    color=0x00ff00
                )
                
                # Add profile info
                embed.add_field(
                    name="👤 Profile",
                    value=f"**User ID:** {profile.user_id}\n**Email:** {profile.email}",
                    inline=False
                )
                
                # Add cycle data
                if yesterday_cycle and yesterday_cycle.score:
                    strain = yesterday_cycle.score.strain if yesterday_cycle.score.strain else "N/A"
                    avg_hr = yesterday_cycle.score.average_heart_rate if yesterday_cycle.score.average_heart_rate else "N/A"
                    max_hr = yesterday_cycle.score.max_heart_rate if yesterday_cycle.score.max_heart_rate else "N/A"
                    energy = yesterday_cycle.score.kilojoules if yesterday_cycle.score.kilojoules else "N/A"
                    
                    embed.add_field(
                        name="📈 Daily Cycle",
                        value=f"**Strain:** 🟢 {strain}\n"
                              f"**Avg HR:** {avg_hr} bpm\n"
                              f"**Max HR:** {max_hr} bpm\n"
                              f"**Energy:** {energy:.0f} kJ" if isinstance(energy, (int, float)) else f"**Energy:** {energy}",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="📈 Daily Cycle",
                        value="No cycle data available",
                        inline=True
                    )
                
                # Add sleep data
                if yesterday_sleep:
                    sleep_score = "N/A"
                    if yesterday_sleep.score:
                        if isinstance(yesterday_sleep.score, dict):
                            sleep_score = yesterday_sleep.score.get('sleep_performance_percentage', 'N/A')
                        else:
                            sleep_score = yesterday_sleep.score
                    
                    # Calculate sleep stages
                    total_sleep = 0
                    light_sleep = 0
                    deep_sleep = 0
                    rem_sleep = 0
                    
                    if yesterday_sleep.score and 'stage_summary' in yesterday_sleep.score:
                        stage_summary = yesterday_sleep.score['stage_summary']
                        light_sleep = (stage_summary.get('total_light_sleep_time_milli', 0) or 0) // 1000
                        deep_sleep = (stage_summary.get('total_slow_wave_sleep_time_milli', 0) or 0) // 1000
                        rem_sleep = (stage_summary.get('total_rem_sleep_time_milli', 0) or 0) // 1000
                        total_sleep = light_sleep + deep_sleep + rem_sleep
                    
                    def format_duration(seconds):
                        if not seconds:
                            return "N/A"
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        return f"{hours}h {minutes}m"
                    
                    embed.add_field(
                        name="😴 Sleep Analysis",
                        value=f"**Score:** 🟢 {sleep_score}\n"
                              f"**Total:** {format_duration(total_sleep)}\n"
                              f"**Light:** {format_duration(light_sleep)}\n"
                              f"**Deep:** {format_duration(deep_sleep)}\n"
                              f"**REM:** {format_duration(rem_sleep)}\n"
                              f"**Resp Rate:** {yesterday_sleep.respiratory_rate:.1f}" if yesterday_sleep.respiratory_rate else f"**Resp Rate:** N/A",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="😴 Sleep Analysis",
                        value="No sleep data available",
                        inline=True
                    )
                
                # Add recovery data
                if yesterday_recovery:
                    score_data = yesterday_recovery.get('score', {})
                    recovery_score = score_data.get('recovery_score') if score_data else "N/A"
                    resting_hr = score_data.get('resting_heart_rate') if score_data else "N/A"
                    hrv = f"{score_data.get('hrv_rmssd_milli', 0):.1f} ms" if score_data and score_data.get('hrv_rmssd_milli') else "N/A"
                    spo2 = f"{score_data.get('spo2_percentage', 0):.1f}%" if score_data and score_data.get('spo2_percentage') else "N/A"
                    skin_temp = f"{score_data.get('skin_temp_celsius', 0):.1f}°C" if score_data and score_data.get('skin_temp_celsius') else "N/A"
                    
                    embed.add_field(
                        name="💪 Recovery Metrics",
                        value=f"**Score:** 🟢 {recovery_score}\n"
                              f"**Resting HR:** {resting_hr} bpm\n"
                              f"**HRV:** {hrv}\n"
                              f"**SpO2:** {spo2}\n"
                              f"**Skin Temp:** {skin_temp}",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="💪 Recovery Metrics",
                        value="No recovery data available",
                        inline=True
                    )
                
                # Add workouts
                if yesterday_workouts:
                    workout_text = ""
                    for i, workout in enumerate(yesterday_workouts[:3]):  # Show max 3 workouts
                        strain = workout.score.strain if workout.score and workout.score.strain else "N/A"
                        avg_hr = workout.score.average_heart_rate if workout.score and workout.score.average_heart_rate else "N/A"
                        max_hr = workout.score.max_heart_rate if workout.score and workout.score.max_heart_rate else "N/A"
                        energy = workout.score.kilojoules if workout.score and workout.score.kilojoules else "N/A"
                        
                        workout_text += f"**{workout.sport_name.title()}**\n"
                        workout_text += f"Strain: 🟢 {strain} | HR: {avg_hr}-{max_hr} bpm\n"
                        if isinstance(energy, (int, float)):
                            workout_text += f"Energy: {energy:.0f} kJ\n"
                        else:
                            workout_text += f"Energy: {energy}\n"
                        workout_text += "\n"
                    
                    if len(yesterday_workouts) > 3:
                        workout_text += f"... and {len(yesterday_workouts) - 3} more workouts"
                    
                    embed.add_field(
                        name="🏃 Workouts",
                        value=workout_text or "No workout data",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🏃 Workouts",
                        value="No workouts recorded",
                        inline=False
                    )
                
                # Add footer
                embed.set_footer(text=f"WHOOP API v2 • Manual Test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Send embed
                await channel.send(embed=embed)
                print("✅ Manual WHOOP data sent to Discord successfully!")
                
            except Exception as e:
                print(f"❌ Error creating embed: {e}")
                import traceback
                traceback.print_exc()
                await channel.send(f"❌ Error fetching WHOOP data: {e}")
            
            # Close bot
            await bot.close()
        
        # Start bot
        await bot.start(discord_token)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("🚀 Starting Manual WHOOP Data Test...\n")
    
    success = await send_manual_data()
    
    if success:
        print("\n🎉 Manual WHOOP data sent successfully!")
    else:
        print("\n❌ Failed to send manual WHOOP data!")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
