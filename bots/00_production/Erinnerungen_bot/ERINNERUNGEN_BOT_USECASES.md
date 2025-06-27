# 🤖 Erinnerungen Bot - Alle Use Cases & Funktionen

## 🎯 **Bot Übersicht**
Der **Erinnerungen Bot** ist ein intelligenter Discord-Bot für automatische tägliche Erinnerungen mit drei Hauptbereichen:
- 🎂 **Geburtstags-Erinnerungen** (aus Notion-Datenbank)
- 🗑️ **Müllkalender-Erinnerungen** (für Schweigheim, Baden-Württemberg)
- 📅 **Wochenübersicht** auf Abruf

---

## 🔄 **Automatische Use Cases (Geplant)**

### 1. 🎂 **Morgendliche Geburtstags-Benachrichtigung** 
**Zeit:** Täglich um 07:00 Uhr  
**Funktion:** 
- Überprüft Notion-Datenbank nach heutigen Geburtstagen
- Sendet automatisch schöne formatierte Nachrichten
- Zeigt Name, Alter und Beziehungsinfo an
- Funktioniert ohne manuellen Eingriff

**Beispiel-Nachricht:**
```
🎉 **GEBURTSTAG HEUTE!** 🎉

🎂 **Anna Müller** wird heute 35 Jahre alt!
   👥 Kollegin
   📅 Geboren am 19.06.1988

Nicht vergessen zu gratulieren! 🎈
```

### 2. 🗑️ **Abendliche Müll-Erinnerung**
**Zeit:** Täglich um 20:00 Uhr  
**Funktion:**
- Überprüft Müllkalender für Schweigheim
- Erinnert am Vorabend, wenn morgen Müll abgeholt wird
- Unterscheidet zwischen verschiedenen Tonnenarten
- Gibt praktische Tipps zur Bereitstellung

**Beispiel-Nachricht:**
```
🗑️ **MÜLL-ERINNERUNG!** 🗑️

Morgen (Freitag, 20.06.2025) wird abgeholt:
♻️ **Gelber Sack** (gelbe Tonne)

📍 **Ort:** Schweigheim, Baden-Württemberg
⏰ **Wichtig:** Tonne bis 06:00 Uhr bereitstellen!
🚛 **Abholung:** Ca. 08:00-12:00 Uhr
```

---

## 🎮 **Manuelle Use Cases (Discord Commands)**

### 3. 📅 **Wochenübersicht abrufen** - `!remind`
**Verwendung:** `!remind` in Discord-Channel eingeben  
**Funktion:**
- Zeigt alle Geburtstage der nächsten 7 Tage
- Zeigt alle Müllabholungen der nächsten Woche
- Perfekt für Wochenplanung
- Auf Abruf verfügbar, wann immer gewünscht

**Beispiel-Output:**
```
🎂 **GEBURTSTAGE - NÄCHSTE WOCHE** 🎂

🎂 **Anna Müller** - in 3 Tagen
   👥 Kollegin | 📅 22.06.1988

🎂 **Peter Schmidt** - in 5 Tagen  
   👥 Nachbar | 📅 24.06.1992

═══════════════════════════════════════

🗑️ **MÜLL - NÄCHSTE WOCHE** 🗑️

📅 **Freitag, 20.06.2025** (morgen)
   ♻️ Gelber Sack (gelbe Tonne)

📅 **Dienstag, 24.06.2025** (in 5 Tagen)
   🗑️ Restmüll (schwarze Tonne)

📍 **Ort:** Schweigheim, Baden-Württemberg
⏰ **Erinnerung:** Tonnen bis 06:00 Uhr bereitstellen
```

### 4. 🧪 **Geburtstage testen** - `!test_geburtstage`
**Verwendung:** `!test_geburtstage` in Discord-Channel eingeben  
**Funktion:**
- Manueller Test der Geburtstags-Funktion
- Überprüft heutige Geburtstage sofort
- Perfekt für Debugging und Entwicklung
- Zeigt ob Notion-Verbindung funktioniert

### 5. 🧪 **Müllkalender testen** - `!test_muell`
**Verwendung:** `!test_muell` in Discord-Channel eingeben  
**Funktion:**
- Manueller Test der Müllkalender-Funktion
- Überprüft morgige Müllabholung sofort
- Hilfreich für Troubleshooting
- Testet API-Verbindung

---

## 🗃️ **Datenquellen & Integration**

