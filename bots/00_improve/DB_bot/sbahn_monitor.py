#!/usr/bin/env python3
"""
S-Bahn Monitor - Live Deutsche Bahn S3 Verbindungen
Überwacht Live-Verspätungen zwischen Schwaikheim und Stuttgart Feuersee

Kommandos:
- "1": Route Schwaikheim → Stuttgart Feuersee  
- "2": Route Stuttgart Feuersee → Schwaikheim
- "status": Bot Status und API Logs Info
- "help": Hilfe und Befehle anzeigen
"""

import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import discord
from discord.ext import commands
import httpx
from dotenv import load_dotenv
import aiofiles

# Environment setup
load_dotenv()
load_dotenv("../../../.env")  # Parent directory for DISCORD_TOKEN

# Logging setup
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DBAPIClient:
    """Deutsche Bahn RIS API Client mit Caching und JSON Logging"""
    
    def __init__(self):
        self.client_id = os.getenv('DB_CLIENT_ID')
        self.api_key = os.getenv('DB_API_KEY')
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = int(os.getenv('CACHE_TTL_MINUTES', 2))
        
        # Station IDs
        self.schwaikheim_id = os.getenv('SCHWAIKHEIM_ID', '8005454')
        self.feuersee_id = os.getenv('FEUERSEE_ID', '8002058')
        
        if not self.client_id or not self.api_key:
            logger.error("DB API Credentials missing! Set DB_CLIENT_ID and DB_API_KEY")
    
    def _get_headers(self) -> Dict[str, str]:
        """API Headers für Deutsche Bahn RIS APIs"""
        return {
            'DB-Client-Id': self.client_id,
            'DB-Api-Key': self.api_key,
            'Accept': 'application/json',
            'User-Agent': 'S3-Live-Monitor/1.0'
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Prüft ob Cache-Eintrag noch gültig ist (2 Minuten TTL)"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cached_time < timedelta(minutes=self.cache_ttl)
    
    async def _log_api_call(self, route: int, route_name: str, origin_id: str, 
                           dest_id: str, success: bool, response_data: Any = None, 
                           error: str = None):
        """Protokolliert API-Aufrufe in JSON-Datei"""
        log_date = datetime.now().strftime('%Y%m%d')
        log_file = f"api_logs/api_log_{log_date}.json"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'route': route,
            'route_name': route_name,
            'origin_id': origin_id,
            'destination_id': dest_id,
            'success': success,
            'api_response': response_data,
            'error': error,
            'response_size': len(response_data) if response_data else 0
        }
        
        try:
            # Existing log file laden oder neue Liste erstellen
            if os.path.exists(log_file):
                async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    logs = json.loads(content) if content.strip() else []
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Aktualisierte Logs speichern
            async with aiofiles.open(log_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(logs, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Fehler beim API-Logging: {e}")
    
    async def get_s3_connections(self, route: int) -> Optional[List[Dict]]:
        """
        Holt S3-Verbindungen für Route 1 oder 2
        Route 1: Schwaikheim → Stuttgart Feuersee
        Route 2: Stuttgart Feuersee → Schwaikheim
        """
        if route == 1:
            origin_id, dest_id = self.schwaikheim_id, self.feuersee_id
            route_name = "Schwaikheim → Stuttgart Feuersee"
        elif route == 2:
            origin_id, dest_id = self.feuersee_id, self.schwaikheim_id
            route_name = "Stuttgart Feuersee → Schwaikheim"
        else:
            logger.error(f"Ungültige Route: {route}")
            return None
        
        cache_key = f"route_{route}_{origin_id}_{dest_id}"
        
        # Cache prüfen
        if self._is_cache_valid(cache_key):
            logger.info(f"Cache hit für Route {route}")
            return self.cache[cache_key]['data']
        
        # API-Aufruf
        url = "https://apis.deutschebahn.com/db-api-marketplace/apis/ris-journeys/v1/journeys"
        params = {
            'origin': origin_id,
            'destination': dest_id,
            'dateTime': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'searchForDeparture': 'true'
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                
                data = response.json()
                journeys = data.get('journeys', [])
                
                # Nur S3-Verbindungen filtern
                s3_journeys = []
                for journey in journeys[:5]:  # Max 5 Verbindungen
                    legs = journey.get('legs', [])
                    for leg in legs:
                        line = leg.get('line', {})
                        if line.get('name') == 'S3':
                            s3_journeys.append(journey)
                            break
                
                # Cache aktualisieren
                self.cache[cache_key] = {
                    'data': s3_journeys,
                    'timestamp': datetime.now()
                }
                
                # API-Aufruf protokollieren
                await self._log_api_call(route, route_name, origin_id, dest_id, True, s3_journeys)
                
                logger.info(f"Route {route}: {len(s3_journeys)} S3-Verbindungen gefunden")
                return s3_journeys
                
        except httpx.HTTPStatusError as e:
            error_msg = f"API HTTP Error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            await self._log_api_call(route, route_name, origin_id, dest_id, False, error=error_msg)
            return None
            
        except Exception as e:
            error_msg = f"API Error: {str(e)}"
            logger.error(error_msg)
            await self._log_api_call(route, route_name, origin_id, dest_id, False, error=error_msg)
            return None

class S3MonitorBot(commands.Bot):
    """S-Bahn S3 Monitor Discord Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.db_client = DBAPIClient()
        self.start_time = datetime.now()
    
    async def on_ready(self):
        """Bot ist bereit"""
        logger.info(f'{self.user} ist online!')
        logger.info(f'Bot läuft in {len(self.guilds)} Discord Servern')
        
        # Status setzen
        activity = discord.Activity(
            type=discord.ActivityType.watching, 
            name="S3 Verspätungen 🚆"
        )
        await self.change_presence(activity=activity)
    
    async def on_message(self, message):
        """Message Event Handler für einfache Kommandos"""
        if message.author.bot:
            return
        
        content = message.content.strip().lower()
        
        if content == "1":
            await self.handle_route_command(message, 1)
        elif content == "2":
            await self.handle_route_command(message, 2)
        elif content == "status":
            await self.handle_status_command(message)
        elif content == "help":
            await self.handle_help_command(message)
    
    async def handle_route_command(self, message, route: int):
        """Behandelt Route 1 oder 2 Kommando"""
        try:
            # Lade-Nachricht
            loading_embed = discord.Embed(
                title="🔄 Lade S3-Verbindungen...",
                description=f"Suche aktuelle Abfahrten für Route {route}",
                color=0xFFA500  # Orange
            )
            loading_msg = await message.reply(embed=loading_embed)
            
            # S3-Verbindungen abrufen
            connections = await self.db_client.get_s3_connections(route)
            
            if connections is None:
                # API-Fehler
                error_embed = discord.Embed(
                    title="❌ API-Fehler",
                    description="Konnte keine Live-Daten von der DB API abrufen.\n\n"
                               "**Mögliche Ursachen:**\n"
                               "• DB API Server temporär nicht verfügbar\n"
                               "• Netzwerkprobleme\n"
                               "• API-Schlüssel ungültig\n"
                               "• Rate-Limit erreicht\n\n"
                               "Bitte versuche es später erneut.",
                    color=0xFF0000  # Rot
                )
                await loading_msg.edit(embed=error_embed)
                return
            
            if not connections:
                # Keine S3-Verbindungen gefunden
                no_trains_embed = discord.Embed(
                    title="🚆 Keine S3-Verbindungen",
                    description=f"Aktuell keine S3-Züge für Route {route} gefunden.\n"
                               "Möglicherweise Betriebspause oder nur andere Linien verfügbar.",
                    color=0xFFFF00  # Gelb
                )
                await loading_msg.edit(embed=no_trains_embed)
                return
            
            # Erfolgreiche Antwort mit S3-Daten
            embed = self.create_route_embed(route, connections)
            await loading_msg.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Fehler bei Route {route}: {e}")
            error_embed = discord.Embed(
                title="💥 Unerwarteter Fehler",
                description=f"Ein unerwarteter Fehler ist aufgetreten:\n`{str(e)}`",
                color=0xFF0000
            )
            await message.reply(embed=error_embed)
    
    def create_route_embed(self, route: int, connections: List[Dict]) -> discord.Embed:
        """Erstellt Rich Embed für Route-Antwort"""
        if route == 1:
            title = "🚆 Route 1: Schwaikheim → Stuttgart Feuersee"
            route_info = "S3 Richtung Stuttgart"
        else:
            title = "🚆 Route 2: Stuttgart Feuersee → Schwaikheim"
            route_info = "S3 Richtung Schwaikheim"
        
        # Farbe basierend auf Verspätungen
        max_delay = 0
        for conn in connections:
            legs = conn.get('legs', [])
            for leg in legs:
                delay = leg.get('departureDelay', 0)
                max_delay = max(max_delay, delay or 0)
        
        if max_delay == 0:
            color = 0x00FF00  # Grün - pünktlich
        elif max_delay <= 3:
            color = 0xFFFF00  # Gelb - kleine Verspätung
        else:
            color = 0xFF0000  # Rot - große Verspätung
        
        embed = discord.Embed(
            title=title,
            description=f"**{route_info}** • Nächste {len(connections)} Abfahrten",
            color=color,
            timestamp=datetime.now()
        )
        
        # Verbindungen hinzufügen
        for i, conn in enumerate(connections[:3], 1):
            legs = conn.get('legs', [])
            if not legs:
                continue
                
            leg = legs[0]  # Erste Teilstrecke
            
            # Abfahrtszeit
            planned_time = leg.get('plannedDepartureDateTime', '')
            actual_time = leg.get('actualDepartureDateTime', planned_time)
            delay = leg.get('departureDelay', 0)
            
            if planned_time:
                planned_dt = datetime.fromisoformat(planned_time.replace('Z', '+00:00'))
                time_str = planned_dt.strftime('%H:%M')
            else:
                time_str = "??"
            
            # Verspätung formatieren
            if delay and delay > 0:
                delay_str = f" ⏰ +{delay} min"
                status_icon = "🟡" if delay <= 3 else "🔴"
            else:
                delay_str = " ✅ pünktlich"
                status_icon = "🟢"
            
            # Gleis-Information
            platform = leg.get('plannedDeparturePlatform', 'unbekannt')
            
            embed.add_field(
                name=f"{status_icon} Abfahrt {i}: {time_str}",
                value=f"**Gleis:** {platform}\n"
                      f"**Status:** {delay_str}\n"
                      f"**Linie:** S3",
                inline=True
            )
        
        # Footer mit Statistiken
        total_delays = sum(leg.get('departureDelay', 0) or 0 
                          for conn in connections 
                          for leg in conn.get('legs', []))
        avg_delay = total_delays / len(connections) if connections else 0
        
        embed.set_footer(
            text=f"🕐 Aktualisiert • ⌀ Verspätung: {avg_delay:.1f} min • Max: {max_delay} min"
        )
        
        return embed
    
    async def handle_status_command(self, message):
        """Bot Status und API-Log Information"""
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Ohne Millisekunden
        
        # Log-Dateien scannen
        log_dir = Path("api_logs")
        log_files = list(log_dir.glob("api_log_*.json")) if log_dir.exists() else []
        total_requests = 0
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                    total_requests += len(logs)
            except:
                pass
        
        embed = discord.Embed(
            title="📊 S3-Monitor Status",
            color=0x0099FF
        )
        
        embed.add_field(
            name="🤖 Bot Information",
            value=f"**Uptime:** {uptime_str}\n"
                  f"**Server:** {len(self.guilds)}\n"
                  f"**Cache TTL:** {self.db_client.cache_ttl} Minuten",
            inline=True
        )
        
        embed.add_field(
            name="🚆 Routen",
            value="**Route 1:** Schwaikheim → Feuersee\n"
                  "**Route 2:** Feuersee → Schwaikheim\n"
                  "**Linie:** S3",
            inline=True
        )
        
        embed.add_field(
            name="📈 API Statistiken",
            value=f"**Log-Dateien:** {len(log_files)}\n"
                  f"**Total Requests:** {total_requests}\n"
                  f"**Cache Einträge:** {len(self.db_client.cache)}",
            inline=True
        )
        
        await message.reply(embed=embed)
    
    async def handle_help_command(self, message):
        """Hilfe-Befehl"""
        embed = discord.Embed(
            title="🚆 S3-Monitor Hilfe",
            description="Live-Überwachung der S3-Verbindungen zwischen Schwaikheim und Stuttgart Feuersee",
            color=0x0099FF
        )
        
        embed.add_field(
            name="📱 Verfügbare Befehle",
            value="**`1`** - Route 1: Schwaikheim → Stuttgart Feuersee\n"
                  "**`2`** - Route 2: Stuttgart Feuersee → Schwaikheim\n"
                  "**`status`** - Bot Status und Statistiken\n"
                  "**`help`** - Diese Hilfe anzeigen",
            inline=False
        )
        
        embed.add_field(
            name="🚆 S3-Fahrplan",
            value="**Takt:** Abfahrten um :23 und :53 jede Stunde\n"
                  "**Fahrzeit:** ~14 Minuten pro Strecke\n"
                  "**Datenquelle:** Deutsche Bahn RIS API (Live)",
            inline=False
        )
        
        embed.add_field(
            name="🎨 Farb-System",
            value="🟢 **Grün:** Alle Züge pünktlich\n"
                  "🟡 **Gelb:** Kleine Verspätungen (≤3 min)\n"
                  "🔴 **Rot:** Große Verspätungen (>3 min)",
            inline=False
        )
        
        embed.set_footer(text="Daten werden alle 2 Minuten aktualisiert")
        
        await message.reply(embed=embed)

async def main():
    """Hauptfunktion - startet den Bot"""
    # Discord Token prüfen
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN nicht gefunden! Prüfe .env Datei.")
        return
    
    # Bot starten
    bot = S3MonitorBot()
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Discord Login fehlgeschlagen! Prüfe DISCORD_TOKEN.")
    except Exception as e:
        logger.error(f"Bot Fehler: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main()) 