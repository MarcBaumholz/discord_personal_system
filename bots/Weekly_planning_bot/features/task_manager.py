import discord
from discord.ext import commands
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from core.database import get_database
from core.models import Task, WeeklyPlan, Priority, TaskCategory

logger = logging.getLogger('weekly_planning_bot.task_manager')

class TaskInteractionView(discord.ui.View):
    """Interactive view for task management with buttons"""
    
    def __init__(self, user_id: int, plan_id: int, tasks: List[Task], timeout: float = 300):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.plan_id = plan_id
        self.tasks = tasks
        self.current_page = 0
        self.tasks_per_page = 5
        
        # Add navigation buttons
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.clear_items()
        
        # Task completion buttons for current page
        start_idx = self.current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, len(self.tasks))
        
        for i in range(start_idx, end_idx):
            task = self.tasks[i]
            button_emoji = "✅" if task.completed else "⬜"
            button_label = f"{task.title[:20]}..."
            
            button = discord.ui.Button(
                label=button_label,
                emoji=button_emoji,
                style=discord.ButtonStyle.success if task.completed else discord.ButtonStyle.secondary,
                custom_id=f"task_{task.id}"
            )
            button.callback = self.create_task_callback(task.id, i)
            self.add_item(button)
        
        # Navigation buttons
        if len(self.tasks) > self.tasks_per_page:
            # Previous page button
            prev_button = discord.ui.Button(
                label="◀️ Previous",
                style=discord.ButtonStyle.primary,
                disabled=self.current_page == 0
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)
            
            # Next page button
            next_button = discord.ui.Button(
                label="Next ▶️",
                style=discord.ButtonStyle.primary,
                disabled=(self.current_page + 1) * self.tasks_per_page >= len(self.tasks)
            )
            next_button.callback = self.next_page
            self.add_item(next_button)
        
        # Action buttons
        refresh_button = discord.ui.Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.secondary
        )
        refresh_button.callback = self.refresh_view
        self.add_item(refresh_button)
        
        stats_button = discord.ui.Button(
            label="📊 Stats",
            style=discord.ButtonStyle.secondary
        )
        stats_button.callback = self.show_stats
        self.add_item(stats_button)
    
    def create_task_callback(self, task_id: int, task_index: int):
        """Create callback function for task button"""
        async def task_callback(interaction: discord.Interaction):
            await self.toggle_task(interaction, task_id, task_index)
        return task_callback
    
    async def toggle_task(self, interaction: discord.Interaction, task_id: int, task_index: int):
        """Toggle task completion status"""
        try:
            # Update task in database
            task = self.tasks[task_index]
            new_status = not task.completed
            
            db = get_database()
            success = await db.update_task_status(task_id, new_status)
            
            if success:
                # Update local task object
                task.completed = new_status
                task.completed_at = datetime.now() if new_status else None
                
                # Update buttons
                self.update_buttons()
                
                # Create updated embed
                embed = await self.create_task_embed()
                
                await interaction.response.edit_message(embed=embed, view=self)
                
                # Send feedback message
                status_text = "completed" if new_status else "reopened"
                await interaction.followup.send(
                    f"✅ Task '{task.title}' has been {status_text}!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Failed to update task. Please try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error toggling task {task_id}: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again.",
                ephemeral=True
            )
    
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = await self.create_task_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        max_pages = (len(self.tasks) - 1) // self.tasks_per_page
        if self.current_page < max_pages:
            self.current_page += 1
            self.update_buttons()
            embed = await self.create_task_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def refresh_view(self, interaction: discord.Interaction):
        """Refresh the task view"""
        try:
            # Reload tasks from database
            db = get_database()
            plan_data = await db.get_weekly_plan(self.user_id)
            
            if plan_data:
                # Update tasks list
                self.tasks = []
                for day_tasks in plan_data['tasks'].values():
                    for task_data in day_tasks:
                        task = Task(
                            id=task_data['id'],
                            title=task_data['title'],
                            completed=task_data['completed'],
                            priority=task_data['priority'],
                            category=task_data['category']
                        )
                        self.tasks.append(task)
                
                self.update_buttons()
                embed = await self.create_task_embed()
                await interaction.response.edit_message(embed=embed, view=self)
                
                await interaction.followup.send(
                    "🔄 Task view refreshed!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Could not refresh tasks. Please try again.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error refreshing task view: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while refreshing.",
                ephemeral=True
            )
    
    async def show_stats(self, interaction: discord.Interaction):
        """Show quick task statistics"""
        try:
            total_tasks = len(self.tasks)
            completed_tasks = sum(1 for task in self.tasks if task.completed)
            completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0
            
            # Category breakdown
            category_stats = {}
            for task in self.tasks:
                if task.category not in category_stats:
                    category_stats[task.category] = {'total': 0, 'completed': 0}
                
                category_stats[task.category]['total'] += 1
                if task.completed:
                    category_stats[task.category]['completed'] += 1
            
            # Create stats embed
            embed = discord.Embed(
                title="📊 Quick Task Statistics",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Overall Progress",
                value=f"{completed_tasks}/{total_tasks} tasks ({completion_rate:.1%})\n"
                      f"{'█' * int(completion_rate * 10)}{'░' * (10 - int(completion_rate * 10))}",
                inline=False
            )
            
            # Category breakdown
            category_text = ""
            for category, stats in category_stats.items():
                emoji = TaskCategory.get_emoji(category)
                rate = stats['completed'] / stats['total'] if stats['total'] > 0 else 0
                category_text += f"{emoji} {category.title()}: {stats['completed']}/{stats['total']} ({rate:.0%})\n"
            
            if category_text:
                embed.add_field(
                    name="By Category",
                    value=category_text,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing task stats: {e}")
            await interaction.response.send_message(
                "❌ Error generating statistics.",
                ephemeral=True
            )
    
    async def create_task_embed(self) -> discord.Embed:
        """Create embed showing current page of tasks"""
        embed = discord.Embed(
            title="🎯 Interactive Task Manager",
            description="Click buttons below to toggle task completion",
            color=discord.Color.green()
        )
        
        start_idx = self.current_page * self.tasks_per_page
        end_idx = min(start_idx + self.tasks_per_page, len(self.tasks))
        
        # Show current page tasks
        task_text = ""
        for i in range(start_idx, end_idx):
            task = self.tasks[i]
            status_emoji = "✅" if task.completed else "⬜"
            priority_emoji = Priority.get_emoji(task.priority)
            category_emoji = TaskCategory.get_emoji(task.category)
            
            task_text += f"{status_emoji} {priority_emoji} {category_emoji} **{task.title}**\n"
            if hasattr(task, 'scheduled_time') and task.scheduled_time:
                task_text += f"   ⏰ {task.scheduled_time.strftime('%H:%M')}\n"
            task_text += "\n"
        
        if task_text:
            embed.add_field(
                name=f"Tasks (Page {self.current_page + 1}/{(len(self.tasks) - 1) // self.tasks_per_page + 1})",
                value=task_text,
                inline=False
            )
        
        # Overall progress
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks if task.completed)
        completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0
        
        progress_bar = "█" * int(completion_rate * 20) + "░" * (20 - int(completion_rate * 20))
        embed.add_field(
            name="Overall Progress",
            value=f"{completed_tasks}/{total_tasks} ({completion_rate:.1%})\n{progress_bar}",
            inline=False
        )
        
        embed.set_footer(text="💡 Click task buttons to toggle completion • 🔄 Refresh • 📊 View stats")
        
        return embed

