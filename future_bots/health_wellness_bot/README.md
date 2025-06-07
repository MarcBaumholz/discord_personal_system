# Health & Wellness Bot

Ein Discord-Bot, der deine Gesundheit und Wohlbefinden überwacht und optimiert, indem er verschiedene Tracking-Funktionen und Erinnerungen bietet.

## Überblick

Der Health & Wellness Bot hilft dir, gesunde Gewohnheiten zu entwickeln und aufrechtzuerhalten, indem er:

- Deinen Wasserkonsum trackt und dich an regelmäßiges Trinken erinnert
- Schlafgewohnheiten analysiert und personalisierte Schlafenszeiten empfiehlt
- Geführte Meditations- und Achtsamkeitsübungen anbietet
- Stimmung und mentales Wohlbefinden verfolgt
- An Medikamente und Vitamine erinnert
- Mit Gesundheits-Apps wie Apple Health oder Google Fit integrierbar ist

## Was spart mir der Bot?

- **Zeit:** Keine manuelle Eingabe in verschiedene Gesundheits-Apps nötig
- **Mentale Energie:** Keine Notwendigkeit, an Wasser, Medikamente oder andere Gesundheitsroutinen zu denken
- **Analyse-Aufwand:** Automatische Auswertung deiner Gesundheitsdaten und personalisierte Empfehlungen
- **Motivation:** Regelmäßige Erinnerungen und Fortschrittstracking halten dich motiviert
- **Organisation:** Ein zentrales System für alle gesundheitsbezogenen Daten und Erinnerungen

## Installation und Einrichtung

1. Stelle sicher, dass Python 3.8+ und pip installiert sind
2. Clone das Repository:
   ```
   git clone [repository-url]
   cd health_wellness_bot
   ```
3. Installiere die Abhängigkeiten:
   ```
   pip install -r requirements.txt
   ```
4. Erstelle eine `.env` Datei mit folgenden Variablen:
   ```
   DISCORD_TOKEN=dein_discord_bot_token
   CHANNEL_ID=dein_discord_kanal_id
   OPENAI_API_KEY=dein_openai_api_key
   NOTION_TOKEN=dein_notion_token
   NOTION_HEALTH_DATABASE_ID=dein_notion_database_id
   WEATHER_API_KEY=dein_weather_api_key
   ```
5. Starte den Bot:
   ```
   python health_bot.py
   ```

## Benötigte API-Keys und Integrationen

- **Discord Bot Token:** Für die Bot-Funktionalität ([Discord Developer Portal](https://discord.com/developers/applications))
- **OpenAI API Key:** Für personalisierte Gesundheitsempfehlungen und Analysen
- **Notion Integration:** Zum Speichern und Verfolgen von Gesundheitsdaten
  - Erstelle eine Notion-Datenbank mit den Spalten: Datum, Wasserkonsum, Schlafzeit, Stimmung, Medikamente, Notizen
- **Weather API Key (OpenWeatherMap):** Für wetterbasierte Aktivitätsempfehlungen

## Hauptfunktionen

### Wasser-Tracking
- Sendet alle 90 Minuten Erinnerungen zum Trinken
- Trackt deinen täglichen Wasserkonsum
- Visualisiert tägliche und wöchentliche Trends
- Passt Empfehlungen basierend auf Gewicht, Aktivitätsniveau und Wetter an

### Schlafanalyse
- Verfolgt deine Schlafenszeiten und -dauer
- Analysiert Qualitätsmuster
- Gibt personalisierte Empfehlungen für optimale Schlafzeiten
- Sendet Erinnerungen für konsistente Schlafenszeiten

### Meditation und Achtsamkeit
- Bietet geführte Meditationen unterschiedlicher Länge
- Timer-Funktionalität für eigene Meditationen
- Tägliche Achtsamkeitstipps und -übungen
- Fortschrittsverfolgung deiner Meditationspraxis

### Stimmungstracking
- Tägliche Check-ins für mentales Wohlbefinden
- Visualisierung von Stimmungstrends
- KI-basierte Anregungen zur Stimmungsverbesserung
- Erkennung von Mustern zwischen Aktivitäten und Stimmung

### Medikamenten-Erinnerungen
- Zeitplanbasierte Erinnerungen für Medikamente und Nahrungsergänzungsmittel
- Tracking von Einnahmen und verpassten Dosen
- Benachrichtigungen für Nachbestellungen

## Discord-Befehle

- `!health help` - Zeigt die Hilfeübersicht
- `!water [Menge in ml]` - Trackt Wasserkonsum
- `!sleep [Stunden]` - Trackt Schlafstunden
- `!mood [1-10]` - Trackt Stimmung auf einer Skala von 1-10
- `!meditate [Minuten]` - Startet einen Meditationstimer
- `!med track [Medikament]` - Trackt Medikamenteneinnahme
- `!med remind [Medikament] [Zeit]` - Setzt eine Erinnerung
- `!health report [daily/weekly/monthly]` - Zeigt Gesundheitsberichte

## Datenstruktur in Notion

Der Bot verwendet eine Notion-Datenbank zur Datenspeicherung mit folgendem Schema:

1. **Tägliche Einträge**
   - Datum (Primärschlüssel)
   - Wasserkonsum (Nummer, ml)
   - Schlafstunden (Nummer)
   - Stimmungswert (Nummer, 1-10)
   - Achtsamkeitsminuten (Nummer)
   - Aktivitätslevel (Select: Niedrig/Mittel/Hoch)
   - Medikamente (Multiselect)
   - Notizen (Text)

2. **Medikamenten-Tracking**
   - Name (Primärschlüssel)
   - Dosierung (Text)
   - Zeitplan (Text)
   - Bestand (Nummer)
   - Nachbestellung nötig (Checkbox)

## Erweiterungsideen

- Integration mit Fitness-Trackern (Fitbit, Garmin)
- Ernährungstracking und Mahlzeitenplanung
- Aktivitätsempfehlungen basierend auf Wetterdaten
- Integration mit Apple Health/Google Fit
- Erweiterte Analysen mit Korrelationen zwischen verschiedenen Gesundheitsfaktoren
- Gruppenherausforderungen für Freunde/Familie
- KI-generierte personalisierte Fitness- und Wellness-Pläne

## Abhängigkeiten

- discord.py
- python-dotenv
- requests
- matplotlib
- pandas
- notion-client
- openai
- schedule 