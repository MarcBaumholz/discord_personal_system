import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import json
import os
from datetime import datetime
import subprocess
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
        
        # Bot status tracking - Updated with current bot names and processes
        self.bot_processes = {
            "Calories Bot": "calories-bot",
            "Health Bot": "health-bot", 
            "Decision Bot": "decision-bot",
            "Erinnerungen Bot": "erinnerungen-bot",
            "Tagebuch Bot": "tagebuch-bot",
            "Preisvergleich Bot": "preisvergleich-bot",
            "Meal Plan Bot": "meal-plan-bot",
            "Weekly Todo Bot": "weekly-todo-bot",
            "YouTube Bot": "youtube-bot",
            "Money Bot": "money-bot",
            "Allgemeine Wohl Bot": "allgemeine-wohl-bot",
            "Todo Bot": "discord-todo-bot"
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
            value="• **12 Production Bots** mit aktuellen Beschreibungen\n• **AI-Powered** Bots mit OpenRouter, LangChain, Notion\n• **Docker-Container** Status-Monitoring\n• **Real-time Updates** der Bot-Funktionalitäten\n• **Responsive Design** mit Dark/Light Theme",
            inline=False
        )
        
        embed.set_footer(
            text="Website mit aktuellen Bot-Informationen • Docker-Container Status • Letzte Aktualisierung: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
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
                "description": "AI-powered food analysis using OpenRouter vision models. Analyzes food images and text descriptions, estimates calories with confidence scores, and automatically saves to Notion database with monthly reports and charts.",
                "features": "AI Vision • OpenRouter • Notion • Monthly Reports • Charts",
                "url": f"{self.website_url}bots/calories.html"
            },
            {
                "name": "🧠 Decision Bot", 
                "description": "Personal decision analysis using CSV-based RAG system. Analyzes decisions against your personal values, goals, identity, and experiences stored in CSV files with detailed recommendations.",
                "features": "RAG • CSV Data • OpenRouter • Personal Analysis",
                "url": f"{self.website_url}bots/decision.html"
            },
            {
                "name": "⏰ Erinnerungen Bot",
                "description": "Automated daily reminders system. Checks Notion database for birthdays and sends notifications at 7 AM, plus trash pickup reminders for Schweigheim area at 8 PM.",
                "features": "Notion • Birthday Tracking • Trash Calendar • Scheduling",
                "url": f"{self.website_url}bots/erinnerungen.html"
            },
            {
                "name": "🏥 Health Bot",
                "description": "Oura Ring health data integration. Fetches daily activity data (calories, steps, active calories), analyzes against personal goals, and sends personalized health reports with tips at 8 AM.",
                "features": "Oura API • Health Analysis • Personalized Tips • Daily Reports",
                "url": f"{self.website_url}bots/health.html"
            },
            {
                "name": "🍳 Meal Plan Bot",
                "description": "Weekly meal planning with Notion integration. Fetches recipes from Notion database, randomly selects 3 for the week, generates meal prep plans and shopping lists, then adds items to Todoist.",
                "features": "Notion • Todoist • AI Planning • Shopping Lists",
                "url": f"{self.website_url}bots/meal-plan.html"
            },
            {
                "name": "💰 Money Bot",
                "description": "AI-powered expense tracking. Automatically processes text and image messages in money channel, uses OpenRouter AI to extract amounts, categories, and descriptions, saves structured entries to Notion.",
                "features": "AI Analysis • OpenRouter • Notion • Receipt Processing",
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
                "description": "AI-powered deal finder using LangChain and LangGraph. Monitors Notion product watchlist, uses Tavily search API to find current offers, and posts detailed deal notifications every Sunday.",
                "features": "LangChain • LangGraph • Tavily Search • Notion • AI Agent",
                "url": f"{self.website_url}bots/preisvergleich.html"
            },
            {
                "name": "📔 Tagebuch Bot", 
                "description": "Automated journal system with Notion integration. Saves journal entries with smart title generation, sends daily reminders at 10 PM, and maintains structured diary in Notion database.",
                "features": "Notion • Smart Titles • Daily Reminders • German Language",
                "url": f"{self.website_url}bots/tagebuch.html"
            },
            {
                "name": "📋 Todo Bot",
                "description": "Smart todo management with Todoist integration. Automatically converts channel messages to todos with intelligent parsing of priority, dates, and family members, plus complete todo management.",
                "features": "Todoist • Smart Parsing • Priority Detection • Family Labels",
                "url": f"{self.website_url}bots/todo.html"
            },
            {
                "name": "✅ Weekly Todo Bot",
                "description": "Interactive household task management. Creates daily todo lists with emoji reactions, persistent progress tracking, automatic daily resets, and multi-user support.",
                "features": "Interactive • Emoji Reactions • Persistence • Daily Reset",
                "url": f"{self.website_url}bots/weekly-todo.html"
            },
            {
                "name": "📺 YouTube Bot",
                "description": "Automated YouTube content delivery. Fetches daily videos from tech subscriptions, posts trending tech videos as fallback, includes video search functionality, and posts rich embeds at 9 AM.",
                "features": "YouTube API • Tech Channels • Trending Videos • Rich Embeds",
                "url": f"{self.website_url}bots/youtube.html"
            },
            {
                "name": "🏠 Allgemeine Wohl Bot",
                "description": "Household activity tracking system. Monitors Discord messages for household activities, uses OpenRouter AI for categorization, maintains ground truth database, and saves structured entries to Notion.",
                "features": "AI Categorization • OpenRouter • Ground Truth • Notion • Statistics",
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

    async def check_bot_running(self, container_name):
        """Check if a Docker container is running"""
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'Up' in result.stdout
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
