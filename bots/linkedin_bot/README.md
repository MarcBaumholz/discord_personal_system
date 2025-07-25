# LinkedIn Network Analyzer Bot

Ein intelligenter Discord Bot, der dein LinkedIn-Netzwerk analysiert, Kontakte nach Themenfeldern kategorisiert, nach Followern rankt und die Top 10 pro Kategorie in einer Notion-Datenbank speichert.

## 🎯 Features

- **LinkedIn Datenimport**: Import von LinkedIn-Verbindungen über CSV-Export
- **KI-gestützte Analyse**: Automatische Kategorisierung und Bewertung der Kontakte
- **Themenfeld-Klassifikation**: 15 verschiedene Branchen-Kategorien
- **Follower-Schätzung**: KI-basierte Einschätzung der Follower-Anzahl
- **Notion Integration**: Automatische Speicherung in strukturierter Datenbank
- **Top 10 Ranking**: Identifikation der wertvollsten Kontakte pro Kategorie
- **Discord Interface**: Einfache Bedienung über Discord-Commands

## 📊 Notion Database Struktur

Der Bot erstellt/nutzt eine Notion-Datenbank mit folgenden Eigenschaften:

| Eigenschaft | Typ | Beschreibung |
|-------------|-----|--------------|
| Name | Title | Vollständiger Name des Kontakts |
| Position | Rich Text | Aktuelle Position/Jobtitel |
| Company | Rich Text | Aktuelles Unternehmen |
| Profile URL | URL | LinkedIn-Profil Link |
| Email | Email | E-Mail-Adresse |
| Follower Count | Number | Geschätzte Anzahl der Follower |
| Topic Category | Select | Themenfeld/Branche (15 Kategorien) |
| Importance Score | Number | Wichtigkeitsbewertung (1-10) |
| Last Interaction | Date | Letzter Kontakt |
| Notes | Rich Text | KI-generierte Notizen |
| Top 10 Flag | Checkbox | Markierung für Top 10 pro Kategorie |
| Created Date | Created Time | Erstellungsdatum |
| Last Updated | Last Edited Time | Letzte Aktualisierung |

## 🏷️ Themenfeld-Kategorien

1. **Artificial Intelligence & Machine Learning**
2. **Software Development & Engineering**
3. **Data Science & Analytics**
4. **Product Management**
5. **Digital Marketing & Growth**
6. **Finance & Investment**
7. **Entrepreneurship & Startups**
8. **Consulting & Strategy**
9. **Sales & Business Development**
10. **Human Resources & Recruiting**
11. **Design & UX/UI**
12. **Content Creation & Media**
13. **Healthcare & Life Sciences**
14. **Education & Training**
15. **Other**

## 🚀 Setup & Installation

### 1. Environment Setup
```bash
# Kopiere die Environment-Vorlage
cp env_example.txt .env

# Bearbeite die .env Datei mit deinen Credentials
nano .env
```

