import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import json
import os
from datetime import datetime
import subprocess
import psutil
from dotenv import load_dotenv

# Load environment variables from main .env file
load_dotenv('../../../.env')

class WebsiteIntegrationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.overview_channel_id = 1361083427264266425
        self.website_url = "https://MarcBaumholz.github.io/discord_personal_system/"
        
        # Bot status tracking
        self.bot_processes = {
            "Calories Bot": "calories_bot.py",
            "Health Bot": "health_bot.py", 
            "Decision Bot": "decision_bot.py",
            "Erinnerungen Bot": "erinnerungen_bot.py",
            "Tagebuch Bot": "tagebuch_bot.py",
            "Preisvergleich Bot": "preisvergleich_bot.py",
            "Meal Plan Bot": "meal_plan_bot.py",
            "Weekly Todo Bot": "weekly_todo_bot.py",
            "YouTube Bot": "youtube_bot.py",
            "Money Bot": "bot.py",
            "Allgemeine Wohl Bot": "allgemeine_wohl_bot.py",
            "Todo Bot": "todo_agent.py"
        }

    async def on_ready(self):
        print(f'{self.user} ist online!')
        await self.post_website_embed()
        # Start status monitoring
        self.status_monitor.start()

    async def post_website_embed(self):
        """Post the main website embed to overview channel"""
        channel = self.get_channel(self.overview_channel_id)
        if not channel:
            print(f"Channel {self.overview_channel_id} nicht gefunden!")
            return

        # Get bot status
        bot_status = await self.get_bot_status()
        
        # Main website embed
        embed = discord.Embed(
            title="🤖 Discord Production Bots Guide",
            description="**Neue Website verfügbar!** Eine vollständige Übersicht aller Production Bots mit Features, Use Cases und Dokumentation.",
            color=0x5865F2,
            url=self.website_url
        )
        
        embed.add_field(
            name="🌐 Website",
            value=f"[**Zur Bot-Übersicht**]({self.website_url})\n*Klick um alle Bots zu erkunden*",
            inline=False
        )
        
        embed.add_field(
            name="📊 Bot Status",
            value=bot_status,
            inline=False
        )
        
        embed.add_field(
            name="✨ Features",
            value="• **12 Production Bots** mit detaillierten Beschreibungen\n• **Use Cases** und praktische Beispiele\n• **Direkte Links** zu README-Dateien\n• **Responsive Design** mit Dark/Light Theme",
            inline=False
        )
        
        embed.set_footer(
            text="Website automatisch generiert aus Repository-Dokumentation",
            icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        )
        
        embed.timestamp = datetime.utcnow()
        
        await channel.send(embed=embed)
        
        # Post individual bot cards as embeds
        await self.post_bot_cards(channel)

    async def post_bot_cards(self, channel):
        """Post individual bot cards as embeds"""
        bot_cards = [
            {
                "name": "🍽️ Calories Bot",
                "description": "Analyzes food images, estimates calories, and stores results in Notion with monthly reports.",
                "features": "Vision • Notion • Reports",
                "url": f"{self.website_url}bots/calories.html"
            },
            {
                "name": "🧠 Decision Bot", 
                "description": "Analyzes decisions against your values, goals, identity, and experiences.",
                "features": "RAG • CSV • Analysis",
                "url": f"{self.website_url}bots/decision.html"
            },
            {
                "name": "⏰ Erinnerungen Bot",
                "description": "Daily birthday reminders from Notion and trash pickup reminders for your area.",
                "features": "Notion • Schedule",
                "url": f"{self.website_url}bots/erinnerungen.html"
            },
            {
                "name": "🏥 Health Bot",
                "description": "Fetches Oura Ring data, analyzes performance, and posts daily health reports.",
                "features": "Oura • Analysis • Reports",
                "url": f"{self.website_url}bots/health.html"
            },
            {
                "name": "🍳 Meal Plan Bot",
                "description": "Generates weekly meal plans from Notion recipes and adds shopping lists to Todoist.",
                "features": "Notion • Todoist",
                "url": f"{self.website_url}bots/meal-plan.html"
            },
            {
                "name": "💰 Money Bot",
                "description": "Parses money-related messages and receipts and saves structured entries to Notion.",
                "features": "AI • Notion",
                "url": f"{self.website_url}bots/money.html"
            }
        ]
        
        # Send first 3 bots in one message
        embed1 = discord.Embed(
            title="🤖 Production Bots - Teil 1",
            description="**Klick auf die Links um Details zu sehen**",
            color=0x00ff00
        )
        
        for i, bot in enumerate(bot_cards[:3]):
            embed1.add_field(
                name=bot["name"],
                value=f"{bot['description']}\n**Features:** {bot['features']}\n[**Details anzeigen**]({bot['url']})",
                inline=False
            )
        
        await channel.send(embed=embed1)
        
        # Send remaining bots
        embed2 = discord.Embed(
            title="🤖 Production Bots - Teil 2", 
            description="**Weitere Bots verfügbar**",
            color=0x0099ff
        )
        
        for bot in bot_cards[3:]:
            embed2.add_field(
                name=bot["name"],
                value=f"{bot['description']}\n**Features:** {bot['features']}\n[**Details anzeigen**]({bot['url']})",
                inline=False
            )
        
        # Add remaining bots
        remaining_bots = [
            {
                "name": "🔎 Preisvergleich Bot",
                "description": "Finds weekly deals for products from your Notion watchlist and posts offers.",
                "features": "Agent • Search • Notion",
                "url": f"{self.website_url}bots/preisvergleich.html"
            },
            {
                "name": "📔 Tagebuch Bot", 
                "description": "Saves journal entries to Notion with daily reminders and smart titles.",
                "features": "Notion • Schedule",
                "url": f"{self.website_url}bots/tagebuch.html"
            },
            {
                "name": "📋 Todo Bot",
                "description": "Turns channel messages into Todos with smart parsing and Todoist integration.",
                "features": "Todoist • Parsing",
                "url": f"{self.website_url}bots/todo.html"
            },
            {
                "name": "✅ Weekly Todo Bot",
                "description": "Interactive daily/weekly household tasks list with emoji reactions and persistence.",
                "features": "Interactive • Schedule", 
                "url": f"{self.website_url}bots/weekly-todo.html"
            },
            {
                "name": "📺 YouTube Bot",
                "description": "Posts daily videos from subscriptions or trending tech videos with rich embeds.",
                "features": "YouTube API • Schedule",
                "url": f"{self.website_url}bots/youtube.html"
            },
            {
                "name": "🏠 Allgemeine Wohl Bot",
                "description": "Tracks household activities and good deeds, categorizes with AI, and saves entries to Notion.",
                "features": "AI • Notion • Tracking",
                "url": f"{self.website_url}bots/allgemeine-wohl.html"
            }
        ]
        
        for bot in remaining_bots:
            embed2.add_field(
                name=bot["name"],
                value=f"{bot['description']}\n**Features:** {bot['features']}\n[**Details anzeigen**]({bot['url']})",
                inline=False
            )
        
        await channel.send(embed=embed2)

    async def get_bot_status(self):
        """Get current status of all production bots"""
        status_lines = []
        running_count = 0
        
        for bot_name, process_name in self.bot_processes.items():
            is_running = await self.check_bot_running(process_name)
            status_emoji = "🟢" if is_running else "🔴"
            status_text = "RUNNING" if is_running else "STOPPED"
            
            if is_running:
                running_count += 1
                
            status_lines.append(f"{status_emoji} **{bot_name}**: {status_text}")
        
        status_summary = f"**{running_count}/{len(self.bot_processes)} Bots aktiv**\n\n"
        status_summary += "\n".join(status_lines[:6])  # Show first 6 bots
        
        if len(status_lines) > 6:
            status_summary += f"\n*... und {len(status_lines) - 6} weitere*"
            
        return status_summary

    async def check_bot_running(self, process_name):
        """Check if a bot process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if process_name in cmdline and 'python' in cmdline.lower():
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False

    @tasks.loop(minutes=30)
    async def status_monitor(self):
        """Monitor bot status and update if needed"""
        try:
            channel = self.get_channel(self.overview_channel_id)
            if not channel:
                return
                
            # Check if we should post a status update
            # This could be enhanced to only post when status changes
            pass
            
        except Exception as e:
            print(f"Status monitor error: {e}")

    @commands.command(name='website')
    async def website_command(self, ctx):
        """Post the website embed"""
        await self.post_website_embed()

    @commands.command(name='bots')
    async def bots_command(self, ctx):
        """Post only the bot cards"""
        await self.post_bot_cards(ctx.channel)

    @commands.command(name='botstatus')
    async def bot_status_command(self, ctx):
        """Show detailed bot status"""
        bot_status = await self.get_bot_status()
        
        embed = discord.Embed(
            title="📊 Production Bots Status",
            description=bot_status,
            color=0x00ff00
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='help_website')
    async def help_website(self, ctx):
        """Show help for website bot"""
        embed = discord.Embed(
            title="🤖 Website Integration Bot - Hilfe",
            description="Dieser Bot integriert die Discord Bots Website in Discord.",
            color=0x5865F2
        )
        
        embed.add_field(
            name="Befehle",
            value="`!website` - Website Embed posten\n`!botstatus` - Bot Status anzeigen\n`!help_website` - Diese Hilfe",
            inline=False
        )
        
        embed.add_field(
            name="Website",
            value=f"[**Zur Bot-Übersicht**]({self.website_url})",
            inline=False
        )
        
        await ctx.send(embed=embed)

# Bot setup and run
async def main():
    bot = WebsiteIntegrationBot()
    
    # Load environment variables
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        print("DISCORD_TOKEN nicht gefunden! Bitte in .env setzen.")
        return
    
    try:
        await bot.start(discord_token)
    except Exception as e:
        print(f"Bot start error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
