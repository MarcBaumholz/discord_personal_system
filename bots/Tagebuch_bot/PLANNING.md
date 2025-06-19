# 📔 Tagebuch Bot - Daily Journal & Reminder System Plan

## 🎯 Ziel (Goal)
Erstelle einen Discord-Bot, der täglich um 22:00 Uhr eine Erinnerung zum Tagebuch schreiben sendet und Tagebucheinträge automatisch in einer Notion-Datenbank speichert mit Titel, Datum und Text.

## 👤 User Stories
- Als Nutzer möchte ich täglich um 22:00 Uhr eine Erinnerung erhalten, damit ich nicht vergesse mein Tagebuch zu führen
- Als Nutzer möchte ich einfach in den Discord-Chat schreiben können und meine Einträge werden automatisch in Notion gespeichert
- Als Nutzer möchte ich, dass meine Tagebucheinträge mit Datum und automatisch generiertem Titel gespeichert werden
- Als Nutzer möchte ich eine Bestätigung erhalten, wenn mein Eintrag erfolgreich gespeichert wurde

## 📦 Datenmodell
**Notion Database URL**: `https://www.notion.so/marcbaumholz/214d42a1faf5803193c6c71b7d4d7c3f?v=214d42a1faf58064a98f000c2b6035da&source=copy_link`

**Eigenschaften der Datenbank**:
- **Titel** (Title): Automatisch generiert aus dem ersten Satz oder Thema des Eintrags
- **Datum** (Date): Das aktuelle Datum des Tagebucheintrags
- **Text** (Rich Text): Der vollständige Tagebucheintrag des Nutzers

**Discord Channel ID**: `1384289197115838625`

## 🔪 MVP Definition
**MVP**: Tägliche Erinnerung um 22:00 Uhr und automatische Speicherung von Tagebucheinträgen in Notion.

**Kernfunktionen**:
1. Tägliche Erinnerung um 22:00 Uhr senden
2. Nachrichten in der Tagebuch-Channel erkennen und verarbeiten
3. Automatische Titel-Generierung aus dem Tagebucheintrag
4. Speicherung in Notion-Datenbank (Titel, Datum, Text)
5. Bestätigungsnachricht nach erfolgreichem Speichern

## 🧱 Architektur-Entscheidungen
**Komponenten**:
- **Discord Bot** (discord.py für Bot-Funktionalität)
- **Scheduler** (schedule für tägliche Erinnerungen)
- **Notion Manager** (notion-client für Datenbankzugriff)
- **Text Processor** (für Titel-Generierung)
- **Message Handler** (für Verarbeitung von Tagebucheinträgen)

## ⚙️ Tech-Stack
**Dependencies**:
- `discord.py>=2.3.0` - Discord Bot Framework
- `notion-client>=2.0.0` - Notion API Client
- `python-dotenv>=0.19.0` - Umgebungsvariablen
- `schedule>=1.2.0` - Task Scheduling
- `asyncio` - Asynchrone Programmierung
- `logging` - Logging und Debugging

## 🚀 Entwicklungsprozess
1. **Venv Setup**: Python Virtual Environment erstellen
2. **Basis Bot**: Discord Bot mit Grundfunktionalität
3. **Notion Integration**: Verbindung zur Tagebuch-Datenbank
4. **Message Processing**: Tagebucheinträge verarbeiten und speichern
5. **Scheduler**: Tägliche Erinnerung um 22:00 Uhr implementieren
6. **Testing**: Manuelle Tests und Validierung
7. **Documentation**: README und Deployment-Anweisungen

## 📝 Dateienstruktur
```
Tagebuch_bot/
├── tagebuch_bot.py (Haupt-Bot-Datei)
├── notion_manager.py (Notion API Integration)
├── text_processor.py (Titel-Generierung)
├── scheduler.py (Tägliche Erinnerungen)
├── requirements.txt (Dependencies)
├── .env.example (Umgebungsvariablen Template)
├── PLANNING.md (Diese Datei)
├── TASK.md (Aufgaben-Tracking)
├── README.md (Dokumentation)
└── tests/
    ├── test_notion_manager.py
    ├── test_text_processor.py
    └── test_tagebuch_bot.py
```

## 🔍 Detaillierte Feature-Spezifikation

### 1. Daily Reminder (scheduler.py)
- Tägliche Ausführung um 22:00 Uhr deutsche Zeit
- Personalisierte Erinnerungsnachricht
- Robuste Zeitzonenbehandlung (Europe/Berlin)
- Logging für Debugging

### 2. Message Processing (tagebuch_bot.py)
- Erkennung von Nachrichten im Tagebuch-Channel
- Filterung von Bot-Nachrichten und Befehlen
- Verarbeitung von Multi-Line Tagebucheinträgen
- Fehlerbehandlung bei ungültigen Eingaben

### 3. Notion Integration (notion_manager.py)
- Automatische Datenbankverbindung über URL
- Speicherung mit Titel, Datum und Text
- Fehlerbehandlung bei API-Problemen
- Logging aller Notion-Transaktionen

### 4. Text Processing (text_processor.py)
- Automatische Titel-Generierung aus erstem Satz
- Fallback auf Datum als Titel bei kurzen Einträgen
- Text-Bereinigung und Formatierung
- Längen-Limitierung für Titel

### 5. Discord Commands
- `!tagebuch_help` - Hilfeinformationen anzeigen
- `!tagebuch_test` - Test-Eintrag erstellen
- `!tagebuch_stats` - Statistiken anzeigen (optional)

## 🧪 Testing-Strategie
1. **Unit Tests**: Jedes Modul einzeln testen
2. **Integration Tests**: Notion API und Discord Bot testen
3. **Manual Testing**: Testeinträge mit verschiedenen Textlängen
4. **Scheduler Testing**: Überprüfung der Timer-Funktionalität

## 📊 Erwartete Ausgabe
**Tägliche Erinnerung**:
```
📔 **Tagebuch-Erinnerung** 📔
Zeit für deinen täglichen Tagebucheintrag! 
Schreibe einfach deine Gedanken des Tages hier in den Chat.

💭 Wie war dein Tag? Was hast du erlebt? Wofür bist du dankbar?
```

**Bestätigungsnachricht**:
```
✅ **Tagebucheintrag gespeichert!**
Titel: "Gedanken zum heutigen Tag"
Datum: 2024-01-15
Text: [Erste 50 Zeichen...]

Dein Eintrag wurde erfolgreich in Notion gespeichert! 📝
```

## 🔐 Umgebungsvariablen
- `DISCORD_TOKEN` - Discord Bot Token 
- `NOTION_TOKEN` - Notion Integration Token
- `TAGEBUCH_CHANNEL_ID=1384289197115838625` - Discord Channel ID
- `TAGEBUCH_DATABASE_ID` - Notion Database ID (extrahiert aus URL)

## 🕒 Zeitplan
- **Phase 1** (Tag 1): Basis Bot und Notion Integration
- **Phase 2** (Tag 2): Message Processing und Speicherung  
- **Phase 3** (Tag 3): Scheduler und tägliche Erinnerungen
- **Phase 4** (Tag 4): Testing und Fehlerbehandlung
- **Phase 5** (Tag 5): Documentation und Deployment

## 🚨 Risiken & Mitigation
- **Notion API Limits**: Rate Limiting implementieren
- **Discord Token Sicherheit**: Env-Dateien nicht committen
- **Zeitzone-Probleme**: pytz für robuste Zeitzonenbehandlung
- **Message Spam**: Cooldown und Validierung implementieren 