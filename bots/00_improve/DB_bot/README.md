# S-Bahn Monitor - Deutsche Bahn Discord Bot

Ein Discord Bot zur Live-Überwachung von S3-Verbindungen zwischen Schwaikheim und Stuttgart Feuersee mit echten Deutsche Bahn APIs.

## 🎯 Features

- **Live S3-Daten**: Echte Deutsche Bahn RIS API Integration
- **Einfache Befehle**: Nur "1", "2", "status", "help" 
- **Rich Discord Embeds**: Farbkodierte Verspätungsanzeige
- **JSON Logging**: Vollständige API-Request Protokollierung
- **Kostenlos**: Nutzt DB API Free-Plan (1000 Requests/Tag)
- **Deutsche UI**: Alle Nachrichten auf Deutsch

## 🚆 Routen

- **Route 1**: Schwaikheim → Stuttgart Feuersee
- **Route 2**: Stuttgart Feuersee → Schwaikheim  
- **Linie**: S3 (echte S-Bahn Daten)
- **Fahrzeit**: ~14 Minuten pro Strecke

## 📱 Discord Befehle

| Befehl | Beschreibung |
|--------|-------------|
| `1` | Route 1: Schwaikheim → Stuttgart Feuersee |
| `2` | Route 2: Stuttgart Feuersee → Schwaikheim |
| `status` | Bot Status und API Statistiken |
| `help` | Hilfe und Befehlsübersicht |

## 🎨 Farb-System

- 🟢 **Grün**: Alle Züge pünktlich
- 🟡 **Gelb**: Kleine Verspätungen (≤3 min)
- 🔴 **Rot**: Große Verspätungen (>3 min)

## 🔧 Setup

### 1. Virtual Environment
```bash
cd /home/pi/Documents/discord/bots/DB_bot
python3 -m venv db_env
source db_env/bin/activate
pip install -r requirements.txt
```

### 2. Deutsche Bahn API Setup

1. **Account erstellen**: [DB API Marketplace](https://developers.deutschebahn.com/db-api-marketplace)
2. **Anwendung anlegen**: Neue Application im Portal erstellen
3. **APIs abonnieren**: 
   - RIS::Stations (Free Plan)
   - RIS::Journeys (Free Plan)
4. **Credentials kopieren**: Client-ID und API-Key notieren

### 3. Environment Configuration

Kopiere `env.example` zu `.env` und fülle aus:

```bash
cp env.example .env
```

```env
# Deutsche Bahn API (Free Plan)
DB_CLIENT_ID=your_client_id_here
DB_API_KEY=your_api_key_here

# Discord Bot Token (aus parent directory)
DISCORD_TOKEN=your_discord_bot_token
```

### 4. Bot starten

```bash
# Virtual Environment aktivieren
source db_env/bin/activate

# Bot starten
python sbahn_monitor.py
```

## 📁 Projektstruktur

```
DB_bot/
├── sbahn_monitor.py          # Haupt-Bot Datei
├── requirements.txt          # Python Dependencies  
├── env.example              # Environment Template
├── api_logs/                # JSON API Logs
│   └── api_log_YYYYMMDD.json
├── db_env/                  # Virtual Environment
├── PLANNING.md              # Projektplanung
├── TASK.md                  # Task Management
└── README.md               # Diese Datei
```

## 📊 API Logging

Alle API-Calls werden in `api_logs/api_log_YYYYMMDD.json` protokolliert:

```json
{
  "timestamp": "2025-06-19T14:44:12.983803",
  "route": 1,
  "route_name": "Schwaikheim → Stuttgart Feuersee",
  "origin_id": "8005454",
  "destination_id": "8002058", 
  "success": true,
  "api_response": [...],
  "error": null,
  "response_size": 16
}
```

## 🔒 Sicherheit & Limits

- **Free Plan**: 1000 Requests/Tag, ~60 Requests/Minute
- **Caching**: 2-Minuten TTL reduziert API-Calls
- **Rate Limiting**: Max 50 Requests/Minute
- **Error Handling**: Keine Mock-Daten, ehrliche Fehlermeldungen

## 🐛 Debugging

### Logs prüfen
```bash
# Bot Logs (stdout)
python sbahn_monitor.py

# API Logs (JSON)
cat api_logs/api_log_$(date +%Y%m%d).json | jq .
```

### Häufige Probleme

1. **Discord Module nicht gefunden**:
   ```bash
   source db_env/bin/activate
   pip install discord.py
   ```

2. **DB API Credentials fehlen**:
   - Prüfe `.env` Datei
   - Verifiziere Client-ID und API-Key im DB Portal

3. **Keine S3-Verbindungen gefunden**:
   - Normal außerhalb der Betriebszeiten
   - Prüfe Station IDs: Schwaikheim (8005454), Feuersee (8002058)

## ⚡ Performance

- **Cache Hit Rate**: ~90% bei normaler Nutzung
- **API Response Time**: ~1-3 Sekunden
- **Memory Usage**: ~50MB Python Prozess
- **CPU Usage**: Minimal (Event-driven)

## 🔄 Updates & Wartung

### Dependencies updaten
```bash
source db_env/bin/activate
pip install --upgrade -r requirements.txt
```

### Logs archivieren
```bash
# Alte Logs komprimieren (monatlich)
cd api_logs
tar -czf logs_$(date +%Y%m).tar.gz api_log_202*.json
rm api_log_202*.json
```

## 📈 Monitoring

Nutze den `status` Befehl im Discord für:
- Bot Uptime
- Cache Statistiken  
- API Request Counter
- Log-Dateien Anzahl

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen
3. Tests hinzufügen
4. Pull Request erstellen

## 📜 Lizenz

MIT License - siehe LICENSE Datei

---

**Entwickelt für Live S3-Monitoring mit kostenlosen Deutsche Bahn APIs** 🚆✨ 