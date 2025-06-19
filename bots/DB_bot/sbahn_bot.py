"""
S-Bahn Monitoring Discord Bot
Commands: "1" for Route 1, "2" for Route 2
"""
import discord
from discord.ext import commands
import structlog
import asyncio
from datetime import datetime
from typing import Optional

# Import our modules
from config import config
from ris_api import ris_api, RouteStatus, SBahnJourney

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class SBahnBot(commands.Bot):
    """S-Bahn monitoring bot for Schwaikheim ↔ Stuttgart Feuersee."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',  # Fallback (we use message content)
            intents=intents,
            description="S-Bahn Monitor: Schwaikheim ↔ Stuttgart Feuersee"
        )
    
    async def setup_hook(self):
        """Called when the bot is starting up."""
        logger.info("Setting up S-Bahn Monitor Bot...")
        
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info("S-Bahn Bot ready", user=self.user.name, guilds=len(self.guilds))
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="S-Bahn delays 🚊"
        )
        await self.change_presence(activity=activity)
    
    async def on_message(self, message):
        """Handle messages: "1" and "2" trigger route checks."""
        # Ignore bot messages
        if message.author == self.user:
            return
        
        # Check for route triggers
        content = message.content.strip()
        
        if content == "1":
            await self.handle_route_check(message, 1)
        elif content == "2":
            await self.handle_route_check(message, 2)
        elif content.lower() in ["help", "hilfe", "?", "sbahn"]:
            await self.send_help(message.channel)
        
        # Process other commands
        await self.process_commands(message)
    
    async def handle_route_check(self, message, route_number: int):
        """Handle route check for route 1 or 2."""
        try:
            # Send typing indicator
            async with message.channel.typing():
                # Get route status
                status = await ris_api.get_route_status(route_number)
                
                # Create and send embed
                embed = self.create_route_embed(status, route_number)
                await message.channel.send(embed=embed)
                
        except Exception as e:
            logger.error("Error handling route check", route=route_number, error=str(e))
            await message.channel.send(f"❌ Fehler beim Abrufen der S-Bahn Daten für Route {route_number}")
    
    def create_route_embed(self, status: RouteStatus, route_number: int) -> discord.Embed:
        """Create a rich embed for route status."""
        # Determine embed color based on delays
        if status.average_delay <= 2:
            color = discord.Color.green()
            status_emoji = "🟢"
        elif status.average_delay <= 5:
            color = discord.Color.orange() 
            status_emoji = "🟡"
        else:
            color = discord.Color.red()
            status_emoji = "🔴"
        
        # Create embed
        embed = discord.Embed(
            title=f"{status_emoji} Route {route_number}: {status.route_name}",
            description=f"**S-Bahn Live-Status** • {status.last_updated.strftime('%H:%M:%S')}",
            color=color,
            timestamp=datetime.now()
        )
        
        # Add next journeys
        if status.next_journeys:
            journeys_text = ""
            for i, journey in enumerate(status.next_journeys[:3], 1):  # Show top 3
                delay_text = self.format_delay(journey.delay_minutes)
                time_str = journey.departure_planned.strftime("%H:%M")
                
                journeys_text += f"**{i}. {journey.line}** um **{time_str}** {delay_text}\n"
                journeys_text += f"   Gleis {journey.platform or '?'}"
                
                if journey.messages:
                    journeys_text += f" • ⚠️ {journey.messages[0][:40]}..."
                journeys_text += "\n\n"
            
            embed.add_field(
                name="🚊 Nächste S-Bahnen",
                value=journeys_text.strip(),
                inline=False
            )
        
        # Add statistics
        stats_text = f"📊 **Durchschnitt:** {status.average_delay:.1f} Min\n"
        stats_text += f"📈 **Max Verspätung:** {status.max_delay} Min\n"
        
        if status.disruptions:
            stats_text += f"⚠️ **Störungen:** {len(status.disruptions)}"
        
        embed.add_field(
            name="📈 Statistik",
            value=stats_text,
            inline=True
        )
        
        # Add quick info
        next_sbahn = status.next_journeys[0] if status.next_journeys else None
        if next_sbahn:
            quick_text = f"🕐 **{next_sbahn.departure_planned.strftime('%H:%M')}**\n"
            quick_text += f"🚊 **{next_sbahn.line}** Gleis **{next_sbahn.platform or '?'}**\n"
            quick_text += self.format_delay(next_sbahn.delay_minutes)
            
            embed.add_field(
                name="⚡ Nächste Fahrt",
                value=quick_text,
                inline=True
            )
        
        # Add disruptions if any
        if status.disruptions:
            disruption_text = "\n".join([f"• {d[:60]}..." for d in status.disruptions[:2]])
            embed.add_field(
                name="⚠️ Aktuelle Störungen",
                value=disruption_text,
                inline=False
            )
        
        embed.set_footer(
            text="💡 Schreibe '1' für Route 1 oder '2' für Route 2 • Daten alle 2 Min aktualisiert",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Deutsche_Bahn_AG-Logo.svg/512px-Deutsche_Bahn_AG-Logo.svg.png"
        )
        
        return embed
    
    def format_delay(self, delay_minutes: int) -> str:
        """Format delay information with appropriate emoji."""
        if delay_minutes == 0:
            return "✅ **pünktlich**"
        elif delay_minutes <= 2:
            return f"🟡 **+{delay_minutes}'**"
        elif delay_minutes <= 5:
            return f"🟠 **+{delay_minutes}'**"
        else:
            return f"🔴 **+{delay_minutes}'**"
    
    async def send_help(self, channel):
        """Send help information."""
        embed = discord.Embed(
            title="🚊 S-Bahn Monitor Hilfe",
            description="Live-Monitoring für deine S-Bahn Routen zwischen Schwaikheim und Stuttgart Feuersee",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📍 Routen",
            value=(
                "**Route 1:** Schwaikheim → Stuttgart Feuersee\n"
                "**Route 2:** Stuttgart Feuersee → Schwaikheim"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Commands",
            value=(
                "**`1`** - Status für Route 1 anzeigen\n"
                "**`2`** - Status für Route 2 anzeigen\n"
                "**`help`** - Diese Hilfe anzeigen"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔄 Features",
            value=(
                "• Live-Verspätungsdaten der Deutschen Bahn\n"
                "• Nächste 3 S-Bahn Abfahrten\n"
                "• Störungsmeldungen und Statistiken\n"
                "• Automatische Updates alle 2 Minuten"
            ),
            inline=False
        )
        
        embed.set_footer(
            text="🚊 Powered by Deutsche Bahn RIS API",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Deutsche_Bahn_AG-Logo.svg/512px-Deutsche_Bahn_AG-Logo.svg.png"
        )
        
        await channel.send(embed=embed)

# Create bot instance
bot = SBahnBot()

def main():
    """Main function to run the bot."""
    if not config.validate():
        logger.error("Configuration validation failed")
        return
    
    try:
        logger.info("Starting S-Bahn Monitor Bot...")
        bot.run(config.DISCORD_TOKEN)
    except Exception as e:
        logger.error("Failed to start bot", error=str(e))

if __name__ == "__main__":
    main() 