#!/usr/bin/env python3
"""
Monthly Calorie Report Generator
Main module for creating and sending monthly calorie reports via Discord
"""

import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
from dotenv import load_dotenv

# Import our custom modules
from notion_data_reader import CalorieDataExtractor
from chart_generator import CalorieChartGenerator

# Import logging system
from logger_config import bot_logger

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CALORIES_CHANNEL_ID = int(os.getenv("CALORIES_CHANNEL_ID", "1382099540391497818"))

class MonthlyReportGenerator:
    """Generates and sends monthly calorie reports"""
    
    def __init__(self):
        self.data_extractor = CalorieDataExtractor()
        self.chart_generator = CalorieChartGenerator()
        
        # Set up Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.setup_bot_events()
    
    def setup_bot_events(self):
        """Setup bot events and commands"""
        
        @self.bot.event
        async def on_ready():
            """Called when the bot is ready"""
            print(f"🤖 Monthly Report Bot is ready!")
            print(f"📊 Bot user: {self.bot.user}")
            print(f"🔗 Connected to Discord")
    
    async def generate_monthly_report(self, year: int, month: int, username: str) -> Dict[str, Any]:
        """
        Generate complete monthly report for a user
        
        Args:
            year: Target year
            month: Target month
            username: Username to generate report for
            
        Returns:
            Dictionary with report data and file paths
        """
        try:
            print(f"📊 Generating monthly report for {username} - {month}/{year}")
            
            # Extract data from Notion
            df = self.data_extractor.get_user_monthly_data(year, month, username)
            stats = self.data_extractor.get_monthly_stats(year, month, username)
            
            if df.empty or stats.get('days_tracked', 0) == 0:
                print(f"⚠️ No data found for {username} in {month}/{year}")
                return {
                    'success': False,
                    'message': f'Keine Kaloriendaten für {username} im {self._get_month_name(month)} {year} gefunden.',
                    'stats': stats
                }
            
            # Generate chart
            chart_filename = f"calorie_report_{username}_{year}_{month:02d}.png"
            chart_path = os.path.join(os.path.dirname(__file__), 'reports', chart_filename)
            
            # Create reports directory if it doesn't exist
            os.makedirs(os.path.dirname(chart_path), exist_ok=True)
            
            chart_success = self.chart_generator.create_monthly_chart(df, stats, chart_path)
            
            if not chart_success:
                return {
                    'success': False,
                    'message': 'Fehler beim Erstellen des Diagramms.',
                    'stats': stats
                }
            
            return {
                'success': True,
                'stats': stats,
                'chart_path': chart_path,
                'chart_filename': chart_filename,
                'data_points': len(df)
            }
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return {
                'success': False,
                'message': f'Fehler beim Erstellen des Berichts: {str(e)}',
                'stats': {}
            }
    
    def create_report_embed(self, report_data: Dict[str, Any]) -> discord.Embed:
        """
        Create a Discord embed for the monthly report
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            Discord embed object
        """
        try:
            if not report_data.get('success', False):
                # Error embed
                embed = discord.Embed(
                    title="❌ Monatsbericht - Fehler",
                    description=report_data.get('message', 'Unbekannter Fehler'),
                    color=discord.Color.red()
                )
                return embed
            
            stats = report_data['stats']
            
            # Success embed
            embed = discord.Embed(
                title=f"📊 Monatsbericht - {stats['username']}",
                description=f"**{self._get_month_name(stats['month'])} {stats['year']}**",
                color=discord.Color.green()
            )
            
            # Main statistics
            embed.add_field(
                name="🔥 Gesamtkalorien",
                value=f"**{stats['total_calories']:,} kcal**",
                inline=True
            )
            
            embed.add_field(
                name="📈 Durchschnitt/Tag",
                value=f"**{stats['average_daily']} kcal**",
                inline=True
            )
            
            embed.add_field(
                name="📅 Getrackte Tage",
                value=f"**{stats['days_tracked']} Tage**",
                inline=True
            )
            
            embed.add_field(
                name="⚡ Höchster Tag",
                value=f"**{stats['max_daily']} kcal**",
                inline=True
            )
            
            embed.add_field(
                name="🔻 Niedrigster Tag", 
                value=f"**{stats['min_daily']} kcal**",
                inline=True
            )
            
            embed.add_field(
                name="📊 Datenpunkte",
                value=f"**{report_data['data_points']}**",
                inline=True
            )
            
            # Add motivational message
            motivation = self._get_motivational_message(stats)
            embed.add_field(
                name="💪 Deine Bilanz",
                value=motivation,
                inline=False
            )
            
            # Footer
            embed.set_footer(
                text=f"🤖 Automatisch generiert am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr"
            )
            
            return embed
            
        except Exception as e:
            print(f"❌ Error creating embed: {e}")
            error_embed = discord.Embed(
                title="❌ Fehler beim Erstellen der Nachricht",
                description=f"Unerwarteter Fehler: {str(e)}",
                color=discord.Color.red()
            )
            return error_embed
    
    def _get_motivational_message(self, stats: Dict[str, Any]) -> str:
        """Generate a motivational message based on stats"""
        try:
            days_tracked = stats.get('days_tracked', 0)
            avg_daily = stats.get('average_daily', 0)
            
            # Personalized messages based on performance
            if days_tracked >= 25:
                consistency = "🌟 Ausgezeichnete Konsistenz! Du hast fast jeden Tag getrackt."
            elif days_tracked >= 20:
                consistency = "👍 Sehr gute Konsistenz beim Tracking!"
            elif days_tracked >= 15:
                consistency = "📈 Gute Tracking-Gewohnheit entwickelt!"
            else:
                consistency = "💡 Tipp: Versuche öfter zu tracken für bessere Einblicke."
            
            if 1800 <= avg_daily <= 2200:
                calorie_feedback = "⚖️ Deine Kalorienzufuhr liegt in einem ausgewogenen Bereich."
            elif avg_daily > 2500:
                calorie_feedback = "🔥 Hohe Kalorienzufuhr - perfekt wenn du aktiv bist!"
            elif avg_daily < 1500:
                calorie_feedback = "🍎 Niedrige Kalorienzufuhr - achte auf ausreichende Nährstoffe."
            else:
                calorie_feedback = "📊 Solide Kalorienbilanz für den Monat!"
            
            return f"{consistency}\n{calorie_feedback}"
            
        except Exception:
            return "🎯 Weiter so beim Kalorie-Tracking!"
    
    async def send_monthly_report(self, year: int, month: int, username: str) -> bool:
        """
        Generate and send monthly report for a specific user
        
        Args:
            year: Target year
            month: Target month
            username: Username to send report to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📤 Sending monthly report for {username}")
            
            # Generate report
            report_data = await self.generate_monthly_report(year, month, username)
            
            # Create embed
            embed = self.create_report_embed(report_data)
            
            # Get channel
            channel = self.bot.get_channel(CALORIES_CHANNEL_ID)
            if not channel:
                print(f"❌ Could not find channel with ID {CALORIES_CHANNEL_ID}")
                return False
            
            # Send message
            if report_data.get('success', False):
                # Send with chart attachment
                chart_file = discord.File(report_data['chart_path'], 
                                        filename=report_data['chart_filename'])
                await channel.send(embed=embed, file=chart_file)
                
                # Clean up chart file
                try:
                    os.remove(report_data['chart_path'])
                    print(f"🧹 Cleaned up chart file: {report_data['chart_path']}")
                except OSError:
                    pass
            else:
                # Send error message only
                await channel.send(embed=embed)
            
            print(f"✅ Monthly report sent for {username}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending report: {e}")
            return False
    
    async def send_all_monthly_reports(self, year: int, month: int) -> Dict[str, Any]:
        """
        Send monthly reports for all users with data
        
        Args:
            year: Target year
            month: Target month
            
        Returns:
            Dictionary with results summary
        """
        try:
            print(f"📊 Generating monthly reports for all users - {month}/{year}")
            
            # Get all users with data for the month
            users = self.data_extractor.get_all_users(year, month)
            
            if not users:
                print(f"⚠️ No users found with data for {month}/{year}")
                return {
                    'success': False,
                    'message': f'Keine Benutzer mit Daten für {month}/{year} gefunden.',
                    'reports_sent': 0,
                    'users': []
                }
            
            print(f"👥 Found {len(users)} users: {users}")
            
            # Send reports for each user
            results = {
                'success': True,
                'total_users': len(users),
                'reports_sent': 0,
                'failed_reports': 0,
                'users': users,
                'details': []
            }
            
            for username in users:
                try:
                    success = await self.send_monthly_report(year, month, username)
                    if success:
                        results['reports_sent'] += 1
                        results['details'].append(f"✅ {username}: Erfolgreich gesendet")
                    else:
                        results['failed_reports'] += 1
                        results['details'].append(f"❌ {username}: Fehler beim Senden")
                        
                    # Small delay between reports
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    results['failed_reports'] += 1
                    results['details'].append(f"❌ {username}: {str(e)}")
                    print(f"❌ Error sending report for {username}: {e}")
            
            # Summary message
            channel = self.bot.get_channel(CALORIES_CHANNEL_ID)
            if channel:
                summary_embed = discord.Embed(
                    title="📋 Monatsbericht - Zusammenfassung",
                    description=f"**{self._get_month_name(month)} {year}**",
                    color=discord.Color.blue()
                )
                
                summary_embed.add_field(
                    name="📊 Berichte versendet",
                    value=f"{results['reports_sent']}/{results['total_users']}",
                    inline=True
                )
                
                summary_embed.add_field(
                    name="👥 Benutzer",
                    value=", ".join(users),
                    inline=False
                )
                
                await channel.send(embed=summary_embed)
            
            return results
            
        except Exception as e:
            print(f"❌ Error sending all reports: {e}")
            return {
                'success': False,
                'message': f'Fehler beim Senden der Berichte: {str(e)}',
                'reports_sent': 0,
                'users': []
            }
    
    def _get_month_name(self, month: int) -> str:
        """Get German month name"""
        month_names = {
            1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
            5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
        }
        return month_names.get(month, f'Monat {month}')
    
    async def run_bot(self):
        """Run the Discord bot"""
        try:
            await self.bot.start(DISCORD_TOKEN)
        except Exception as e:
            print(f"❌ Error running bot: {e}")

# Command-line interface for testing
async def test_monthly_report():
    """Test function for monthly report generation"""
    try:
        generator = MonthlyReportGenerator()
        
        # Test with current month - 1 (previous month)
        now = datetime.now()
        if now.month == 1:
            test_year = now.year - 1
            test_month = 12
        else:
            test_year = now.year
            test_month = now.month - 1
        
        print(f"\n🧪 Testing monthly report generation for {test_month}/{test_year}")
        
        # Get users for testing
        users = generator.data_extractor.get_all_users(test_year, test_month)
        if users:
            test_user = users[0]  # Test with first user
            print(f"👤 Testing with user: {test_user}")
            
            # Generate report (without Discord)
            report_data = await generator.generate_monthly_report(test_year, test_month, test_user)
            print(f"📊 Report result: {report_data}")
            
            if report_data.get('success'):
                print("✅ Monthly report generation successful!")
            else:
                print("❌ Monthly report generation failed")
        else:
            print("⚠️ No users found for testing")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_monthly_report()) 