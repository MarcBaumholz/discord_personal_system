import discord
from discord.ext import commands
import os
import random
import json
import requests
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Channel ID for erinnerungen
ERINNERUNGEN_CHANNEL_ID = int(os.getenv("ERINNERUNGEN_CHANNEL_ID"))

# Notion database ID (will be extracted from database name)
NOTION_DATABASE_ID = None

# ------ Notion API Functions ------

def get_notion_headers():
    """Return headers for Notion API requests"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def find_recipe_database():
    """Find the 'Rezepte schnell' database in Notion"""
    global NOTION_DATABASE_ID
    
    url = "https://api.notion.com/v1/search"
    payload = {
        "filter": {
            "value": "database",
            "property": "object"
        },
        "query": "Rezepte schnell"
    }
    
    response = requests.post(url, headers=get_notion_headers(), json=payload)
    data = response.json()
    
    if response.status_code == 200 and data.get('results'):
        for db in data['results']:
            if db.get('title') and any(text.get('plain_text') == 'Rezepte schnell' for text in db['title']):
                NOTION_DATABASE_ID = db['id']
                return True
    
    return False

def get_recipes_from_notion():
    """Get recipes from Notion database"""
    if not NOTION_DATABASE_ID:
        if not find_recipe_database():
            return []
    
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(url, headers=get_notion_headers())
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    recipes = []
    
    for item in data.get('results', []):
        props = item.get('properties', {})
        name_prop = props.get('Rezeptname', {})
        
        if name_prop and 'title' in name_prop:
            title_text = ''.join([text.get('plain_text', '') for text in name_prop['title']])
            recipes.append({
                'id': item['id'],
                'name': title_text
            })
    
    return recipes

# ------ Todoist API Functions ------

def get_todoist_headers():
    """Return headers for Todoist API requests"""
    return {
        "Authorization": f"Bearer {TODOIST_API_KEY}",
        "Content-Type": "application/json"
    }

def extract_shopping_list(meal_plan):
    """Extract the shopping list section from the meal plan text"""
    # Look for common patterns that indicate the shopping list section
    shopping_list_patterns = [
        r"(?:Shopping List|Einkaufsliste|Shopping list):(.*?)(?:Prep Schedule|Preparation|$)",
        r"(?:Ingredients|Items needed):(.*?)(?:Prep Schedule|Preparation|$)",
        r"(?:Shopping List|Einkaufsliste):\s*([\s\S]*?)(?:\n\n\d\.|\n\n[A-Z]|\n\nPrep|$)"
    ]
    
    shopping_list = ""
    for pattern in shopping_list_patterns:
        match = re.search(pattern, meal_plan, re.IGNORECASE | re.DOTALL)
        if match:
            shopping_list = match.group(1).strip()
            break
    
    # If no specific section found, try to look for list-like structures with categories
    if not shopping_list:
        # Look for lines that seem to be part of a shopping list
        lines = meal_plan.split('\n')
        shopping_list_lines = []
        in_shopping_list = False
        
        for line in lines:
            # Check if we've reached a line that indicates a shopping list
            if re.search(r"(Shopping|Grocery|Einkauf)", line, re.IGNORECASE) and not in_shopping_list:
                in_shopping_list = True
                shopping_list_lines.append(line)
            # Check if we've found a line that indicates the end of the shopping list
            elif in_shopping_list and re.search(r"(Prep|Schedule|Preparation)", line, re.IGNORECASE):
                in_shopping_list = False
            # Add line if we're in the shopping list section
            elif in_shopping_list and line.strip():
                shopping_list_lines.append(line)
        
        shopping_list = "\n".join(shopping_list_lines)
    
    return shopping_list

def format_shopping_list_for_todoist(shopping_list):
    """Format the extracted shopping list for Todoist"""
    items = []
    current_category = "Shopping"
    
    # Split the shopping list into lines
    lines = shopping_list.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line is a category header
        if line.endswith(':') or (line.isupper() and len(line) > 2):
            current_category = line.rstrip(':')
            continue
        
        # Clean up the item text
        item = re.sub(r'^[-•*]\s*', '', line).strip()
        if item:
            items.append({
                "content": item,
                "description": f"From meal plan - Category: {current_category}"
            })
    
    return items

def add_to_todoist(items):
    """Add items to Todoist Einkaufsliste project"""
    url = "https://api.todoist.com/rest/v2/tasks"
    headers = get_todoist_headers()
    
    # Define the Einkaufsliste project ID
    project_id = "einkaufsliste-6Xf57RMwPXphCf4P"
    
    # First, get proper project ID (numerical format) using project name
    projects_url = "https://api.todoist.com/rest/v2/projects"
    projects_response = requests.get(projects_url, headers=headers)
    
    if projects_response.status_code == 200:
        projects = projects_response.json()
        for project in projects:
            if project["name"].lower() == "einkaufsliste":
                project_id = project["id"]
                break
    
    added_items = []
    for item in items:
        # Add to the Einkaufsliste project
        task_data = {
            "content": item["content"],
            "description": item["description"],
            "project_id": project_id
        }
        
        response = requests.post(url, headers=headers, json=task_data)
        if response.status_code == 200:
            added_items.append(item["content"])
    
    return added_items

# ------ OpenRouter API Functions ------

def generate_meal_plan(selected_recipes):
    """Generate meal plan and shopping list using OpenRouter"""
    recipe_names = [recipe['name'] for recipe in selected_recipes]
    
    prompt = f"""Generate a concise meal prep plan for the following 3 meals for Sunday:
