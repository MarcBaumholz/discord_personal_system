import logging
import discord
import datetime
import matplotlib.pyplot as plt
import io
import os
from dotenv import load_dotenv
import openai

# Setup logging
logger = logging.getLogger("report_generator")

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class ReportGenerator:
    def __init__(self, notion_manager):
        self.notion_manager = notion_manager
        logger.info("Report generator initialized")
    
    async def generate_report(self, ctx, timeframe):
        """Generate a health report for the specified timeframe"""
        try:
            # Determine time range based on timeframe
            if timeframe == "daily":
                days = 1
                title = "Tagesbericht"
            elif timeframe == "weekly":
                days = 7
                title = "Wochenbericht"
            elif timeframe == "monthly":
                days = 30
                title = "Monatsbericht"
            else:
                await ctx.send("❌ Ungültiger Zeitraum. Bitte wähle 'daily', 'weekly' oder 'monthly'.")
                return
            
            # Fetch data from Notion
            health_data = self.notion_manager.get_user_health_data(days=days)
            
            if not health_data or health_data.get("days_tracked", 0) < 1:
                await ctx.send("❌ Nicht genügend Daten für einen Bericht verfügbar.")
                return
            
            # Create the report
            embed = await self._create_report_embed(health_data, title, days)
            
            # Generate chart if weekly or monthly report
            if timeframe in ["weekly", "monthly"]:
                chart = await self._create_health_chart(days)
                
                if chart:
                    await ctx.send(embed=embed, file=chart)
                else:
                    await ctx.send(embed=embed)
            else:
                await ctx.send(embed=embed)
            
            # Add AI insights for weekly and monthly reports
            if timeframe in ["weekly", "monthly"] and health_data.get("days_tracked", 0) >= 3:
                await self._send_ai_insights(ctx, health_data, timeframe)
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler beim Erstellen des Berichts aufgetreten.")
    
    async def _create_report_embed(self, health_data, title, days):
        """Create a Discord embed with health report data"""
        # Create embed
        embed = discord.Embed(
            title=f"🌱 {title} - Gesundheit & Wohlbefinden",
            description=f"Übersicht der letzten {days} Tage",
            color=0x2ecc71
        )
        
        # Add tracked days info
        days_tracked = health_data.get("days_tracked", 0)
        tracking_rate = (days_tracked / days) * 100
        embed.add_field(
            name="📊 Tracking",
            value=f"{days_tracked}/{days} Tagen getrackt ({tracking_rate:.0f}%)",
            inline=False
        )
        
        # Add water consumption
        avg_water = health_data.get("avg_water", 0)
        embed.add_field(
            name="💧 Wasserkonsum",
            value=f"Ø {avg_water}ml pro Tag",
            inline=True
        )
        
        # Add sleep data
        avg_sleep = health_data.get("avg_sleep", 0)
        sleep_emoji = "😴" if avg_sleep >= 7 else "😐" if avg_sleep >= 6 else "😟"
        embed.add_field(
            name="🛌 Schlaf",
            value=f"Ø {avg_sleep:.1f} Stunden {sleep_emoji}",
            inline=True
        )
        
        # Add mood data
        avg_mood = health_data.get("avg_mood", 0)
        mood_emoji = "😊" if avg_mood >= 7 else "🙂" if avg_mood >= 5 else "😕"
        embed.add_field(
            name="🧠 Stimmung",
            value=f"Ø {avg_mood:.1f}/10 {mood_emoji}",
            inline=True
        )
        
        # Add meditation data
        avg_meditation = health_data.get("avg_meditation", 0)
        embed.add_field(
            name="🧘 Meditation",
            value=f"Ø {avg_meditation:.1f} Minuten/Tag",
            inline=True
        )
        
        # Add activity level
        activity_level = health_data.get("activity_level", "Mittel")
        activity_emoji = "🏃" if activity_level == "Hoch" else "🚶" if activity_level == "Mittel" else "🧍"
        embed.add_field(
            name="🏃 Aktivität",
            value=f"{activity_emoji} {activity_level}",
            inline=True
        )
        
        # Set footer
        embed.set_footer(text=f"Generiert am {datetime.datetime.now().strftime('%d.%m.%Y um %H:%M')}")
        
        return embed
    
    async def _create_health_chart(self, days):
        """Create a combined chart of health metrics over time"""
        try:
            # Get data for charts
            water_data = self.notion_manager.get_water_data(days=days)
            
            if not water_data or len(water_data) < 3:
                return None
            
            # Create the chart
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
            
            # Plot water data
            dates = list(water_data.keys())
            water_values = list(water_data.values())
            
            ax1.bar(dates, water_values, color='royalblue', alpha=0.7)
            ax1.set_title('Wasserkonsum')
            ax1.set_ylabel('Menge (ml)')
            ax1.axhline(y=2500, color='navy', linestyle='--', alpha=0.5, label='Ziel: 2500ml')
            ax1.legend()
            
            # Try to get sleep and mood data
            try:
                # Get sleep data
                sleep_data = {}
                mood_data = {}
                
                # Query Notion for entries in date range
                end_date = datetime.datetime.now().date()
                start_date = end_date - datetime.timedelta(days=days-1)
                
                query_params = {
                    "database_id": self.notion_manager.health_db_id,
                    "filter": {
                        "and": [
                            {
                                "property": "Datum",
                                "date": {
                                    "on_or_after": start_date.strftime("%Y-%m-%d")
                                }
                            },
                            {
                                "property": "Datum",
                                "date": {
                                    "on_or_before": end_date.strftime("%Y-%m-%d")
                                }
                            }
                        ]
                    },
                    "sorts": [
                        {
                            "property": "Datum",
                            "direction": "ascending"
                        }
                    ]
                }
                
                response = self.notion_manager.client.databases.query(**query_params)
                results = response.get("results", [])
                
                # Extract data
                for entry in results:
                    properties = entry.get("properties", {})
                    date_prop = properties.get("Datum", {}).get("date", {})
                    
                    if date_prop and date_prop.get("start"):
                        date_str = date_prop.get("start")
                        # Format the date for display
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                        display_date = date_obj.strftime("%d.%m")
                        
                        # Get sleep hours
                        sleep_hours = self.notion_manager._extract_number_property(properties, "Schlafstunden")
                        if sleep_hours > 0:
                            sleep_data[display_date] = sleep_hours
                        
                        # Get mood rating
                        mood_rating = self.notion_manager._extract_number_property(properties, "Stimmungswert")
                        if mood_rating > 0:
                            mood_data[display_date] = mood_rating
                
                # Plot sleep and mood on shared axis
                ax2.plot(dates, [sleep_data.get(date, 0) for date in dates], marker='o', color='purple', label='Schlaf (Std)')
                ax2.plot(dates, [mood_data.get(date, 0) for date in dates], marker='s', color='orange', label='Stimmung (1-10)')
                ax2.set_title('Schlaf & Stimmung')
                ax2.set_ylabel('Wert')
                ax2.set_ylim(0, 10.5)
                ax2.legend()
                
            except Exception as e:
                logger.error(f"Error getting sleep/mood data: {str(e)}")
                # If error, just continue with water chart
            
            # Format x-axis
            plt.xticks(rotation=45)
            plt.xlabel('Datum')
            plt.tight_layout()
            
            # Save chart to buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            
            # Create Discord file object
            chart = discord.File(buf, 'health_chart.png')
            plt.close(fig)
            
            return chart
            
        except Exception as e:
            logger.error(f"Error creating health chart: {str(e)}")
            return None
    
    async def _send_ai_insights(self, ctx, health_data, timeframe):
        """Generate and send AI insights based on health data"""
        try:
            # Create a prompt for OpenAI
            prompt = f"""
            Analysiere folgende Gesundheitsdaten einer Person über {timeframe}:
            
            Wasserdurchschnitt: {health_data.get('avg_water', 0)}ml/Tag
            Schlafstunden: {health_data.get('avg_sleep', 0)} Stunden/Tag
            Stimmungswert: {health_data.get('avg_mood', 0)}/10
            Meditationsminuten: {health_data.get('avg_meditation', 0)} Min/Tag
            Aktivitätslevel: {health_data.get('activity_level', 'Mittel')}
            
            Erstelle eine kurze, personalisierte Gesundheitsanalyse (max. 3 Sätze) mit 1-2 
            umsetzbare Verbesserungsvorschläge basierend auf diesen Daten.
            Verbinde Schlaf, Stimmung und andere Faktoren in deiner Analyse, wenn möglich.
            Verwende einen motivierenden, positiven Ton.
            """
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=200,
                temperature=0.7
            )
            
            insights = response.choices[0].text.strip()
            
            # Send the insights as a follow-up message
            await ctx.send(f"✨ **KI Analyse:**\n\n{insights}")
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            # Silently fail as this is a supplementary feature 