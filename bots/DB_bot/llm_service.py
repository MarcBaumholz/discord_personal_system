"""
LLM service for generating intelligent responses using OpenRouter.
"""
import openai
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from config import config
from db_api import TrainDeparture
import json

logger = structlog.get_logger()

class LLMService:
    """Service for generating natural language responses about train information."""
    
    def __init__(self):
        if config.OPENROUTER_API_KEY:
            self.client = openai.OpenAI(
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL
            )
        else:
            self.client = None
            logger.warning("OpenRouter API key not configured - using fallback responses")
    
    async def generate_connection_summary(self, connection_data: Dict[str, Any]) -> str:
        """Generate a natural language summary of train connection status."""
        if not self.client:
            return self._generate_fallback_summary(connection_data)
        
        try:
            # Prepare the data for the LLM
            trains_info = []
            for train in connection_data.get("trains", []):
                train_info = {
                    "train_number": train.train_number,
                    "destination": train.destination,
                    "scheduled_time": train.scheduled_time.strftime("%H:%M"),
                    "delay_minutes": train.delay_minutes,
                    "platform": train.platform,
                    "is_cancelled": train.is_cancelled,
                    "messages": train.messages
                }
                trains_info.append(train_info)
            
            summary = connection_data.get("summary", {})
            
            prompt = f"""
Erstelle eine freundliche und informative Zusammenfassung der aktuellen Zugverbindung von {connection_data['from_station']} nach {connection_data['to_station']}.

Aktuelle Zugdaten:
{json.dumps(trains_info, indent=2, ensure_ascii=False)}

Zusammenfassung:
- Durchschnittliche Verspätung: {summary.get('average_delay', 0):.1f} Minuten
- Maximale Verspätung: {summary.get('max_delay', 0)} Minuten
- Pünktlichkeitsrate: {summary.get('on_time_ratio', 0)*100:.0f}%
- Ausfälle: {summary.get('cancelled_trains', 0)}

Anforderungen:
- Verwende freundlichen, hilfreichen Ton
- Fasse die wichtigsten Informationen zusammen
- Erwähne auffällige Verspätungen oder Ausfälle
- Gib praktische Empfehlungen wenn nötig
- Antwort auf Deutsch
- Maximal 3 Sätze
- Verwende Emojis für bessere Lesbarkeit
"""

            response = self.client.chat.completions.create(
                model=config.DEFAULT_LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein hilfreicher Assistent für Deutsche Bahn Verbindungen. Antworte knapp und freundlich."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Failed to generate LLM response", error=str(e))
            return self._generate_fallback_summary(connection_data)
    
    def _generate_fallback_summary(self, connection_data: Dict[str, Any]) -> str:
        """Generate a simple fallback summary when LLM is not available."""
        from_station = connection_data.get("from_station", "")
        to_station = connection_data.get("to_station", "")
        summary = connection_data.get("summary", {})
        trains = connection_data.get("trains", [])
        
        avg_delay = summary.get("average_delay", 0)
        cancelled = summary.get("cancelled_trains", 0)
        
        # Build a simple summary
        if not trains:
            return f"🚫 Keine aktuellen Zugdaten für {from_station} → {to_station} verfügbar."
        
        status_emoji = "🟢" if avg_delay <= 2 else "🟡" if avg_delay <= 10 else "🔴"
        
        result = f"{status_emoji} **{from_station} → {to_station}**\n"
        
        if cancelled > 0:
            result += f"⚠️ {cancelled} Zug(züge) ausgefallen! "
        
        if avg_delay <= 2:
            result += "Züge fahren weitgehend pünktlich ✅"
        elif avg_delay <= 5:
            result += f"Leichte Verspätungen (~{avg_delay:.0f} Min) 🕐"
        elif avg_delay <= 15:
            result += f"Mittlere Verspätungen (~{avg_delay:.0f} Min) ⏰"
        else:
            result += f"Erhebliche Verspätungen (~{avg_delay:.0f} Min) 🚨"
        
        # Add next train info
        if trains:
            next_train = trains[0]
            delay_text = f"+{next_train.delay_minutes}'" if next_train.delay_minutes > 0 else "pünktlich"
            result += f"\n🚆 Nächster Zug: {next_train.train_number} um {next_train.scheduled_time.strftime('%H:%M')} ({delay_text})"
        
        return result
    
    async def generate_help_message(self) -> str:
        """Generate a help message for bot commands."""
        if not self.client:
            return self._get_fallback_help()
        
        try:
            prompt = """
Erstelle eine kurze, freundliche Hilfe-Nachricht für einen Deutsche Bahn Discord Bot.

Der Bot hat folgende Befehle:
- /db-status - Zeigt alle gespeicherten Verbindungen an
- /db-setup [von] [nach] - Speichert eine neue Verbindung (max. 3)
- /db-check [von] [nach] - Prüft eine spezifische Verbindung
- /db-help - Zeigt diese Hilfe an

Anforderungen:
- Freundlicher, hilfsbereiter Ton
- Kurze Erklärung was der Bot kann
- Beispiel für einen Befehl
- Auf Deutsch
- Mit passenden Emojis
- Maximal 5 Zeilen
"""

            response = self.client.chat.completions.create(
                model=config.DEFAULT_LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein hilfreicher Discord Bot Assistent. Erstelle knapp und klar."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=250,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Failed to generate help message", error=str(e))
            return self._get_fallback_help()
    
    def _get_fallback_help(self) -> str:
        """Fallback help message when LLM is not available."""
        return """🚆 **Deutsche Bahn Bot Hilfe**

🔍 `/db-status` - Zeige deine gespeicherten Verbindungen
💾 `/db-setup München Hamburg` - Speichere eine neue Verbindung
📊 `/db-check Berlin Frankfurt` - Prüfe eine spezifische Verbindung  
❓ `/db-help` - Zeige diese Hilfe

Du kannst bis zu 3 Verbindungen speichern für schnellen Zugriff! 🎯"""
    
    async def generate_error_message(self, error_type: str, context: str = "") -> str:
        """Generate a user-friendly error message."""
        error_messages = {
            "station_not_found": f"🚫 Station '{context}' wurde nicht gefunden. Bitte prüfe die Schreibweise.",
            "max_connections": f"⚠️ Du hast bereits {config.MAX_CONNECTIONS_PER_USER} Verbindungen gespeichert. Entferne zuerst eine alte Verbindung.",
            "connection_exists": f"📍 Die Verbindung '{context}' ist bereits gespeichert.",
            "no_connections": "📋 Du hast noch keine Verbindungen gespeichert. Nutze `/db-setup [von] [nach]` um eine zu erstellen.",
            "api_error": "🔧 Entschuldigung, es gab ein Problem beim Abrufen der Zugdaten. Versuche es bitte später nochmal.",
            "general": "❌ Es ist ein Fehler aufgetreten. Bitte versuche es erneut."
        }
        
        return error_messages.get(error_type, error_messages["general"])

# Create a global LLM service instance
llm_service = LLMService() 