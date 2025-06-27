#!/usr/bin/env python3
"""
Deutsche Bahn API Test Script
Tests verschiedene Endpunkte und Authentifizierungsmethoden
"""
import asyncio
import httpx
import json
from datetime import datetime
from api_config import db_config

async def test_api_endpoint(url: str, headers: dict, params: dict = None) -> dict:
    """Test einen API-Endpunkt."""
    print(f"\n🔗 Testing: {url}")
    print(f"📋 Headers: {headers}")
    print(f"📋 Params: {params}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers, params=params)
            
            print(f"📡 Status Code: {response.status_code}")
            print(f"📋 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ SUCCESS - Response Size: {len(json.dumps(data))} bytes")
                    return {"success": True, "data": data, "status": response.status_code}
                except:
                    print(f"✅ SUCCESS - Text Response: {response.text[:200]}...")
                    return {"success": True, "data": response.text, "status": response.status_code}
            else:
                print(f"❌ FAILED - {response.status_code}: {response.text[:200]}")
                return {"success": False, "error": response.text, "status": response.status_code}
                
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")
        return {"success": False, "error": str(e), "status": 0}

async def test_all_endpoints():
    """Teste alle möglichen API-Endpunkte."""
    print("🚊 Deutsche Bahn API Test Suite")
    print("=" * 50)
    
    # Test Headers Varianten
    headers_variants = [
        # Variant 1: Nur DB-Api-Key
        {
            "DB-Api-Key": db_config.DB_API_KEY,
            "Accept": "application/json",
            "User-Agent": "S3-Live-Monitor/1.0"
        },
        # Variant 2: Client-Id + Api-Key
        {
            "DB-Client-Id": db_config.DB_CLIENT_ID or db_config.DB_API_KEY,
            "DB-Api-Key": db_config.DB_API_KEY,
            "Accept": "application/json",
            "User-Agent": "S3-Live-Monitor/1.0"
        },
        # Variant 3: Bearer Token
        {
            "Authorization": f"Bearer {db_config.DB_API_KEY}",
            "Accept": "application/json",
            "User-Agent": "S3-Live-Monitor/1.0"
        },
        # Variant 4: Nur Accept Header (für öffentliche APIs)
        {
            "Accept": "application/json",
            "User-Agent": "S3-Live-Monitor/1.0"
        }
    ]
    
    # Test Endpunkte
    test_cases = [
        {
            "name": "Timetables API - Departures Schwaikheim",
            "url": db_config.get_timetables_url(db_config.SCHWAIKHEIM_ID, "departures"),
            "params": {"date": datetime.now().strftime("%Y%m%d"), "hour": "14"}
        },
        {
            "name": "RIS Journeys API",
            "url": db_config.get_journeys_url(),
            "params": {
                "originEvaId": db_config.SCHWAIKHEIM_ID,
                "destinationEvaId": db_config.FEUERSEE_ID,
                "time": datetime.now().strftime("%Y-%m-%dT%H:%M")
            }
        },
        {
            "name": "RIS Stations API",
            "url": db_config.get_stations_url(),
            "params": {"searchString": "Schwaikheim"}
        },
        {
            "name": "Alternative HAFAS API (Community)",
            "url": "https://v6.db.transport.rest/stops",
            "params": {"query": "Schwaikheim", "results": 5}
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{'='*50}")
        print(f"🧪 Test Case: {test_case['name']}")
        print(f"{'='*50}")
        
        for i, headers in enumerate(headers_variants, 1):
            print(f"\n--- Header Variant {i} ---")
            result = await test_api_endpoint(
                test_case["url"], 
                headers, 
                test_case.get("params")
            )
            
            if result["success"]:
                print(f"🎉 WORKING COMBINATION FOUND!")
                results.append({
                    "test_case": test_case["name"],
                    "url": test_case["url"],
                    "headers": headers,
                    "params": test_case.get("params"),
                    "status": result["status"]
                })
                break  # Stop testing other header variants for this endpoint
    
    # Zusammenfassung
    print(f"\n{'='*50}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    
    if results:
        print("✅ WORKING ENDPOINTS FOUND:")
        for result in results:
            print(f"  🔗 {result['test_case']}")
            print(f"     URL: {result['url']}")
            print(f"     Status: {result['status']}")
    else:
        print("❌ NO WORKING ENDPOINTS FOUND!")
        print("\n🔧 NEXT STEPS:")
        print("1. ✅ Überprüfe API-Credentials in .env")
        print("2. ✅ Registriere dich bei DB API Marketplace")
        print("3. ✅ Beantrage Zugang zu den benötigten APIs")
        print("4. ✅ Verwende alternative Community APIs")
    
    return results

async def test_credentials():
    """Teste API-Credentials."""
    print("\n🔑 API CREDENTIALS CHECK")
    print("-" * 30)
    print(f"DB_API_KEY: {'✅ Set' if db_config.DB_API_KEY else '❌ Missing'}")
    print(f"DB_CLIENT_ID: {'✅ Set' if db_config.DB_CLIENT_ID else '⚠️ Missing'}")
    print(f"DB_CLIENT_SECRET: {'✅ Set' if db_config.DB_CLIENT_SECRET else '⚠️ Missing'}")
    
    if not db_config.DB_API_KEY:
        print("\n❌ CRITICAL: DB_API_KEY fehlt!")
        print("Setze DB_API_KEY in der .env Datei:")
        print("DB_API_KEY=your_api_key_here")
        return False
    
    return True

if __name__ == "__main__":
    print("🚊 Deutsche Bahn API Comprehensive Test")
    print("Testing all endpoints and authentication methods...")
    
    async def main():
        # Test credentials first
        if not await test_credentials():
            return
        
        # Test all endpoints
        results = await test_all_endpoints()
        
        # Save results
        if results:
            with open("api_test_results.json", "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to api_test_results.json")
    
    asyncio.run(main()) 