#!/usr/bin/env python3
"""
Weekly Todo Bot with Notion Integration and LLM Enhancement
Fetches weekly cleaning tasks from Notion, enhances them with AI, and posts to Discord
"""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json
import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# API Clients
from notion_client import Client as NotionClient
from openai import OpenAI

# Load environment variables from main discord directory
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
HAUSHALTSPLAN_CHANNEL_ID = int(os.getenv("HAUSHALTSPLAN_CHANNEL_ID"))
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("CLEANDB_ID")
OPENAI_API_KEY = "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"

# Initialize clients
notion = NotionClient(auth=NOTION_TOKEN)
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Global variables
active_todo_messages = {}
weekly_tasks_file = "weekly_tasks.json"

class WeeklyTask:
    """Represents a weekly cleaning task"""
    def __init__(self, name: str, description: str = "", priority: int = 5, improved_desc: str = ""):
        self.name = name
        self.description = description
        self.priority = priority
        self.improved_desc = improved_desc or description
        self.completed = False
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "improved_desc": self.improved_desc,
            "completed": self.completed
        }

class NotionHandler:
    """Handles all Notion API interactions"""
    
    @staticmethod
    async def fetch_weekly_tasks() -> List[WeeklyTask]:
        """Fetch weekly tasks from Notion database"""
        try:
            print("🔍 Fetching weekly tasks from Notion...")
            
            # Query the database for weekly tasks
            response = notion.databases.query(
                database_id=NOTION_DATABASE_ID,
                filter={
                    "property": "Mehrfachauswahl",
                    "multi_select": {
                        "contains": "Weekly"
                    }
                }
            )
            
            tasks = []
            for page in response.get("results", []):
                # Extract task name from title property
                title_prop = page.get("properties", {}).get("Name", {})
                if title_prop.get("type") == "title":
                    title_list = title_prop.get("title", [])
                    if title_list:
                        task_name = title_list[0].get("text", {}).get("content", "Unnamed Task")
                        
                        # Extract description from Text property
                        text_prop = page.get("properties", {}).get("Text", {})
                        description = ""
                        if text_prop.get("type") == "rich_text":
                            text_list = text_prop.get("rich_text", [])
                            if text_list:
                                description = text_list[0].get("text", {}).get("content", "")
                        
                        task = WeeklyTask(name=task_name, description=description)
                        tasks.append(task)
                        print(f"  ✅ Found task: {task_name}")
            
            print(f"📊 Retrieved {len(tasks)} weekly tasks from Notion")
            return tasks
            
        except Exception as e:
            print(f"❌ Error fetching from Notion: {e}")
            # Return fallback tasks based on the image data
            fallback_tasks = [
                WeeklyTask("Saugen", "Alle Räume gründlich staubsaugen"),
                WeeklyTask("Wischen", "Böden in Küche und Bad wischen"),
                WeeklyTask("Bäder", "Badezimmer komplett reinigen"),
            ]
            print(f"🔄 Using {len(fallback_tasks)} fallback tasks")
            return fallback_tasks

