# 📔 Tagebuch Bot

Ein Discord Bot, der automatisch Tagebucheinträge in einer Notion-Datenbank speichert und täglich Erinnerungen sendet.

## 🎯 Features

- **Automatische Speicherung**: Tagebucheinträge werden automatisch in Notion gespeichert
- **Tägliche Erinnerungen**: Jeden Abend um 22:00 Uhr eine Erinnerung zum Tagebuch schreiben
- **Intelligente Titel-Generierung**: Automatische Titel basierend auf dem Eintraginhalt
- **Discord Integration**: Einfache Bedienung direkt im Discord Chat
- **Datum-Tracking**: Automatische Datumszuordnung für jeden Eintrag

## 🔧 Setup

### 1. Virtual Environment erstellen

```bash
cd discord/bots/Tagebuch_bot
python3 -m venv tagebuch_env
source tagebuch_env/bin/activate  # Linux/Mac
# oder
tagebuch_env\Scripts\activate  # Windows
```

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 3. Umgebungsvariablen konfigurieren

Kopiere `env.example` zu `.env` und fülle die Werte aus:

```bash
cp env.example .env
```

Bearbeite `.env`:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here

# Notion Configuration  
NOTION_TOKEN=your_notion_integration_token_here
TAGEBUCH_DATABASE_ID=214d42a1faf5803193c6c71b7d4d7c3f

# Discord Channel Configuration
TAGEBUCH_CHANNEL_ID=1384289197115838625

# Timezone Configuration (optional)
TIMEZONE=Europe/Berlin
```

### 4. Notion Setup

1. **Notion Integration erstellen**:
   - Gehe zu [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Erstelle eine neue Integration
   - Kopiere den "Internal Integration Token"

2. **Datenbank konfigurieren**:
   - Die Datenbank sollte folgende Eigenschaften haben:
     - `Titel` (Title) - Titel des Tagebucheintrags
     - `Datum` (Date) - Datum des Eintrags
     - `Text` (Rich Text) - Inhalt des Tagebucheintrags

3. **Integration verbinden**:
   - Öffne deine Notion-Datenbank
   - Klicke auf "..." → "Add connections" → Deine Integration auswählen

### 5. Discord Bot Setup

1. **Bot erstellen**: [Discord Developer Portal](https://discord.com/developers/applications)
2. **Bot Token kopieren** und in `.env` einfügen
3. **Bot Permissions**:
   - Send Messages
   - Read Message History
   - Use Slash Commands
   - Embed Links

## 🚀 Verwendung

### Bot starten

```bash
source tagebuch_env/bin/activate
python tagebuch_bot.py
```

### Tagebuch schreiben

Schreibe einfach eine Nachricht in den konfigurierten Discord-Kanal:

```
Heute war ein wunderschöner Tag! Ich habe viel Zeit im Park verbracht und ein interessantes Buch gelesen. Besonders dankbar bin ich für das schöne Wetter und die Zeit zum Entspannen.
```

Der Bot wird automatisch:
- Einen passenden Titel generieren
- Den Eintrag mit dem aktuellen Datum versehen
- Alles in der Notion-Datenbank speichern
- Eine Bestätigung senden

### Befehle

- `!tagebuch_help` - Hilfe anzeigen
- `!tagebuch_test` - Test-Eintrag erstellen
- `!tagebuch_reminder` - Test-Erinnerung senden

## 📋 Projektstruktur

```
Tagebuch_bot/
├── tagebuch_bot.py      # Haupt-Bot-Datei
├── notion_manager.py    # Notion API Integration
├── text_processor.py    # Titel-Generierung & Text-Verarbeitung
├── scheduler.py         # Tägliche Erinnerungen
├── requirements.txt     # Python Dependencies
├── env.example         # Umgebungsvariablen Template
├── README.md           # Diese Datei
├── PLANNING.md         # Projekt-Planung
├── TASK.md            # Aufgaben-Tracking
└── tagebuch_env/      # Virtual Environment
```

## 🔒 Sicherheit

- **Environment Variables**: Alle sensiblen Daten werden über Umgebungsvariablen verwaltet
- **Virtual Environment**: Isolierte Python-Umgebung
- **Logging**: Ausführliche Logs für Debugging und Monitoring

## 🐛 Troubleshooting

### Häufige Probleme

1. **"NOTION_TOKEN not found"**
   - Prüfe ob `.env` Datei existiert und korrekt ausgefüllt ist
   - Stelle sicher, dass die Notion Integration korrekt konfiguriert ist

2. **"Database not found"**
   - Prüfe die Database ID in der URL
   - Stelle sicher, dass die Integration Zugriff auf die Datenbank hat

3. **"Discord permissions error"**
   - Prüfe die Bot-Permissions im Discord Server
   - Stelle sicher, dass der Bot im richtigen Kanal schreiben kann

### Logs überprüfen

```bash
tail -f tagebuch_bot.log
```

## 📊 Monitoring

Der Bot erstellt automatisch Log-Dateien:
- `tagebuch_bot.log` - Alle Bot-Aktivitäten
- Console Output - Live-Status während der Ausführung

## 🔄 Weiterentwicklung

Geplante Features:
- Statistiken über Tagebucheinträge
- Backup-Funktionalität
- Mehrsprachige Unterstützung
- Web-Interface für Konfiguration

## 📝 Lizenz

Dieses Projekt ist für den persönlichen Gebrauch entwickelt.

## 🤝 Beitragen

Bei Fragen oder Verbesserungsvorschlägen, gerne Issues erstellen oder Pull Requests einreichen. 