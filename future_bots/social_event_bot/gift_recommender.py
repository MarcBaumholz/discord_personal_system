import logging
import discord
import os
import random
from dotenv import load_dotenv
import openai

# Setup logging
logger = logging.getLogger("gift_recommender")

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class GiftRecommender:
    def __init__(self, bot, notion_manager):
        self.bot = bot
        self.notion_manager = notion_manager
        logger.info("Gift recommender initialized")
        
        # Default gift categories for fallbacks
        self.gift_categories = {
            "Geburtstag": [
                "Bücher", "Elektronik", "Kleidung", "Erlebnisse", 
                "Schmuck", "Hobby-Zubehör", "Gutscheine", "Selbstgemachtes"
            ],
            "Weihnachten": [
                "Bücher", "Gemütliche Kleidung", "Dekoration", "Elektronik", 
                "Gourmet-Lebensmittel", "Spiele", "Gutscheine", "Selbstgemachtes"
            ],
            "Jubiläum": [
                "Schmuck", "Erlebnisse", "Reisen", "Personalisierte Geschenke", 
                "Luxus-Artikel", "Erinnerungsstücke", "Gemeinsame Aktivitäten"
            ],
            "Hochzeit": [
                "Haushaltsgeräte", "Dekoration", "Reisegutscheine", "Erlebnisse", 
                "Geschenkkorb", "Personalisierte Geschenke", "Wohnaccessoires"
            ]
        }
    
    async def generate_gift_ideas(self, ctx, person, occasion="Geburtstag"):
        """Generate personalized gift ideas for a person"""
        try:
            # Check if person exists in database
            person_data = self.notion_manager.get_birthday(person)
            
            if not person_data:
                await ctx.send(f"⚠️ Ich habe keine Informationen über {person} in der Datenbank gefunden. Die Geschenkideen könnten weniger personalisiert sein.")
                person_info = None
            else:
                person_info = {
                    "relation": person_data.get("relation", ""),
                    "notes": person_data.get("notes", ""),
                    "previous_gifts": person_data.get("last_gift", "")
                }
            
            # Send typing indicator while generating ideas
            async with ctx.typing():
                # Try to generate ideas with OpenAI
                ideas = await self._generate_ai_gift_ideas(person, occasion, person_info)
                
                if not ideas:
                    # Fallback to category-based suggestions
                    ideas = self._generate_fallback_gift_ideas(occasion)
                
                # Prepare response message
                message = f"🎁 **Geschenkideen für {person} ({occasion}):**\n\n"
                
                for i, idea in enumerate(ideas, 1):
                    message += f"{i}. {idea}\n"
                
                # Add additional note if person is in database
                if person_data and person_data.get("gift_ideas"):
                    message += f"\n💡 **Gespeicherte Geschenkideen:** {person_data['gift_ideas']}"
                
                # Add tip for saving ideas
                message += f"\n\nUm eine Idee zu speichern, nutze `!gift add {person} [Idee]`"
                
                await ctx.send(message)
        
        except Exception as e:
            logger.error(f"Error generating gift ideas: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler bei der Generierung von Geschenkideen aufgetreten. Bitte versuche es später erneut.")
    
    async def add_gift_idea(self, ctx, person, idea):
        """Add a gift idea for a person"""
        try:
            # Check if person exists in database
            person_data = self.notion_manager.get_birthday(person)
            
            if not person_data:
                # Ask if user wants to add the person first
                confirm_msg = await ctx.send(f"⚠️ {person} ist noch nicht in der Datenbank. Möchtest du die Person hinzufügen? Reagiere mit ✅ für Ja oder ❌ für Nein.")
                await confirm_msg.add_reaction("✅")
                await confirm_msg.add_reaction("❌")
                
                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
                
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == "✅":
                        await ctx.send(f"Um {person} hinzuzufügen, nutze `!birthday add {person} [Datum]`")
                        await ctx.send(f"Danach kannst du die Geschenkidee mit `!gift add {person} {idea}` speichern.")
                    else:
                        # Store idea temporarily
                        await ctx.send(f"⚠️ Die Idee wurde nicht gespeichert, da {person} nicht in der Datenbank ist.")
                    
                    return
                    
                except:
                    await ctx.send("⏱️ Zeit abgelaufen.")
                    return
            
            # Update gift ideas in the database
            current_ideas = person_data.get("gift_ideas", "")
            
            if current_ideas:
                updated_ideas = f"{current_ideas}, {idea}"
            else:
                updated_ideas = idea
            
            success = self.notion_manager.update_birthday(
                person_data["id"], 
                {"gift_ideas": updated_ideas}
            )
            
            if success:
                await ctx.send(f"✅ Geschenkidee für {person} wurde gespeichert!")
            else:
                await ctx.send("❌ Es ist ein Fehler beim Speichern der Geschenkidee aufgetreten.")
        
        except Exception as e:
            logger.error(f"Error adding gift idea: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler aufgetreten. Bitte versuche es später erneut.")
    
    async def list_gift_ideas(self, ctx, person):
        """List saved gift ideas for a person"""
        try:
            # Check if person exists in database
            person_data = self.notion_manager.get_birthday(person)
            
            if not person_data:
                await ctx.send(f"❌ Ich habe keine Informationen über {person} in der Datenbank gefunden.")
                return
            
            # Get gift ideas
            gift_ideas = person_data.get("gift_ideas", "")
            last_gift = person_data.get("last_gift", "")
            
            if not gift_ideas and not last_gift:
                await ctx.send(f"Keine Geschenkideen für {person} gespeichert. Generiere neue mit `!gift idea {person}`")
                return
            
            # Prepare message
            message = f"🎁 **Gespeicherte Geschenkideen für {person}:**\n\n"
            
            if gift_ideas:
                # Split by commas and create a list
                ideas_list = [idea.strip() for idea in gift_ideas.split(",")]
                for i, idea in enumerate(ideas_list, 1):
                    message += f"{i}. {idea}\n"
            
            if last_gift:
                message += f"\n🎀 **Letztes Geschenk:** {last_gift}"
            
            await ctx.send(message)
        
        except Exception as e:
            logger.error(f"Error listing gift ideas: {str(e)}")
            await ctx.send("❌ Es ist ein Fehler aufgetreten. Bitte versuche es später erneut.")
    
    async def _generate_ai_gift_ideas(self, person, occasion, person_info=None):
        """Generate gift ideas using OpenAI"""
        try:
            # Create a prompt based on available information
            prompt = f"Generiere 5 kreative und spezifische Geschenkideen für {person} zum {occasion}."
            
            if person_info:
                if person_info.get("relation"):
                    prompt += f" Die Person ist ein(e) {person_info['relation']}."
                
                if person_info.get("notes"):
                    prompt += f" Notizen über die Person: {person_info['notes']}."
                
                if person_info.get("previous_gifts"):
                    prompt += f" Frühere Geschenke: {person_info['previous_gifts']}."
            
            prompt += " Die Ideen sollten konkret, originell und erschwinglich sein."
            
            # Call OpenAI API
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=200,
                temperature=0.7,
                top_p=1.0
            )
            
            # Process the response
            content = response.choices[0].text.strip()
            
            # Parse the ideas into a list
            ideas = []
            for line in content.split("\n"):
                # Remove numbering and leading dashes or asterisks
                cleaned_line = line.strip()
                if cleaned_line:
                    # Remove common list markers
                    for marker in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-", "*", "•"]:
                        if cleaned_line.startswith(marker):
                            cleaned_line = cleaned_line[len(marker):].strip()
                            break
                    
                    if cleaned_line:
                        ideas.append(cleaned_line)
            
            # Return at least 5 ideas
            return ideas[:5] if len(ideas) >= 5 else ideas
            
        except Exception as e:
            logger.error(f"Error generating AI gift ideas: {str(e)}")
            return None
    
    def _generate_fallback_gift_ideas(self, occasion):
        """Generate fallback gift ideas based on categories"""
        # Get relevant categories
        categories = self.gift_categories.get(occasion, self.gift_categories["Geburtstag"])
        
        # Select 3-4 random categories
        selected_categories = random.sample(categories, min(4, len(categories)))
        
        # Create generic ideas based on categories
        ideas = []
        
        category_ideas = {
            "Bücher": [
                "Ein Bestseller aus dem Lieblingsgenre",
                "Ein schön illustriertes Fotobuch oder Bildband",
                "Ein personalisiertes Notizbuch oder Journal"
            ],
            "Elektronik": [
                "Drahtlose Kopfhörer",
                "Smartwatch oder Fitness-Tracker",
                "Eine portable Powerbank im eleganten Design"
            ],
            "Kleidung": [
                "Ein hochwertiger Schal oder eine Mütze",
                "Ein T-Shirt mit einem witzigen Aufdruck",
                "Gemütliche Hausschuhe"
            ],
            "Erlebnisse": [
                "Konzertkarten für einen Lieblingskünstler",
                "Ein Gutschein für ein schönes Restaurant",
                "Ein Tagesausflug zu einem besonderen Ort"
            ],
            "Schmuck": [
                "Eine schlichte, elegante Halskette",
                "Personalisiertes Armband mit Gravur",
                "Stilvolle Manschettenknöpfe"
            ],
            "Hobby-Zubehör": [
                "Hochwertiges Zubehör für ein bekanntes Hobby",
                "Ein Starter-Kit für ein neues Hobby",
                "Ein Buch über Techniken zur Verbesserung im Lieblingshobby"
            ],
            "Gutscheine": [
                "Ein Gutschein für den Lieblingsladen",
                "Ein Streaming-Dienst Abonnement",
                "Ein Wellness-Gutschein"
            ],
            "Selbstgemachtes": [
                "Selbstgebackene Kekse oder Kuchen",
                "Ein selbstgestaltetes Fotoalbum mit gemeinsamen Erinnerungen",
                "Selbstgemachte Badebomben oder Seifen"
            ],
            "Gemütliche Kleidung": [
                "Ein flauschiger Bademantel",
                "Warme, gemusterte Socken",
                "Ein kuscheliger Pullover"
            ],
            "Dekoration": [
                "Stilvolle Wohnaccessoires",
                "Eine schöne Pflanze oder Blumenarrangement",
                "Ein personalisiertes Kunstwerk oder Poster"
            ],
            "Gourmet-Lebensmittel": [
                "Ein Set mit hochwertigen Gewürzen",
                "Besondere Schokolade oder Pralinen",
                "Ein Gourmet-Geschenkkorb mit Delikatessen"
            ],
            "Spiele": [
                "Ein Gesellschaftsspiel für gemeinsame Abende",
                "Ein Puzzle mit einem besonderen Motiv",
                "Ein Kartenspiel mit Insider-Witzen"
            ],
            "Reisen": [
                "Ein Wochenendtrip in ein schönes Hotel",
                "Reisezubehör wie ein Nackenpolster oder eine Schlafmaske",
                "Ein Reiseführer für ein Traumziel"
            ],
            "Personalisierte Geschenke": [
                "Ein Kissen mit einem besonderen Foto",
                "Eine Tasse mit einem persönlichen Spruch",
                "Ein personalisierter Kalender mit Familienfotos"
            ],
            "Luxus-Artikel": [
                "Ein hochwertiger Füllfederhalter",
                "Ein edles Portemonnaie oder eine Handtasche",
                "Eine Flasche besonderen Wein oder Spirituosen"
            ],
            "Erinnerungsstücke": [
                "Ein Fotorahmen mit einem gemeinsamen Moment",
                "Ein Sammelalbum für besondere Erinnerungen",
                "Eine Collage mit Highlights der Beziehung"
            ],
            "Gemeinsame Aktivitäten": [
                "Tickets für ein gemeinsames Erlebnis",
                "Ein Kochkurs für zwei",
                "Ein Escape Room Abenteuer"
            ],
            "Haushaltsgeräte": [
                "Ein hochwertiger Mixer oder Küchenmaschine",
                "Ein Aromaölverteiler",
                "Ein intelligenter Lautsprecher"
            ],
            "Wohnaccessoires": [
                "Schöne Kissen oder Überwürfe",
                "Kunstvolle Wanddekoration",
                "Stilvolle Vasen oder Kerzenhalter"
            ]
        }
        
        # Create ideas from selected categories
        for category in selected_categories:
            category_options = category_ideas.get(category, [f"Etwas aus der Kategorie {category}"])
            idea = random.choice(category_options)
            ideas.append(f"{idea} ({category})")
        
        # Add a generic idea if we have fewer than 5
        if len(ideas) < 5:
            general_ideas = [
                "Ein personalisiertes Geschenk mit einem gemeinsamen Insider-Witz",
                "Ein Gutschein für ein gemeinsames Erlebnis",
                "Etwas Praktisches, das im Alltag nützlich ist",
                "Ein kreatives DIY-Geschenk mit persönlicher Note",
                "Ein Abonnement für einen Lieblingsservice"
            ]
            
            while len(ideas) < 5 and general_ideas:
                idea = general_ideas.pop(random.randrange(len(general_ideas)))
                ideas.append(idea)
        
        return ideas 