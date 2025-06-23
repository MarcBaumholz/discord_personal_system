#!/usr/bin/env python3
"""
Refactored Meal Plan Bot - Optimized for efficiency and better workflow
Flow: Notion recipes → Extract details → LLM shopping list → Todoist → Present to user
"""

import discord
from discord.ext import commands
import os
import random
import json
import requests
import re
import schedule
import threading
import time
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from main discord directory
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
MEALPLAN_CHANNEL_ID = int(os.getenv("ERINNERUNGEN_CHANNEL_ID", "1361083869729919046"))

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Global variables
NOTION_DATABASE_ID = None
TODOIST_PROJECT_ID = None

class Recipe:
    """Recipe data class"""
    def __init__(self, id, name, url="", ingredients="", instructions="", tags=""):
        self.id = id
        self.name = name
        self.url = url
        self.ingredients = ingredients
        self.instructions = instructions
        self.tags = tags

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
        "filter": {"value": "database", "property": "object"},
        "query": "Rezepte schnell"
    }
    
    response = requests.post(url, headers=get_notion_headers(), json=payload)
    data = response.json()
    
    if response.status_code == 200 and data.get('results'):
        for db in data['results']:
            if db.get('title') and any(text.get('plain_text') == 'Rezepte schnell' for text in db['title']):
                NOTION_DATABASE_ID = db['id']
                print(f"✅ Found Rezepte database: {NOTION_DATABASE_ID}")
                return True
    
    print("❌ Could not find 'Rezepte schnell' database")
    return False

