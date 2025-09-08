#!/bin/bash
# Einfaches Bot Start Script
# Startet alle bekannten Bot Container wieder

echo "🚀 Starte alle Discord Bots..."

# Todo Bot
echo "1. Starte Todo Bot..."
cd /home/pi/Documents/discord/bots/00_production/todo_bot
docker-compose -f docker-compose.todo.yml up -d &

# Calories Bot  
echo "2. Starte Calories Bot..."
cd /home/pi/Documents/discord/bots/00_production/Calories_bot
docker-compose up -d &

# Money Bot
echo "3. Starte Money Bot..."
cd /home/pi/Documents/discord/bots/00_production/money_bot-1
docker-compose up -d &

# Erinnerungen Bot
echo "4. Starte Erinnerungen Bot..."
cd /home/pi/Documents/discord/bots/00_production/Erinnerungen_bot
docker-compose up -d &

# Tagebuch Bot
echo "5. Starte Tagebuch Bot..."
cd /home/pi/Documents/discord/bots/00_production/Tagebuch_bot
docker-compose up -d &

# Preisvergleich Bot
echo "6. Starte Preisvergleich Bot..."
cd /home/pi/Documents/discord/bots/00_production/preisvergleich_bot
docker-compose up -d &

# Allgemeine Wohl Bot
echo "7. Starte Allgemeine Wohl Bot..."
cd /home/pi/Documents/discord/bots/00_production/allgemeineWohl
docker-compose up -d &

# Warten auf alle Jobs
wait

echo "🎉 Alle Bots gestartet! Warte 30 Sekunden für Startnachrichten..."
sleep 30

echo "📊 Aktueller Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(discord|bot)"

echo "
📋 Überprüfe Discord Channels:
   • Todo Bot: Channel 1368180016785002536 
   • Calories Bot: Channel 1382099540391497818
   • Money Bot: Entsprechende Channels
   • Erinnerungen Bot: Channel 1361084010847015241
   • Tagebuch Bot: Channel 1384289197115838625
   • Preisvergleich Bot: Entsprechende Channels
   • Allgemeine Wohl Bot: Channel 1361083769427202291
"