1. {recipe_names[0]}
2. {recipe_names[1]}
3. {recipe_names[2]}

Please provide:
1. A very brief description of each meal (2-3 sentences max)
2. A compact shopping list organized by categories (produce, meat, dairy, etc.)
3. A short prep schedule for Sunday

Important: Structure the shopping list section clearly under a "SHOPPING LIST:" header and organize items by category.

Keep your response brief and focused - maximum 600 words total.
"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen/qwen2.5-vl-3b-instruct:free",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,  # Reduced from 800 to 500
        "temperature": 0.7
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
    
    return "Sorry, I couldn't generate a meal plan at this time."

# ------ Discord Bot Functions ------

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f"Logged in as {bot.user}")
    print(f"Using erinnerungen channel ID: {ERINNERUNGEN_CHANNEL_ID}")
    print("Meal Plan Bot is ready!")
    
    # Send welcome message
    channel = bot.get_channel(ERINNERUNGEN_CHANNEL_ID)
    if channel:
        await channel.send("🍽️ Meal Plan Bot is online! React with 👍 to get meal suggestions for Sunday prep.")

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Only process messages in the erinnerungen channel
    if message.channel.id == ERINNERUNGEN_CHANNEL_ID:
        # Check for thumbs up emoji
        if "👍" in message.content or ":thumbsup:" in message.content:
            await message.add_reaction("🔍")  # Add reaction to show we're processing
            await generate_weekly_meal_plan(message.channel)
            await message.remove_reaction("🔍", bot.user)
            await message.add_reaction("✅")
    
    await bot.process_commands(message)

async def generate_weekly_meal_plan(channel):
    """Main function to generate and send meal plan"""
    # Step 1: Fetch recipes from Notion
    await channel.send("🔍 Fetching recipes from Notion...")
    recipes = get_recipes_from_notion()
    
    if not recipes:
        await channel.send("❌ Couldn't find recipes in your Notion database. Please check your configuration.")
        return
    
    # Step 2: Select 3 random recipes
    await channel.send(f"📋 Found {len(recipes)} recipes. Selecting 3 random ones...")
    selected_recipes = random.sample(recipes, min(3, len(recipes)))
    
    selected_names = "\n".join([f"• {recipe['name']}" for recipe in selected_recipes])
    await channel.send(f"🍽️ Selected meals for Sunday prep:\n{selected_names}")
    
    # Step 3: Generate meal plan with OpenRouter
    await channel.send("⏳ Generating your meal plan and shopping list...")
    meal_plan = generate_meal_plan(selected_recipes)
    
    # Step 4: Extract and save shopping list to Todoist
    await channel.send("📝 Extracting shopping list and saving to Todoist...")
    
    shopping_list_text = extract_shopping_list(meal_plan)
    if shopping_list_text:
        todoist_items = format_shopping_list_for_todoist(shopping_list_text)
        added_items = add_to_todoist(todoist_items)
        
        if added_items:
            await channel.send(f"✅ Added {len(added_items)} items to your Todoist shopping list!")
            
            # Send the extracted shopping list to the discord channel
            await send_long_message(channel, f"🛒 **Shopping List (added to Todoist):**\n\n{shopping_list_text}")
        else:
            await channel.send("❌ Failed to add items to Todoist. Continuing with meal plan only.")
    else:
        await channel.send("⚠️ Could not extract shopping list from the meal plan. Continuing with full plan only.")
    
    # Step 5: Send the meal plan - properly chunked to respect Discord's 2000 char limit
    await send_long_message(channel, f"🍳 **Your Sunday Meal Prep Plan:**\n\n{meal_plan}")

async def send_long_message(channel, content):
    """Send a message that might exceed Discord's 2000 character limit"""
    if len(content) <= 1900:  # Using 1900 to be safe
        await channel.send(content)
        return
        
    # Split the content into parts
    parts = []
    current_part = ""
    
    # Split by lines first for more natural breaks
    lines = content.split('\n')
    for line in lines:
        # If adding this line would exceed the limit, start a new part
        if len(current_part) + len(line) + 1 > 1900:  # +1 for newline
            parts.append(current_part)
            current_part = line + '\n'
        else:
            current_part += line + '\n'
    
    # Add the last part if not empty
    if current_part:
        parts.append(current_part)
    
    # Send each part
    for i, part in enumerate(parts):
        header = f"**Part {i+1}/{len(parts)}**\n" if len(parts) > 1 else ""
        await channel.send(f"{header}{part}")

@bot.command(name="help_meal")
async def help_meal(ctx):
    """Show help information"""
    if ctx.channel.id == ERINNERUNGEN_CHANNEL_ID:
        help_text = """
🍽️ **Meal Plan Bot Help**

To get a weekly meal plan:
1. Type 👍 or `:thumbsup:` in this channel
2. The bot will select 3 random recipes from your Notion "Rezepte schnell" database
3. It will generate a meal prep plan and shopping list for Sunday
4. The shopping list will be automatically added to your Todoist account
5. Both the meal plan and shopping list will be sent to this channel

That's it! Enjoy your organized meal planning.
        """
        await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN) 