def extract_detailed_recipe_info(page_id):
    """Extract detailed information from a recipe page"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=get_notion_headers())
    
    if response.status_code != 200:
        return None
    
    page_data = response.json()
    props = page_data.get('properties', {})
    
    # Extract basic info
    recipe_info = {
        'url': page_data.get('url', ''),
        'ingredients': '',
        'instructions': '',
        'tags': ''
    }
    
    # Extract ingredients from rich text or textarea properties
    for prop_name, prop_data in props.items():
        if 'ingredient' in prop_name.lower() or 'zutat' in prop_name.lower():
            if prop_data.get('type') == 'rich_text' and prop_data.get('rich_text'):
                recipe_info['ingredients'] = ''.join([text.get('plain_text', '') for text in prop_data['rich_text']])
        
        elif 'instruction' in prop_name.lower() or 'anweisung' in prop_name.lower() or 'zubereitung' in prop_name.lower():
            if prop_data.get('type') == 'rich_text' and prop_data.get('rich_text'):
                recipe_info['instructions'] = ''.join([text.get('plain_text', '') for text in prop_data['rich_text']])
        
        elif 'tag' in prop_name.lower() or 'category' in prop_name.lower():
            if prop_data.get('type') == 'multi_select':
                recipe_info['tags'] = ', '.join([tag.get('name', '') for tag in prop_data.get('multi_select', [])])
    
    return recipe_info

def get_recipes_from_notion():
    """Get 2 random recipes with detailed information from Notion database"""
    if not NOTION_DATABASE_ID:
        if not find_recipe_database():
            return []
    
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(url, headers=get_notion_headers())
    
    if response.status_code != 200:
        print(f"❌ Notion API error: {response.status_code}")
        return []
    
    data = response.json()
    all_recipes = []
    
    print(f"🔍 Processing {len(data.get('results', []))} recipes from Notion...")
    
    for item in data.get('results', []):
        props = item.get('properties', {})
        name_prop = props.get('Rezeptname', {}) or props.get('Name', {}) or props.get('Title', {})
        
        if name_prop and 'title' in name_prop:
            title_text = ''.join([text.get('plain_text', '') for text in name_prop['title']])
            if title_text:  # Only include recipes with names
                all_recipes.append({
                    'id': item['id'],
                    'name': title_text
                })
    
    # Select 2 random recipes
    selected_recipes = random.sample(all_recipes, min(2, len(all_recipes)))
    
    # Get detailed information for each selected recipe
    detailed_recipes = []
    for recipe_data in selected_recipes:
        print(f"📖 Extracting details for: {recipe_data['name']}")
        details = extract_detailed_recipe_info(recipe_data['id'])
        
        recipe = Recipe(
            id=recipe_data['id'],
            name=recipe_data['name'],
            url=details['url'] if details else '',
            ingredients=details['ingredients'] if details else '',
            instructions=details['instructions'] if details else '',
            tags=details['tags'] if details else ''
        )
        detailed_recipes.append(recipe)
    
    return detailed_recipes

# ------ Todoist API Functions ------

def get_todoist_headers():
    """Return headers for Todoist API requests"""
    return {
        "Authorization": f"Bearer {TODOIST_API_KEY}",
        "Content-Type": "application/json"
    }

def find_todoist_project():
    """Find the Einkaufsliste project in Todoist"""
    global TODOIST_PROJECT_ID
    
    url = "https://api.todoist.com/rest/v2/projects"
    response = requests.get(url, headers=get_todoist_headers())
    
    if response.status_code == 200:
        projects = response.json()
        for project in projects:
            if project["name"].lower() in ["einkaufsliste", "shopping", "groceries"]:
                TODOIST_PROJECT_ID = project["id"]
                print(f"✅ Found Todoist project: {project['name']} (ID: {TODOIST_PROJECT_ID})")
                return True
    
    print("❌ Could not find Einkaufsliste project in Todoist")
    return False

def add_items_to_todoist(shopping_items):
    """Add shopping items to Todoist one by one"""
    if not TODOIST_PROJECT_ID:
        if not find_todoist_project():
            return []
    
    url = "https://api.todoist.com/rest/v2/tasks"
    headers = get_todoist_headers()
    added_items = []
    
    print(f"📝 Adding {len(shopping_items)} items to Todoist...")
    
    for item in shopping_items:
        task_data = {
            "content": item,
            "project_id": TODOIST_PROJECT_ID,
            "description": "Generated by Meal Plan Bot"
        }
        
        response = requests.post(url, headers=headers, json=task_data)
        if response.status_code == 200:
            added_items.append(item)
            print(f"  ✅ Added: {item}")
        else:
            print(f"  ❌ Failed to add: {item}")
    
    return added_items

# ------ OpenRouter AI Functions ------

def generate_shopping_list(recipes):
    """Generate optimized shopping list using OpenRouter with fallback to direct parsing"""
    
    # First try to extract ingredients directly as fallback
    fallback_items = []
    all_ingredients = ""
    
    for recipe in recipes:
        if recipe.ingredients:
            all_ingredients += f"{recipe.name}: {recipe.ingredients}\n"
            # Parse ingredients directly
            for ingredient in recipe.ingredients.split('\n'):
                ingredient = ingredient.strip()
                if ingredient and not ingredient.startswith('#'):
                    # Clean up common ingredient formats
                    ingredient = re.sub(r'^[-•*]\s*', '', ingredient).strip()
                    if ingredient:
                        fallback_items.append(ingredient)
    
    print(f"📝 Extracted {len(fallback_items)} ingredients directly from recipes")
    
    # Try OpenRouter API for optimization
    recipe_info = ""
    for i, recipe in enumerate(recipes, 1):
        recipe_info += f"\n{i}. **{recipe.name}**\n"
        if recipe.ingredients:
            recipe_info += f"   Ingredients: {recipe.ingredients}\n"
        recipe_info += "\n"
    
    # Simplified prompt for better success rate
    prompt = f"""Convert these recipe ingredients into a clean shopping list:
{recipe_info}

Create a shopping list with one item per line, format: "- Item (quantity)"
Remove duplicates and combine similar items.
Keep it simple and clear."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.1   # Very low temperature for consistent output
    }
    
    try:
        print("🤖 Trying OpenRouter API for shopping list optimization...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                shopping_list = result['choices'][0]['message']['content'].strip()
                
                # Parse the shopping list into individual items
                items = []
                for line in shopping_list.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                        item = re.sub(r'^[-•*]\s*', '', line).strip()
                        if item:
                            items.append(item)
                
                if len(items) > 0:
                    print(f"✅ OpenRouter generated {len(items)} optimized shopping list items")
                    return items, shopping_list
        
        print(f"⚠️ OpenRouter API issue (status: {response.status_code}), using direct extraction")
        
    except Exception as e:
        print(f"⚠️ OpenRouter error: {e}, using direct extraction")
    
    # Fallback: Use directly extracted ingredients
    if fallback_items:
        print(f"🔄 Using fallback: {len(fallback_items)} ingredients extracted directly")
        shopping_list_text = "\n".join([f"- {item}" for item in fallback_items])
        return fallback_items, shopping_list_text
    
    # Last resort: Use recipe names
    print("❌ No ingredients found, using recipe names as items")
    recipe_names = [f"{recipe.name} ingredients" for recipe in recipes]
    shopping_list_text = "\n".join([f"- {item}" for item in recipe_names])
    return recipe_names, shopping_list_text

# ------ Discord Bot Functions ------

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f"🤖 {bot.user} is online!")
    print(f"📍 Using channel ID: {MEALPLAN_CHANNEL_ID}")
    
    channel = bot.get_channel(MEALPLAN_CHANNEL_ID)
    if channel:
        await channel.send("🍽️ Meal Plan Bot is online! React with 👍 or type 'meal' to get recipes. Auto-posting every Friday at 5 PM!")
    
    # Start scheduler in background
    def run_scheduler():
        def trigger_meal_plan():
            # Use asyncio.run_coroutine_threadsafe to run async function from thread
            asyncio.run_coroutine_threadsafe(scheduled_meal_plan(), bot.loop)
        
        schedule.every().friday.at("17:00").do(trigger_meal_plan)
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("⏰ Scheduler started - will post meal plan every Friday at 5 PM")

