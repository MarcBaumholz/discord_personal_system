"""
Deutsche Bahn Discord Bot - Main bot implementation.
"""
import discord
from discord.ext import commands
import structlog
import asyncio
import os
from datetime import datetime
from typing import Optional

# Import our modules
from config import config
from database import db_manager, TrainConnection
from db_api import db_api
from llm_service import llm_service

# Configure structured logging
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

class DBBot(commands.Bot):
    """Deutsche Bahn Discord Bot for monitoring train delays."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',  # Fallback prefix (we use slash commands)
            intents=intents,
            description="Deutsche Bahn Delay Monitor Bot"
        )
        
    async def setup_hook(self):
        """Called when the bot is starting up."""
        logger.info("Setting up Deutsche Bahn Bot...")
        
        # Initialize database
        if not await db_manager.initialize():
            logger.error("Failed to initialize database")
            return
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info("Synced slash commands", count=len(synced))
        except Exception as e:
            logger.error("Failed to sync commands", error=str(e))
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info("Bot is ready", user=self.user.name, guilds=len(self.guilds))
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Deutsche Bahn delays 🚆"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        logger.error("Command error", error=str(error), command=ctx.command)

# Create bot instance
bot = DBBot()

@bot.tree.command(name="db-status", description="Zeige deine gespeicherten Zugverbindungen an")
async def db_status(interaction: discord.Interaction):
    """Show user's saved train connections with current status."""
    await interaction.response.defer()
    
    try:
        # Update user activity
        await db_manager.add_user(interaction.user.id, interaction.user.display_name)
        await db_manager.update_user_activity(interaction.user.id)
        
        # Get user's connections
        connections = await db_manager.get_user_connections(interaction.user.id)
        
        if not connections:
            error_msg = await llm_service.generate_error_message("no_connections")
            await interaction.followup.send(error_msg)
            return
        
        # Build response with current status for each connection
        embed = discord.Embed(
            title="🚆 Deine Zugverbindungen",
            description=f"Du hast {len(connections)} von {config.MAX_CONNECTIONS_PER_USER} Verbindungen gespeichert",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for i, conn in enumerate(connections, 1):
            try:
                # Get current status for this connection
                status_data = await db_api.get_connection_status(conn.from_station, conn.to_station)
                summary_text = await llm_service.generate_connection_summary(status_data)
                
                embed.add_field(
                    name=f"{i}. {conn.from_station} → {conn.to_station}",
                    value=summary_text,
                    inline=False
                )
                
            except Exception as e:
                logger.error("Failed to get connection status", connection=conn, error=str(e))
                embed.add_field(
                    name=f"{i}. {conn.from_station} → {conn.to_station}",
                    value="⚠️ Status konnte nicht abgerufen werden",
                    inline=False
                )
        
        embed.set_footer(text="💡 Nutze /db-check für detaillierte Informationen")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error("Error in db_status command", user_id=interaction.user.id, error=str(e))
        error_msg = await llm_service.generate_error_message("general")
        await interaction.followup.send(error_msg)

@bot.tree.command(name="db-setup", description="Speichere eine neue Zugverbindung")
async def db_setup(interaction: discord.Interaction, von: str, nach: str, alias: str = None):
    """Save a new train connection for monitoring."""
    await interaction.response.defer()
    
    try:
        # Update user activity
        await db_manager.add_user(interaction.user.id, interaction.user.display_name)
        
        # Validate stations exist
        from_stations = await db_api.search_stations(von)
        to_stations = await db_api.search_stations(nach)
        
        if not from_stations:
            error_msg = await llm_service.generate_error_message("station_not_found", von)
            await interaction.followup.send(error_msg)
            return
            
        if not to_stations:
            error_msg = await llm_service.generate_error_message("station_not_found", nach)
            await interaction.followup.send(error_msg)
            return
        
        # Use the best matching station names
        from_station = from_stations[0].name
        to_station = to_stations[0].name
        
        # Try to add the connection
        success = await db_manager.add_connection(
            interaction.user.id, 
            from_station, 
            to_station, 
            alias
        )
        
        if not success:
            # Check if it's because of max connections or duplicate
            connections = await db_manager.get_user_connections(interaction.user.id)
            if len(connections) >= config.MAX_CONNECTIONS_PER_USER:
                error_msg = await llm_service.generate_error_message("max_connections")
            else:
                error_msg = await llm_service.generate_error_message("connection_exists", f"{from_station} → {to_station}")
            await interaction.followup.send(error_msg)
            return
        
        # Success - show the new connection with current status
        embed = discord.Embed(
            title="✅ Verbindung gespeichert!",
            description=f"**{from_station} → {to_station}**",
            color=discord.Color.green()
        )
        
        if alias:
            embed.add_field(name="Alias", value=alias, inline=True)
        
        # Get current status
        try:
            status_data = await db_api.get_connection_status(from_station, to_station)
            summary_text = await llm_service.generate_connection_summary(status_data)
            embed.add_field(name="Aktueller Status", value=summary_text, inline=False)
        except Exception as e:
            logger.warning("Could not get initial status", error=str(e))
            embed.add_field(name="Status", value="⚠️ Status wird beim nächsten Check verfügbar sein", inline=False)
        
        embed.set_footer(text="💡 Nutze /db-status um alle Verbindungen zu sehen")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error("Error in db_setup command", user_id=interaction.user.id, error=str(e))
        error_msg = await llm_service.generate_error_message("general")
        await interaction.followup.send(error_msg)

@bot.tree.command(name="db-check", description="Prüfe eine spezifische Zugverbindung")
async def db_check(interaction: discord.Interaction, von: str, nach: str):
    """Check a specific train connection for delays."""
    await interaction.response.defer()
    
    try:
        # Update user activity
        await db_manager.add_user(interaction.user.id, interaction.user.display_name)
        await db_manager.update_user_activity(interaction.user.id)
        
        # Validate stations
        from_stations = await db_api.search_stations(von)
        to_stations = await db_api.search_stations(nach)
        
        if not from_stations:
            error_msg = await llm_service.generate_error_message("station_not_found", von)
            await interaction.followup.send(error_msg)
            return
            
        if not to_stations:
            error_msg = await llm_service.generate_error_message("station_not_found", nach)
            await interaction.followup.send(error_msg)
            return
        
        from_station = from_stations[0].name
        to_station = to_stations[0].name
        
        # Get connection status
        status_data = await db_api.get_connection_status(from_station, to_station)
        
        if not status_data.get("trains"):
            await interaction.followup.send(f"🚫 Keine aktuellen Zugdaten für {from_station} → {to_station} verfügbar.")
            return
        
        # Generate summary
        summary_text = await llm_service.generate_connection_summary(status_data)
        
        # Create detailed embed
        embed = discord.Embed(
            title=f"🚆 {from_station} → {to_station}",
            description=summary_text,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Add train details
        trains = status_data["trains"][:5]  # Show max 5 trains
        for i, train in enumerate(trains, 1):
            delay_text = f"+{train.delay_minutes}'" if train.delay_minutes > 0 else "pünktlich"
            status = "❌ AUSFALL" if train.is_cancelled else delay_text
            platform_text = f"Gleis {train.platform}" if train.platform else "Gleis unbekannt"
            
            train_info = f"**{train.scheduled_time.strftime('%H:%M')}** → {train.destination}\n"
            train_info += f"{platform_text} • {status}"
            
            if train.messages:
                train_info += f"\n💬 {train.messages[0][:50]}..."
            
            embed.add_field(
                name=f"{i}. {train.train_number}",
                value=train_info,
                inline=True
            )
        
        # Add summary statistics
        summary = status_data["summary"]
        stats_text = f"📊 **Statistik:**\n"
        stats_text += f"• Züge: {summary['total_trains']}\n"
        stats_text += f"• Ø Verspätung: {summary['average_delay']:.1f} Min\n"
        stats_text += f"• Pünktlichkeit: {summary['on_time_ratio']*100:.0f}%"
        
        if summary['cancelled_trains'] > 0:
            stats_text += f"\n• Ausfälle: {summary['cancelled_trains']}"
        
        embed.add_field(name="📈 Zusammenfassung", value=stats_text, inline=False)
        embed.set_footer(text="🔄 Daten werden alle 5 Minuten aktualisiert")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error("Error in db_check command", user_id=interaction.user.id, error=str(e))
        error_msg = await llm_service.generate_error_message("api_error")
        await interaction.followup.send(error_msg)

@bot.tree.command(name="db-help", description="Zeige Hilfe für den Deutsche Bahn Bot")
async def db_help(interaction: discord.Interaction):
    """Show help information for the bot."""
    await interaction.response.defer()
    
    try:
        help_text = await llm_service.generate_help_message()
        
        embed = discord.Embed(
            title="🤖 Deutsche Bahn Bot",
            description=help_text,
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Befehle im Detail",
            value=(
                "**`/db-status`** - Zeigt alle deine gespeicherten Verbindungen mit aktuellem Status\n"
                "**`/db-setup <von> <nach> [alias]`** - Speichert eine neue Verbindung (max. 3)\n"
                "**`/db-check <von> <nach>`** - Zeigt detaillierte Informationen für eine Verbindung\n"
                "**`/db-help`** - Zeigt diese Hilfe an"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Tipps",
            value=(
                "• Verwende kurze Stationsnamen (z.B. 'Berlin' statt 'Berlin Hauptbahnhof')\n"
                "• Der Bot findet automatisch die beste passende Station\n"
                "• Daten werden alle 5 Minuten aktualisiert für bessere Performance\n"
                "• Du kannst bis zu 3 Verbindungen für schnellen Zugriff speichern"
            ),
            inline=False
        )
        
        embed.set_footer(text="🚆 Powered by Deutsche Bahn API | Made with ❤️")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error("Error in db_help command", error=str(e))
        fallback_help = await llm_service.generate_help_message()
        await interaction.followup.send(fallback_help)

@bot.tree.command(name="db-remove", description="Entferne eine gespeicherte Verbindung")
async def db_remove(interaction: discord.Interaction, verbindung_nummer: int):
    """Remove a saved connection by number."""
    await interaction.response.defer()
    
    try:
        # Get user's connections
        connections = await db_manager.get_user_connections(interaction.user.id)
        
        if not connections:
            error_msg = await llm_service.generate_error_message("no_connections")
            await interaction.followup.send(error_msg)
            return
        
        if verbindung_nummer < 1 or verbindung_nummer > len(connections):
            await interaction.followup.send(
                f"❌ Ungültige Verbindungsnummer. Wähle eine Zahl zwischen 1 und {len(connections)}."
            )
            return
        
        # Get the connection to remove
        connection_to_remove = connections[verbindung_nummer - 1]
        
        # Remove the connection
        success = await db_manager.remove_connection(
            interaction.user.id, 
            connection_to_remove.id
        )
        
        if success:
            embed = discord.Embed(
                title="🗑️ Verbindung entfernt",
                description=f"**{connection_to_remove.from_station} → {connection_to_remove.to_station}** wurde gelöscht.",
                color=discord.Color.orange()
            )
            embed.set_footer(text="💡 Nutze /db-setup um eine neue Verbindung hinzuzufügen")
            await interaction.followup.send(embed=embed)
        else:
            error_msg = await llm_service.generate_error_message("general")
            await interaction.followup.send(error_msg)
            
    except Exception as e:
        logger.error("Error in db_remove command", user_id=interaction.user.id, error=str(e))
        error_msg = await llm_service.generate_error_message("general")
        await interaction.followup.send(error_msg)

def main():
    """Main function to run the bot."""
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed")
        return
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the bot
    try:
        logger.info("Starting Deutsche Bahn Discord Bot...")
        bot.run(config.DISCORD_TOKEN)
    except Exception as e:
        logger.error("Failed to start bot", error=str(e))

if __name__ == "__main__":
    main()