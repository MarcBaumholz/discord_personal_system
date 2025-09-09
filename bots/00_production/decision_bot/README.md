# 🧠 Decision Bot

Ein Discord Bot, der Entscheidungsfragen anhand persönlicher Werte, Ziele und Erfahrungen analysiert und personalisierte Empfehlungen gibt.

## 🎯 Zweck

Der Decision Bot hilft dir bei wichtigen Lebensentscheidungen, indem er:
- Deine Fragen gegen deine persönlichen Werte analysiert
- Prüft, ob Entscheidungen zu deinen Zielen passen
- Detaillierte, umsetzbare Empfehlungen gibt
- Reflexionsfragen für tieferes Nachdenken stellt
- Risiken und Nutzen bewertet

## 🚀 Quick Start

### 1. Umgebung einrichten
```bash
# Virtuelle Umgebung erstellen
python -m venv decision_env
source decision_env/bin/activate  # Linux/Mac
# oder
decision_env\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt
```

### 2. Environment Variablen
Erstelle eine `.env` Datei im Parent-Verzeichnis (`discord/.env`):
```
DISCORD_TOKEN=dein_discord_token
OPENROUTER_API_KEY=dein_openrouter_key
```

### 3. CSV-Daten hochladen
Lade deine persönlichen Daten in den `upload/` Ordner:

**values.csv** - Deine Werte und Prinzipien:
```csv
Category,Description,Importance
Value,Familie an erster Stelle,Hoch
Value,Authentizität leben,Hoch
Value,Kontinuierliches Lernen,Mittel
```

**goals.csv** - Deine Ziele:
```csv
Category,Description,Timeframe
Goal,Gesund und fit bleiben,Langfristig
Goal,Neues Hobby lernen,Kurzfristig
Goal,Karriere vorantreiben,Mittelfristig
```

**identity.csv** - Deine Persönlichkeit:
```csv
Category,Description,Strength
Trait,Introvertiert,Hoch
Trait,Analytisch,Hoch
Trait,Empathisch,Mittel
```

**experiences.csv** - Wichtige Erfahrungen:
```csv
Category,Description,Lesson
Experience,Job-Wechsel vor 2 Jahren,Work-Life-Balance ist wichtig
Experience,Umzug nach Stuttgart,Flexibilität zahlt sich aus
```

### 4. Bot starten
```bash
python decision_bot.py
```

## 💬 Verwendung

### Grundlegende Nutzung
Stelle einfach eine Frage im designierten Discord-Channel (1384282192171110412):

**Beispiel-Fragen:**
- "Soll ich den neuen Job annehmen?"
- "Ist es richtig, dass ich umziehe?"
- "Soll ich mehr Zeit für meine Hobbys einplanen?"
- "Soll ich dieses Wochenende arbeiten oder entspannen?"

### Bot-Befehle
- `!status` - Zeigt aktuellen Datenstatus
- `!reload` - Lädt CSV-Daten neu
- `!help` - Zeigt Hilfe-Information

## 📊 Antwort-Format

Der Bot gibt strukturierte Antworten mit:

🎯 **ALIGNMENT-ANALYSE**
- Bewertung der Übereinstimmung mit Werten (1-10)
- Bewertung der Übereinstimmung mit Zielen (1-10)
- Bewertung der Übereinstimmung mit Identität (1-10)

🧠 **DETAILLIERTE BEGRÜNDUNG**
- Aspekte, die zu deinen Werten passen
- Unterstützung deiner Ziele
- Widersprüche zu Werten/Zielen

⚡ **HANDLUNGSEMPFEHLUNGEN**
- 3-5 konkrete, umsetzbare Schritte
- Prioritäten für die Entscheidung

💭 **REFLEXIONS-FRAGEN**
- Tiefere Fragen zum Nachdenken

⚠️ **RISIKO-NUTZEN-BEWERTUNG**
- Positive Auswirkungen
- Mögliche Herausforderungen

## 🔧 Technische Details

### Architektur
- **decision_bot.py** - Haupt-Bot mit Discord-Integration
- **csv_data_loader.py** - CSV-Datei-Verarbeitung
- **openrouter_service.py** - LLM-API-Integration (DeepSeek)
- **decision_analyzer.py** - Kern-Analyse-Logik