async def scheduled_meal_plan():
    """Scheduled meal plan function for Friday 5 PM"""
    channel = bot.get_channel(MEALPLAN_CHANNEL_ID)
    if channel:
        await channel.send("📅 **Friday 5 PM Auto-Meal Plan!** Time for your weekly recipe selection! 🍽️")
        await generate_meal_plan_workflow(channel)

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    if message.author == bot.user:
        return
    
    if message.channel.id == MEALPLAN_CHANNEL_ID:
        if "👍" in message.content or ":thumbsup:" in message.content or "meal" in message.content.lower():
            await message.add_reaction("🔍")
            await generate_meal_plan_workflow(message.channel)
            await message.remove_reaction("🔍", bot.user)
            await message.add_reaction("✅")
    
    await bot.process_commands(message)

async def generate_meal_plan_workflow(channel):
    """Main workflow: Notion → Details → LLM → Todoist → Present"""
    
    try:
        # Step 1: Retrieve 2 random recipes from Notion
        await channel.send("🔍 **Step 1:** Fetching 2 random recipes from Notion...")
        recipes = get_recipes_from_notion()
        
        if len(recipes) < 2:
            await channel.send("❌ Could not find enough recipes in Notion database. Please check your configuration.")
            return
        
        recipe_names = "\n".join([f"• {recipe.name}" for recipe in recipes])
        await channel.send(f"📋 **Selected recipes:**\n{recipe_names}")
        
        # Step 2: Generate shopping list using LLM (single API call)
        await channel.send("🤖 **Step 2:** Generating optimized shopping list with AI...")
        shopping_items, shopping_list_text = generate_shopping_list(recipes)
        
        if not shopping_items:
            await channel.send("❌ Could not generate shopping list. Continuing with recipe details only.")
            shopping_items = ["Ingredients for selected recipes (check recipe details)"]
        
        # Step 3: Add items to Todoist step by step
        await channel.send(f"📝 **Step 3:** Adding {len(shopping_items)} items to Todoist...")
        added_items = add_items_to_todoist(shopping_items)
        
        if added_items:
            await channel.send(f"✅ Successfully added {len(added_items)} items to Todoist Einkaufsliste!")
        else:
            await channel.send("⚠️ Could not add items to Todoist. Check your configuration.")
        
        # Step 4: Present recipes with links and shopping list
        await channel.send("📖 **Step 4:** Here are your recipes and shopping list!")
        
        # Send recipes with links
        for i, recipe in enumerate(recipes, 1):
            embed = discord.Embed(
                title=f"🍽️ Recipe {i}: {recipe.name}",
                url=recipe.url if recipe.url else None,
                color=discord.Color.green()
            )
            
            if recipe.url:
                embed.add_field(name="🔗 Recipe Link", value=f"[Click here to view recipe]({recipe.url})", inline=False)
            
            if recipe.ingredients:
                # Truncate ingredients if too long
                ingredients = recipe.ingredients[:500] + "..." if len(recipe.ingredients) > 500 else recipe.ingredients
                embed.add_field(name="🥘 Ingredients", value=ingredients, inline=False)
            
            if recipe.instructions:
                # Truncate instructions if too long
                instructions = recipe.instructions[:500] + "..." if len(recipe.instructions) > 500 else recipe.instructions
                embed.add_field(name="👨‍🍳 Instructions", value=instructions, inline=False)
            
            if recipe.tags:
                embed.add_field(name="🏷️ Tags", value=recipe.tags, inline=True)
            
            embed.set_footer(text="Happy cooking! 👨‍🍳")
            await channel.send(embed=embed)
        
        # Send shopping list with Todoist link
        todoist_link = f"https://todoist.com/app/project/{TODOIST_PROJECT_ID}" if TODOIST_PROJECT_ID else "https://todoist.com/app"
        
        shopping_embed = discord.Embed(
            title="🛒 Shopping List",
            description=f"**Added to Todoist:** {len(added_items)} items\n\n{shopping_list_text}",
            color=discord.Color.blue()
        )
        shopping_embed.add_field(
            name="📱 Open in Todoist",
            value=f"[🔗 Click here to view your Einkaufsliste]({todoist_link})",
            inline=False
        )
        shopping_embed.set_footer(text="Items have been added to your Todoist Einkaufsliste project!")
        await channel.send(embed=shopping_embed)
        
        await channel.send("🎉 **Meal planning complete!** Enjoy your cooking! 👨‍🍳✨")
        
    except Exception as e:
        print(f"❌ Error in meal plan workflow: {e}")
        await channel.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="help_meal")
