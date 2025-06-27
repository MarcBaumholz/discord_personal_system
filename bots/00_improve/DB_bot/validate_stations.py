#!/usr/bin/env python3
"""
Station ID Validation für Schwaikheim und Feuersee
"""
import httpx
import asyncio
import os
from dotenv import load_dotenv
import json

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)
DB_API_KEY = os.getenv('DB_APICLIENT', '')

async def validate_stations():
    """Validate station IDs via RIS Stations API."""
    
    if not DB_API_KEY:
        print("❌ DB_API_KEY nicht gefunden - kann Stationen nicht validieren")
        return
    
    headers = {
        'Authorization': f'Bearer {DB_API_KEY}',
        'Accept': 'application/json'
    }
    
    stations_to_check = [
        ("Schwaikheim", ""),
        ("Stuttgart Feuersee", "Feuersee"),
        ("Feuersee", "")
    ]
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for station_name, alt_name in stations_to_check:
            print(f"\n=== {station_name.upper()} ===")
            
            try:
                url = f"https://apis.deutschebahn.com/db-api-marketplace/apis/ris-stations/v1/stations?name={station_name}"
                response = await client.get(url, headers=headers)
                
                print(f"API Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'stations' in data and data['stations']:
                        for i, station in enumerate(data['stations'][:3]):  # Show top 3 matches
                            print(f"\n{i+1}. Station Match:")
                            print(f"   ID (IBNR): {station.get('ibnr', 'N/A')}")
                            print(f"   Name: {station.get('name', 'N/A')}")
                            print(f"   Ort: {station.get('address', {}).get('city', 'N/A')}")
                            
                            # Check coordinates
                            coords = station.get('coordinates', {})
                            if coords:
                                print(f"   Koordinaten: {coords.get('latitude', 'N/A')}, {coords.get('longitude', 'N/A')}")
                    else:
                        print("   Keine Stationen gefunden")
                        
                elif response.status_code == 401:
                    print("   ❌ Authentifizierung fehlgeschlagen - API Key prüfen")
                elif response.status_code == 404:
                    print("   ❌ Endpoint nicht gefunden")
                else:
                    print(f"   ❌ API Error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"   ❌ Request Error: {e}")

async def test_journey_api():
    """Test journey API with current IDs."""
    print("\n" + "="*50)
    print("TESTE AKTUELLE IDs (8005462 → 8002058)")
    print("="*50)
    
    if not DB_API_KEY:
        print("❌ DB_API_KEY nicht verfügbar")
        return
    
    headers = {
        'Authorization': f'Bearer {DB_API_KEY}',
        'Accept': 'application/json'
    }
    
    params = {
        'origin': '8005462',  # Current Schwaikheim ID
        'destination': '8002058',  # Current Feuersee ID
        'limit': 3
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-journeys/v1/journeys"
            response = await client.get(url, headers=headers, params=params)
            
            print(f"Journey API Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'journeys' in data and data['journeys']:
                    journey = data['journeys'][0]
                    if 'legs' in journey and journey['legs']:
                        leg = journey['legs'][0]
                        origin = leg.get('origin', {})
                        destination = leg.get('destination', {})
                        line = leg.get('line', {})
                        
                        print(f"✅ Verbindung gefunden!")
                        print(f"   Von: {origin.get('name', 'N/A')}")
                        print(f"   Nach: {destination.get('name', 'N/A')}")
                        print(f"   Linie: {line.get('name', 'N/A')}")
                        print(f"   Produkt: {line.get('product', 'N/A')}")
                        
                        # Berechne Fahrtzeit
                        dep_time = origin.get('plannedDepartureTime', '')
                        arr_time = destination.get('plannedArrivalTime', '')
                        if dep_time and arr_time:
                            from datetime import datetime
                            dep = datetime.fromisoformat(dep_time.replace('Z', '+00:00'))
                            arr = datetime.fromisoformat(arr_time.replace('Z', '+00:00'))
                            duration = arr - dep
                            print(f"   Fahrtzeit: {duration.total_seconds() // 60:.0f} Minuten")
                else:
                    print("❌ Keine Verbindungen gefunden")
            else:
                print(f"❌ Journey API Error: {response.status_code}")
                print(f"Response: {response.text[:300]}...")
                
    except Exception as e:
        print(f"❌ Journey Test Error: {e}")

if __name__ == "__main__":
    print("🔍 VALIDIERE STATION IDs FÜR S-BAHN ROUTEN")
    print("=" * 50)
    
    asyncio.run(validate_stations())
    asyncio.run(test_journey_api()) 