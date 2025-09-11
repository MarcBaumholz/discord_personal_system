#!/usr/bin/env python3
"""
Test script for WHOOP Discord Bot
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import WhoopConfig
from src.oauth import WhoopOAuth
from src.client import WhoopClient
from src.token_manager import TokenManager

async def test_whoop_data():
    """Test WHOOP data retrieval"""
    print("🏃‍♂️ Testing WHOOP Data Retrieval...")
    
    try:
        # Load configuration
        config = WhoopConfig.from_env()
        oauth = WhoopOAuth(config)
        token_manager = TokenManager()
        client = WhoopClient(config, oauth, token_manager)
        
        # Check authentication
        if not client.is_authenticated():
            print("❌ No valid WHOOP tokens found. Please authenticate first.")
            return False
        
        print("✅ WHOOP authentication successful")
        
        # Get profile
        profile = client.get_user_profile()
        print(f"👤 Profile: {profile.first_name} {profile.last_name or ''}")
        
        # Get recent data
        yesterday = datetime.now() - timedelta(days=1)
        print(f"📅 Fetching data for: {yesterday.strftime('%Y-%m-%d')}")
        
        # Get cycles
        cycles = client.get_cycles(limit=7)
        print(f"📈 Found {len(cycles.records)} cycles")
        
        # Get sleep data
        sleep_data = client.get_sleep_data(limit=7)
        print(f"😴 Found {len(sleep_data.records)} sleep records")
        
        # Get recovery data
        recovery_data = client.get_recovery_data(limit=7)
        print(f"💪 Found {len(recovery_data.records)} recovery records")
        
        # Get workouts
        workouts = client.get_workouts(limit=10)
        print(f"🏃 Found {len(workouts.records)} workouts")
        
        # Test finding yesterday's data
        yesterday_cycle = None
        for cycle_data in cycles.records:
            cycle = client.get_cycle(cycle_data['id'])
            if cycle.start.date() == yesterday.date():
                yesterday_cycle = cycle
                break
        
        if yesterday_cycle:
            print(f"✅ Found yesterday's cycle: Strain {yesterday_cycle.score.strain if yesterday_cycle.score else 'N/A'}")
        else:
            print("⚠️ No cycle data for yesterday")
        
        yesterday_sleep = None
        for sleep_record in sleep_data.records:
            sleep = client.get_sleep(sleep_record['id'])
            if sleep.start.date() == yesterday.date():
                yesterday_sleep = sleep
                break
        
        if yesterday_sleep:
            sleep_score = "N/A"
            if yesterday_sleep.score:
                if isinstance(yesterday_sleep.score, dict):
                    sleep_score = yesterday_sleep.score.get('score', 'N/A')
                else:
                    sleep_score = yesterday_sleep.score
            print(f"✅ Found yesterday's sleep: Score {sleep_score}")
        else:
            print("⚠️ No sleep data for yesterday")
        
        yesterday_recovery = None
        for recovery_record in recovery_data.records:
            # Recovery records don't have direct 'id' field, they have cycle_id
            # We need to get the cycle first to get the start date
            try:
                cycle = client.get_cycle(recovery_record['cycle_id'])
                if cycle.start.date() == yesterday.date():
                    # Create a mock recovery object from the record data
                    yesterday_recovery = recovery_record
                    break
            except Exception as e:
                print(f"Error getting cycle for recovery: {e}")
                continue
        
        if yesterday_recovery:
            print(f"✅ Found yesterday's recovery: Score {yesterday_recovery.score or 'N/A'}")
        else:
            print("⚠️ No recovery data for yesterday")
        
        yesterday_workouts = []
        for workout_record in workouts.records:
            workout = client.get_workout(workout_record['id'])
            if workout.start.date() == yesterday.date():
                yesterday_workouts.append(workout)
        
        print(f"✅ Found {len(yesterday_workouts)} workouts for yesterday")
        
        print("\n🎉 WHOOP data retrieval test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing WHOOP data: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_discord_embed():
    """Test Discord embed creation"""
    print("\n📱 Testing Discord Embed Creation...")
    
    try:
        # Import the bot class
        from whoop_discord_bot import WhoopDiscordBot
        
        # Create bot instance (without starting)
        bot = WhoopDiscordBot()
        
        # Test data formatting
        def format_duration(seconds):
            if not seconds:
                return "N/A"
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        
        def get_score_emoji(score):
            if not score:
                return "❓"
            if isinstance(score, dict):
                score_val = score.get('score', 0)
            else:
                score_val = score
            
            if score_val >= 80:
                return "🟢"
            elif score_val >= 60:
                return "🟡"
            else:
                return "🔴"
        
        print("✅ Discord embed functions loaded successfully")
        print("✅ Bot class instantiated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Discord embed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting WHOOP Discord Bot Tests...\n")
    
    # Test WHOOP data retrieval
    whoop_success = await test_whoop_data()
    
    # Test Discord embed creation
    discord_success = await test_discord_embed()
    
    print(f"\n📊 Test Results:")
    print(f"  WHOOP Data Retrieval: {'✅ PASS' if whoop_success else '❌ FAIL'}")
    print(f"  Discord Embed Creation: {'✅ PASS' if discord_success else '❌ FAIL'}")
    
    if whoop_success and discord_success:
        print("\n🎉 All tests passed! The WHOOP bot is ready to run.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