async def help_meal(ctx):
    """Show help information"""
    if ctx.channel.id == MEALPLAN_CHANNEL_ID:
        embed = discord.Embed(
            title="🍽️ Meal Plan Bot Help",
            description="Your intelligent meal planning assistant!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🚀 How to use",
            value="• **Manual:** React with 👍 or type 'meal'\n• **Automatic:** Every Friday at 5:00 PM",
            inline=False
        )
        
        embed.add_field(
            name="🔄 What it does",
            value="1. Fetches 2 random recipes from Notion\n2. Extracts detailed recipe information\n3. Generates optimized shopping list with AI\n4. Adds items to Todoist step by step\n5. Presents recipes with links and shopping list",
            inline=False
        )
        
        embed.add_field(
            name="📅 Commands",
            value="• `!help_meal` - Show this help\n• `!test_meal` - Test meal plan workflow\n• `!next_meal` - Show next scheduled post",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Requirements",
            value="• Notion 'Rezepte schnell' database\n• Todoist 'Einkaufsliste' project\n• OpenRouter API (free tier)",
            inline=False
        )
        
        await ctx.send(embed=embed)

@bot.command(name="test_meal")
async def test_meal(ctx):
    """Test the meal plan workflow"""
    if ctx.channel.id == MEALPLAN_CHANNEL_ID:
        await ctx.send("🧪 Starting meal plan test...")
        await generate_meal_plan_workflow(ctx.channel)

@bot.command(name="next_meal")
async def next_meal(ctx):
    """Show when the next scheduled meal plan will be posted"""
    if ctx.channel.id == MEALPLAN_CHANNEL_ID:
        now = datetime.now()
        # Calculate next Friday 5 PM
        days_until_friday = (4 - now.weekday()) % 7  # Friday is day 4
        if days_until_friday == 0 and now.hour >= 17:  # If it's Friday after 5 PM, next Friday
            days_until_friday = 7
        
        next_friday = now.replace(hour=17, minute=0, second=0, microsecond=0)
        if days_until_friday > 0:
            next_friday = next_friday.replace(day=now.day + days_until_friday)
        
        embed = discord.Embed(
            title="📅 Next Scheduled Meal Plan",
            description=f"Next automatic meal plan: **Friday at 5:00 PM**",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="⏰ Time until next post",
            value=f"In {days_until_friday} days" if days_until_friday > 0 else "Today at 5 PM!",
            inline=False
        )
        embed.add_field(
            name="🍽️ Manual trigger",
            value="Type 'meal' or react with 👍 anytime for instant meal plan",
            inline=False
        )
        
        await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    if not all([DISCORD_TOKEN, NOTION_TOKEN, OPENROUTER_API_KEY, TODOIST_API_KEY]):
        print("❌ Missing required environment variables!")
        print("Required: DISCORD_TOKEN, NOTION_TOKEN, OPENROUTER_API_KEY, TODOIST_API_KEY")
        exit(1)
    
    print("🚀 Starting Refactored Meal Plan Bot...")
    bot.run(DISCORD_TOKEN) 