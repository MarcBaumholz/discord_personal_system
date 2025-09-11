import os
import discord
from notion_client import Client
from datetime import datetime
import asyncio
import json
import re
from dotenv import load_dotenv
import openai
import sys

# Add log bot directory to path for API monitoring
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'log_bot'))
from api_monitor_shared import track_openrouter_call

# --- Environment Variable Loading ---
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Config ---
NOTION_API_KEY = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("ALLGEMEINE_WOHL_DATABASE_ID")
GROUND_TRUTH_DATABASE_ID = os.getenv("GROUND_TRUTH_DATABASE_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("ALLGEMEINE_WOHL_CHANNEL_ID"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Notion & AI Clients ---
notion = Client(auth=NOTION_API_KEY)
ai_client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- Discord Client ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# --- Bot State ---
bot_state = {
    "top_activities": ["Kochen", "Putzen", "Einkaufen", "Wäsche waschen", "Müll rausbringen"]
}
STATE_FILE = os.path.join(os.path.dirname(__file__), "bot_state.json")
ground_truth_cache = {}  # Cache for ground truth activities {name: id}

def load_state():
    global bot_state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            bot_state = json.load(f)

# --- Ground Truth Management ---
async def load_ground_truth_cache():
    """Loads all activities from the Ground Truth database into a cache."""
    global ground_truth_cache
    try:
        response = await asyncio.to_thread(
            notion.databases.query,
            database_id=GROUND_TRUTH_DATABASE_ID
        )
        
        for page in response.get("results", []):
            properties = page.get("properties", {})
            activity_title = properties.get("Aktivität", {}).get("title", [])
            if activity_title:
                name = activity_title[0].get("text", {}).get("content")
                ground_truth_cache[name] = page["id"]
        print(f"✅ Ground Truth Cache geladen: {len(ground_truth_cache)} Einträge gefunden.")
    except Exception as e:
        print(f"❌ Fehler beim Laden des Ground Truth Caches: {e}")

async def populate_ground_truth_if_empty():
    """Checks if the Ground Truth DB is empty and fills it from the MD file."""
    try:
        response = await asyncio.to_thread(
            notion.databases.query,
            database_id=GROUND_TRUTH_DATABASE_ID,
            page_size=1
        )
        if len(response.get("results", [])) > 0:
            print("ℹ️ Ground Truth Datenbank ist bereits befüllt.")
            return

        print("⏳ Ground Truth Datenbank ist leer. Befülle sie aus der Markdown-Datei...")
        ideas_file = os.path.join(os.path.dirname(__file__), "ALLGEMEINE_WOHL_IDEEN.md")
        
        with open(ideas_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract activities from markdown tables
        table_rows = re.findall(r"\|\s*([^|]+?)\s*\|\s*([\d-]+)\s*\|", content)
        for row in table_rows:
            activity, time_str = row
            activity = activity.strip()
            
            # Skip headers and separators
            if activity in ["Aktivität", "---", "**Küche**", "**Wohnbereich**", "**Bad**", "**Wäsche**"] or activity.startswith("**"):
                continue
            
            try:
                time_int = int(time_str.split('-')[0])  # Take lower bound
                properties = {
                    "Aktivität": {"title": [{"text": {"content": activity}}]},
                    "Zeit in min": {"number": time_int}
                }
                await asyncio.to_thread(
                    notion.pages.create,
                    parent={"database_id": GROUND_TRUTH_DATABASE_ID},
                    properties=properties
                )
                print(f"  -> '{activity}' zur Ground Truth DB hinzugefügt.")
            except (ValueError, IndexError):
                continue

        print("✅ Ground Truth Datenbank erfolgreich befüllt.")
    except Exception as e:
        print(f"❌ Fehler beim Befüllen der Ground Truth Datenbank: {e}")

# --- Activity Analysis ---
async def analyze_activity_with_ai(activity_text: str):
    """Enhanced activity analysis using AI with fallback to rule-based matching."""
    ground_truth_activities = list(ground_truth_cache.keys())
    
    # Try AI analysis first
    ai_result = await get_ai_analysis(activity_text, ground_truth_activities)
    if ai_result and ai_result.get("success"):
        return ai_result
    
    # Fallback to rule-based analysis
    print(f"🔄 AI failed, using fallback analysis for: {activity_text}")
    return get_fallback_analysis(activity_text, ground_truth_activities)

async def get_ai_analysis(activity_text: str, ground_truth_activities: list):
    """Get AI analysis with structured prompt."""
    
    # Create a focused list of top matches for the AI
    focused_activities = get_focused_activity_list(activity_text, ground_truth_activities)
    
    prompt = f"""Analysiere die deutsche Aktivität: "{activity_text}"

Aufgaben:
1. Zeit schätzen (nur Zahl in Minuten)
2. Kategorie bestimmen: Haushalt, Organisation, Soziales, Selbstfürsorge, Garten, Handwerkliches, Sonstiges
3. Beste Übereinstimmung aus der Liste finden

Verfügbare Aktivitäten:
{json.dumps(focused_activities, ensure_ascii=False)}

Antwort als JSON:
{{
  "zeit": <minuten>,
  "kategorie": "<kategorie>",
  "ground_truth_activity_name": "<exakter_name_oder_null>",
  "confidence": <0.0_bis_1.0>
}}"""

    try:
        completion = await asyncio.to_thread(
            ai_client.chat.completions.create,
            model="deepseek/deepseek-chat-v3.1:free",
            messages=[
                {"role": "system", "content": "Du antwortest nur mit gültigem JSON. Keine Erklärungen."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=150,
        )
        
        # Track successful API call
        track_openrouter_call("allgemeine-wohl-bot", "deepseek/deepseek-chat-v3.1:free", True)
        
        response_text = completion.choices[0].message.content.strip()
        print(f"🤖 AI Response: {response_text}")
        
        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            result = json.loads(json_text)
            
            # Validate result
            if validate_ai_result(result, ground_truth_activities):
                result["success"] = True
                print(f"✅ AI Analyse erfolgreich: {result}")
                return result
        
    except Exception as e:
        # Track failed API call
        track_openrouter_call("allgemeine-wohl-bot", "deepseek/deepseek-chat-v3.1:free", False)
        print(f"⚠️ AI Analyse Fehler: {e}")
    
    return {"success": False}

def get_focused_activity_list(activity_text: str, all_activities: list, max_items: int = 15):
    """Get a focused list of activities most likely to match."""
    activity_lower = activity_text.lower()
    focused = []
    
    # First: exact substring matches
    for activity in all_activities:
        if activity_lower in activity.lower() or activity.lower() in activity_lower:
            focused.append(activity)
    
    # Second: word matches
    words = [w for w in activity_lower.split() if len(w) > 3]
    for word in words:
        for activity in all_activities:
            if word in activity.lower() and activity not in focused:
                focused.append(activity)
                
    # Third: category-based additions
    if "putzen" in activity_lower:
        for activity in all_activities:
            if "putzen" in activity.lower() or "sauber" in activity.lower():
                if activity not in focused:
                    focused.append(activity)
    
    # Limit and add some random ones if too few
    if len(focused) < 8:
        for activity in all_activities[:10]:
            if activity not in focused:
                focused.append(activity)
    
    return focused[:max_items]

def validate_ai_result(result: dict, ground_truth_activities: list) -> bool:
    """Validate AI result structure and content."""
    required_keys = ["zeit", "kategorie", "ground_truth_activity_name", "confidence"]
    
    # Check all required keys exist
    if not all(key in result for key in required_keys):
        return False
    
    # Check types
    if not isinstance(result["zeit"], (int, float)) or result["zeit"] <= 0:
        return False
    
    if not isinstance(result["kategorie"], str):
        return False
        
    if not isinstance(result["confidence"], (int, float)) or not 0 <= result["confidence"] <= 1:
        return False
    
    # Check if ground truth activity exists in our list
    gt_name = result["ground_truth_activity_name"]
    if gt_name is not None and gt_name not in ground_truth_activities:
        result["ground_truth_activity_name"] = None
        result["confidence"] = 0.3
    
    return True

def get_fallback_analysis(activity_text: str, ground_truth_activities: list):
    """Rule-based fallback analysis."""
    activity_lower = activity_text.lower().strip()
    best_match = None
    
    # Enhanced matching logic
    best_score = 0
    for gt_activity in ground_truth_activities:
        score = calculate_similarity_score(activity_lower, gt_activity.lower())
        if score > best_score:
            best_score = score
            best_match = gt_activity
    
    # Only use match if score is high enough
    if best_score < 0.3:
        best_match = None
    
    # Smart time and category estimation
    zeit, kategorie = estimate_time_and_category(activity_lower)
    
    confidence = min(0.9, best_score) if best_match else 0.2
    
    result = {
        "zeit": zeit,
        "kategorie": kategorie,
        "ground_truth_activity_name": best_match,
        "confidence": confidence,
        "success": True
    }
    
    print(f"✅ Fallback Analyse: {result}")
    return result

def calculate_similarity_score(input_text: str, gt_text: str) -> float:
    """Calculate similarity score between input and ground truth text."""
    score = 0.0
    
    # Exact match
    if input_text == gt_text:
        return 1.0
    
    # Substring matches
    if input_text in gt_text:
        score += 0.8
    elif gt_text in input_text:
        score += 0.7
    
    # Word overlap
    input_words = set(input_text.split())
    gt_words = set(gt_text.split())
    
    if input_words and gt_words:
        overlap = len(input_words.intersection(gt_words))
        total_words = len(input_words.union(gt_words))
        word_score = overlap / total_words
        score += word_score * 0.6
    
    # Special keyword boosting
    keywords = {
        "kochen": ["kochen", "essen", "zubereiten"],
        "putzen": ["putzen", "reinigen", "sauber", "wischen"],
        "einkaufen": ["einkaufen", "shoppen", "kaufen"],
        "wäsche": ["wäsche", "waschen", "trocknen"]
    }
    
    for category, words in keywords.items():
        if any(word in input_text for word in words) and any(word in gt_text for word in words):
            score += 0.3
    
    return min(1.0, score)

def estimate_time_and_category(activity_text: str) -> tuple:
    """Estimate time and category based on activity text."""
    
    # Time estimation rules
    time_rules = {
        "kochen": 60,
        "putzen": 30,
        "einkaufen": 60,
        "wäsche": 15,
        "müll": 5,
        "duschen": 15,
        "aufräumen": 20,
        "staubsaugen": 25,
        "bad": 20,
        "küche": 25
    }
    
    # Category rules
    category_rules = {
        "kochen": "Selbstfürsorge",
        "essen": "Selbstfürsorge",
        "duschen": "Selbstfürsorge",
        "putzen": "Haushalt",
        "waschen": "Haushalt",
        "einkaufen": "Haushalt",
        "aufräumen": "Haushalt",
        "müll": "Haushalt",
        "garten": "Garten",
        "pflanzen": "Garten",
        "reparatur": "Handwerkliches",
        "sozial": "Soziales"
    }
    
    zeit = 15  # default
    kategorie = "Haushalt"  # default
    
    for keyword, time_est in time_rules.items():
        if keyword in activity_text:
            zeit = time_est
            break
    
    for keyword, cat in category_rules.items():
        if keyword in activity_text:
            kategorie = cat
            break
    
    return zeit, kategorie

# --- Entry Creation ---
async def add_notion_entry(activity, zeit, kategorie, person, ground_truth_activity_name=None):
    """Creates a new entry in the Notion database."""
    properties = {
        "Aktivität": {"title": [{"text": {"content": activity}}]},
        "Zeit": {"number": zeit},
        "Kategorie": {"select": {"name": kategorie}},
        "Person": {"select": {"name": person}},
        "Datum": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
    }
    
    # Add bestMatch select field if we found a ground truth match
    if ground_truth_activity_name:
        properties["bestMatch"] = {"select": {"name": ground_truth_activity_name}}
    
    try:
        await asyncio.to_thread(
            notion.pages.create,
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties
        )
        return True
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Notion-Eintrags: {e}")
        return False

# --- Bot Commands & Logic ---
async def send_start_message(channel):
    """Sends the initial start message with shortcuts."""
    embed = discord.Embed(
        title="🌟 Allgemeine Wohl Bot",
        description="Tracke deine Aktivitäten für ein besseres Wohlbefinden!",
        color=0x00ff00
    )
    embed.add_field(
        name="Top 5 Aktivitäten (Shortcuts)",
        value="\n".join([f"{i+1}. {activity}" for i, activity in enumerate(bot_state["top_activities"])]),
        inline=False
    )
    embed.add_field(
        name="Verwendung",
        value="• Schreibe einfach deine Aktivität\n• Nutze Shortcuts: 1, 2, 3, 4, 5\n• Für Hilfe: !aw help",
        inline=False
    )
    await channel.send(embed=embed)

@client.event
async def on_ready():
    print(f"✅ Bot eingeloggt als {client.user}")
    load_state()
    await populate_ground_truth_if_empty()
    await load_ground_truth_cache()
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await send_start_message(channel)

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != CHANNEL_ID:
        return

    content = message.content.strip()
    person = message.author.display_name

    # Handle shortcuts directly (1, 2, 3, 4, 5)
    if content in ["1", "2", "3", "4", "5"]:
        shortcut_index = int(content) - 1
        if shortcut_index < len(bot_state["top_activities"]):
            activity_text = bot_state["top_activities"][shortcut_index]
            
            async with message.channel.typing():
                # Get analysis
                result = await analyze_activity_with_ai(activity_text)
                zeit = result.get("zeit", 15)
                kategorie = result.get("kategorie", "Haushalt")
                gt_activity_name = result.get("ground_truth_activity_name")
                confidence = result.get("confidence", 0.0)

                # Add to Notion - pass the activity name directly for bestMatch
                best_match = gt_activity_name if gt_activity_name and confidence >= 0.5 else None
                success = await add_notion_entry(activity_text, zeit, kategorie, person, best_match)
                
                if success:
                    await message.add_reaction("✅")
                    response = f"✅ **{activity_text}** hinzugefügt!\n"
                    response += f"⏰ Zeit: {zeit} Min | 🏷️ Kategorie: {kategorie}"
                    if best_match:
                        response += f"\n🎯 Best Match: {best_match}"
                    await message.reply(response)
                else:
                    await message.add_reaction("❌")
                    await message.reply("❌ Fehler beim Hinzufügen zur Datenbank!")
        return

    # Handle !aw commands
    if content.lower().startswith("!aw"):
        parts = content.split()[1:]
        
        if not parts or parts[0] == "help":
            embed = discord.Embed(title="🤖 Bot Befehle", color=0x0099ff)
            embed.add_field(name="!aw help", value="Diese Hilfe anzeigen", inline=False)
            embed.add_field(name="!aw start", value="Start-Nachricht erneut senden", inline=False)
            embed.add_field(name="!aw top", value="Top 5 Aktivitäten anzeigen", inline=False)
            embed.add_field(name="Shortcuts", value="1, 2, 3, 4, 5 für schnelle Eingabe", inline=False)
            await message.reply(embed=embed)
            
        elif parts[0] == "start":
            await send_start_message(message.channel)
            
        elif parts[0] == "top":
            top_list = "\n".join([f"{i+1}. {activity}" for i, activity in enumerate(bot_state["top_activities"])])
            embed = discord.Embed(title="🏆 Top 5 Aktivitäten", description=top_list, color=0xffd700)
            await message.reply(embed=embed)
        return

    # Handle regular activity input
    if content:
        async with message.channel.typing():
            # Extract time from message if present (e.g., "putzen 30 min")
            time_match = re.search(r'(\d+)\s*(min|minuten|minutes?)', content.lower())
            user_specified_time = int(time_match.group(1)) if time_match else None
            
            # Clean activity text (remove time specification)
            clean_activity = re.sub(r'\d+\s*(min|minuten|minutes?)', '', content).strip()
            
            # Get analysis
            result = await analyze_activity_with_ai(clean_activity)
            
            # Use user-specified time if available, otherwise analysis estimate
            zeit = user_specified_time if user_specified_time else result.get("zeit", 15)
            kategorie = result.get("kategorie", "Haushalt")
            gt_activity_name = result.get("ground_truth_activity_name")
            confidence = result.get("confidence", 0.0)

            # Add to Notion - pass the activity name directly for bestMatch
            best_match = gt_activity_name if gt_activity_name and confidence >= 0.5 else None
            success = await add_notion_entry(clean_activity, zeit, kategorie, person, best_match)
            
            if success:
                await message.add_reaction("✅")
                response = f"✅ **{clean_activity}** hinzugefügt!\n"
                response += f"⏰ Zeit: {zeit} Min | 🏷️ Kategorie: {kategorie}"
                if best_match:
                    response += f"\n🎯 Best Match: {best_match}"
                elif user_specified_time:
                    response += f"\n⏱️ Ihre angegebene Zeit wurde verwendet"
                await message.reply(response)
            else:
                await message.add_reaction("❌")
                await message.reply("❌ Fehler beim Hinzufügen zur Datenbank!")

def run():
    if not all([NOTION_API_KEY, DISCORD_BOT_TOKEN, CHANNEL_ID, NOTION_DATABASE_ID, GROUND_TRUTH_DATABASE_ID, OPENROUTER_API_KEY]):
        print("❌ Fehler: Wichtige Umgebungsvariablen sind nicht gesetzt. Bitte prüfen Sie die .env Datei.")
        return
    client.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    run()
