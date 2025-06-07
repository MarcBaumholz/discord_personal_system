# Social & Event Koordinator Bot

Ein Discord-Bot, der dir bei der Planung und Koordination von sozialen Ereignissen und dem Verwalten von wichtigen Terminen hilft.

## Überblick

Der Social & Event Koordinator Bot hilft dir mit:

- Terminplanung direkt über Discord
- Erinnerungen an Geburtstage und Jubiläen deiner Freunde und Familie
- Verwaltung von Geschenkideen für besondere Anlässe
- Planung von Events mit Teilnehmermanagement
- Integration mit deinem Kalender
- Automatischen Erinnerungen an soziale Verpflichtungen

## Was spart mir der Bot?

- **Zeit:** Keine manuelle Terminplanung und -abstimmung mehr nötig
- **Mentale Energie:** Nie wieder vergessene Geburtstage oder Jubiläen
- **Organisation:** Ein zentrales System für alle sozialen Verpflichtungen und Events
- **Kommunikation:** Automatisierte Benachrichtigungen an Teilnehmer
- **Kreativität:** Personalisierte Geschenkvorschläge für jeden Anlass

## Installation und Einrichtung

1. Stelle sicher, dass Python 3.8+ und pip installiert sind
2. Clone das Repository:
   ```
   git clone [repository-url]
   cd social_event_bot
   ```
3. Installiere die Abhängigkeiten:
   ```
   pip install -r requirements.txt
   ```
4. Erstelle eine `.env` Datei mit folgenden Variablen:
   ```
   DISCORD_TOKEN=dein_discord_bot_token
   EVENT_CHANNEL_ID=dein_discord_kanal_id
   NOTION_TOKEN=dein_notion_token
   NOTION_BIRTHDAY_DATABASE_ID=dein_notion_geburtstags_db_id
   NOTION_EVENTS_DATABASE_ID=dein_notion_events_db_id
   OPENAI_API_KEY=dein_openai_api_key
   GOOGLE_CALENDAR_CREDENTIALS=pfad_zu_deinen_google_credentials.json
   ```
5. Starte den Bot:
   ```
   python social_bot.py
   ```

## Benötigte API-Keys und Integrationen

- **Discord Bot Token:** Für die Bot-Funktionalität ([Discord Developer Portal](https://discord.com/developers/applications))
- **Notion Integration:** Zum Speichern von Geburtstagen, Events und Geschenkideen
  - Erstelle eine Notion-Datenbank für Geburtstage mit den Spalten: Name, Datum, Beziehung, Notizen, Geschenkideen
  - Erstelle eine Notion-Datenbank für Events mit den Spalten: Name, Datum, Ort, Teilnehmer, Notizen, Status
- **OpenAI API Key:** Für personalisierte Geschenkvorschläge
- **Google Calendar API:** Für die Kalendersynchronisation

## Hauptfunktionen

### Geburtstags- und Jubiläumsmanagement
- Trackt wichtige Daten von Freunden und Familie
- Sendet rechtzeitige Erinnerungen (1 Woche, 3 Tage und am Tag selbst)
- Verwaltet Geschenkideen für jede Person
- Generiert personalisierte Geschenkvorschläge mit KI

### Event-Planung
- Erstellt neue Events mit Datum, Uhrzeit und Ort
- Verwaltet Teilnehmerlisten
- Sendet Einladungen über Discord
- Sammelt RSVPs direkt über Bot-Interaktionen
- Sendet Erinnerungen vor dem Event

### Terminplanung
- Schlägt Termine basierend auf freien Zeitfenstern vor
- Koordiniert Gruppenplanung durch Abstimmungsfeature
- Synchronisiert mit Google Kalender

### Erinnerungen
- Automatisierte Erinnerungen an soziale Verpflichtungen
- Anpassbare Erinnerungszeiten
- Verschiedene Erinnerungsmodi (direkte Nachricht, Kanal-Mention, etc.)

## Discord-Befehle

- `!social help` - Zeigt die Hilfeübersicht
- `!birthday add [Name] [Datum TT.MM.YYYY]` - Fügt einen Geburtstag hinzu
- `!birthday list` - Zeigt anstehende Geburtstage
- `!gift idea [Person] [Anlass]` - Generiert Geschenkideen
- `!event create` - Startet den Event-Erstellungsdialog
- `!event list` - Zeigt anstehende Events
- `!invite [Event-ID] @User` - Lädt einen Benutzer zu einem Event ein
- `!schedule meeting` - Startet den Terminplanungsassistenten

## Datenstruktur in Notion

Der Bot verwendet zwei Notion-Datenbanken:

1. **Geburtstage/Jubiläen**
   - Name (Primärschlüssel, Text)
   - Datum (Datum)
   - Beziehung (Select: Familie/Freund/Kollege/Andere)
   - Notizen (Text)
   - Geschenkideen (Text)
   - Letztes Geschenk (Text)
   - Erinnerung (Checkbox)

2. **Events**
   - Name (Primärschlüssel, Text)
   - Datum (Datum)
   - Uhrzeit (Text)
   - Ort (Text)
   - Beschreibung (Text)
   - Teilnehmer (Relation zur Personendatenbank)
   - Status (Select: Geplant/Bestätigt/Abgeschlossen/Abgesagt)
   - Organisator (Text)
   - Erinnerung (Checkbox)

## Erweiterungsideen

- Integration mit Doodle für komplexere Terminabstimmungen
- Automatische Foto-Galerie-Erstellung nach Events
- Location-Vorschläge für Treffen basierend auf gemeinsamen Interessen
- Budget-Tracking für Events und Geschenke
- Einbindung von Wetterdaten für optimale Event-Planung
- Automatische Nachfolgekommunikation nach Events

## Abhängigkeiten

- discord.py
- python-dotenv
- notion-client
- openai
- google-auth
- google-api-python-client
- pytz
- asyncio 