class LLMHandler:
    """Handles all LLM interactions for task enhancement"""
    
    @staticmethod
    async def rank_tasks(tasks: List[WeeklyTask]) -> List[WeeklyTask]:
        """Use LLM to rank tasks by priority"""
        try:
            task_list = "\n".join([f"- {task.name}: {task.description}" for task in tasks])
            
            prompt = f"""
            Please rank these weekly cleaning tasks by priority (1-10, where 10 is most important).
            Consider factors like hygiene, frequency needed, and household impact.
            
            Tasks:
            {task_list}
            
            Respond with just the task names and their priority numbers in this format:
            TaskName: 8
            TaskName: 6
            etc.
            """
            
            response = openai_client.chat.completions.create(
                model="moonshotai/kimi-k2:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            rankings = response.choices[0].message.content.strip().split('\n')
            
            # Parse rankings and update tasks
            for line in rankings:
                if ':' in line:
                    task_name, priority_str = line.split(':', 1)
                    task_name = task_name.strip()
                    try:
                        priority = int(priority_str.strip())
                        for task in tasks:
                            if task.name.lower() in task_name.lower() or task_name.lower() in task.name.lower():
                                task.priority = priority
                                break
                    except ValueError:
                        continue
            
            # Sort by priority (highest first)
            tasks.sort(key=lambda x: x.priority, reverse=True)
            print("🎯 Tasks ranked by AI priority")
            
        except Exception as e:
            print(f"❌ Error ranking tasks with LLM: {e}")
            # Assign random priorities as fallback
            for i, task in enumerate(tasks):
                task.priority = 10 - i
        
        return tasks
    
    @staticmethod
    async def improve_random_task(tasks: List[WeeklyTask]) -> WeeklyTask:
        """Improve a random task description using LLM"""
        if not tasks:
            return None
            
        try:
            # Select random task to improve
            task_to_improve = random.choice(tasks)
            
            prompt = f"""
            Improve this cleaning task description to be more detailed, motivating, and actionable.
            Keep it concise but helpful. Add specific tips or techniques.
            
            Original task: {task_to_improve.name}
            Current description: {task_to_improve.description}
            
            Provide an improved description in German (since the original tasks are in German):
            """
            
            response = openai_client.chat.completions.create(
                model="moonshotai/kimi-k2:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            
            improved_description = response.choices[0].message.content.strip()
            task_to_improve.improved_desc = improved_description
            
            print(f"✨ Improved task: {task_to_improve.name}")
            return task_to_improve
            
        except Exception as e:
            print(f"❌ Error improving task with LLM: {e}")
            return None
    
    @staticmethod
    async def generate_weekly_intro(tasks: List[WeeklyTask], improved_task: WeeklyTask = None) -> str:
        """Generate an engaging intro message for the weekly tasks"""
        try:
            improved_info = f"\n🌟 This week's AI-enhanced task: {improved_task.name}" if improved_task else ""
            
            prompt = f"""
            Create a motivating and friendly introduction for weekly household cleaning tasks.
            Keep it brief, encouraging, and in German. Mention that these are the weekly cleaning priorities.
            {improved_info}
            
            Number of tasks: {len(tasks)}
            
            Write a short, enthusiastic message to present these weekly tasks:
            """
            
            response = openai_client.chat.completions.create(
                model="moonshotai/kimi-k2:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.8
            )
            
            intro = response.choices[0].message.content.strip()
            return intro
            
        except Exception as e:
            print(f"❌ Error generating intro: {e}")
            return "🏠 Zeit für die wöchentliche Reinigung! Hier sind eure Aufgaben:"

class WeeklyTaskManager:
    """Manages weekly task data and persistence"""
    
    @staticmethod
    def save_weekly_tasks(tasks: List[WeeklyTask]):
        """Save tasks to file"""
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tasks": [task.to_dict() for task in tasks]
        }
        with open(weekly_tasks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_weekly_tasks() -> List[WeeklyTask]:
        """Load tasks from file"""
        if os.path.exists(weekly_tasks_file):
            with open(weekly_tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tasks = []
                for task_data in data.get("tasks", []):
                    task = WeeklyTask(
                        name=task_data["name"],
                        description=task_data["description"],
                        priority=task_data["priority"],
                        improved_desc=task_data["improved_desc"]
                    )
                    task.completed = task_data["completed"]
                    tasks.append(task)
                return tasks
        return []

async def create_weekly_embed(tasks: List[WeeklyTask], intro_message: str) -> discord.Embed:
    """Create the weekly tasks embed"""
    embed = discord.Embed(
        title="🗓️ Wöchentliche Haushaltsaufgaben",
        description=intro_message,
        color=discord.Color.green()
    )
    
    for i, task in enumerate(tasks, 1):
        status = "✅" if task.completed else "⬜"
        priority_stars = "⭐" * min(task.priority, 5) if task.priority > 5 else "⭐" * task.priority
        
        description_to_show = task.improved_desc if task.improved_desc != task.description else task.description
        
        embed.add_field(
            name=f"{i}. {task.name} {priority_stars}",
            value=f"Status: {status}\n📝 {description_to_show}",
            inline=False
        )
    
    embed.set_footer(text=f"Woche vom {datetime.now().strftime('%d.%m.%Y')} | Reagiere mit Zahlen zum Abhaken!")
    return embed

async def process_and_send_weekly_tasks(channel):
    """Main function to process and send weekly tasks"""
    try:
        print("🚀 Starting weekly task processing...")
        
        # 1. Fetch tasks from Notion
        tasks = await NotionHandler.fetch_weekly_tasks()
        
        if not tasks:
            await channel.send("❌ Keine wöchentlichen Aufgaben gefunden!")
            return
        
        # 2. Rank tasks with LLM
        tasks = await LLMHandler.rank_tasks(tasks)
        
        # 3. Improve one random task
        improved_task = await LLMHandler.improve_random_task(tasks)
        
        # 4. Generate intro message
        intro = await LLMHandler.generate_weekly_intro(tasks, improved_task)
        
        # 5. Save tasks
        WeeklyTaskManager.save_weekly_tasks(tasks)
        
        # 6. Create and send embed
        embed = await create_weekly_embed(tasks, intro)
        message = await channel.send(embed=embed)
        
        # 7. Add reactions
        for i in range(1, min(10, len(tasks) + 1)):
            await message.add_reaction(f"{i}\u20e3")
        
        # Store message for reaction handling
        active_todo_messages[message.id] = tasks
        
        print("✅ Weekly tasks posted successfully!")
        
    except Exception as e:
        print(f"❌ Error processing weekly tasks: {e}")
        await channel.send(f"❌ Fehler beim Laden der Aufgaben: {e}")

@bot.event
async def on_ready():
    print(f"🤖 {bot.user} ist online!")
    print(f"📍 Kanal ID: {HAUSHALTSPLAN_CHANNEL_ID}")
    
@bot.event
async def on_ready():
    print(f"🤖 {bot.user} ist online!")
    print(f"📍 Kanal ID: {HAUSHALTSPLAN_CHANNEL_ID}")
    
    channel = bot.get_channel(HAUSHALTSPLAN_CHANNEL_ID)
    if channel:
        startup_message = (
            "🗓️ **Weekly Todo Bot ist online!** 🤖\n\n"
            "Ich organisiere deine wöchentlichen Haushaltsaufgaben! Das kann ich:\n"
            "• 📋 Aufgaben aus deiner Notion-Datenbank holen\n"
            "• 🤖 AI-unterstützte Aufgaben-Verbesserungen und Priorisierung\n"
            "• ✅ Interaktive Todo-Listen mit Reaktions-Abhaken\n"
            "• 📅 Automatische wöchentliche Posts (Freitags 8:00)\n"
            "• ⭐ Intelligente Prioritäts-Bewertung\n\n"
            "**Befehle:**\n"
            "• `!weekly_status` - Aktuellen Status anzeigen\n"
            "• `!help_weekly` - Detaillierte Hilfe\n"
            "• Schreibe `Cleaning` - Sofortige wöchentliche Aufgaben\n\n"
            "Reagiere mit Zahlen (1️⃣-9️⃣) um Aufgaben abzuhaken!\n"
            "Automatische Posts jeden Freitag um 8:00 Uhr."
        )
        await channel.send(startup_message)
    
    # Start scheduler in background
    def run_scheduler():
        schedule.every().friday.at("08:00").do(lambda: asyncio.create_task(scheduled_weekly_post()))
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("⏰ Scheduler started - will post every Friday at 8 AM")

async def scheduled_weekly_post():
    """Scheduled weekly post function"""
    channel = bot.get_channel(HAUSHALTSPLAN_CHANNEL_ID)
    if channel:
        await process_and_send_weekly_tasks(channel)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.channel.id == HAUSHALTSPLAN_CHANNEL_ID:
        if "cleaning" in message.content.lower() or "reinigung" in message.content.lower():
            await process_and_send_weekly_tasks(message.channel)
    
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reactions to mark tasks complete"""
    if user == bot.user:
        return
    
    if reaction.message.id in active_todo_messages:
        if str(reaction.emoji)[0].isdigit() and str(reaction.emoji).endswith('\u20e3'):
            task_index = int(str(reaction.emoji)[0]) - 1
            tasks = active_todo_messages[reaction.message.id]
            
            if 0 <= task_index < len(tasks):
                # Toggle completion
                tasks[task_index].completed = not tasks[task_index].completed
                
                # Save updated tasks
                WeeklyTaskManager.save_weekly_tasks(tasks)
                
                # Update embed
                intro = "🏠 Wöchentliche Reinigungsaufgaben (aktualisiert)"
                updated_embed = await create_weekly_embed(tasks, intro)
                await reaction.message.edit(embed=updated_embed)

@bot.command(name="weekly_status")
async def weekly_status(ctx):
    """Show current weekly task status"""
    if ctx.channel.id == HAUSHALTSPLAN_CHANNEL_ID:
        tasks = WeeklyTaskManager.load_weekly_tasks()
        if tasks:
            completed = sum(1 for task in tasks if task.completed)
            total = len(tasks)
            percentage = (completed / total) * 100 if total > 0 else 0
            
            await ctx.send(f"📊 **Wöchentlicher Fortschritt:** {completed}/{total} Aufgaben erledigt ({percentage:.1f}%)")
        else:
            await ctx.send("❌ Keine wöchentlichen Aufgaben geladen.")

@bot.command(name="help_weekly")
async def help_weekly(ctx):
    """Show help for weekly bot"""
    if ctx.channel.id == HAUSHALTSPLAN_CHANNEL_ID:
        help_text = """
🤖 **Weekly Todo Bot Hilfe**

**Aufgaben anzeigen:**
- Schreibe `Cleaning` oder `Reinigung`
- Automatisch jeden Freitag um 8:00 Uhr

**Aufgaben abhaken:**
- Reagiere mit der Nummer der Aufgabe (1️⃣, 2️⃣, etc.)
- Nochmal reagieren zum rückgängig machen

**Befehle:**
- `!weekly_status` - Aktueller Fortschritt
- `!help_weekly` - Diese Hilfe

**Features:**
- 🔗 Lädt Aufgaben aus Notion
- 🤖 KI-Verbesserung der Beschreibungen  
- 🎯 Intelligente Priorisierung
- 📅 Automatische wöchentliche Posts
        """
        await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    if not all([DISCORD_TOKEN, HAUSHALTSPLAN_CHANNEL_ID, NOTION_TOKEN, OPENAI_API_KEY]):
        print("❌ Missing required environment variables!")
        print("Required: DISCORD_TOKEN, HAUSHALTSPLAN_CHANNEL_ID, NOTION_TOKEN, OPENROUTER_API_KEY")
        exit(1)
    
    print("🚀 Starting Weekly Todo Bot...")
    bot.run(DISCORD_TOKEN) 