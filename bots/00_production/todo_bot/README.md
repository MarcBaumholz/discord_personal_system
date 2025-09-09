# Todo Bot

Automatischer Discord Bot für Todo-Verwaltung mit Todoist-Integration.

## Features

- ✅ **Automatische Todo-Erstellung**: Jede Nachricht im Channel wird automatisch als Todo erstellt
- 🎯 **Smart Parsing**: Erkennt automatisch Priorität, Datum und Familienmitglieder
- 📝 **Todo-Liste**: `!todo` zeigt alle aktiven Todos schön formatiert
- ✅ **Todo-Verwaltung**: Complete und Delete Funktionen
- 📊 **Statistiken**: Übersicht über alle Todos
- 🧪 **Comprehensive Testing**: Vollständige Test-Suite für alle Funktionen
- 🐳 **Docker Support**: Containerized deployment mit Health Checks
- 🔧 **Fixed Issues**: Alle bekannten Probleme behoben (Priority Mapping, API Parameter, etc.)

## Channel

Der Bot überwacht den Channel: `1368180016785002536`

## Commands

- `!todo` - Alle aktiven Todos anzeigen
- `!complete <suche>` - Todo als erledigt markieren
- `!delete <suche>` - Todo löschen  
- `!stats` - Statistiken anzeigen
- `!help_todo` - Hilfe anzeigen

## Smart Features

### Priorität (automatische Erkennung)
- `wichtig`, `dringend`, `urgent`, `sofort` → Hohe Priorität (🔴)
- `hoch`, `high` → Mittlere-hohe Priorität (🟠)
- `normal`, `medium` → Normale Priorität (🟡)
- `niedrig`, `low`, `später` → Niedrige Priorität (🟢)

### Datum (automatische Erkennung)
- `heute`, `today` → Heute fällig
- `morgen`, `tomorrow` → Morgen fällig  
- `übermorgen` → Übermorgen fällig
- `montag`, `dienstag`, etc. → Nächster Wochentag
- `15.12`, `31.01` → Spezifisches Datum
- `nächste woche`, `next week` → Nächste Woche

### Familie/Labels (automatische Erkennung)
- `Marc`, `papa` → Label "Marc"
- `Maggie`, `mama` → Label "Maggie"  
- `gemeinsam`, `together`, `alle` → Label "Familie"
- Wenn nichts erkannt wird → Label mit Discord Username

## Beispiele

```
Wichtig: Einkaufen morgen
→ Todo mit hoher Priorität, fällig morgen

Marc soll den Müll rausbringen heute
→ Todo mit Label "Marc", fällig heute

Gemeinsam: Urlaub planen nächste Woche  
→ Todo mit Label "Familie", fällig nächste Woche

Arzttermin vereinbaren
→ Einfaches Todo mit normaler Priorität

piuztzen
→ Einfaches Todo mit niedriger Priorität

Wichtig: piuztzen heute
→ Todo mit hoher Priorität, fällig heute

Marc soll piuztzen morgen
→ Todo mit Label "Marc", fällig morgen
```

## Testing

### Test-Suite ausführen

```bash
# Alle Tests ausführen
python3 comprehensive_test.py

# Spezifische Piuztzen-Tests
python3 test_piuztzen.py

# Discord Bot Simulation
python3 test_discord_bot.py

# Original Todoist API Tests
python3 test_todo_bot.py
```

### Test-Ergebnisse
- ✅ **9/9 Tests bestanden** in der Comprehensive Test Suite
- ✅ **Priority Mapping** funktioniert korrekt (🔴=4, 🟠=3, 🟡=2, 🟢=1)
- ✅ **Date Parsing** erkennt alle Zeitangaben korrekt
- ✅ **Label Detection** funktioniert für alle Familienmitglieder
- ✅ **"piuztzen" Funktionalität** vollständig getestet und funktionsfähig
- ✅ **Todoist API Integration** funktioniert einwandfrei

## Installation

1. Requirements installieren:
```bash
pip install -r requirements.txt
```

2. Environment Variables in `.env` setzen:
```
DISCORD_TOKEN=your_discord_token
TODOIST_API_KEY=your_todoist_api_key
WEEKLY_PLANNING_CHANNEL_ID=1368180016785002536
```

