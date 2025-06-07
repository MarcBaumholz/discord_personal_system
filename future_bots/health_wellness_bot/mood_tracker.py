import logging
import discord
import datetime
import matplotlib.pyplot as plt
import io
import os
import random
from dotenv import load_dotenv
import openai

# Setup logging
logger = logging.getLogger("mood_tracker")

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class MoodTracker:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        self.mood_emojis = {
            1: "😞", 2: "😔", 3: "😕", 4: "😐", 5: "🙂",
            6: "😊", 7: "😄", 8: "😁", 9: "🤩", 10: "🥳"
        }
        self.mood_descriptions = {
            "low": ["sehr schlecht", "niedergeschlagen", "traurig", "erschöpft"],
            "medium": ["okay", "neutral", "mittelmäßig", "gemischt"],
            "high": ["gut", "fröhlich", "energiegeladen", "ausgezeichnet"]
        }
        logger.info("Mood tracker initialized")
    
    async def track_mood(self, ctx, rating):
        """Track mood rating and update Notion database"""
        if rating < 1 or rating > 10:
            await ctx.send("❌ Bitte bewerte deine Stimmung auf einer Skala von 1-10.")
            return
        
        try:
            # Get current date
            today = datetime.datetime.now().date()
            
            # Add mood entry to Notion database
            daily_entry = self.notion_manager.get_or_create_daily_entry(today)
            
            # Update the database
            result = self.notion_manager.update_daily_entry(daily_entry["id"], {"moodRating": rating})
            
            if not result:
                await ctx.send("❌ Es ist ein Fehler beim Speichern aufgetreten. Bitte versuche es später erneut.")
                return
            
            # Get emoji for the mood
            emoji = self.mood_emojis.get(rating, "😐")
            
            # Send confirmation message
            await ctx.send(f"{emoji} Stimmung getrackt: {rating}/10")
            
            # Offer encouragement or suggestions based on mood
            await self._provide_mood_response(ctx, rating)
            
            # Periodically show mood pattern
            if ctx.message.content.lower().endswith("--show"):
                await self.generate_mood_chart(ctx)
        
        except Exception as e:
            logger.error(f"Error tracking mood: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler beim Tracking aufgetreten. Bitte versuche es später erneut.")
    
    async def _provide_mood_response(self, ctx, rating):
        """Provide an appropriate response based on the mood rating"""
        try:
            if rating <= 3:
                # Low mood - offer support
                response = await self._generate_mood_suggestion(ctx, "low", rating)
                await ctx.send(f"Tut mir leid, dass du dich nicht so gut fühlst. {response}")
            
            elif rating <= 6:
                # Medium mood - neutral response
                if random.random() < 0.5:  # Only respond sometimes for neutral moods
                    response = await self._generate_mood_suggestion(ctx, "medium", rating)
                    await ctx.send(response)
            
            elif rating >= 8:
                # High mood - positive reinforcement
                await ctx.send(f"Toll! Freut mich, dass du dich so gut fühlst! 🎉")
        
        except Exception as e:
            logger.error(f"Error providing mood response: {str(e)}")
            # Silently fail as this is a supplementary feature
    
    async def _generate_mood_suggestion(self, ctx, mood_category, rating):
        """Generate a personalized mood suggestion using OpenAI"""
        try:
            mood_term = random.choice(self.mood_descriptions[mood_category])
            
            # Get user data for more personalized suggestions
            user_data = self.notion_manager.get_user_health_data(days=5)
            
            # Check for existing patterns
            sleep_info = f"Du hast in letzter Zeit durchschnittlich {user_data.get('avg_sleep', 0)} Stunden geschlafen." if user_data else ""
            
            # Create a prompt for OpenAI
            prompt = f"""
            Die Person fühlt sich heute {mood_term} (Bewertung: {rating}/10).
            {sleep_info}
            
            Erstelle einen kurzen, freundlichen und empathischen Vorschlag (maximal 2 Sätze), 
            wie die Person ihre Stimmung verbessern oder aufrechterhalten könnte.
            Sei konkret und gib einen praktischen Tipp, der sofort umsetzbar ist.
            Vermeide Klischees und verwende keine Fragen.
            """
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=100,
                temperature=0.7
            )
            
            suggestion = response.choices[0].text.strip()
            return suggestion
            
        except Exception as e:
            logger.error(f"Error generating mood suggestion: {str(e)}")
            
            # Fallback suggestions if API fails
            if mood_category == "low":
                fallbacks = [
                    "Vielleicht hilft dir ein kurzer Spaziergang an der frischen Luft.",
                    "Wie wäre es mit einer kurzen Meditation oder ein paar tiefen Atemzügen?",
                    "Manchmal kann Musik die Stimmung heben - wie wäre es mit deinem Lieblingssong?"
                ]
            elif mood_category == "medium":
                fallbacks = [
                    "Wie wäre es mit einer kleinen Pause und einer Tasse Tee?",
                    "Ein kurzer Moment der Dankbarkeit kann die Stimmung heben.",
                    "Du machst das gut - denk daran, kleine Erfolge zu feiern."
                ]
            else:
                fallbacks = [
                    "Mach weiter so!",
                    "Denk daran, dir Zeit für dich zu nehmen.",
                    "Teile deine positive Energie mit anderen!"
                ]
                
            return random.choice(fallbacks)
    
    async def generate_mood_chart(self, ctx):
        """Generate and send a chart of weekly mood patterns"""
        try:
            # Get mood data for the last 7 days
            mood_data = self._get_mood_data(days=7)
            
            if not mood_data or len(mood_data) < 3:  # Need at least 3 days of data
                await ctx.send("⚠️ Es sind nicht genügend Daten für ein Stimmungsdiagramm vorhanden. Tracke deine Stimmung für einige Tage.")
                return
            
            # Create the chart
            fig, ax = plt.subplots(figsize=(10, 6))
            dates = list(mood_data.keys())
            ratings = list(mood_data.values())
            
            # Create color gradient based on mood values
            colors = [self._get_mood_color(rating) for rating in ratings]
            
            ax.bar(dates, ratings, color=colors)
            
            # Add reference lines
            ax.axhline(y=3, color='r', linestyle='--', alpha=0.3, label='Niedrig')
            ax.axhline(y=7, color='g', linestyle='--', alpha=0.3, label='Hoch')
            
            ax.set_title('Stimmungsverlauf der letzten Tage')
            ax.set_xlabel('Datum')
            ax.set_ylabel('Stimmungswert (1-10)')
            ax.set_ylim(0, 10.5)
            ax.set_yticks(range(1, 11))
            ax.legend()
            
            # Add mood emojis as labels
            for i, rating in enumerate(ratings):
                ax.text(i, rating + 0.3, self.mood_emojis.get(rating, ""), ha='center', va='bottom', fontsize=12)
            
            # Rotate date labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart to buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            
            # Send chart to Discord
            await ctx.send("📊 Hier ist dein Stimmungsverlauf der letzten Tage:", 
                          file=discord.File(buf, 'mood_chart.png'))
            
            # If enough data is available, also provide mood analysis
            if len(mood_data) >= 5:
                await self.provide_mood_analysis(ctx, mood_data)
            
            plt.close(fig)  # Close the figure to free memory
            
        except Exception as e:
            logger.error(f"Error generating mood chart: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler beim Erstellen des Diagramms aufgetreten.")
    
    def _get_mood_color(self, rating):
        """Get a color on a gradient from red (1) to green (10) based on mood rating"""
        if rating <= 3:
            # Red to orange
            r = 1.0
            g = 0.3 * rating / 3
            b = 0
        elif rating <= 7:
            # Orange to yellow
            r = 1.0
            g = 0.3 + 0.7 * (rating - 3) / 4
            b = 0
        else:
            # Yellow to green
            r = 1.0 - 0.8 * (rating - 7) / 3
            g = 1.0
            b = 0
        
        return (r, g, b)
    
    async def provide_mood_analysis(self, ctx, mood_data):
        """Provide AI-generated analysis of mood patterns"""
        try:
            # Calculate metrics
            avg_mood = sum(mood_data.values()) / len(mood_data)
            variance = sum((m - avg_mood) ** 2 for m in mood_data.values()) / len(mood_data)
            stability = "stabil" if variance < 2 else "wechselhaft" if variance < 4 else "stark schwankend"
            
            trend = "gleichbleibend"
            if len(mood_data) >= 5:
                recent = list(mood_data.values())[-3:]
                earlier = list(mood_data.values())[:-3]
                if sum(recent)/len(recent) > sum(earlier)/len(earlier) + 0.5:
                    trend = "positiv"
                elif sum(recent)/len(recent) < sum(earlier)/len(earlier) - 0.5:
                    trend = "negativ"
            
            # Get additional health data for context
            health_data = self.notion_manager.get_user_health_data(days=7)
            sleep_info = f"Durchschnittliche Schlafstunden: {health_data.get('avg_sleep', 0)} Stunden/Tag" if health_data else ""
            
            # Create a prompt for OpenAI
            prompt = f"""
            Analysiere folgende Stimmungsdaten einer Person:
            
            Durchschnittliche Stimmungsbewertung: {avg_mood:.1f}/10
            Stimmungsstabilität: {stability} (Varianz: {variance:.1f})
            Trend der letzten Tage: {trend}
            {sleep_info}
            
            Erstelle eine kurze, einfühlsame Analyse (maximal 3 Sätze) mit einem konkreten, 
            personalisierten Tipp zur emotionalen Selbstpflege.
            Verwende einen verständnisvollen und unterstützenden Ton.
            """
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            analysis = response.choices[0].text.strip()
            await ctx.send(f"🧠 **Stimmungsanalyse:**\n\n{analysis}")
            
        except Exception as e:
            logger.error(f"Error generating mood analysis: {str(e)}")
            # Silently fail, as this is a supplementary feature
    
    def _get_mood_data(self, days=7):
        """Get mood data for the specified number of days"""
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
            
            # Extract mood data
            mood_data = {}
            for entry in results:
                properties = entry.get("properties", {})
                date_prop = properties.get("Datum", {}).get("date", {})
                
                if date_prop and date_prop.get("start"):
                    date_str = date_prop.get("start")
                    # Format the date for display
                    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    display_date = date_obj.strftime("%d.%m")
                    
                    # Get mood rating
                    mood_rating = self.notion_manager._extract_number_property(properties, "Stimmungswert")
                    if mood_rating > 0:  # Only include days with tracked mood
                        mood_data[display_date] = mood_rating
            
            return mood_data
            
        except Exception as e:
            logger.error(f"Error getting mood data: {str(e)}")
            return {} 