#!/usr/bin/env python3
"""
Quick WHOOP API test - generates URL and waits for manual input
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
    print("🚀 Quick WHOOP Data Test")
    print("=" * 30)
    
    # Load configuration
    config = WhoopConfig.from_env()
    oauth = WhoopOAuth(config)
    
    # Generate authorization URL
    auth_url = oauth.get_authorization_url()
    
    print(f"\n📱 ÖFFNE DIESE URL IN DEINEM BROWSER:")
    print(f"\n{auth_url}\n")
    
    print("📋 SCHRITTE:")
    print("1. Klicke auf die URL oben")
    print("2. Melde dich bei WHOOP an")
    print("3. Erlaube alle Berechtigungen für 'Morgenroutine'")
    print("4. Du wirst weitergeleitet zu: http://localhost:8080/callback?code=...")
    print("5. Kopiere die GESAMTE URL aus der Adressleiste")
    print("6. Komm zurück und füge sie hier ein")
    
    print(f"\n⏰ WICHTIG: Mache das schnell, bevor die Session abläuft!")
    print(f"   (Du hast etwa 5-10 Minuten Zeit)")
    
    # Wait for user input
    callback_url = input(f"\n🔗 Füge hier die komplette Callback-URL ein: ").strip()
    
    if not callback_url:
        print("❌ Keine URL eingegeben. Test abgebrochen.")
        return
    
    try:
        # Extract code and get tokens
        code, state = extract_code_from_url(callback_url)
        print(f"\n✅ Autorisierungscode erhalten: {code[:10]}...")
        
        token_response = oauth.exchange_code_for_token(code)
        print("✅ Zugriffstoken erhalten!")
        print(f"   Token läuft ab in: {token_response.expires_in} Sekunden")
        
        # Initialize client
        client = WhoopClient(config, oauth)
        
        print("\n🔍 Teste API-Verbindung...")
        if client.test_connection():
            print("✅ API-Verbindung erfolgreich!")
        else:
            print("❌ API-Verbindung fehlgeschlagen")
            return
        
        print("\n📊 Lade deine WHOOP-Daten...")
        
        # Get profile
        try:
            profile = client.get_user_profile()
            print(f"\n👤 Profil:")
            print(f"   Benutzer-ID: {profile.user_id}")
            print(f"   E-Mail: {profile.email}")
            if profile.first_name:
                print(f"   Name: {profile.first_name} {profile.last_name or ''}")
        except Exception as e:
            print(f"❌ Profil-Fehler: {e}")
        
        # Get body measurements
        try:
            body = client.get_body_measurements()
            print(f"\n📏 Körpermaße:")
            if body.height_meter:
                print(f"   Größe: {body.height_meter:.2f} Meter")
            if body.weight_kilogram:
                print(f"   Gewicht: {body.weight_kilogram:.1f} kg")
            if body.max_heart_rate:
                print(f"   Max. Herzfrequenz: {body.max_heart_rate} bpm")
        except Exception as e:
            print(f"❌ Körpermaße-Fehler: {e}")
        
        # Get recent data (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Cycles
        try:
            cycles = client.get_cycles(start=start_date, end=end_date, limit=5)
            print(f"\n📈 Letzte Zyklen (7 Tage):")
            print(f"   {len(cycles.records)} Zyklen gefunden")
            
            for i, cycle_data in enumerate(cycles.records[:3]):
                cycle = client.get_cycle(cycle_data['id'])
                print(f"   Zyklus {i+1}: {cycle.start.date()}")
                if cycle.score and cycle.score.strain:
                    print(f"     Belastung: {cycle.score.strain:.1f}")
                if cycle.score and cycle.score.average_heart_rate:
                    print(f"     Ø Herzfrequenz: {cycle.score.average_heart_rate} bpm")
        except Exception as e:
            print(f"❌ Zyklen-Fehler: {e}")
        
        # Sleep
        try:
            sleep_data = client.get_sleep_data(start=start_date, end=end_date, limit=5)
            print(f"\n😴 Letzter Schlaf (7 Tage):")
            print(f"   {len(sleep_data.records)} Schlafaufzeichnungen gefunden")
            
            for i, sleep_record in enumerate(sleep_data.records[:3]):
                sleep = client.get_sleep(sleep_record['id'])
                print(f"   Schlaf {i+1}: {sleep.start.date()}")
                if sleep.score:
                    print(f"     Score: {sleep.score:.1f}")
                if sleep.stage_summary:
                    total_sleep = (sleep.stage_summary.light_sleep_time_seconds or 0) + \
                                 (sleep.stage_summary.slow_wave_sleep_time_seconds or 0) + \
                                 (sleep.stage_summary.rem_sleep_time_seconds or 0)
                    print(f"     Gesamtschlaf: {total_sleep // 3600}h {(total_sleep % 3600) // 60}m")
        except Exception as e:
            print(f"❌ Schlaf-Fehler: {e}")
        
        # Recovery
        try:
            recovery_data = client.get_recovery_data(start=start_date, end=end_date, limit=5)
            print(f"\n💪 Letzte Erholung (7 Tage):")
            print(f"   {len(recovery_data.records)} Erholungsaufzeichnungen gefunden")
            
            for i, recovery_record in enumerate(recovery_data.records[:3]):
                recovery = client.get_recovery(recovery_record['id'])
                print(f"   Erholung {i+1}: {recovery.start.date()}")
                if recovery.score:
                    print(f"     Score: {recovery.score:.1f}")
                if recovery.resting_heart_rate:
                    print(f"     Ruheherzfrequenz: {recovery.resting_heart_rate} bpm")
                if recovery.hrv_rmssd_milli_seconds:
                    print(f"     HRV: {recovery.hrv_rmssd_milli_seconds:.1f} ms")
        except Exception as e:
            print(f"❌ Erholung-Fehler: {e}")
        
        # Workouts
        try:
            workouts = client.get_workouts(start=start_date, end=end_date, limit=5)
            print(f"\n🏃 Letzte Workouts (7 Tage):")
            print(f"   {len(workouts.records)} Workouts gefunden")
            
            for i, workout_record in enumerate(workouts.records[:3]):
                workout = client.get_workout(workout_record['id'])
                print(f"   Workout {i+1}: {workout.start.date()}")
                print(f"     Sport: {workout.sport_name}")
                if workout.score and workout.score.strain:
                    print(f"     Belastung: {workout.score.strain:.1f}")
                if workout.score and workout.score.kilojoules:
                    print(f"     Energie: {workout.score.kilojoules:.0f} kJ")
        except Exception as e:
            print(f"❌ Workout-Fehler: {e}")
        
        print(f"\n🎉 Test erfolgreich abgeschlossen!")
        print(f"\nNächste Schritte:")
        print(f"- Führe 'python examples/data_export.py' aus, um alle Daten als CSV zu exportieren")
        print(f"- Führe 'python examples/webhook_server.py' für Echtzeit-Updates aus")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        print(f"\nFehlerbehebung:")
        print(f"- Stelle sicher, dass du die GESAMTE Callback-URL kopiert hast")
        print(f"- Prüfe, dass du alle Berechtigungen für die App erlaubt hast")
        print(f"- Vergewissere dich, dass dein WHOOP-Konto aktiv ist")
        print(f"- Versuche es erneut mit einem neuen URL")


if __name__ == "__main__":
    main()
