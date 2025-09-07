# 🐳 Discord Bot Docker Management Guide

*Wie du Änderungen an deinen Discord Bots machst und live pusht*

## 📋 Überblick der containerisierten Bots

Alle folgenden Bots laufen jetzt in Docker Containern:

| Bot Name | Container Name | Status | Beschreibung |
|----------|----------------|--------|--------------|
| **Money Bot** | `money-bot` | ✅ Läuft | Finanz-Tracking mit AI-Analyse |
| **Allgemeine Wohl Bot** | `allgemeine-wohl-bot` | ✅ Läuft | Haushalts-Aktivitäten tracking |
| **Calories Bot** | `calories-bot` | 🔧 Setup ready | Kalorienverfolgung mit Reports |
| **Erinnerungen Bot** | `erinnerungen-bot` | 🔧 Setup ready | Müll, Geburtstage, Termine |
| **Decision Bot** | `decision-bot` | 🔧 Setup ready | AI-gestützte Entscheidungshilfe |
| **Preisvergleich Bot** | `preisvergleich-bot` | 🔧 Setup ready | Automatischer Preisvergleich |

---

## 🚀 Schneller Start - Alle Bots starten

```bash
# Alle Bots nacheinander starten
cd /home/pi/Documents/discord/bots/00_production

# Bereits laufende Bots
# money_bot-1 und allgemeineWohl laufen bereits

# Neue Bots starten
cd Calories_bot && ./setup.sh build && ./setup.sh start && cd ..
cd Erinnerungen_bot && ./setup.sh build && ./setup.sh start && cd ..
cd decision_bot && ./setup.sh build && ./setup.sh start && cd ..
cd preisvergleich_bot && ./setup.sh build && ./setup.sh start && cd ..
```

---

## 🔧 Code-Änderungen live pushen - Der komplette Workflow

### 📝 **Schritt 1: Code bearbeiten**

Bearbeite die Bot-Dateien direkt im Ordner:
```bash
# Beispiel: Calories Bot ändern
nano /home/pi/Documents/discord/bots/00_production/Calories_bot/calories_bot.py
```

### 🔄 **Schritt 2: Änderungen live pushen**

#### **Option A: Schneller Neustart (empfohlen für kleine Änderungen)**
```bash
cd /home/pi/Documents/discord/bots/00_production/Calories_bot
./restart_bot.sh
```

#### **Option B: Vollständiger Rebuild (für größere Änderungen oder neue Dependencies)**
```bash
cd /home/pi/Documents/discord/bots/00_production/Calories_bot
./setup.sh stop
./setup.sh build
./setup.sh start
```

#### **Option C: Hot-Reload ohne Rebuild (nur bei Code-Änderungen)**
```bash
cd /home/pi/Documents/discord/bots/00_production/Calories_bot
docker compose down
docker compose up -d
```

### 📊 **Schritt 3: Änderungen verifizieren**
```bash
# Status prüfen
./setup.sh status

# Live-Logs anschauen
./setup.sh logs

# Alle Container Status
docker ps
```

---

## 🛠️ Bot-spezifische Kommandos

### **Calories Bot** 🍎
```bash
cd /home/pi/Documents/discord/bots/00_production/Calories_bot

# Verfügbare Kommandos
./setup.sh build     # Docker Image bauen
./setup.sh start     # Bot starten
./setup.sh stop      # Bot stoppen
./setup.sh restart   # Bot neustarten
./setup.sh logs      # Live-Logs anzeigen
./setup.sh status    # Status anzeigen
./setup.sh cleanup   # Alles entfernen
./restart_bot.sh     # Schneller Neustart
```

### **Erinnerungen Bot** 📅
```bash
cd /home/pi/Documents/discord/bots/00_production/Erinnerungen_bot

# Gleiche Kommandos wie oben verfügbar
./setup.sh start
./restart_bot.sh
```

### **Decision Bot** 🎯
```bash
cd /home/pi/Documents/discord/bots/00_production/decision_bot

# Gleiche Kommandos wie oben verfügbar
./setup.sh start
./restart_bot.sh
```