3. Bot starten:
```bash
python todo_agent.py
```

## Docker

### Container Status
Der Bot läuft bereits in einem Docker Container:
- **Container Name**: `discord-todo-bot`
- **Status**: ✅ Running (Healthy)
- **Health Check**: Alle 60 Sekunden
- **Restart Policy**: unless-stopped

### Container Management

```bash
# Container Status prüfen
docker ps | grep todo

# Container Logs anzeigen
docker logs discord-todo-bot

# Container neu starten (mit neuer Version)
docker-compose -f docker-compose.todo.yml down
docker-compose -f docker-compose.todo.yml up -d --build

# Container stoppen
docker stop discord-todo-bot

# Container starten
docker start discord-todo-bot
```

### Docker Compose

```bash
# Mit Docker Compose starten
docker-compose -f docker-compose.todo.yml up -d

# Mit Docker Compose stoppen
docker-compose -f docker-compose.todo.yml down

# Logs anzeigen
docker-compose -f docker-compose.todo.yml logs -f
```

### Environment Variables
Der Container verwendet die `.env` Datei aus dem übergeordneten Verzeichnis:
- `DISCORD_TOKEN` - Discord Bot Token
- `TODOIST_API_KEY` - Todoist API Key
- `WEEKLY_PLANNING_CHANNEL_ID` - Discord Channel ID (1368180016785002536)

## Troubleshooting

### Häufige Probleme

1. **"piuztzen" erstellt kein Todo**
   - ✅ **Gelöst**: Priority mapping und API Parameter wurden behoben
   - **Test**: `python3 test_piuztzen.py`

2. **Container startet nicht**
   - Prüfe Environment Variables: `docker logs discord-todo-bot`
   - Prüfe .env Datei: `cat ../.env | grep DISCORD_TOKEN`

3. **Priority Mapping falsch**
   - ✅ **Gelöst**: Duplicate 'wichtig' key wurde entfernt
   - **Test**: `python3 comprehensive_test.py`

4. **Todoist API Fehler**
   - Prüfe API Key: `python3 test_todo_bot.py`
   - Prüfe Internetverbindung

### Debug Commands

```bash
# Container Logs in Echtzeit
docker logs -f discord-todo-bot

# Container Health Status
docker inspect discord-todo-bot | grep -A 5 Health

# Environment Variables im Container prüfen
docker exec discord-todo-bot env | grep -E "(DISCORD|TODOIST|WEEKLY)"

# Bot Test im Container ausführen
docker exec discord-todo-bot python test_piuztzen.py
```

## Changelog

### Version 2.0 (Current)
- ✅ Fixed priority mapping (removed duplicate 'wichtig' key)
- ✅ Fixed API parameter issue (removed 'creator' parameter)
- ✅ Added comprehensive test suite (9 tests, 100% pass rate)
- ✅ Added specific "piuztzen" functionality tests
- ✅ Added Discord bot simulation tests
- ✅ Updated Docker configuration with health checks
- ✅ Improved error handling and logging
- ✅ Fixed priority emoji display in tests

## ✅ Current Status (September 2025)

**🟢 BOT IS LIVE AND OPERATIONAL**

The Todo Bot is currently running in a Docker container and fully functional.

### Bot Status
- **Container**: `todo_bot_todo-bot` - Running (Healthy)
- **Uptime**: 1+ hour (recently restarted)
- **Health Check**: ✅ Healthy
- **Last Restart**: September 9, 2025

### Recent Updates
- ✅ **Stable Operation**: Bot running continuously without issues
- ✅ **Docker Health Checks**: Automated monitoring and restart capability
- ✅ **Todoist Integration**: Active API connectivity for todo management
- ✅ **Smart Parsing**: Working priority, date, and family member detection
- ✅ **Comprehensive Testing**: All 9 tests passing (100% success rate)

### Tested Functionality
- ✅ Automatic todo creation from Discord messages
- ✅ Smart parsing of priority, dates, and family members
- ✅ Todoist API integration for CRUD operations
- ✅ "piuztzen" functionality fully working
- ✅ Priority mapping (🔴=4, 🟠=3, 🟡=2, 🟢=1)
- ✅ Date parsing for various German time expressions
- ✅ Family member label detection (Marc, Maggie, Familie)
