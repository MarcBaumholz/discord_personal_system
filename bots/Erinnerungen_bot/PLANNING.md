# Erinnerungen Bot - Implementation Plan

## 🎯 Goal
Entwickle einen Discord Bot, der täglich zwei wichtige Erinnerungen versendet:
1. **Geburtstags-Erinnerungen** aus einer Notion-Datenbank
2. **Müllkalender-Erinnerungen** für Schweigheim, Baden-Württemberg

Der Bot soll automatisch täglich checken und proaktiv Erinnerungen in den Discord-Channel (ID: 1361084010847015241) senden.

## 👤 User Stories
- Als User möchte ich täglich automatisch über anstehende Geburtstage informiert werden
- Als User möchte ich am Vorabend über die Müllabholung am nächsten Tag informiert werden
- Als User möchte ich, dass der Bot aus meiner bestehenden Notion-Geburtstagsdatenbank liest
- Als User möchte ich keine manuellen Befehle eingeben müssen - alles soll automatisch laufen

## 📦 Data Model

**Entities:**
- **Birthday**: name, date, relation (aus Notion-Datenbank)
- **Waste**: waste_type, collection_date, reminder_date (von Müllkalender API)
- **Channel**: discord_channel_id (aus Environment)

**Relations:**
- Notion database → Birthday entries
- Müllkalender API → Waste collection schedule

## 🔪 MVP Features

### Core Features:
1. **Environment Setup**: Discord Token, Channel ID, Notion Token & Database ID
2. **Geburtstage-Modul** (`geburtstage.py`):
   - Täglicher Check der Notion-Datenbank
   - Erkennung von Geburtstagen am aktuellen Tag
   - Formatierte Discord-Nachricht senden
3. **Müllkalender-Modul** (`muellkalender.py`):
   - API-Integration für Schweigheim Müllkalender
   - Check: Wird morgen Müll abgeholt?
   - Erinnerung am Vorabend senden
4. **Scheduler**: Täglich um 07:00 für Geburtstage und um 20:00 für Müll-Erinnerungen
5. **Discord Integration**: Nachrichten in spezifischen Channel senden

### Datenquellen:
- **Geburtstage**: Notion-Datenbank (https://www.notion.so/marcbaumholz/214d42a1faf580fa8eccd0ddfd69ca98)
- **Müllkalender**: Baden-Württemberg API oder Web-Scraping für Schweigheim

## 📝 System Architecture

```
Erinnerungen Bot (erinnerungen_bot.py)
├── Geburtstage Module (geburtstage.py) → Notion API
├── Müllkalender Module (muellkalender.py) → Müllkalender API/Scraper
├── Scheduler (scheduler.py) → Background threads
├── Notion Manager (notion_manager.py) → Notion Client
└── Discord Client → Discord API (Channel: 1361084010847015241)
```

## 🔭 Implementation Steps

### Phase 1: Setup & Structure
1. Erstelle Environment-File mit allen nötigen Keys
2. Erstelle requirements.txt mit Dependencies
3. Aktiviere Python venv
4. Erstelle Hauptbot-Datei (erinnerungen_bot.py)

### Phase 2: Geburtstage-Feature
1. Implementiere `notion_manager.py` für Notion-API-Calls
2. Implementiere `geburtstage.py` mit:
   - Datenbank-Abfrage
   - Datumsvergleich (heute == Geburtstag?)
   - Nachrichten-Formatierung
3. Teste Geburtstage-Feature

### Phase 3: Müllkalender-Feature
1. Recherchiere Müllkalender-API für Schweigheim
2. Implementiere `muellkalender.py` mit:
   - API-Integration oder Web-Scraping
   - Logik: Wird morgen abgeholt?
   - Tonnen-Art erkennen (Restmüll, Gelber Sack, etc.)
3. Teste Müllkalender-Feature

### Phase 4: Scheduling & Integration
1. Implementiere `scheduler.py` für automatische Checks
2. Integriere beide Module in Hauptbot
3. Teste vollständige Integration
4. Deploy und Monitor

## ⚙️ Tech Stack
- **Backend**: Python 3.11
- **Discord**: discord.py
- **Database**: Notion API (notion-client)
- **Scheduling**: schedule library
- **HTTP Requests**: requests library
- **Environment**: python-dotenv
- **Logging**: Python logging module

## 🚀 Development Process

### Environment Variables (.env):
```
DISCORD_TOKEN=your_discord_token
ERINNERUNGEN_CHANNEL_ID=1361084010847015241
NOTION_TOKEN=your_notion_token
GEBURTSTAGE_DATABASE_ID=214d42a1faf580fa8eccd0ddfd69ca98
```

### Deployment:
- Lokaler Server (Raspberry Pi)
- Virtual Environment isoliert
- Automatischer Start via systemd
- Logging für Debugging

## 🧪Testing Strategy
1. **Unit Tests**: Jedes Modul einzeln testen
2. **Integration Tests**: Bot-Discord-Verbindung testen
3. **Manual Tests**: 
   - Testgeburtstag in Notion anlegen
   - Müllkalender-Antwort simulieren
4. **Live Tests**: Mit echten Daten aber in Test-Channel

## 📅 Timeline
- **Tag 1**: Setup, Structure, Environment
- **Tag 2**: Geburtstage-Feature implementieren & testen
- **Tag 3**: Müllkalender-Feature implementieren & testen
- **Tag 4**: Integration, Scheduling, Final Testing
- **Tag 5**: Deployment & Monitoring

## 🔍 Recherche Notizen

### Notion-Datenbank Struktur:
- URL: https://www.notion.so/marcbaumholz/214d42a1faf580fa8eccd0ddfd69ca98
- Vermutete Felder: Name, Geburtsdatum, evtl. Beziehung
- API-Access über Notion Integration

### Müllkalender Schweigheim:
- Recherche nötig: Offizielle API oder Website-Scraping
- Alternativen: iCal-Feed, JSON-API, HTML-Parsing
- Wichtige Müllarten: Restmüll, Gelber Sack, Papier, Bio

## 💡 Future Enhancements
- Wochenübersicht der kommenden Geburtstage
- Müllkalender für ganze Woche anzeigen
- Personalisierte Geburtstagsgrüße
- Integration weiterer Erinnerungstypen (Termine, etc.)
- Web-Dashboard für Verwaltung 