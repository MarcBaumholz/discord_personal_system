# 🤖 Todo Bot - Vollständiges Setup & Benutzerhandbuch

## 📋 Übersicht

Der Todo Bot wandelt automatisch jede Discord-Nachricht im festgelegten Channel (`1368180016785002536`) in ein Todoist-Todo um. Er bietet intelligente Erkennung von Prioritäten, Terminen und Familienmitgliedern.

## 🎯 Features

### ✅ Automatische Todo-Erstellung
- **Jede Nachricht** im Channel wird automatisch als Todo erstellt
- **Kein Command nötig** - einfach normal schreiben
- **Bestätigung** mit Embed-Nachricht und ✅ Reaction

### 🧠 Intelligente Erkennung

#### Prioritäten (automatisch erkannt):
- `wichtig`, `dringend`, `urgent`, `sofort` → 🔴 Urgent (Priorität 4)
- `hoch`, `high` → 🟠 Hoch (Priorität 3)
- `normal`, `medium` → 🟡 Normal (Priorität 2)
- `niedrig`, `low`, `später` → 🟢 Niedrig (Priorität 1)

#### Termine (automatisch erkannt):
- `heute`, `today` → Heute fällig
- `morgen`, `tomorrow` → Morgen fällig
- `übermorgen` → Übermorgen fällig
- `montag`, `dienstag`, `mittwoch`, etc. → Nächster Wochentag
- `15.12`, `31.01` → Spezifisches Datum (DD.MM)
- `nächste woche`, `next week` → Nächste Woche
- `nächster monat`, `next month` → Nächster Monat

#### Familie/Labels (automatisch erkannt):
- `Marc`, `papa` → Label "Marc"
- `Maggie`, `mama` → Label "Maggie"
- `gemeinsam`, `together`, `alle` → Label "Familie"
- **Default**: Wenn nichts erkannt wird → Label mit Discord Username

### 💬 Commands

#### `!todo` oder `!list`
Zeigt alle aktiven Todos schön formatiert an
```
!todo
```

#### `!complete <suchbegriff>` oder `!done <suchbegriff>`
Markiert ein Todo als erledigt
```
!complete Einkaufen
!done Müll rausbringen
```

#### `!delete <suchbegriff>` oder `!del <suchbegriff>`
Löscht ein Todo komplett
```
!delete Alte Aufgabe
!del Test Todo
```

#### `!stats`
Zeigt Statistiken über alle Todos
```
!stats
```

#### `!help_todo`
Zeigt die Hilfe an
```
!help_todo
```

## 📝 Beispiele

### Einfache Todos
```
Einkaufen gehen
→ Normal Priority, kein Datum, Label: [Username]

Müll rausbringen
→ Normal Priority, kein Datum, Label: [Username]
```

### Mit Priorität
```
Wichtig: Arzttermin vereinbaren
→ 🟠 Hoch Priority, kein Datum

Dringend: Rechnung bezahlen heute
→ 🔴 Urgent Priority, fällig heute

Niedrig: Buch lesen später
→ 🟢 Niedrig Priority, kein Datum
```

### Mit Terminen
```
Einkaufen heute
→ Fällig heute

Zahnarzt morgen
→ Fällig morgen

Meeting am Montag
→ Fällig nächsten Montag

Urlaub buchen 15.12
→ Fällig am 15. Dezember

Projekt abschließen nächste Woche
→ Fällig nächste Woche
```

### Mit Familie/Labels
```
Marc soll Müll rausbringen
→ Label "Marc"

Maggie: Einkaufen gehen
→ Label "Maggie"

Papa soll Auto waschen
→ Label "Marc"

Gemeinsam: Urlaub planen
→ Label "Familie"

Alle: Wohnzimmer aufräumen
→ Label "Familie"
```

### Komplexe Beispiele
```
Wichtig: Marc soll dringend heute Müll rausbringen
→ 🔴 Urgent Priority, fällig heute, Label "Marc"

Gemeinsam: Weihnachtsgeschenke kaufen nächste Woche
→ 🟡 Normal Priority, fällig nächste Woche, Label "Familie"

Niedrig: Maggie kann später Blumen gießen
→ 🟢 Niedrig Priority, kein Datum, Label "Maggie"
```

## 🚀 Installation & Setup

### Voraussetzungen
- Python 3.11+
- Discord Bot Token
- Todoist API Token
- Virtual Environment (empfohlen)

### 1. Environment Setup
```bash
# Aktiviere Virtual Environment (falls vorhanden)
source /home/pi/Documents/calories_env/bin/activate

# Oder erstelle neues Environment
python3 -m venv todo_env
source todo_env/bin/activate
```

### 2. Installation
```bash
cd /home/pi/Documents/discord/bots/00_production/todo_bot

# Installiere Requirements
pip install -r requirements.txt

# Führe Setup aus
chmod +x setup.sh
./setup.sh
```

