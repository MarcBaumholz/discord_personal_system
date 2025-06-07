import logging
import discord
import asyncio
import datetime
import random
import os
from dotenv import load_dotenv
import openai

# Setup logging
logger = logging.getLogger("meditation_module")

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class MeditationModule:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        self.active_sessions = {}  # Store user meditation sessions
        
        # Presets for different meditation types
        self.meditation_presets = {
            "quick": {
                "name": "Kurze Achtsamkeitsmeditation",
                "description": "Eine schnelle Meditation für zwischendurch, ideal für Anfänger.",
                "duration": 5,
                "type": "mindfulness"
            },
            "breathing": {
                "name": "Atemmeditation",
                "description": "Fokussiere dich auf deinen Atem, um Ruhe und Klarheit zu finden.",
                "duration": 10,
                "type": "breathing"
            },
            "body_scan": {
                "name": "Body Scan",
                "description": "Entspanne systematisch deinen ganzen Körper vom Kopf bis zu den Zehen.",
                "duration": 15,
                "type": "body_scan"
            },
            "gratitude": {
                "name": "Dankbarkeitsmeditation",
                "description": "Reflektiere über Dinge, für die du dankbar bist, um positive Emotionen zu kultivieren.",
                "duration": 7,
                "type": "gratitude"
            },
            "stress_relief": {
                "name": "Stressabbau",
                "description": "Spezielle Techniken zur Entspannung und zum Abbau von Anspannung.",
                "duration": 12,
                "type": "stress_relief"
            }
        }
        
        logger.info("Meditation module initialized")
    
    async def handle_meditation(self, ctx, minutes=None):
        """Handle meditation commands"""
        user_id = ctx.author.id
        
        # Check if user is already in a meditation session
        if user_id in self.active_sessions:
            await ctx.send("⚠️ Du hast bereits eine aktive Meditationssitzung. Möchtest du diese beenden? Antworte mit `ja` oder `nein`.")
            
            def check(m):
                return m.author.id == user_id and m.channel.id == ctx.channel.id and m.content.lower() in ["ja", "nein"]
            
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                if msg.content.lower() == "ja":
                    await self._end_meditation(ctx, user_id)
                else:
                    await ctx.send("Deine aktuelle Meditation wird fortgesetzt.")
                return
            except asyncio.TimeoutError:
                await ctx.send("Keine Antwort erhalten. Deine aktuelle Meditation wird fortgesetzt.")
                return
        
        # If minutes specified, start a timer
        if minutes is not None:
            if not (1 <= minutes <= 60):
                await ctx.send("❌ Bitte wähle eine Meditationsdauer zwischen 1 und 60 Minuten.")
                return
            
            await self._start_meditation_timer(ctx, minutes)
            return
        
        # Otherwise, show meditation options
        await self._show_meditation_options(ctx)
    
    async def _show_meditation_options(self, ctx):
        """Show available meditation options"""
        options_text = "🧘 **Meditationsoptionen:**\n\n"
        
        for key, preset in self.meditation_presets.items():
            options_text += f"• `!meditate {preset['duration']} {key}` - **{preset['name']}** ({preset['duration']} Min.)\n"
            options_text += f"  {preset['description']}\n\n"
        
        options_text += "Oder gib einfach `!meditate [Minuten]` ein, um einen Timer zu starten."
        
        # Get a meditation tip
        tip = await self._generate_meditation_tip()
        if tip:
            options_text += f"\n\n**Tipp des Tages:**\n{tip}"
        
        await ctx.send(options_text)
    
    async def _start_meditation_timer(self, ctx, minutes, preset_key=None):
        """Start a meditation timer"""
        user_id = ctx.author.id
        
        # Get preset if specified
        preset = None
        if preset_key and preset_key in self.meditation_presets:
            preset = self.meditation_presets[preset_key]
            meditation_type = preset['type']
            meditation_name = preset['name']
        else:
            # Default to mindfulness if no preset
            meditation_type = "mindfulness"
            meditation_name = "Meditation"
        
        # Get guided meditation text if using a preset
        guided_text = await self._get_guided_meditation(meditation_type) if preset else None
        
        # Start time for tracking
        start_time = datetime.datetime.now()
        
        # Store session info
        self.active_sessions[user_id] = {
            "start_time": start_time,
            "duration": minutes,
            "type": meditation_type
        }
        
        # Send starting message
        if guided_text:
            await ctx.send(f"🧘 **{meditation_name} ({minutes} Minuten)**\n\n{guided_text}")
            await ctx.send(f"Der Timer beginnt jetzt. Ich werde dich in {minutes} Minuten benachrichtigen.")
        else:
            await ctx.send(f"🧘 Deine {minutes}-minütige Meditation beginnt jetzt. Ich werde dich benachrichtigen, wenn die Zeit abgelaufen ist.")
        
        # Wait for the specified time
        await asyncio.sleep(minutes * 60)
        
        # Check if session still exists (wasn't manually ended)
        if user_id in self.active_sessions:
            # Calculate actual meditation time
            end_time = datetime.datetime.now()
            actual_duration = (end_time - start_time).total_seconds() / 60
            
            # Track in Notion
            await self._track_meditation(ctx, actual_duration, meditation_type)
            
            # Remove from active sessions
            del self.active_sessions[user_id]
            
            # Send completion message
            await ctx.send(f"✨ {ctx.author.mention} Deine Meditation ist abgeschlossen. Ich hoffe, du fühlst dich erfrischt und zentriert!")
            
            # Send a post-meditation reflection prompt
            await self._send_reflection_prompt(ctx, meditation_type)
    
    async def _end_meditation(self, ctx, user_id):
        """End an active meditation session"""
        if user_id not in self.active_sessions:
            await ctx.send("Du hast keine aktive Meditationssitzung.")
            return
        
        # Calculate actual meditation time
        session = self.active_sessions[user_id]
        end_time = datetime.datetime.now()
        actual_duration = (end_time - session["start_time"]).total_seconds() / 60
        
        # Only track if meditated for at least 1 minute
        if actual_duration >= 1:
            await self._track_meditation(ctx, actual_duration, session["type"])
            await ctx.send(f"Meditation beendet. Du hast für {actual_duration:.1f} Minuten meditiert.")
        else:
            await ctx.send("Meditation beendet. Die Sitzung war zu kurz, um getrackt zu werden.")
        
        # Remove from active sessions
        del self.active_sessions[user_id]
    
    async def _track_meditation(self, ctx, duration, meditation_type):
        """Track meditation in Notion database"""
        try:
            # Round to nearest minute
            duration_rounded = round(duration)
            
            # Get or create today's entry
            today = datetime.datetime.now().date()
            daily_entry = self.notion_manager.get_or_create_daily_entry(today)
            
            # Add existing meditation minutes if any
            current_minutes = daily_entry.get("meditationMinutes", 0)
            updated_minutes = current_minutes + duration_rounded
            
            # Update notes with meditation type
            notes = daily_entry.get("notes", "")
            time_str = datetime.datetime.now().strftime("%H:%M")
            new_note = f"{time_str}: {meditation_type} Meditation ({duration_rounded} Min.)"
            
            if notes:
                updated_notes = f"{notes}\n{new_note}"
            else:
                updated_notes = new_note
            
            # Update the database
            self.notion_manager.update_daily_entry(daily_entry["id"], {
                "meditationMinutes": updated_minutes,
                "notes": updated_notes
            })
            
            logger.info(f"Tracked meditation: {duration_rounded} minutes of {meditation_type}")
            
        except Exception as e:
            logger.error(f"Error tracking meditation: {str(e)}")
    
    async def _get_guided_meditation(self, meditation_type):
        """Get a guided meditation introduction based on the type"""
        try:
            # Create a prompt for OpenAI
            prompt = f"""
            Erstelle eine kurze Einleitung für eine geführte {meditation_type} Meditation.
            Bitte nur 3-4 Sätze, klar und beruhigend formuliert, mit einer Anleitung, 
            wie der Nutzer die Meditation beginnen soll.
            Verwende eine sanfte, anleitende Sprache ohne Floskeln.
            """
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            guided_text = response.choices[0].text.strip()
            return guided_text
            
        except Exception as e:
            logger.error(f"Error getting guided meditation: {str(e)}")
            
            # Fallback texts if API fails
            fallbacks = {
                "mindfulness": "Finde eine bequeme Sitzposition. Atme tief ein und aus. Beobachte deine Gedanken ohne zu urteilen.",
                "breathing": "Atme langsam und tief durch die Nase ein. Halte kurz den Atem an. Atme langsam durch den Mund aus.",
                "body_scan": "Beginne mit deiner Aufmerksamkeit bei den Zehen. Bewege dich langsam nach oben. Spüre jeden Teil deines Körpers.",
                "gratitude": "Denke an drei Dinge, für die du dankbar bist. Spüre die Dankbarkeit in deinem Körper. Lächle sanft.",
                "stress_relief": "Spanne jeden Muskel in deinem Körper an. Halte die Spannung für 5 Sekunden. Lasse dann alle Anspannung los."
            }
            
            return fallbacks.get(meditation_type, "Schließe deine Augen. Atme tief ein und aus. Lass alle Gedanken ziehen.")
    
    async def _generate_meditation_tip(self):
        """Generate a meditation tip of the day"""
        try:
            # Create a prompt for OpenAI
            prompt = """
            Erstelle einen kurzen, praktischen Tipp zur Verbesserung der Meditationspraxis.
            Der Tipp sollte konkret, umsetzbar und für Anfänger verständlich sein.
            Maximal 2 Sätze, prägnant und klar formuliert.
            """
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=100,
                temperature=0.7
            )
            
            tip = response.choices[0].text.strip()
            return tip
            
        except Exception as e:
            logger.error(f"Error generating meditation tip: {str(e)}")
            
            # Fallback tips if API fails
            fallbacks = [
                "Fokussiere dich auf deinen Atem, wenn deine Gedanken abschweifen.",
                "Qualität ist wichtiger als Quantität - 5 Minuten volle Konzentration sind wertvoller als 30 Minuten im Gedankenkarussell.",
                "Versuche, zur gleichen Zeit zu meditieren, um eine Routine zu etablieren.",
                "Beurteile deine Meditation nicht als 'gut' oder 'schlecht' - jede Sitzung ist wertvoll."
            ]
            
            return random.choice(fallbacks)
    
    async def _send_reflection_prompt(self, ctx, meditation_type):
        """Send a reflection prompt after meditation"""
        try:
            # Create a prompt for OpenAI
            prompt = f"""
            Erstelle eine kurze Reflexionsfrage nach einer {meditation_type} Meditation.
            Die Frage sollte zur Selbstreflexion anregen und den Nutzer einladen, 
            über die Erfahrung nachzudenken.
            Formuliere die Frage in einem Satz, direkt und klar.
            """
            
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=100,
                temperature=0.7
            )
            
            reflection = response.choices[0].text.strip()
            
            # Only send sometimes to avoid being annoying
            if random.random() < 0.7:
                await ctx.send(f"💭 **Zur Reflexion:** {reflection}")
            
        except Exception as e:
            logger.error(f"Error sending reflection prompt: {str(e)}")
            # Silently fail as this is a supplementary feature 