### **Preisvergleich Bot** 💰
```bash
cd /home/pi/Documents/discord/bots/00_production/preisvergleich_bot

# Gleiche Kommandos wie oben verfügbar
./setup.sh start
./restart_bot.sh
```

### **Money Bot** 💵 (bereits laufend)
```bash
cd /home/pi/Documents/discord/bots/00_production/money_bot-1

./setup.sh restart   # Neustart
./setup.sh logs      # Logs anzeigen
```

### **Allgemeine Wohl Bot** 🏠 (bereits laufend)
```bash
cd /home/pi/Documents/discord/bots/00_production/allgemeineWohl

./setup.sh restart   # Neustart
./setup.sh logs      # Logs anzeigen
```

---

## 🔍 Debugging & Monitoring

### **Alle laufenden Container anzeigen**
```bash
docker ps
```

### **Logs von spezifischem Bot anschauen**
```bash
# Beispiele
docker compose logs -f calories-bot
docker compose logs -f erinnerungen-bot
docker compose logs -f decision-bot
docker compose logs -f preisvergleich-bot
docker compose logs -f money-bot
docker compose logs -f allgemeine-wohl-bot
```

### **Container Health Status prüfen**
```bash
docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
```

### **Container Ressourcen-Verbrauch**
```bash
docker stats
```

---

## 🚨 Troubleshooting

### **Bot startet nicht:**
1. **Environment Variablen prüfen:**
   ```bash
   # Haupt-.env Datei prüfen
   cat /home/pi/Documents/discord/.env
   ```

2. **Build-Logs prüfen:**
   ```bash
   cd /path/to/bot
   ./setup.sh build
   ```

3. **Container Logs prüfen:**
   ```bash
   ./setup.sh logs
   ```

### **"Port already in use" Fehler:**
```bash
# Alle Container stoppen
docker stop $(docker ps -q)

# Dann einzeln wieder starten
```

### **Dependencies fehlen:**
```bash
# Requirements.txt aktualisieren und neu bauen
cd /path/to/bot
./setup.sh stop
./setup.sh build
./setup.sh start
```

### **Container läuft aber Bot antwortet nicht:**
1. Discord Token prüfen
2. Bot Permissions in Discord prüfen
3. Channel IDs in .env prüfen

---

## 📂 Datei-Struktur für eigene Änderungen

```
discord/bots/00_production/
├── money_bot-1/              # ✅ Läuft bereits
│   ├── bot.py               # Hauptbot-Code
│   ├── docker-compose.yml
│   ├── setup.sh
│   └── restart_bot.sh
├── allgemeineWohl/          # ✅ Läuft bereits  
│   ├── allgemeine_wohl_bot.py
│   ├── docker-compose.yml
│   ├── setup.sh
│   └── restart_bot.sh
├── Calories_bot/            # 🔧 Setup ready
│   ├── calories_bot.py      # Hauptbot-Code
│   ├── chart_generator.py   # Diagramm-Erstellung
│   ├── monthly_report.py    # Monatsberichte
│   ├── docker-compose.yml
│   ├── setup.sh
│   └── restart_bot.sh
├── Erinnerungen_bot/        # 🔧 Setup ready
│   ├── erinnerungen_bot.py  # Hauptbot-Code
│   ├── geburtstage.py       # Geburtstags-Manager
│   ├── muellkalender.py     # Müllkalender
│   ├── docker-compose.yml
│   ├── setup.sh
│   └── restart_bot.sh
├── decision_bot/            # 🔧 Setup ready
│   ├── decision_bot.py      # Hauptbot-Code
│   ├── rag_system.py        # AI-Entscheidungssystem
│   ├── vector_store.py      # Vektordatenbank
│   ├── docker-compose.yml
│   ├── setup.sh
│   └── restart_bot.sh
└── preisvergleich_bot/      # 🔧 Setup ready
    ├── preisvergleich_bot.py # Hauptbot-Code
    ├── agent.py             # Preisvergleichs-Agent
    ├── offer_finder.py      # Angebots-Finder
    ├── docker-compose.yml
    ├── setup.sh
    └── restart_bot.sh
```

