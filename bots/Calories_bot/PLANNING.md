# 🍽️ Calories Bot - Monthly Tracking Feature Plan

## 🎯 Ziel (Goal)
Erstelle eine monatliche Kalorienverfolgung-Funktionalität, die am 1. eines jeden Monats automatisch ausgeführt wird, um die Kalorienaufnahme pro Nutzer zu analysieren und als visualisiertes Diagramm über Discord zu versenden.

## 👤 User Stories
- Als Nutzer möchte ich eine monatliche Zusammenfassung meiner Kalorienaufnahme erhalten, damit ich meine Ernährungsgewohnheiten verstehe
- Als Nutzer möchte ich ein visuelles Diagramm meiner täglichen Kalorienaufnahme sehen, damit ich Trends erkennen kann
- Als Nutzer möchte ich diese Berichte automatisch erhalten, ohne sie manuell anfordern zu müssen

## 📦 Datenmodell
**Existierende Notion Database**: `FOODIATE_DB_ID = 20ed42a1faf5807497c2f350ff84ea8d`

**Eigenschaften der Datenbank**:
- **Food** (Title): Identifizierter Nahrungsname
- **Calories** (Text): Geschätzte Kalorien mit "kcal" Einheit
- **date** (Date): Datum der Analyse
- **person** (Select): Einzelauswahl mit verfügbaren Namen (z.B. "Marc", "Nick") 
- **confidence** (Number): Vertrauenswert der Analyse (0-100)
- **Picture** (Files): Das hochgeladene Lebensmittelbild

## 🔪 MVP Definition
**MVP**: Monatlicher Bericht mit täglicher Kalorienaufnahme pro Nutzer, visualisiert als Diagramm und via Discord versandt.

**Kernfunktionen**:
1. Datenextraktion aus Notion DB gefiltert nach Nutzer und Monat
2. Tägliche Kaloriensummen berechnen
3. Diagramm erstellen (matplotlib)
4. Discord-Nachricht mit Statistiken und Diagramm senden
5. Automatische monatliche Ausführung (Cron/Scheduler)

## 🧱 Architektur-Entscheidungen
**Komponenten**:
- **Monthly Report Generator** (Python-Modul)
- **Chart Creator** (matplotlib für Visualisierung)
- **Discord Notifier** (für das Senden der Berichte)
- **Scheduler** (für die monatliche Ausführung)
- **Database Reader** (für Notion API-Zugriff)

## ⚙️ Tech-Stack
**Neue Dependencies**:
- `matplotlib>=3.7.0` - Für Diagrammerstellung
- `pandas>=2.0.0` - Für Datenverarbeitung und -analyse
- `schedule>=1.2.0` - Für die Zeitplanung der monatlichen Berichte

**Bestehender Stack**:
- Discord.py - Discord-Integration
- Notion-client - Datenbankzugriff
- Python-dotenv - Umgebungsvariablen

## 🚀 Entwicklungsprozess
1. **Initialisierung**: Neue Abhängigkeiten installieren
2. **Datenmodell**: Notion DB-Reader implementieren
3. **Chart Creator**: Matplotlib-basierte Diagrammerstellung
4. **Discord Integration**: Nachrichten mit Diagrammen senden
5. **Scheduler**: Monatliche Ausführung am 1. jeden Monats
6. **Testing**: Manuelle Tests und Validierung
7. **Deployment**: Integration in bestehende Bot-Struktur

## 📝 Dateienstruktur
```
Calories_bot/
├── calories_bot.py (bestehend)
├── monthly_report.py (NEU - Hauptmodul)
├── chart_generator.py (NEU - Diagrammerstellung)
├── notion_data_reader.py (NEU - Datenextraktion)
├── scheduler.py (NEU - Zeitplanung)
├── requirements.txt (erweitert)
└── README.md (aktualisiert)
```

## 🔍 Detaillierte Feature-Spezifikation

### 1. Datenextraktion (notion_data_reader.py)
- Abruf aller Einträge aus dem aktuellen/vorherigen Monat
- Filterung nach Benutzer (person-Eigenschaft)
- Extraktion von Datum, Kalorien und Nutzer
- Datenbereinigung und -validierung

### 2. Datenverarbeitung (monthly_report.py)
- Gruppierung der Daten nach Nutzer und Tag
- Berechnung täglicher Kaloriensummen
- Statistische Auswertung (Durchschnitt, Min, Max)
- Trendanalyse

### 3. Visualisierung (chart_generator.py)
- Liniendiagramm für tägliche Kalorienaufnahme
- Balkendiagramm für Wochensummen
- Anpassbare Farben und Stil
- Export als PNG für Discord

### 4. Discord-Integration (monthly_report.py)
- Embed mit Monatsstatistiken
- Diagramm als Anhang
- Personalisierte Nachrichten pro Nutzer
- Fehlerbehandlung

### 5. Scheduler (scheduler.py)
- Ausführung am 1. jeden Monats um 09:00 Uhr
- Robuste Zeitzonenbehandlung
- Logging und Fehlerbehandlung
- Manuelle Auslösung für Tests

## 🧪 Testing-Strategie
1. **Unit Tests**: Jedes Modul einzeln testen
2. **Integration Tests**: Ende-zu-Ende-Tests mit Test-Datenbank
3. **Manual Testing**: Testlauf mit realen Daten
4. **Discord Testing**: Überprüfung der Nachrichtenformatierung

## 📊 Erwartete Ausgabe
**Discord-Nachricht pro Nutzer**:
- Persönliche Begrüßung
- Monatsstatistiken (Gesamt, Durchschnitt, Min/Max)
- Angehängtes Diagramm (PNG)
- Motivierende Nachricht oder Tipps

**Diagramm-Features**:
- X-Achse: Tage des Monats
- Y-Achse: Kalorien
- Linie: Tägliche Aufnahme
- Horizontale Linie: Monatsdurchschnitt
- Titel und Labels in Deutsch 