### **Notion-Datenbank (Geburtstage)**
- **URL:** https://www.notion.so/marcbaumholz/214d42a1faf580fa8eccd0ddfd69ca98
- **Erwartete Felder:**
  - Name (Title)
  - Geburtsdatum (Date)
  - Beziehung (Select/Text) - Optional
- **Integration:** Über Notion API mit Token

### **Müllkalender (Schweigheim)**
- **Ort:** Schweigheim, Baden-Württemberg
- **Quelle:** AWRM (Abfallwirtschaft Rems-Murr)
- **Unterstützte Tonnen:**
  - 🗑️ Restmüll (schwarze Tonne)
  - ♻️ Gelber Sack (gelbe Tonne)
  - 🍂 Biotonne (braune Tonne)
  - 📄 Papier (blaue Tonne)

---

## ⏰ **Zeitplan-Übersicht**

| Zeit  | Funktion | Use Case |
|-------|----------|----------|
| 07:00 | 🎂 Geburtstags-Check | Automatische morgendliche Benachrichtigung |
| 20:00 | 🗑️ Müll-Check | Erinnerung für morgige Abholung |
| 24/7  | 🎮 Commands | `!remind`, `!test_geburtstage`, `!test_muell` |

---

## 🎯 **Nutzer-Benefits**

### **Für Privatpersonen:**
- ✅ Nie wieder Geburtstage vergessen
- ✅ Nie wieder Müllabholung verpassen
- ✅ Automatisch und zuverlässig
- ✅ Deutsche Lokalisierung
- ✅ Wochenplanung auf Knopfdruck

### **Für Familien:**
- ✅ Zentrale Erinnerungen für alle
- ✅ Praktische Müll-Tipps
- ✅ Übersichtliche Formatierung
- ✅ Integration in bestehenden Discord-Server

### **Für WGs/Mitbewohner:**
- ✅ Gemeinsame Müll-Erinnerungen
- ✅ Geteilte Geburtstags-Notifications
- ✅ Automatische Koordination

---

## 🛠️ **Technical Use Cases**

### **Entwickler/Admin:**
- ✅ Umfangreiche Logging-Funktionen
- ✅ Test-Commands für Debugging
- ✅ Modulare Architektur
- ✅ Environment-basierte Konfiguration
- ✅ Graceful Error Handling

### **Monitoring:**
- ✅ Log-Dateien für alle Aktivitäten
- ✅ Console-Output für Live-Monitoring
- ✅ Connection-Tests für APIs
- ✅ Error-Tracking und Recovery

---

## 🚀 **Deployment Use Cases**

### **Lokaler Server (Raspberry Pi):**
- ✅ 24/7 Betrieb möglich
- ✅ Niedrige Kosten
- ✅ Volle Kontrolle über Daten
- ✅ Virtual Environment isoliert

### **Cloud Deployment:**
- ✅ Docker-ready (Container verfügbar)
- ✅ Scalierbar für mehrere Server
- ✅ Automatische Restarts
- ✅ Environment Variables Support

---

## 🔮 **Zukünftige Use Cases (Roadmap)**

### **Geplante Erweiterungen:**
- 📅 **Termine-Integration** (Google Calendar, Outlook)
- 💌 **Personalisierte Nachrichten** (verschiedene Grüße je Person)
- 🌐 **Web-Dashboard** (grafische Verwaltung)
- 📊 **Statistiken** (verpasste vs. rechtzeitige Erinnerungen)
- 🔔 **Mobile Push-Notifications** (zusätzlich zu Discord)
- 🏠 **Smart Home Integration** (Alexa, Google Home)

### **Erweiterte Müllkalender-Features:**
- 🗺️ **Multi-City Support** (andere Städte in Baden-Württemberg)
- 📱 **iCal Export** (für persönliche Kalender)
- 🚛 **Live-Tracking** (GPS-basierte Abholzeiten)
- ♻️ **Recycling-Tipps** (was gehört in welche Tonne)

---

## 💡 **Use Case Zusammenfassung**

Der **Erinnerungen Bot** deckt folgende Haupt-Use-Cases ab:

1. **🔄 Automatisch:** Tägliche Geburtstags- und Müll-Erinnerungen
2. **📅 Auf Abruf:** Wochenübersicht mit `!remind` Command
3. **🧪 Testing:** Manual Commands für Entwicklung/Debugging
4. **🏠 Lokal:** Perfekt für Familie/WG in Schweigheim
5. **🔧 Wartung:** Umfangreiche Logging- und Monitoring-Features

**Der Bot ist komplett funktional und produktionsbereit!** 🚀 