---

## ⚡ Häufige Änderungs-Szenarien

### **🔧 Bot-Logik ändern**
```bash
# 1. Code bearbeiten
nano /path/to/bot/bot_file.py

# 2. Schnell neustarten
cd /path/to/bot
./restart_bot.sh

# 3. Testen
./setup.sh logs
```

### **📦 Neue Dependencies hinzufügen**
```bash
# 1. requirements.txt bearbeiten
nano /path/to/bot/requirements.txt

# 2. Container neu bauen
cd /path/to/bot
./setup.sh stop
./setup.sh build
./setup.sh start
```

### **⚙️ Environment Variablen ändern**
```bash
# 1. Haupt-.env bearbeiten
nano /home/pi/Documents/discord/.env

# 2. Alle betroffenen Bots neustarten
cd /path/to/bot
./restart_bot.sh
```

### **🔍 Neues Feature testen**
```bash
# 1. Code ändern
# 2. Backup vom Container machen (optional)
docker commit bot-name bot-name-backup

# 3. Testen
./restart_bot.sh
./setup.sh logs

# 4. Bei Problemen zurückrollen
docker stop bot-name
docker run -d --name bot-name bot-name-backup
```

---

## 🔄 Batch-Operationen für alle Bots

### **Alle Bots neustarten**
```bash
#!/bin/bash
cd /home/pi/Documents/discord/bots/00_production

echo "🔄 Restarting all bots..."
cd money_bot-1 && ./restart_bot.sh && cd ..
cd allgemeineWohl && ./restart_bot.sh && cd ..
cd Calories_bot && ./restart_bot.sh && cd ..
cd Erinnerungen_bot && ./restart_bot.sh && cd ..
cd decision_bot && ./restart_bot.sh && cd ..
cd preisvergleich_bot && ./restart_bot.sh && cd ..
echo "✅ All bots restarted!"
```

### **Status aller Bots prüfen**
```bash
#!/bin/bash
echo "📊 Bot Status Overview:"
echo "====================="
docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}" | grep -E "(money-bot|allgemeine-wohl-bot|calories-bot|erinnerungen-bot|decision-bot|preisvergleich-bot)"
```

---

## 🎯 Best Practices für Entwicklung

### **1. Immer testen vor Live-Push**
```bash
# Lokale Tests
python bot.py  # Außerhalb des Containers testen

# Container-Tests
./restart_bot.sh && ./setup.sh logs
```

### **2. Logs monitoren bei Änderungen**
```bash
# In separatem Terminal
./setup.sh logs

# Dann Änderungen machen und live beobachten
```

### **3. Environment Variablen sicher handhaben**
- Niemals Secrets in Code
- Immer über .env Datei
- Backup von .env vor Änderungen

### **4. Container Health Checks nutzen**
```bash
# Gesundheitsstatus prüfen
docker ps | grep "(healthy)"
```

---

## 📚 Weitere nützliche Kommandos

```bash
# Alle gestoppten Container entfernen
docker container prune

# Nicht verwendete Images entfernen
docker image prune

# Logs von allen Bots parallel
docker logs -f money-bot &
docker logs -f allgemeine-wohl-bot &
docker logs -f calories-bot &

# Container-Shell öffnen (debugging)
docker exec -it calories-bot /bin/bash

# Git Integration für Code-Versionierung
git add . && git commit -m "Bot update" && git push
```

---

## 🎉 Zusammenfassung

Mit diesem Setup kannst du:

✅ **Schnell Änderungen pushen** mit `./restart_bot.sh`  
✅ **Alle Bots überwachen** mit `docker ps` und `./setup.sh logs`  
✅ **Sicher entwickeln** mit Container-Isolation  
✅ **Einfach skalieren** mit Docker Compose  
✅ **Zuverlässig deployen** mit Health Checks  

**Ein Bot-Update dauert jetzt nur noch 10-30 Sekunden! 🚀**
