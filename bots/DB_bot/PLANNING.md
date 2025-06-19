# S-Bahn Monitor - Deutsche Bahn Discord Bot

## 🎯 Ziel (Goal)
Entwicklung eines Discord Bots zur Live-Überwachung von S3-Verbindungen zwischen Schwaikheim und Stuttgart Feuersee mit kostenlosen DB APIs, der präzise Verspätungsinformationen und Echtzeit-Abfahrten anzeigt.

## 👤 User Stories
- Als Nutzer möchte ich "1" eingeben und sofort die nächsten S3-Abfahrten von Schwaikheim → Stuttgart Feuersee sehen
- Als Nutzer möchte ich "2" eingeben und sofort die nächsten S3-Abfahrten von Stuttgart Feuersee → Schwaikheim sehen  
- Als Nutzer möchte ich "status" eingeben und Bot-Status sowie API-Logs einsehen
- Als Nutzer möchte ich "help" eingeben und eine Übersicht der verfügbaren Befehle erhalten

## 📦 Datenmodell
```
Entities: 
- Route 1: Schwaikheim (8005454) → Stuttgart Feuersee (8002058)
- Route 2: Stuttgart Feuersee (8002058) → Schwaikheim (8005454)
- S3 Linie: Korrekte S-Bahn Linie für diese Strecke
- Fahrzeit: ~14 Minuten pro Strecke
- Takt: :23 und :53 jede Stunde

API Logging:
- api_logs/api_log_YYYYMMDD.json (tägliche JSON-Logs)
- Vollständige Request/Response Protokollierung
```

## 🔪 MVP Definition
**MVP**: Discord Bot mit einfachen Triggern "1"/"2" für Live-S3-Abfahrten, kostenlose DB RIS-APIs, JSON-Logging, deutsche Benutzeroberfläche.

**Nicht im MVP**: Mock-Daten, komplexe Slash Commands, Datenbankpersistierung, LLM-Integration

## 🔭 Zukunftsperspektive
**Modus**: Produktiver Live-Bot mit kostenlosen DB APIs
- Free-Plan Nutzung: ~1000 Requests/Tag (ausreichend für gelegentliche Abfragen)
- Rate Limiting: 2-Minuten Cache + max 50 Requests/Minute
- Live-Only Daten: Keine Mock-Fallbacks

## 🧱 Architekturentscheidung
**Komponenten:**
- Discord Bot (discord.py) mit Message-Event-Handler
- DB RIS-API Client (httpx) mit Authentication
- JSON-Logging System für API-Aufrufe
- Cache-System (2min TTL) für Performance
- Rich Discord Embeds mit Farbkodierung

## ⚙️ Tech-Stack
```
Stack: 
- Python 3.11 (discord.py 2.3.2, httpx 0.27.0)
- DB RIS APIs (RIS::Stations, RIS::Journeys)  
- JSON Logging (strukturiert mit Timestamps)
- Discord Rich Embeds (Color-coded delays)
- Virtual Environment (db_env)
```

## 🚀 Entwicklungsprozess
```
Process:
1. Virtual Environment Setup + Requirements Installation
2. DB API Account Setup + Free-Plan Subscriptions  
3. Core Bot Implementation (Message Handler + API Client)
4. Rich Discord Embeds + German Localization
5. JSON Logging System + API Request Tracking
6. Live Testing + Rate Limit Monitoring
7. Error Handling + Fallback Messages
8. Documentation + User Guide
```

## 💰 Kosten & API Limits
- **Kostenfrei**: Free-Plan für RIS::Stations + RIS::Journeys
- **Limits**: ~1000 Requests/Tag, ~60 Requests/Minute  
- **Verbrauch**: ~4-8 Requests bei 2 Abfragen → weit unter Limit
- **Überwachung**: JSON-Logs tracken Request-Anzahl

## 🔐 Security & Best Practices
- Client-ID + API-Key sicher in .env speichern
- Rate Limiting gegen API-Überlastung
- Strukturiertes Logging für Debugging
- Fehlerbehandlung ohne Mock-Fallbacks
- Deutsche Fehlermeldungen für Benutzerfreundlichkeit

## 📋 Implementierungsreihenfolge
1. **Phase 1**: Venv Setup + Requirements ✅
2. **Phase 2**: DB API Account + Free Subscriptions  
3. **Phase 3**: Core Bot + Message Handler
4. **Phase 4**: RIS API Client + Authentication
5. **Phase 5**: Rich Embeds + German UI
6. **Phase 6**: JSON Logging System  
7. **Phase 7**: Live Testing + Monitoring
8. **Phase 8**: Error Handling + Documentation 