# 🏥 Health Bot

Ein automatisierter Discord Bot, der täglich Ihre Oura Ring Gesundheitsdaten abruft, analysiert und personalisierte Gesundheitsberichte mit Tipps in einen Discord-Kanal sendet.

## 🎯 Features

- **Oura Ring Integration**: Automatischer Abruf von täglichen Aktivitätsdaten (Kalorien, Schritte, aktive Kalorien)
- **Intelligente Analyse**: Bewertung des Gesundheitsstatus basierend auf personalisierten Zielen
- **Personalisierte Tipps**: 2-3 maßgeschneiderte Empfehlungen basierend auf Ihrer Leistung
- **Discord Integration**: Schöne, formatierte Berichte als Rich Embeds
- **Automatisierung**: Tägliche Berichte um 8:00 Uhr (konfigurierbar)
- **Startup-Benachrichtigung**: Informative Startnachricht erklärt Bot-Funktionen und Ziele
- **Fehlerbehandlung**: Robuste API-Fehlerbehandlung und Wiederherstellung

## 📊 Gesundheitsstatus-Levels

- **🟢 Excellent** (90-100%): Überdurchschnittliche Leistung bei Kalorien und Aktivität
- **🟡 Good** (70-89%): Gute Leistung, nah an den Zielen
- **🟠 Average** (50-69%): Durchschnittliche Leistung mit Verbesserungspotential
- **🔴 Needs Improvement** (<50%): Niedrige Aktivität, Fokus auf mehr Bewegung

## 🚀 Installation & Setup

### 1. Umgebung vorbereiten

```bash
# Repository klonen oder zu health_bot Verzeichnis navigieren
cd discord/bots/health_bot

# Virtuelle Umgebung erstellen
python3 -m venv health_env

# Umgebung aktivieren
source health_env/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

### 2. Umgebungsvariablen konfigurieren

Kopieren Sie `env.example` zu `.env` und füllen Sie Ihre Daten ein:

```bash
cp env.example .env
```

Bearbeiten Sie `.env`:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
HEALTH_CHANNEL_ID=1384293986251964527

# Oura API Configuration  
OURA_ACCESS_TOKEN=your_oura_access_token_here

# Health Bot Settings (optional - Standard-Werte werden verwendet)
DAILY_SCHEDULE_TIME=08:00
TARGET_CALORIES=2200
TARGET_ACTIVE_CALORIES=450
TARGET_STEPS=8000
```

### 3. Discord Bot Setup

1. Gehen Sie zu [Discord Developer Portal](https://discord.com/developers/applications)
2. Erstellen Sie eine neue Application
3. Erstellen Sie einen Bot und kopieren Sie den Token
4. Fügen Sie den Bot zu Ihrem Server hinzu mit den Berechtigungen:
   - `Send Messages`
   - `Use Slash Commands`
   - `Embed Links`

### 4. Oura API Access Token

1. Gehen Sie zu [Oura Cloud](https://cloud.ouraring.com/)
2. Navigieren Sie zu "Personal Access Tokens"
3. Erstellen Sie einen neuen Token
4. Kopieren Sie den Token in Ihre `.env` Datei

## 🏃 Bot starten

```bash
# Umgebung aktivieren (falls noch nicht aktiv)
source health_env/bin/activate

# Bot starten
python health_bot.py
```

## 📝 Bot-Befehle

Alle Befehle können nur im konfigurierten Gesundheits-Kanal verwendet werden:

- `!health test` - Manuell einen Gesundheitsbericht generieren
- `!health status` - Bot-Status und Konfiguration anzeigen

## 🚀 Startup-Benachrichtigung

Wenn der Health Bot startet, sendet er automatisch eine informative Nachricht in den Gesundheits-Kanal, die folgende Informationen enthält:

- **🔄 Automatische Berichte**: Zeitplan für tägliche Berichte
- **📊 Überwachte Daten**: Welche Gesundheitsdaten analysiert werden
- **🎯 Deine Ziele**: Personalisierte Zielwerte für Kalorien und Schritte
- **💬 Befehle**: Verfügbare Bot-Befehle und Keywords
- **🤖 Bot Status**: Aktueller Verbindungsstatus und Konfiguration

Diese Startup-Nachricht hilft Benutzern zu verstehen, was der Bot macht und wie sie ihn verwenden können.

## 🧪 Tests ausführen

```bash
# Umgebung aktivieren
source health_env/bin/activate

# Tests ausführen
python -m pytest tests/ -v
```

## 📁 Projektstruktur

```
health_bot/
├── health_bot.py          # Hauptbot mit Discord Integration
├── oura_client.py         # Oura API Client
├── health_analyzer.py     # Gesundheitsanalyse-Logic
├── config.py             # Konfigurationsmanagement
├── requirements.txt      # Python Dependencies
├── env.example          # Umgebungsvariablen-Template
├── README.md            # Diese Datei
├── PLANNING.md          # Projekt-Planung
├── TASK.md             # Task-Management
└── tests/              # Unit Tests
    ├── test_oura_client.py
    └── test_health_analyzer.py
```

## 🎯 Konfiguration

### Zielwerte anpassen

Die Standard-Zielwerte können in der `.env` Datei angepasst werden:

- `TARGET_CALORIES`: Tägliche Gesamtkalorien (Standard: 2200)
- `TARGET_ACTIVE_CALORIES`: Aktive Kalorien (Standard: 450)
- `TARGET_STEPS`: Tägliche Schritte (Standard: 8000)

### Zeitplan ändern

Der Bot sendet standardmäßig um 8:00 Uhr einen Bericht. Dies kann über `DAILY_SCHEDULE_TIME` geändert werden (Format: HH:MM).

## 🔧 Troubleshooting

### Bot startet nicht
- Überprüfen Sie alle Umgebungsvariablen in `.env`
- Stellen Sie sicher, dass der Discord Token gültig ist
- Überprüfen Sie, ob der Bot die richtigen Berechtigungen hat

### Keine Oura-Daten
- Überprüfen Sie den Oura Access Token
- Stellen Sie sicher, dass Ihr Oura Ring Daten für gestern hat
- Überprüfen Sie die API-Logs für Fehlermeldungen

### Discord-Nachrichten werden nicht gesendet
- Überprüfen Sie die Channel-ID
- Stellen Sie sicher, dass der Bot Zugriff auf den Kanal hat
- Überprüfen Sie die Bot-Berechtigungen

## 🔮 Zukünftige Erweiterungen

- **Datenpeicherung**: Historische Gesundheitsdaten speichern
- **Wöchentliche Berichte**: Wöchentliche Zusammenfassungen
- **Ziel-Anpassung**: Dynamische Zielanpassung basierend auf Leistung
- **Multi-User**: Unterstützung mehrerer Benutzer

## 📄 Lizenz

Dieses Projekt ist für persönlichen Gebrauch bestimmt. Bitte respektieren Sie die Terms of Service von Oura und Discord.

## 🤝 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Logs für Fehlermeldungen
2. Stellen Sie sicher, dass alle Tests erfolgreich sind
3. Überprüfen Sie Ihre Konfiguration

---

**Powered by Oura Ring API & Discord.py** 🏃‍♂️💪 