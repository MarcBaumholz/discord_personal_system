import logging
import discord
import datetime
import matplotlib.pyplot as plt
import io
import os
from dotenv import load_dotenv
import openai

# Setup logging
logger = logging.getLogger("sleep_tracker")

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class SleepTracker:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        self.optimal_sleep = 8.0  # Default optimal sleep hours
        logger.info("Sleep tracker initialized")
    
    async def track_sleep(self, ctx, hours):
        """Track sleep hours and update Notion database"""
        if hours <= 0 or hours > 24:
            await ctx.send("❌ Bitte gib eine gültige Schlafstundenzahl zwischen 0 und 24 an.")
            return
        
        try:
            # Get current date for yesterday (assuming sleep is logged in the morning for previous night)
            today = datetime.datetime.now().date()
            
            # Add sleep entry to Notion database
            daily_entry = self.notion_manager.get_or_create_daily_entry(today)
            
            # Update the database
            result = self.notion_manager.update_daily_entry(daily_entry["id"], {"sleepHours": hours})
            
            if not result:
                await ctx.send("❌ Es ist ein Fehler beim Speichern aufgetreten. Bitte versuche es später erneut.")
                return
            
            # Evaluate sleep quality and provide feedback
            emoji, message = self._evaluate_sleep_quality(hours)
            
            # Send confirmation message with evaluation
            await ctx.send(f"{emoji} {hours} Schlafstunden getrackt!\n{message}")
            
            # Periodically show sleep pattern
            if ctx.message.content.lower().endswith("--show"):
                await self.generate_sleep_chart(ctx)
        
        except Exception as e:
            logger.error(f"Error tracking sleep: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler beim Tracking aufgetreten. Bitte versuche es später erneut.")
    
    def _evaluate_sleep_quality(self, hours):
        """Evaluate sleep quality and return emoji and message"""
        if hours < 6:
            return "😴", "Das ist weniger als empfohlen. Probiere heute früher ins Bett zu gehen."
        elif 6 <= hours < 7:
            return "🙂", "Das ist okay, aber etwas mehr Schlaf könnte dir gut tun."
        elif 7 <= hours <= 9:
            return "😊", "Perfekt! Das ist die empfohlene Schlafmenge für Erwachsene."
        else:
            return "🛌", "Das ist mehr als die durchschnittliche Empfehlung. Fühlst du dich ausgeruht?"
    
    async def generate_sleep_chart(self, ctx):
        """Generate and send a chart of weekly sleep patterns"""
        try:
            # Get sleep data for the last 10 days
            sleep_data = self._get_sleep_data(days=10)
            
            if not sleep_data or len(sleep_data) < 3:  # Need at least 3 days of data
                await ctx.send("⚠️ Es sind nicht genügend Daten für ein Schlafdiagramm vorhanden. Tracke deinen Schlaf für einige Tage.")
                return
            
            # Create the chart
            fig, ax = plt.subplots(figsize=(10, 6))
            dates = list(sleep_data.keys())
            hours = list(sleep_data.values())
            
            ax.plot(dates, hours, marker='o', linestyle='-', color='purple', linewidth=2)
            ax.axhline(y=self.optimal_sleep, color='g', linestyle='--', label=f'Optimal: {self.optimal_sleep}h')
            
            # Fill between optimal range (7-9 hours)
            ax.axhspan(7, 9, alpha=0.2, color='green', label='Empfohlener Bereich')
            
            ax.set_title('Schlafmuster der letzten Tage')
            ax.set_xlabel('Datum')
            ax.set_ylabel('Schlafstunden')
            ax.set_ylim(0, max(max(hours) * 1.1, 10))
            ax.legend()
            
            # Rotate date labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart to buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            
            # Send chart to Discord
            await ctx.send("📊 Hier ist dein Schlafmuster der letzten Tage:", 
                          file=discord.File(buf, 'sleep_chart.png'))
            
            # If enough data is available, also provide sleep analysis
            if len(sleep_data) >= 5:
                await self.provide_sleep_analysis(ctx, sleep_data)
            
            plt.close(fig)  # Close the figure to free memory
            
        except Exception as e:
            logger.error(f"Error generating sleep chart: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler beim Erstellen des Diagramms aufgetreten.")
    
    async def provide_sleep_analysis(self, ctx, sleep_data):
        """Provide AI-generated analysis of sleep patterns"""
        try:
            # Calculate metrics
            avg_sleep = sum(sleep_data.values()) / len(sleep_data)
            variance = sum((hrs - avg_sleep) ** 2 for hrs in sleep_data.values()) / len(sleep_data)
            consistency = "hoch" if variance < 1 else "mittel" if variance < 2 else "niedrig"
            
            trend = "stabil"
            if len(sleep_data) >= 5:
                recent = list(sleep_data.values())[-3:]
                earlier = list(sleep_data.values())[:-3]
                if sum(recent)/len(recent) > sum(earlier)/len(earlier) + 0.5:
                    trend = "steigend"
                elif sum(recent)/len(recent) < sum(earlier)/len(earlier) - 0.5:
                    trend = "fallend"
            
            # Create a prompt for OpenAI
            prompt = f"""
            Analysiere folgende Schlafdaten einer Person:
            
            Durchschnittliche Schlafstunden: {avg_sleep:.1f} Stunden/Tag
            Konsistenz des Schlafrhythmus: {consistency} (Varianz: {variance:.1f})
            Trend der letzten Tage: {trend}
            
            Erstelle eine kurze, freundliche Analyse (maximal 3 Sätze) mit 1-2 konkreten, 
            personalisierten Tipps zur Verbesserung der Schlafqualität.
            Verwende einen motivierenden, aber nicht belehrenden Ton.
            """
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            analysis = response.choices[0].text.strip()
            await ctx.send(f"💤 **Schlafanalyse:**\n\n{analysis}")
            
        except Exception as e:
            logger.error(f"Error generating sleep analysis: {str(e)}")
            # Silently fail, as this is a supplementary feature
    
    def _get_sleep_data(self, days=7):
        """Get sleep data for the specified number of days"""
        try:
            # Calculate date range
            end_date = datetime.datetime.now().date()
            start_date = end_date - datetime.timedelta(days=days-1)
            
            # Query Notion for entries in date range
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
            
            # Extract sleep data
            sleep_data = {}
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
                    if sleep_hours > 0:  # Only include days with tracked sleep
                        sleep_data[display_date] = sleep_hours
            
            return sleep_data
            
        except Exception as e:
            logger.error(f"Error getting sleep data: {str(e)}")
            return {} 