class TaskManagerCog(commands.Cog):
    """Task management cog with interactive features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = get_database()
    
    @commands.command(name="tasks")
    async def interactive_tasks(self, ctx, action: str = "view"):
        """Interactive task management command
        
        Usage:
        !tasks - View and manage tasks interactively
        !tasks quick - Quick task overview
        !tasks category [category] - Filter by category
        """
        try:
            # Get user from database
            user = await self.db.get_or_create_user(str(ctx.author.id), ctx.author.display_name)
            
            if action == "quick":
                await self.show_quick_overview(ctx, user['id'])
                return
            
            if action.startswith("category"):
                parts = action.split()
                category = parts[1] if len(parts) > 1 else None
                await self.show_category_tasks(ctx, user['id'], category)
                return
            
            # Get current weekly plan
            plan_data = await self.db.get_weekly_plan(user['id'])
            
            if not plan_data:
                embed = discord.Embed(
                    title="❌ No Weekly Plan Found",
                    description="Create a weekly plan first using `!plan`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Convert to Task objects
            tasks = []
            for day_name, day_tasks in plan_data['tasks'].items():
                for task_data in day_tasks:
                    task = Task(
                        id=task_data['id'],
                        title=task_data['title'],
                        completed=task_data['completed'],
                        priority=task_data['priority'],
                        category=task_data['category']
                    )
                    if task_data.get('time'):
                        try:
                            hour, minute = map(int, task_data['time'].split(':'))
                            task.scheduled_time = datetime.min.time().replace(hour=hour, minute=minute)
                        except:
                            pass
                    tasks.append(task)
            
            if not tasks:
                embed = discord.Embed(
                    title="📋 No Tasks Found",
                    description="Your weekly plan doesn't have any tasks yet.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return
            
            # Create interactive view
            view = TaskInteractionView(user['id'], plan_data['id'], tasks)
            embed = await view.create_task_embed()
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in interactive_tasks: {e}")
            await ctx.send("❌ An error occurred. Please try again.")
    
    async def show_quick_overview(self, ctx, user_id: int):
        """Show quick task overview without interactive elements"""
        try:
            plan_data = await self.db.get_weekly_plan(user_id)
            
            if not plan_data:
                await ctx.send("❌ No weekly plan found. Create one first using `!plan`")
                return
            
            embed = discord.Embed(
                title="📋 Quick Task Overview",
                color=discord.Color.blue()
            )
            
            total_tasks = plan_data['total_tasks']
            completed_tasks = plan_data['completed_tasks']
            completion_rate = plan_data['completion_rate']
            
            embed.add_field(
                name="Overall Progress",
                value=f"{completed_tasks}/{total_tasks} ({completion_rate:.1%})\n"
                      f"{'█' * int(completion_rate * 10)}{'░' * (10 - int(completion_rate * 10))}",
                inline=False
            )
            
            # Today's tasks
            today = datetime.now().strftime('%A')
            today_tasks = plan_data['tasks'].get(today, [])
            
            if today_tasks:
                today_text = ""
                for task in today_tasks[:5]:  # Show first 5 tasks
                    status = "✅" if task['completed'] else "⬜"
                    today_text += f"{status} {task['title']}\n"
                
                if len(today_tasks) > 5:
                    today_text += f"... and {len(today_tasks) - 5} more tasks"
                
                embed.add_field(
                    name=f"Today ({today})",
                    value=today_text,
                    inline=False
                )
            
            embed.set_footer(text="Use `!tasks` for interactive task management")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in show_quick_overview: {e}")
            await ctx.send("❌ Error generating overview.")
    
    async def show_category_tasks(self, ctx, user_id: int, category: str = None):
        """Show tasks filtered by category"""
        try:
            plan_data = await self.db.get_weekly_plan(user_id)
            
            if not plan_data:
                await ctx.send("❌ No weekly plan found.")
                return
            
            # Filter tasks by category
            filtered_tasks = []
            for day_tasks in plan_data['tasks'].values():
                for task in day_tasks:
                    if not category or task['category'].lower() == category.lower():
                        filtered_tasks.append(task)
            
            if not filtered_tasks:
                category_name = category.title() if category else "All"
                await ctx.send(f"❌ No tasks found for category: {category_name}")
                return
            
            embed = discord.Embed(
                title=f"📂 Tasks by Category: {category.title() if category else 'All'}",
                color=discord.Color.purple()
            )
            
            # Group by completion status
            completed = [t for t in filtered_tasks if t['completed']]
            pending = [t for t in filtered_tasks if not t['completed']]
            
            if pending:
                pending_text = ""
                for task in pending[:10]:  # Show first 10
                    emoji = TaskCategory.get_emoji(task['category'])
                    pending_text += f"⬜ {emoji} {task['title']}\n"
                
                if len(pending) > 10:
                    pending_text += f"... and {len(pending) - 10} more"
                
                embed.add_field(
                    name=f"Pending ({len(pending)})",
                    value=pending_text,
                    inline=False
                )
            
            if completed:
                completed_text = ""
                for task in completed[:5]:  # Show first 5
                    emoji = TaskCategory.get_emoji(task['category'])
                    completed_text += f"✅ {emoji} {task['title']}\n"
                
                if len(completed) > 5:
                    completed_text += f"... and {len(completed) - 5} more"
                
                embed.add_field(
                    name=f"Completed ({len(completed)})",
                    value=completed_text,
                    inline=False
                )
            
            completion_rate = len(completed) / len(filtered_tasks) if filtered_tasks else 0
            embed.add_field(
                name="Progress",
                value=f"{len(completed)}/{len(filtered_tasks)} ({completion_rate:.1%})",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in show_category_tasks: {e}")
            await ctx.send("❌ Error filtering tasks by category.")
    
    @commands.command(name="task")
    async def quick_task_toggle(self, ctx, *, task_title: str):
        """Quick toggle task completion by title
        
        Usage: !task [partial task title]
        """
        try:
            user = await self.db.get_or_create_user(str(ctx.author.id), ctx.author.display_name)
            plan_data = await self.db.get_weekly_plan(user['id'])
            
            if not plan_data:
                await ctx.send("❌ No weekly plan found.")
                return
            
            # Find matching tasks
            matching_tasks = []
            for day_tasks in plan_data['tasks'].values():
                for task in day_tasks:
                    if task_title.lower() in task['title'].lower():
                        matching_tasks.append(task)
            
            if not matching_tasks:
                await ctx.send(f"❌ No tasks found matching: '{task_title}'")
                return
            
            if len(matching_tasks) > 1:
                # Multiple matches - show options
                embed = discord.Embed(
                    title="🔍 Multiple Tasks Found",
                    description="Multiple tasks match your search. Please be more specific:",
                    color=discord.Color.orange()
                )
                
                for i, task in enumerate(matching_tasks[:5]):
                    status = "✅" if task['completed'] else "⬜"
                    embed.add_field(
                        name=f"{i+1}. {task['title']}",
                        value=f"{status} Category: {task['category']}",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                return
            
            # Single match - toggle it
            task = matching_tasks[0]
            new_status = not task['completed']
            
            success = await self.db.update_task_status(task['id'], new_status)
            
            if success:
                status_text = "completed" if new_status else "reopened"
                status_emoji = "✅" if new_status else "⬜"
                
                embed = discord.Embed(
                    title=f"{status_emoji} Task {status_text.title()}!",
                    description=f"**{task['title']}**",
                    color=discord.Color.green() if new_status else discord.Color.blue()
                )
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to update task.")
                
        except Exception as e:
            logger.error(f"Error in quick_task_toggle: {e}")
            await ctx.send("❌ An error occurred.")

async def setup(bot):
    """Set up the TaskManager cog"""
    await bot.add_cog(TaskManagerCog(bot)) 