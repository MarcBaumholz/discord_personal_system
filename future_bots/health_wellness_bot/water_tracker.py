import datetime
import discord
from discord.ext import commands
import logging
import matplotlib.pyplot as plt
import io
import os
from dotenv import load_dotenv
import openai

# Setup logging
logger = logging.getLogger("water_tracker")

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class WaterTracker:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        self.daily_goal = 2500  # Default daily water goal in ml
        self.user_goals = {}  # Store user-specific goals
        logger.info("Water tracker initialized")
    
    async def track_water(self, ctx, amount):
        """Track water consumption and update Notion database"""
        if amount <= 0:
            await ctx.send("❌ Bitte gib eine positive Wassermenge an.")
            return
        
        try:
            # Get current date
            today = datetime.datetime.now().date()
            
            # Add water entry to Notion database
            daily_entry = self.notion_manager.get_or_create_daily_entry(today)
            current_water = daily_entry.get("waterAmount", 0)
            updated_water = current_water + amount
            
            # Update the database
            self.notion_manager.update_daily_entry(daily_entry["id"], {"waterAmount": updated_water})
            
            # Calculate progress towards goal
            user_goal = self.user_goals.get(ctx.author.id, self.daily_goal)
            progress = min(100, int((updated_water / user_goal) * 100))
            
            # Create progress bar
            progress_bar = self._create_progress_bar(progress)
            
            # Send confirmation message with progress
            await ctx.send(f"💧 {amount}ml Wasser getrackt! Tageskonsum: {updated_water}ml\n"
                         f"Tagesziel ({user_goal}ml): {progress_bar} {progress}%")
            
            # If reached 100% of goal, send congratulations
            if progress == 100 and current_water < user_goal:
                await ctx.send(f"🎉 Glückwunsch {ctx.author.mention}! Du hast dein tägliches Wasserziel erreicht!")
            
            # If significant progress (> 75%), generate visualization occasionally
            if progress > 75 and updated_water >= 2000:
                await self.generate_weekly_chart(ctx)
        
        except Exception as e:
            logger.error(f"Error tracking water: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler beim Tracking aufgetreten. Bitte versuche es später erneut.")
    
    def _create_progress_bar(self, percentage, length=10):
        """Create a text-based progress bar"""
        filled_length = int(length * percentage / 100)
        bar = '🟦' * filled_length + '⬜' * (length - filled_length)
        return bar
    
    async def set_water_goal(self, ctx, goal):
        """Set a personalized water consumption goal"""
        if goal < 500 or goal > 5000:
            await ctx.send("❌ Bitte wähle ein Ziel zwischen 500ml und 5000ml.")
            return
        
        self.user_goals[ctx.author.id] = goal
        await ctx.send(f"🎯 Dein tägliches Wasserziel wurde auf {goal}ml gesetzt!")
    
    async def get_personalized_recommendation(self, ctx):
        """Generate a personalized water recommendation using OpenAI"""
        try:
            # Get user data from Notion
            user_data = self.notion_manager.get_user_health_data(days=7)
            
            if not user_data:
                await ctx.send("Es sind nicht genügend Daten für eine personalisierte Empfehlung vorhanden.")
                return
            
            # Create a prompt for OpenAI
            prompt = f"""
            Basierend auf folgenden Gesundheitsdaten der letzten 7 Tage:
            
            Wasserdurchschnitt: {user_data.get('avg_water', 0)}ml/Tag
            Schlafstunden: {user_data.get('avg_sleep', 0)} Stunden/Tag
            Aktivitätsgrad: {user_data.get('activity_level', 'Mittel')}
            
            Erstelle bitte eine kurze, freundliche Empfehlung für die optimale tägliche Wassermenge und 2-3 Tipps, 
            wie man mehr Wasser trinken kann. Halte es unter 100 Wörtern und verwende einen motivierenden Ton.
            """
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            recommendation = response.choices[0].text.strip()
            await ctx.send(f"💧 **Personalisierte Wasserempfehlung:**\n\n{recommendation}")
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            await ctx.send("Ich konnte keine personalisierte Empfehlung erstellen. Bitte versuche es später erneut.")
    
    async def generate_weekly_chart(self, ctx):
        """Generate and send a chart of weekly water consumption"""
        try:
            # Get water data for the last 7 days
            water_data = self.notion_manager.get_water_data(days=7)
            
            if not water_data or len(water_data) < 3:  # Need at least 3 days of data
                return  # Silently return if not enough data
            
            # Create the chart
            fig, ax = plt.subplots(figsize=(10, 6))
            dates = list(water_data.keys())
            amounts = list(water_data.values())
            
            ax.bar(dates, amounts, color='royalblue')
            ax.axhline(y=self.daily_goal, color='r', linestyle='-', label=f'Ziel: {self.daily_goal}ml')
            
            ax.set_title('Wöchentlicher Wasserkonsum')
            ax.set_xlabel('Datum')
            ax.set_ylabel('Menge (ml)')
            ax.set_ylim(0, max(max(amounts) * 1.1, self.daily_goal * 1.1))
            ax.legend()
            
            # Rotate date labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart to buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            
            # Send chart to Discord
            await ctx.send("📊 Hier ist dein wöchentlicher Wasserkonsum:", 
                          file=discord.File(buf, 'water_chart.png'))
            
            plt.close(fig)  # Close the figure to free memory
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            # No need to notify user of this error 