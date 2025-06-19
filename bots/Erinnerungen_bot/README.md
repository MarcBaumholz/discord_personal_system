# Erinnerungen Bot

Ein Discord Bot für automatische tägliche Erinnerungen mit zwei Hauptfunktionen:

## 🎯 Funktionen

### 1. 🎂 Geburtstags-Erinnerungen
- Tägliche Überprüfung einer Notion-Datenbank
- Automatische Benachrichtigung bei Geburtstagen
- Schöne formatierte Nachrichten mit Alter und Beziehungsinfos
- Läuft täglich um 07:00 Uhr

### 2. 🗑️ Müllkalender-Erinnerungen  
- Überprüfung des Müllkalenders für Schweigheim, Baden-Württemberg
- Erinnerung am Vorabend (20:00 Uhr) wenn morgen Müll abgeholt wird
- Erkennung verschiedener Tonnenarten (Restmüll, Bio, Gelber Sack, Papier)
- Praktische Tipps zur rechtzeitigen Bereitstellung

## 🔧 Setup

### 1. Environment Variables
Erstelle eine `.env` Datei basierend auf `env.example`:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here

# Discord Channel IDs
ERINNERUNGEN_CHANNEL_ID=1361084010847015241

# Notion API Configuration  
NOTION_TOKEN=your_notion_integration_token_here
GEBURTSTAGE_DATABASE_ID=214d42a1faf580fa8eccd0ddfd69ca98

# Timezone Configuration
TIMEZONE=Europe/Berlin

# Logging Configuration
LOG_LEVEL=INFO
```

### 2. Dependencies installieren
```bash
# Virtual Environment aktivieren
source erinnerungen_env/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

### 3. Notion Integration einrichten
1. Gehe zu https://www.notion.so/my-integrations
2. Erstelle eine neue Integration
3. Kopiere den API-Token zu NOTION_TOKEN
4. Teile deine Geburtstagsdatenbank mit der Integration

### 4. Discord Bot einrichten
1. Gehe zu https://discord.com/developers/applications
2. Erstelle eine neue Anwendung und Bot
3. Kopiere den Bot-Token zu DISCORD_TOKEN
4. Lade den Bot auf deinen Server ein mit den nötigen Berechtigungen

## 🚀 Bot starten

```bash
# Virtual Environment aktivieren
source erinnerungen_env/bin/activate

# Bot starten
python erinnerungen_bot.py
```

## 🎮 Befehle

- `!test_geburtstage` - Manuelle Überprüfung der heutigen Geburtstage
- `!test_muell` - Manuelle Überprüfung der morgigen Müllabholung

## 📁 Projektstruktur

```
erinnerungen_bot/
├── erinnerungen_bot.py      # Hauptbot-Datei
├── notion_manager.py        # Notion API Integration
├── geburtstage.py          # Geburtstags-Management
├── muellkalender.py        # Müllkalender-Management  
├── scheduler.py            # Automatische Zeitplanung
├── requirements.txt        # Python Dependencies
├── env.example            # Environment Variables Vorlage
├── PLANNING.md            # Detaillierte Planung
├── TASK.md               # Aufgabenliste
└── README.md             # Diese Datei
```

## ⏰ Zeitplan

- **07:00 Uhr**: Geburtstags-Check und Benachrichtigung
- **20:00 Uhr**: Müllkalender-Check und Erinnerung für morgen

## 🗃️ Datenquellen

### Notion-Datenbank (Geburtstage)
- **URL**: https://www.notion.so/marcbaumholz/214d42a1faf580fa8eccd0ddfd69ca98
- **Erwartete Felder**: 
  - Name (Title)
  - Geburtsdatum (Date)
  - Beziehung (Optional, Select/Text)

### Müllkalender (Schweigheim)
- **Quelle**: Abfallwirtschaft Rems-Murr (AWRM)
- **Ort**: Schweigheim, Baden-Württemberg
- **Pattern-basierte Simulation** der Abholtermine

## 🐛 Logging

Der Bot erstellt automatisch Log-Dateien:
- `erinnerungen_bot.log` - Alle Bot-Aktivitäten
- Console Output - Echtzeitausgabe

## 🔍 Testing

### Manueller Test
```bash
# Bot starten und in Discord testen:
!test_geburtstage
!test_muell
```

### Notion-Verbindung testen
```python
# In Python-Shell
from notion_manager import NotionManager
manager = NotionManager()
await manager.test_connection()
```

## 🛠️ Troubleshooting

### Häufige Probleme:

1. **"NOTION_TOKEN not found"**
   - Überprüfe die `.env` Datei
   - Stelle sicher, dass der Notion-Token korrekt ist

2. **"Channel not found"**
   - Überprüfe die ERINNERUNGEN_CHANNEL_ID
   - Stelle sicher, dass der Bot Zugriff auf den Channel hat

3. **"Bot not responding"**
   - Überprüfe die Discord-Token
   - Stelle sicher, dass der Bot die nötigen Berechtigungen hat

4. **"No birthdays found"**
   - Überprüfe die Notion-Datenbank-Struktur
   - Stelle sicher, dass die Database-ID korrekt ist

## 📝 Development Notes

- Alle Dateien sind unter 400 Zeilen gehalten (modular)
- Extensive Logging für Debugging
- Timezone-bewusste Datumsverarbeitung
- Graceful Error Handling
- Async/Await für Performance

## 🔄 Future Enhancements

- Web-Dashboard für Verwaltung
- Weitere Erinnerungstypen (Termine, etc.)
- Integration mit echtem AWRM-API
- Personalisierte Geburtstagsgrüße
- Wochenübersicht kommender Events

## 📞 Support

Bei Problemen oder Fragen:
1. Überprüfe die Logs (`erinnerungen_bot.log`)
2. Teste die Notion-API-Verbindung
3. Verifiziere Discord-Bot-Berechtigungen 