#!/usr/bin/env python3
"""
Discord Todo Bot with Todoist Integration
Automatically converts messages to todos and manages family task organization
"""

import os
import re
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('todo_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TodoBot')

@dataclass
class TodoItem:
    """Represents a Todoist todo item"""
    id: str
    content: str
    description: str = ""
    priority: int = 1
    due_date: Optional[str] = None
    labels: List[str] = None
    project_id: Optional[str] = None
    completed: bool = False
    created_at: Optional[str] = None
    creator: Optional[str] = None

class TodoistAPI:
    """Wrapper for Todoist API operations"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.todoist.com/rest/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request to Todoist"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
                
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def create_task(self, content: str, description: str = "", priority: int = 1, 
                   due_date: Optional[str] = None, labels: Optional[List[str]] = None,
                   project_id: Optional[str] = None) -> Optional[TodoItem]:
        """Create a new task in Todoist"""
        data = {
            "content": content,
            "description": description,
            "priority": priority
        }
        
        if due_date:
            data["due_string"] = due_date
        if labels:
            data["labels"] = labels
        if project_id:
            data["project_id"] = project_id
            
        result = self._make_request("POST", "/tasks", data)
        if result:
            return TodoItem(
                id=result["id"],
                content=result["content"],
                description=result.get("description", ""),
                priority=result.get("priority", 1),
                due_date=result.get("due", {}).get("string") if result.get("due") else None,
                labels=result.get("labels", []),
                project_id=result.get("project_id"),
                completed=result.get("is_completed", False),
                created_at=result.get("created_at")
            )
        return None
    
    def get_active_tasks(self, project_id: Optional[str] = None) -> List[TodoItem]:
        """Get all active tasks"""
        params = {"filter": "!@completed"}
        if project_id:
            params["project_id"] = project_id
            
        result = self._make_request("GET", "/tasks", params)
        if result:
            return [
                TodoItem(
                    id=task["id"],
                    content=task["content"],
                    description=task.get("description", ""),
                    priority=task.get("priority", 1),
                    due_date=task.get("due", {}).get("string") if task.get("due") else None,
                    labels=task.get("labels", []),
                    project_id=task.get("project_id"),
                    completed=task.get("is_completed", False),
                    created_at=task.get("created_at")
                )
                for task in result
            ]
        return []
    
    def complete_task(self, task_id: str) -> bool:
        """Mark task as completed"""
        result = self._make_request("POST", f"/tasks/{task_id}/close")
        return result is not None
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        result = self._make_request("DELETE", f"/tasks/{task_id}")
        return result is not None

class TodoBot(commands.Bot):
    """Discord Bot for Todo Management with Todoist Integration"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize Todoist API
        self.todoist = TodoistAPI(os.getenv('TODOIST_API_KEY'))
        self.todo_channel_id = int(os.getenv('WEEKLY_PLANNING_CHANNEL_ID', '1368180016785002536'))
        
        # Priority keywords mapping
        self.priority_keywords = {
            'urgent': 4, 'wichtig': 4, 'dringend': 4, 'sofort': 4,
            'hoch': 3, 'high': 3, 'wichtig': 3,
            'normal': 2, 'medium': 2,
            'niedrig': 1, 'low': 1, 'später': 1
        }
        
        # Date parsing patterns
        self.date_patterns = {
            r'\b(heute|today)\b': 'today',
            r'\b(morgen|tomorrow)\b': 'tomorrow',
            r'\b(übermorgen)\b': 'in 2 days',
            r'\b(nächste woche|next week)\b': 'next week',
            r'\b(nächster monat|next month)\b': 'next month',
            r'\b(\d{1,2})\.(\d{1,2})\b': lambda m: f"{m.group(2)}/{m.group(1)}",  # DD.MM -> MM/DD
            r'\b(montag|monday)\b': 'monday',
            r'\b(dienstag|tuesday)\b': 'tuesday',
            r'\b(mittwoch|wednesday)\b': 'wednesday',
            r'\b(donnerstag|thursday)\b': 'thursday',
            r'\b(freitag|friday)\b': 'friday',
            r'\b(samstag|saturday)\b': 'saturday',
            r'\b(sonntag|sunday)\b': 'sunday'
        }
        
        # Family member labels
        self.family_labels = {
            'marc': 'Marc', 'maggie': 'Maggie', 'mama': 'Maggie', 'papa': 'Marc',
            'gemeinsam': 'Familie', 'together': 'Familie', 'alle': 'Familie'
        }
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} is connected and ready!')
        logger.info(f'Monitoring channel ID: {self.todo_channel_id}')
        
        # Test Todoist connection
        try:
            tasks = self.todoist.get_active_tasks()
            logger.info(f'Successfully connected to Todoist. Found {len(tasks)} active tasks.')
        except Exception as e:
            logger.error(f'Failed to connect to Todoist: {e}')
    
    async def on_message(self, message):
        """Handle incoming messages"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only process messages from the todo channel
        if message.channel.id != self.todo_channel_id:
            await self.process_commands(message)
            return
        
        # Skip commands
        if message.content.startswith('!'):
            await self.process_commands(message)
            return
        
        # Convert message to todo
        await self.create_todo_from_message(message)
        await self.process_commands(message)
    
    def parse_message_for_todo(self, message: discord.Message) -> Dict[str, Any]:
        """Parse message content for todo details"""
        content = message.content.lower()
        
        # Extract priority
        priority = 1
        for keyword, prio in self.priority_keywords.items():
            if keyword in content:
                priority = max(priority, prio)
        
        # Extract due date
        due_date = None
        for pattern, replacement in self.date_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if callable(replacement):
                    due_date = replacement(match)
                else:
                    due_date = replacement
                break
        
        # Extract family member labels
        labels = []
        for keyword, label in self.family_labels.items():
            if keyword in content:
                labels.append(label)
        
        # If no specific family member mentioned, use message author
        if not labels:
            labels.append(message.author.display_name)
        
        # Clean content for todo title
        todo_content = message.content
        
        return {
            'content': todo_content,
            'description': f'Created from Discord message by {message.author.display_name}\nOriginal: {message.content}',
            'priority': priority,
            'due_date': due_date,
            'labels': labels,
            'creator': message.author.display_name
        }
    
    async def create_todo_from_message(self, message: discord.Message):
        """Create a todo item from Discord message"""
        try:
            todo_data = self.parse_message_for_todo(message)
            
            # Create todo in Todoist
            todo = self.todoist.create_task(**todo_data)
            
            if todo:
                # Create confirmation embed
                embed = discord.Embed(
                    title="✅ Todo erstellt!",
                    description=f"**{todo.content}**",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                
                if todo.due_date:
                    embed.add_field(name="📅 Fällig", value=todo.due_date, inline=True)
                
                if todo.labels:
                    embed.add_field(name="🏷️ Labels", value=", ".join(todo.labels), inline=True)
                
                priority_emoji = ["", "🟢", "🟡", "🟠", "🔴"]
                embed.add_field(name="⚡ Priorität", value=priority_emoji[todo.priority], inline=True)
                
                embed.set_footer(text=f"Todo ID: {todo.id}")
                
                await message.reply(embed=embed, delete_after=10)
                
                # Add reaction to original message
                await message.add_reaction("✅")
                
                logger.info(f"Created todo: {todo.content} (ID: {todo.id})")
                
            else:
                await message.reply("❌ Fehler beim Erstellen des Todos!", delete_after=5)
                logger.error("Failed to create todo")
                
        except Exception as e:
            logger.error(f"Error creating todo: {e}")
            await message.reply("❌ Fehler beim Erstellen des Todos!", delete_after=5)
    
    @commands.command(name='todo', aliases=['todos', 'list'])
    async def show_todos(self, ctx):
        """Show all active todos"""
        try:
            tasks = self.todoist.get_active_tasks()
            
            if not tasks:
                embed = discord.Embed(
                    title="📝 Todo Liste",
                    description="Keine aktiven Todos gefunden! 🎉",
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
                return
            
            # Sort by priority (highest first) and due date
            tasks.sort(key=lambda x: (-x.priority, x.due_date or 'zzz'))
            
            # Create embed
            embed = discord.Embed(
                title="📝 Aktive Todo Liste",
                color=0x3498db,
                timestamp=datetime.utcnow()
            )
            
            priority_emoji = ["", "🟢", "🟡", "🟠", "🔴"]
            
            for i, task in enumerate(tasks[:20]):  # Limit to 20 todos
                priority_icon = priority_emoji[task.priority]
                due_info = f" 📅 {task.due_date}" if task.due_date else ""
                labels_info = f" 🏷️ {', '.join(task.labels)}" if task.labels else ""
                
                field_name = f"{priority_icon} Todo #{i+1}"
                field_value = f"**{task.content}**{due_info}{labels_info}"
                
                if task.description and not task.description.startswith('Created from Discord'):
                    field_value += f"\n*{task.description[:100]}{'...' if len(task.description) > 100 else ''}*"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
            
            if len(tasks) > 20:
                embed.set_footer(text=f"Zeige 20 von {len(tasks)} Todos")
            else:
                embed.set_footer(text=f"Gesamt: {len(tasks)} Todos")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing todos: {e}")
            await ctx.send("❌ Fehler beim Laden der Todos!")
    
    @commands.command(name='complete', aliases=['done', 'erledigt'])
    async def complete_todo(self, ctx, *, search_term: str):
        """Mark a todo as completed"""
        try:
            tasks = self.todoist.get_active_tasks()
            
            # Find task by content match
            matching_tasks = [task for task in tasks if search_term.lower() in task.content.lower()]
            
            if not matching_tasks:
                await ctx.send(f"❌ Kein Todo gefunden mit '{search_term}'")
                return
            
            if len(matching_tasks) > 1:
                embed = discord.Embed(
                    title="🤔 Mehrere Todos gefunden",
                    description="Bitte sei spezifischer:",
                    color=0xffaa00
                )
                for i, task in enumerate(matching_tasks[:5]):
                    embed.add_field(
                        name=f"Todo #{i+1}",
                        value=task.content,
                        inline=False
                    )
                await ctx.send(embed=embed)
                return
            
            # Complete the todo
            task = matching_tasks[0]
            if self.todoist.complete_task(task.id):
                embed = discord.Embed(
                    title="✅ Todo erledigt!",
                    description=f"**{task.content}**",
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
                await ctx.message.add_reaction("✅")
            else:
                await ctx.send("❌ Fehler beim Abschließen des Todos!")
            
        except Exception as e:
            logger.error(f"Error completing todo: {e}")
            await ctx.send("❌ Fehler beim Abschließen des Todos!")
    
    @commands.command(name='delete', aliases=['remove', 'del'])
    async def delete_todo(self, ctx, *, search_term: str):
        """Delete a todo"""
        try:
            tasks = self.todoist.get_active_tasks()
            
            # Find task by content match
            matching_tasks = [task for task in tasks if search_term.lower() in task.content.lower()]
            
            if not matching_tasks:
                await ctx.send(f"❌ Kein Todo gefunden mit '{search_term}'")
                return
            
            if len(matching_tasks) > 1:
                embed = discord.Embed(
                    title="🤔 Mehrere Todos gefunden",
                    description="Bitte sei spezifischer:",
                    color=0xffaa00
                )
                for i, task in enumerate(matching_tasks[:5]):
                    embed.add_field(
                        name=f"Todo #{i+1}",
                        value=task.content,
                        inline=False
                    )
                await ctx.send(embed=embed)
                return
            
            # Delete the todo
            task = matching_tasks[0]
            if self.todoist.delete_task(task.id):
                embed = discord.Embed(
                    title="🗑️ Todo gelöscht!",
                    description=f"**{task.content}**",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                await ctx.message.add_reaction("🗑️")
            else:
                await ctx.send("❌ Fehler beim Löschen des Todos!")
            
        except Exception as e:
            logger.error(f"Error deleting todo: {e}")
            await ctx.send("❌ Fehler beim Löschen des Todos!")
    
    @commands.command(name='stats')
    async def show_stats(self, ctx):
        """Show todo statistics"""
        try:
            tasks = self.todoist.get_active_tasks()
            
            # Count by priority
            priority_counts = {1: 0, 2: 0, 3: 0, 4: 0}
            label_counts = {}
            due_today = 0
            overdue = 0
            
            today = datetime.now().date()
            
            for task in tasks:
                priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1
                
                for label in task.labels or []:
                    label_counts[label] = label_counts.get(label, 0) + 1
                
                if task.due_date:
                    # Simple check for today/overdue (could be improved with proper date parsing)
                    if 'heute' in task.due_date.lower() or 'today' in task.due_date.lower():
                        due_today += 1
            
            embed = discord.Embed(
                title="📊 Todo Statistiken",
                color=0x9b59b6,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📈 Gesamt", 
                value=f"**{len(tasks)}** aktive Todos", 
                inline=True
            )
            
            embed.add_field(
                name="📅 Heute fällig", 
                value=f"**{due_today}** Todos", 
                inline=True
            )
            
            # Priority breakdown
            priority_text = "\n".join([
                f"🔴 Urgent: {priority_counts[4]}",
                f"🟠 Hoch: {priority_counts[3]}",
                f"🟡 Normal: {priority_counts[2]}",
                f"🟢 Niedrig: {priority_counts[1]}"
            ])
            embed.add_field(name="⚡ Nach Priorität", value=priority_text, inline=False)
            
            # Top labels
            if label_counts:
                top_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                label_text = "\n".join([f"🏷️ {label}: {count}" for label, count in top_labels])
                embed.add_field(name="👥 Nach Person/Label", value=label_text, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
            await ctx.send("❌ Fehler beim Laden der Statistiken!")
    
    @commands.command(name='help_todo')
    async def help_todo(self, ctx):
        """Show todo bot help"""
        embed = discord.Embed(
            title="🤖 Todo Bot Hilfe",
            description="Automatische Todo-Verwaltung mit Todoist",
            color=0x3498db
        )
        
        embed.add_field(
            name="📝 Automatisch",
            value="Jede Nachricht in diesem Channel wird als Todo erstellt!",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Smart Features",
            value="• **Priorität**: `wichtig`, `dringend`, `urgent` → Hohe Priorität\n"
                  "• **Datum**: `heute`, `morgen`, `montag`, `15.12` → Fälligkeitsdatum\n"
                  "• **Familie**: `Marc`, `Maggie`, `gemeinsam` → Automatische Labels",
            inline=False
        )
        
        embed.add_field(
            name="💬 Commands",
            value="`!todo` - Alle aktiven Todos anzeigen\n"
                  "`!complete <suche>` - Todo als erledigt markieren\n"
                  "`!delete <suche>` - Todo löschen\n"
                  "`!stats` - Statistiken anzeigen",
            inline=False
        )
        
        embed.add_field(
            name="💡 Beispiele",
            value="• `Wichtig: Einkaufen morgen`\n"
                  "• `Marc soll den Müll rausbringen`\n"
                  "• `Gemeinsam: Urlaub planen nächste Woche`",
            inline=False
        )
        
        await ctx.send(embed=embed)

def main():
    """Run the Todo Bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        return
    
    todoist_token = os.getenv('TODOIST_API_KEY')
    if not todoist_token:
        logger.error("TODOIST_API_KEY not found in environment variables!")
        return
    
    bot = TodoBot()
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