### CSV-Daten-Struktur
- **values.csv** - Persönliche Werte und Prinzipien
- **goals.csv** - Ziele und Aspirationen
- **identity.csv** - Persönlichkeitsmerkmale
- **experiences.csv** - Wichtige Lebenserfahrungen

### Unterstützte CSV-Formate
Der Bot erkennt automatisch Spalten mit Keywords:
- Werte: `value`, `wert`, `principle`
- Ziele: `goal`, `ziel`, `objective`, `target`
- Identität: `identity`, `self`, `personality`, `trait`
- Erfahrungen: `experience`, `lesson`, `learning`, `story`

## 🛠️ Entwicklung

### Testing
```bash
# CSV-Loader testen
python -c "from csv_data_loader import CSVDataLoader; loader = CSVDataLoader(); print(loader.load_all_data())"

# OpenRouter-Service testen (benötigt API-Key)
python -c "from openrouter_service import OpenRouterService; service = OpenRouterService()"
```

### Logging
Logs werden in der Konsole ausgegeben mit verschiedenen Levels:
- INFO: Normale Operationen
- WARNING: Potenzielle Probleme
- ERROR: Fehler, die Aufmerksamkeit benötigen

### Error Handling
Der Bot behandelt gracefully:
- Fehlende CSV-Dateien
- Malformed CSV-Daten
- OpenRouter API-Fehler
- Discord-Verbindungsprobleme

## 🔒 Datenschutz

- CSV-Dateien werden nur lokal gespeichert
- Keine persönlichen Daten in Logs
- API-Keys sicher über Environment-Variablen
- Daten werden nur für Analyse verwendet, nicht dauerhaft gespeichert

## ⚡ Performance

- Asynchrone API-Calls für schnelle Antworten
- CSV-Daten werden beim Start geladen und im Memory gehalten
- Lange Antworten werden automatisch aufgeteilt für Discord

## 🐛 Troubleshooting

**Bot reagiert nicht:**
- Prüfe, ob DISCORD_TOKEN korrekt ist
- Stelle sicher, dass der Bot im richtigen Channel schreibt (1384282192171110412)

**Keine Daten gefunden:**
- Prüfe, ob CSV-Dateien im `upload/` Ordner sind
- Verwende `!reload` um Daten neu zu laden
- Prüfe CSV-Format mit `!status`

**OpenRouter-Fehler:**
- Prüfe OPENROUTER_API_KEY in .env
- Stelle sicher, dass du Guthaben hast

## 📝 Changelog

### v1.0.0
- ✅ Grundlegende Discord-Bot-Funktionalität
- ✅ CSV-Datenverarbeitung mit automatischer Kategorisierung
- ✅ OpenRouter-Integration mit DeepSeek-Modell
- ✅ Strukturierte Entscheidungsanalyse
- ✅ Deutsche Antworten mit Emojis und Formatierung
- ✅ Error Handling und Logging
- ✅ Status-, Reload- und Help-Befehle

## ✅ Current Status (September 2025)

**🟡 BOT READY FOR DEPLOYMENT**

The Decision Bot is fully developed and ready to run, but not currently deployed in Docker.

### Development Status
- **Code**: ✅ Complete and tested
- **Docker**: ❌ Not currently containerized
- **Deployment**: 🟡 Ready for manual startup
- **Last Update**: September 2025

### Features Ready
- ✅ **CSV Data Processing**: Automatic categorization of values, goals, identity, experiences
- ✅ **OpenRouter Integration**: DeepSeek model for decision analysis
- ✅ **Structured Analysis**: Alignment analysis, recommendations, reflection questions
- ✅ **German Language Support**: Native German responses with emojis
- ✅ **Error Handling**: Graceful handling of missing data and API errors
- ✅ **Discord Integration**: Full Discord bot functionality

### To Deploy
1. Set up environment variables in `.env`
2. Upload CSV data files to `upload/` directory
3. Run: `python decision_bot.py`
4. Consider Docker containerization for production use 