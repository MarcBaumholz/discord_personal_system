#!/usr/bin/env python3
"""Analyze live Oura data and provide specific health improvements for tomorrow."""

from oura_client import OuraClient
from health_analyzer import HealthAnalyzer
from config import Config
import json

def analyze_live_data_for_improvements():
    """Fetch live data and provide 2 specific improvements for tomorrow."""
    
    print("🔍 FETCHING LIVE OURA DATA...")
    config = Config()
    client = OuraClient(config.OURA_ACCESS_TOKEN)

    # Get comprehensive health data
    data = client.get_yesterday_data()

    if data:
        print("✅ LIVE DATA RETRIEVED SUCCESSFULLY")
        print(f"📅 Data Date: {data.date}")
        print("=" * 50)
        
        # Display all available metrics
        print("📊 YOUR CURRENT HEALTH METRICS:")
        if data.sleep_score: print(f"   💤 Sleep Score: {data.sleep_score}/100")
        if data.readiness_score: print(f"   🔋 Readiness Score: {data.readiness_score}/100")
        if data.activity_score: print(f"   🏃 Activity Score: {data.activity_score}/100")
        if data.total_calories: print(f"   🔥 Total Calories: {data.total_calories} kcal")
        if data.active_calories: print(f"   ⚡ Active Calories: {data.active_calories} kcal")
        if data.steps: print(f"   👟 Steps: {data.steps:,}")
        if data.spo2_average: print(f"   🫁 SpO2: {data.spo2_average:.1f}%")
        if data.cardiovascular_age: print(f"   ❤️  Cardiovascular Age: {data.cardiovascular_age} years")
        if data.resilience_level: print(f"   🛡️  Resilience: {data.resilience_level}")
        if data.temperature_deviation: print(f"   🌡️  Temperature Deviation: {data.temperature_deviation:.2f}°C")
        
        print()
        print("=" * 50)
        print("🎯 2 SPECIFIC IMPROVEMENTS FOR TOMORROW:")
        print("=" * 50)
        
        improvements = []
        
        # Sleep improvements
        if data.sleep_score and data.sleep_score < 80:
            sleep_contributors = data.sleep_contributors or {}
            if sleep_contributors:
                lowest_sleep = min(sleep_contributors, key=sleep_contributors.get)
                improvements.append(f"😴 SLEEP IMPROVEMENT: Your {lowest_sleep} score was {sleep_contributors[lowest_sleep]}/100. Tomorrow: Go to bed 30 minutes earlier and ensure room temperature is 18-20°C for better {lowest_sleep}.")
            else:
                improvements.append(f"😴 SLEEP IMPROVEMENT: Sleep score {data.sleep_score}/100. Tomorrow: Establish consistent bedtime routine - no screens 1 hour before bed, room completely dark.")
        
        # Readiness improvements  
        if data.readiness_score and data.readiness_score < 85:
            readiness_contributors = data.readiness_contributors or {}
            if readiness_contributors:
                lowest_readiness = min(readiness_contributors, key=readiness_contributors.get)
                if "activity_balance" in lowest_readiness:
                    improvements.append(f"⚖️  RECOVERY IMPROVEMENT: Your activity balance is low ({readiness_contributors[lowest_readiness]}/100). Tomorrow: Take a 20-minute gentle walk and do 10 minutes of stretching instead of intense exercise.")
                elif "hrv" in lowest_readiness.lower():
                    improvements.append(f"🫀 HRV IMPROVEMENT: Heart rate variability needs attention. Tomorrow: Practice 10 minutes of deep breathing (4-7-8 technique) and avoid alcohol/caffeine after 2 PM.")
                else:
                    improvements.append(f"🔋 READINESS IMPROVEMENT: {lowest_readiness} is low ({readiness_contributors[lowest_readiness]}/100). Tomorrow: Focus on stress reduction and recovery activities.")
            else:
                improvements.append(f"🔋 READINESS IMPROVEMENT: Readiness {data.readiness_score}/100. Tomorrow: Prioritize recovery - take a warm bath, do gentle stretching, and ensure 7-8 hours sleep.")
        
        # Activity improvements
        if data.activity_score and data.activity_score < 85:
            if data.active_calories and data.active_calories < 600:
                improvements.append(f"🔥 ACTIVITY IMPROVEMENT: Active calories {data.active_calories} below target. Tomorrow: Add 2 x 15-minute brisk walks and take stairs instead of elevators to reach 600+ active calories.")
            elif data.steps and data.steps < 8000:
                improvements.append(f"👟 MOVEMENT IMPROVEMENT: Only {data.steps:,} steps yesterday. Tomorrow: Set hourly movement reminders and aim for 10,000 steps through parking further away and walking meetings.")
            else:
                improvements.append(f"🏃 ACTIVITY IMPROVEMENT: Activity score {data.activity_score}/100. Tomorrow: Add 20 minutes of moderate intensity exercise (brisk walk, cycling, or swimming).")
        
        # SpO2 improvements
        if data.spo2_average and data.spo2_average < 96:
            improvements.append(f"💨 BREATHING IMPROVEMENT: SpO2 at {data.spo2_average:.1f}% could be higher. Tomorrow: Practice diaphragmatic breathing exercises for 10 minutes and ensure good air quality in bedroom.")
        
        # Temperature deviation
        if data.temperature_deviation and abs(data.temperature_deviation) > 0.3:
            improvements.append(f"🌡️  RECOVERY IMPROVEMENT: Temperature deviation {data.temperature_deviation:.2f}°C indicates stress. Tomorrow: Focus on hydration (2.5L water), avoid alcohol, and do 15 minutes meditation.")
        
        # If all scores are high, suggest optimization
        if not improvements:
            if data.sleep_score and data.sleep_score >= 80 and data.readiness_score and data.readiness_score >= 85:
                improvements.append("🚀 PERFORMANCE OPTIMIZATION: Your metrics are excellent! Tomorrow: Try a new activity (swimming, cycling, yoga) to challenge your body differently while maintaining recovery.")
                improvements.append("📈 CONSISTENCY BOOST: Maintain your current routine but add 5 minutes of morning sunlight exposure and evening gratitude practice for enhanced circadian rhythm.")
        
        # Display top 2 improvements
        for i, improvement in enumerate(improvements[:2], 1):
            print(f"{i}. {improvement}")
            print()
        
        if len(improvements) < 2:
            print("2. 💪 OVERALL OPTIMIZATION: Your health metrics are strong! Tomorrow: Focus on maintaining consistency in sleep timing and add 5 minutes of mindfulness practice for mental wellness.")
            
    else:
        print("❌ NO LIVE DATA AVAILABLE")
        print("Unable to retrieve current Oura data. Please ensure:")
        print("- Your Oura Ring is charged and synced")
        print("- The access token is valid") 
        print("- Data sync is up to date")

if __name__ == "__main__":
    analyze_live_data_for_improvements() 