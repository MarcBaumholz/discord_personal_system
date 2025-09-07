# Todo Bot

Automatischer Discord Bot für Todo-Verwaltung mit Todoist-Integration.

## Features

- ✅ **Automatische Todo-Erstellung**: Jede Nachricht im Channel wird automatisch als Todo erstellt
- 🎯 **Smart Parsing**: Erkennt automatisch Priorität, Datum und Familienmitglieder
- 📝 **Todo-Liste**: `!todo` zeigt alle aktiven Todos schön formatiert
- ✅ **Todo-Verwaltung**: Complete und Delete Funktionen
- 📊 **Statistiken**: Übersicht über alle Todos

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
```

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

```bash
docker build -t todo-bot .
docker run -d --name todo-bot --env-file .env todo-bot
```