### 2. Discord Bot Setup
1. Gehe zu [Discord Developer Portal](https://discord.com/developers/applications)
2. Erstelle eine neue Application
3. Füge einen Bot hinzu und kopiere den Token
4. Lade den Bot mit folgenden Berechtigungen ein:
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History

### 3. Notion Integration Setup
1. Gehe zu [Notion Integrations](https://www.notion.so/my-integrations)
2. Erstelle eine neue Integration
3. Kopiere den Internal Integration Token
4. Erstelle eine neue Seite für die Datenbank
5. Teile die Seite mit deiner Integration

### 4. OpenRouter API Setup
1. Registriere dich bei [OpenRouter](https://openrouter.ai)
2. Erstelle einen API-Key (kostenloser Tier verfügbar)
3. Füge den Key zur .env Datei hinzu

### 5. LinkedIn Daten Export
1. Gehe zu LinkedIn → Einstellungen & Datenschutz
2. Datenschutz → Kopie deiner Daten anfordern
3. Wähle "Verbindungen" aus und lade die CSV herunter

## 🎮 Bot Commands

### `!linkedin_help`
Zeigt alle verfügbaren Commands und Kategorien an.

### `!upload_linkedin`
Zeigt Anweisungen zum Export und Upload der LinkedIn-Daten.

### `!analyze_network <csv_path>`
Analysiert das LinkedIn-Netzwerk aus der CSV-Datei:
- Parst die LinkedIn-Verbindungen
- Führt KI-Analyse für jeden Kontakt durch
- Kategorisiert nach Themenfeldern
- Bewertet Wichtigkeit und schätzt Follower
- Speichert alles in Notion

Beispiel:
```
!analyze_network /path/to/linkedin_connections.csv
```

### `!top_contacts [category]`
Zeigt die Top-Kontakte an, optional gefiltert nach Kategorie:

```bash
# Alle Top-Kontakte anzeigen
!top_contacts

# Top-Kontakte in einer spezifischen Kategorie
!top_contacts "Artificial Intelligence & Machine Learning"
```

## 🔍 KI-Analyse Funktionen

Der Bot nutzt OpenAI/Claude für:

1. **Follower-Schätzung**: Realistische Einschätzung basierend auf Position und Unternehmen
2. **Themenfeld-Klassifikation**: Automatische Zuordnung zu einer der 15 Kategorien
3. **Wichtigkeits-Score**: Bewertung von 1-10 basierend auf Einfluss und Netzwerk
4. **Notizen-Generierung**: Kurze Notizen über den Wert der Verbindung

## 📈 Ranking-System

Kontakte werden ranked nach:
1. **Importance Score** (Primär): KI-bewerteter Einfluss und Wert
2. **Follower Count** (Sekundär): Geschätzte Reichweite

Die Top 10 pro Kategorie werden automatisch in Notion markiert.

## 🛠️ Technische Details

### API-Beschränkungen
- **LinkedIn API**: Aufgrund der restriktiven LinkedIn API wird CSV-Import genutzt
- **Rate Limiting**: 1 Sekunde Pause zwischen KI-Analysen
- **Batch Processing**: Fortschrittsanzeige bei großen Netzwerken

### Fehlerbehandlung
- Validierung der CSV-Struktur
- Fallback-Werte bei KI-Analyse-Fehlern
- Detaillierte Error-Messages in Discord

### Datenformat
Unterstützte CSV-Formate:
- LinkedIn Connections Export (Standard)
- Manuell erstellte CSV mit Spalten: Name, Position, Company, Email

## 🔧 Erweiterte Konfiguration

### Custom Categories
Passe die `TOPIC_CATEGORIES` Liste im Code an, um eigene Kategorien hinzuzufügen.

### AI Model Wechsel
Ändere das `model` Parameter in der `analyze_contact_with_ai` Funktion:
```python
model="anthropic/claude-3.5-haiku"  # Günstig und schnell
model="openai/gpt-4o-mini"          # Hohe Qualität
```

### Notion Database Schema
Das Database-Schema kann in der `create_contacts_database` Funktion angepasst werden.

## 🚨 Wichtige Hinweise

1. **Datenschutz**: Beachte die Datenschutzrichtlinien beim Umgang mit LinkedIn-Daten
2. **LinkedIn ToS**: Verwende nur offizielle Export-Funktionen
3. **API Costs**: OpenRouter-Calls können Kosten verursachen (aber sehr günstig)
4. **Backup**: Sichere deine Notion-Datenbank regelmäßig

## 📝 Workflow Beispiel

1. **Export**: LinkedIn-Verbindungen als CSV exportieren
2. **Upload**: CSV-Datei auf den Server uploaden
3. **Analyze**: `!analyze_network` Command ausführen
4. **Review**: Results in Discord anschauen
5. **Notion**: Top-Kontakte in Notion-Datenbank verwalten
6. **Action**: Gezielte Outreach-Kampagnen starten

## 🎯 Use Cases

- **Networking Strategy**: Identifikation wichtiger Kontakte pro Branche
- **Content Distribution**: Finde Influencer für spezifische Themen
- **Business Development**: Prioritisierung von Sales-Kontakten
- **Knowledge Sharing**: Verbindung zu Experten in bestimmten Bereichen
- **Career Development**: Aufbau strategischer Beziehungen

## 🔄 Regelmäßige Updates

Führe die Analyse regelmäßig durch, um:
- Neue Verbindungen zu erfassen
- Importance Scores zu aktualisieren
- Kategorie-Zuordnungen zu verfeinern
- Interaction-Daten zu pflegen
