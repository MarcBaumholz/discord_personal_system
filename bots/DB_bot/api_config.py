#!/usr/bin/env python3
"""
Deutsche Bahn API - Korrekte Endpunkte und Authentifizierung
"""
import os
from dotenv import load_dotenv

# Load environment from parent directory
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

class DBApiConfig:
    """Korrekte Deutsche Bahn API Konfiguration."""
    
    # API Credentials
    DB_CLIENT_ID = os.getenv("DB_CLIENT_ID", "")
    DB_API_KEY = os.getenv("DB_API_KEY", "")
    DB_CLIENT_SECRET = os.getenv("DB_CLIENT_SECRET", "")
    
    # Fallback für alte Konfiguration
    if not DB_API_KEY:
        DB_API_KEY = os.getenv("DB_APICLIENT", "")
    
    # Station IDs (korrekt nach Wikipedia)
    SCHWAIKHEIM_ID = "8005454"
    FEUERSEE_ID = "8002058"
    
    # API Base URLs (offizielle Deutsche Bahn API)
    RIS_JOURNEYS_BASE = "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-journeys/v1"
    TIMETABLES_BASE = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1"
    STATIONS_BASE = "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-stations/v1"
    
    # Alternative API Endpunkte
    ALTERNATIVE_APIS = {
        "hafas": "https://v6.db.transport.rest",  # Community API (falls verfügbar)
        "opendata": "https://download-data.deutschebahn.com/static/datasets/timetables",
        "ris_disruptions": "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-disruptions/v1"
    }
    
    @classmethod
    def get_headers(cls) -> dict:
        """Korrekte HTTP Headers für Deutsche Bahn API."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "S3-Live-Monitor/1.0"
        }
        
        # Deutsche Bahn API verwendet entweder:
        # 1. DB-Client-Id + DB-Api-Key (bevorzugt)
        # 2. Oder nur DB-Api-Key
        if cls.DB_CLIENT_ID:
            headers["DB-Client-Id"] = cls.DB_CLIENT_ID
            
        if cls.DB_API_KEY:
            headers["DB-Api-Key"] = cls.DB_API_KEY
            
        return headers
    
    @classmethod
    def get_timetables_url(cls, station_id: str, endpoint: str = "departures") -> str:
        """Generiere Timetables API URL."""
        return f"{cls.TIMETABLES_BASE}/station/{station_id}/{endpoint}"
    
    @classmethod
    def get_journeys_url(cls) -> str:
        """Generiere RIS Journeys API URL."""
        return f"{cls.RIS_JOURNEYS_BASE}/journeys"
    
    @classmethod
    def get_stations_url(cls, query: str = "") -> str:
        """Generiere Stations API URL."""
        return f"{cls.STATIONS_BASE}/stations"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validiere API-Konfiguration."""
        if not cls.DB_API_KEY:
            print("❌ DB_API_KEY fehlt in der Konfiguration!")
            return False
            
        if not cls.DB_CLIENT_ID:
            print("⚠️ DB_CLIENT_ID fehlt - verwende nur DB_API_KEY")
            
        return True
    
    @classmethod
    def get_route_config(cls, route_number: int) -> dict:
        """Route-Konfiguration für S3 Schwaikheim ↔ Feuersee."""
        if route_number == 1:
            return {
                "name": "Schwaikheim → Stuttgart Feuersee",
                "origin": cls.SCHWAIKHEIM_ID,
                "destination": cls.FEUERSEE_ID
            }
        elif route_number == 2:
            return {
                "name": "Stuttgart Feuersee → Schwaikheim",
                "origin": cls.FEUERSEE_ID,
                "destination": cls.SCHWAIKHEIM_ID
            }
        else:
            raise ValueError(f"Ungültige Route: {route_number}")

# Globale Instanz
db_config = DBApiConfig()

if __name__ == "__main__":
    print("🔧 Deutsche Bahn API Konfiguration")
    print(f"DB_API_KEY: {'✅ Vorhanden' if db_config.DB_API_KEY else '❌ Fehlt'}")
    print(f"DB_CLIENT_ID: {'✅ Vorhanden' if db_config.DB_CLIENT_ID else '⚠️ Fehlt'}")
    print(f"Validation: {'✅ OK' if db_config.validate_config() else '❌ Fehler'}")
    print(f"Headers: {db_config.get_headers()}")
    print(f"Timetables URL: {db_config.get_timetables_url('8005454')}")
    print(f"Route 1: {db_config.get_route_config(1)}")
    print(f"Route 2: {db_config.get_route_config(2)}") 