### 3. Konfiguration
Stelle sicher, dass in `.env` folgende Variablen gesetzt sind:
```env
DISCORD_TOKEN=dein_discord_token
TODOIST_API_KEY=dein_todoist_api_key
WEEKLY_PLANNING_CHANNEL_ID=1368180016785002536
```

### 4. Test
```bash
# Teste die API-Verbindung
python test_todo_bot.py

# Health Check
python health_check.py
```

### 5. Starten

#### Einzeln starten:
```bash
python todo_agent.py
```

#### Im Multi-Bot System:
```bash
cd /home/pi/Documents/discord/bots/00_production
python start_multibot.py
```

## 🐳 Docker Deployment

### Einzelner Todo Bot
```bash
# Build
docker build -t todo-bot .

# Run
docker run -d --name todo-bot --env-file .env todo-bot
```

### Multi-Bot System
```bash
# Start alle Bots inklusive Todo Bot
docker-compose -f docker-compose.multibot.yml up -d
```

## 🔧 Troubleshooting

### Bot antwortet nicht
1. Prüfe, ob der Bot online ist: `python health_check.py`
2. Prüfe die Logs: `tail -f todo_bot.log`
3. Teste die API: `python test_todo_bot.py`

### Todos werden nicht erstellt
1. Prüfe Todoist API Key: In `.env` und bei Todoist
2. Prüfe Channel ID: Muss `1368180016785002536` sein
3. Prüfe Bot-Permissions: Bot braucht Lese- und Schreibrechte

### Priorität/Datum nicht erkannt
1. Verwende deutsche oder englische Keywords
2. Schreibe Datum in unterstützten Formaten
3. Teste mit einfachen Beispielen

### Performance Issues
1. Zu viele Todos? Verwende `!stats` für Übersicht
2. Logs zu groß? Lösche alte Logs
3. API Rate Limits? Warte und teste später

## 📊 Monitoring

### Health Check
```bash
# Manueller Check
python health_check.py

# Automatisch (Crontab)
*/5 * * * * cd /path/to/todo_bot && python health_check.py >> health.log
```

### Logs
```bash
# Live Logs anschauen
tail -f todo_bot.log

# Letzte Fehler
grep ERROR todo_bot.log | tail -10

# Statistiken
grep "Created todo" todo_bot.log | wc -l  # Anzahl erstellter Todos
```

## 🔄 Updates & Wartung

### Bot Update
```bash
# Code aktualisieren
git pull

# Dependencies aktualisieren
pip install -r requirements.txt --upgrade

# Bot neu starten
# (Je nach Setup: Docker restart, systemctl restart, etc.)
```

### Daten-Backup
- **Todos**: Sind in Todoist gespeichert (automatisches Backup)
- **Logs**: Regelmäßig archivieren
- **Config**: `.env` Datei sichern

## 🎨 Anpassungen

### Neue Prioritäts-Keywords
In `todo_agent.py`, Zeile ~69:
```python
self.priority_keywords = {
    'urgent': 4, 'wichtig': 4, 'dringend': 4, 'sofort': 4,
    'hoch': 3, 'high': 3,
    'normal': 2, 'medium': 2,
    'niedrig': 1, 'low': 1, 'später': 1,
    # Füge hier neue Keywords hinzu:
    'kritisch': 4, 'asap': 4
}
```

### Neue Familienmitglieder
In `todo_agent.py`, Zeile ~85:
```python
self.family_labels = {
    'marc': 'Marc', 'maggie': 'Maggie',
    'mama': 'Maggie', 'papa': 'Marc',
    'gemeinsam': 'Familie', 'together': 'Familie', 'alle': 'Familie',
    # Füge hier neue Mitglieder hinzu:
    'oma': 'Oma', 'opa': 'Opa'
}
```

### Neuen Channel hinzufügen
In `.env`:
```env
# Zusätzlicher Channel (erfordert Code-Anpassung)
ANOTHER_TODO_CHANNEL_ID=123456789
```

## 📈 Erweiterte Features (Ideen)

### Was noch cool wäre:

1. **📱 Recurring Todos**: `täglich`, `wöchentlich`, `monatlich`
2. **🎯 Sub-Tasks**: Automatische Erkennung von Listen
3. **📊 Analytics**: Wöchentliche Reports per DM
4. **🔔 Reminders**: Discord-Erinnerungen vor Fälligkeit
5. **📋 Templates**: Vordefinierte Todo-Vorlagen
6. **🏷️ Auto-Projects**: Automatische Projektzeuweisung basierend auf Keywords
7. **📸 Attachments**: Screenshots zu Todos hinzufügen
8. **🗣️ Voice**: Sprach-Nachrichten zu Todos umwandeln
9. **⏱️ Time Tracking**: Zeit-Erfassung für Todos
10. **🤖 AI Integration**: GPT für besseres Todo-Parsing

Sag Bescheid, welche Features dich interessieren! 🚀
