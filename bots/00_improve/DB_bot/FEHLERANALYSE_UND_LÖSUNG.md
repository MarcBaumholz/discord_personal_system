# 🚊 Deutsche Bahn API - Fehleranalyse und Lösung

## 🔴 Aktueller Fehler

### Symptome
```
📡 API Response Status: 404
❌ API Endpoint nicht gefunden
```

### Ursache
Die verwendeten API-Endpunkte sind **falsch** oder **veraltet**.

## 🔧 Korrektur der API-Endpunkte

### 1. Problem: Falsche API URLs

**Aktuelle (falsche) URLs in sbahn_monitor.py:**
```python
api_url = "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-journeys/v1/journeys"
```

**Korrekte API URLs für Deutsche Bahn:**
```python
# RIS Journeys API (DB Transporteure)
api_url = "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-journeys/v1/journeys"

# Oder alternative Timetables API
api_url = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/station/{eva_number}/arrivals"
```

### 2. Problem: Falsche Authentifizierung

**Aktuell:**
```python
headers = {
    "Authorization": f"Bearer {DB_API_KEY}",
    # ...
}
```

**Korrekt für Deutsche Bahn API:**
```python
headers = {
    "DB-Client-Id": DB_CLIENT_ID,
    "DB-Api-Key": DB_API_KEY,
    "Accept": "application/json",
    "User-Agent": "S3-Live-Monitor/1.0"
}
```

## 🔑 Neue API-Schlüssel erforderlich

### Benötigte Variablen in .env:
```bash
# Deutsche Bahn API Credentials
DB_CLIENT_ID=your_client_id_here
DB_API_KEY=your_api_key_here
DB_CLIENT_SECRET=your_client_secret_here  # Falls erforderlich

# Oder für OAuth-basierte APIs:
DB_ACCESS_TOKEN=your_access_token_here
```

## 📋 Schritte zur Lösung

### Schritt 1: Richtige API-Endpunkte implementieren
- ✅ Korrekte URLs für RIS Journeys API verwenden
- ✅ Station-IDs validieren (Schwaikheim: 8005454, Feuersee: 8002058)
- ✅ Parameter-Namen prüfen

### Schritt 2: Authentifizierung korrigieren
- ✅ DB-Client-Id und DB-Api-Key Header verwenden
- ✅ Bearer Token durch Client-ID/API-Key ersetzen
- ✅ OAuth-Flow implementieren falls erforderlich

### Schritt 3: API-Response Format anpassen
- ✅ Response-Struktur der echten DB API analysieren
- ✅ Parser-Funktionen entsprechend anpassen
- ✅ Fehlerbehandlung für echte API-Fehler

### Schritt 4: Testing mit echten Daten
- ✅ API-Aufruf mit korrekten Credentials testen
- ✅ Logging für Debugging erweitern
- ✅ Mock-Daten entfernen und nur echte Daten verwenden

## 🛠️ Implementierung

### Neue config.py Variablen:
```python
class Config:
    # Deutsche Bahn API (neue Struktur)
    DB_CLIENT_ID = os.getenv("DB_CLIENT_ID", "")
    DB_API_KEY = os.getenv("DB_API_KEY", "")
    DB_CLIENT_SECRET = os.getenv("DB_CLIENT_SECRET", "")
    
    # Base URLs für verschiedene APIs
    RIS_JOURNEYS_BASE_URL = "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-journeys/v1"
    TIMETABLES_BASE_URL = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1"
    STATIONS_BASE_URL = "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-stations/v1"
```

### Neue HTTP Headers:
```python
def get_db_headers(self) -> Dict[str, str]:
    return {
        "DB-Client-Id": self.DB_CLIENT_ID,
        "DB-Api-Key": self.DB_API_KEY,
        "Accept": "application/json",
        "User-Agent": "S3-Live-Monitor/1.0"
    }
```

## ⚠️ Wichtige Hinweise

1. **API-Registrierung erforderlich:** Neue Credentials bei DB API Marketplace beantragen
2. **Rate Limits:** Deutsche Bahn APIs haben strikte Rate Limits
3. **Station-IDs prüfen:** EVA-Nummern müssen korrekt sein
4. **API-Dokumentation:** Offizielle DB API Docs für exakte Parameter verwenden

## 🔄 Nächste Schritte

1. **Sofort:** Korrekte API-Endpunkte implementieren
2. **Dann:** Neue API-Credentials beantragen/konfigurieren
3. **Testing:** Mit echten DB API-Daten testen
4. **Optimierung:** Caching und Fehlerbehandlung verbessern

---
*Status: KRITISCH - API funktioniert nicht ohne korrekte Endpunkte und Credentials* 