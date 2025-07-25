#!/usr/bin/env python3
"""
Money Bot - Discord Money Tracker Bot
Automatically tracks money entries from Discord channel to Notion database.
"""

import discord
from discord.ext import commands
import os
import logging
import re
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
import aiohttp
import base64
from io import BytesIO
from typing import Optional, Dict, Any
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import calendar
import asyncio

# Import required libraries
from notion_client import Client as NotionClient
from openai import OpenAI

# Load environment variables from main discord directory
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
print(env_path)
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") 
MONEY_CHANNEL_ID = 1396903503624016024  # Money channel ID
NOTION_TOKEN = os.getenv("NOTION_TOKEN") 
MONEY_DB_ID = "237d42a1faf5802496cadffa99784181"  # Money database ID
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize clients
notion = NotionClient(auth=NOTION_TOKEN)
openai_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('money_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('money_bot')

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class MoneyAnalyzer:
    """Analyzes text and images for money-related information"""
    
    @staticmethod
    async def analyze_text(text: str, author: str) -> Optional[Dict[str, Any]]:
        """Analyze text for money information using AI"""
        try:
            prompt = f"""
            Analyze this text for money/expense information:
            "{text}"
            
            Extract:
            1. Amount in euros (as a number)
            2. Category of expense (e.g., "Food", "Transport", "Shopping", "Bills", "Entertainment", etc.)
            3. Brief description
            
            Respond in JSON format:
            {{
                "amount": 12.50,
                "category": "Food",
                "description": "brief description of the expense"
            }}
            
            If no clear money amount is found, set amount to 0.
            """
            
            response = openai_client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"AI Analysis: {response_text}")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                import json
                data = json.loads(json_match.group())
                return {
                    "amount": float(data.get("amount", 0)),
                    "category": data.get("category", "Other"),
                    "description": data.get("description", text[:100]),
                    "author": author,
                    "type": "text"
                }
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
        
        return None
    
    @staticmethod
    async def analyze_image(image_url: str, author: str) -> Optional[Dict[str, Any]]:
        """Analyze image for money information using AI vision"""
        try:
            # Download image and convert to base64
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    image_data = await response.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            prompt = """
            Analyze this image for money/expense information like receipts, price tags, or bills.
            
            Extract:
            1. Total amount in euros (as a number)
            2. Category of expense (e.g., "Food", "Transport", "Shopping", "Bills", etc.)
            3. Brief description of what was purchased
            
            Respond in JSON format:
            {
                "amount": 12.50,
                "category": "Food",
                "description": "brief description of the purchase"
            }
            
            If no clear money amount is found, set amount to 0.
            """
            
            response = openai_client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"AI Image Analysis: {response_text}")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                import json
                data = json.loads(json_match.group())
                return {
                    "amount": float(data.get("amount", 0)),
                    "category": data.get("category", "Other"),
                    "description": data.get("description", "Image expense"),
                    "author": author,
                    "type": "image",
                    "image_url": image_url
                }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
        
        return None

class NotionManager:
    """Manages Notion database operations"""
    
    @staticmethod
    def get_person_from_author(author: str) -> str:
        """Map Discord author to Notion Person select options"""
        author_lower = author.lower()
        if 'marc' in author_lower or 'baumholz' in author_lower:
            return 'Marc'
        elif 'ralf' in author_lower:
            return 'Ralf'
        elif 'nick' in author_lower:
            return 'Nick'
        else:
            logger.info(f"Unknown author '{author}', defaulting to Marc")
            return 'Marc'  # Default fallback
    
    @staticmethod
    async def save_money_entry(data: Dict[str, Any]) -> bool:
        """Save money entry to Notion database"""
        try:
            logger.info(f"Saving to Notion: {data}")
            
            # Build properties for new page
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": data["description"][:100]  # Limit title length
                            }
                        }
                    ]
                },
                "Amount": {
                    "number": data["amount"]
                },
                "kategorie": {
                    "multi_select": [
                        {
                            "name": data["category"]
                        }
                    ]
                },
                "Person": {
                    "select": {
                        "name": NotionManager.get_person_from_author(data["author"])
                    }
                },
                "Beschreibung": {
                    "rich_text": [
                        {
                            "text": {
                                "content": data["description"]
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            }
            
            # Add image if present
            if data.get("image_url"):
                properties["Bilder"] = {
                    "files": [
                        {
                            "type": "external",
                            "name": "Money Image",
                            "external": {
                                "url": data["image_url"]
                            }
                        }
                    ]
                }
            
            # Create new page in Notion database
            new_page = notion.pages.create(
                parent={"database_id": MONEY_DB_ID},
                properties=properties
            )
            
            logger.info(f"✅ Successfully saved to Notion")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving to Notion: {e}")
            return False
    
    @staticmethod
    async def get_monthly_data(year: int, month: int) -> list:
        """Get all expenses for a specific month from Notion database"""
        try:
            # Calculate start and end dates for the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            # Query Notion database
            response = notion.databases.query(
                database_id=MONEY_DB_ID,
                filter={
                    "and": [
                        {
                            "property": "Date",
                            "date": {
                                "on_or_after": start_date.isoformat()
                            }
                        },
                        {
                            "property": "Date",
                            "date": {
                                "before": end_date.isoformat()
                            }
                        }
                    ]
                }
            )
            
            expenses = []
            for page in response.get('results', []):
                props = page.get('properties', {})
                
                # Extract data safely
                amount = props.get('Amount', {}).get('number', 0) or 0
                
                # Extract categories (multi-select)
                categories = []
                kategorie_data = props.get('kategorie', {}).get('multi_select', [])
                for cat in kategorie_data:
                    categories.append(cat.get('name', ''))
                category = ', '.join(categories) if categories else 'Other'
                
                # Extract person
                person_data = props.get('Person', {}).get('select', {})
                person = person_data.get('name', 'Unknown') if person_data else 'Unknown'
                
                # Extract description
                beschreibung_data = props.get('Beschreibung', {}).get('rich_text', [])
                description = ''
                if beschreibung_data:
                    description = beschreibung_data[0].get('text', {}).get('content', '')
                
                # Extract date
                date_data = props.get('Date', {}).get('date', {})
                date_str = date_data.get('start', '') if date_data else ''
                
                expenses.append({
                    'amount': amount,
                    'category': category,
                    'person': person,
                    'description': description,
                    'date': date_str
                })
            
            logger.info(f"Retrieved {len(expenses)} expenses for {month}/{year}")
            return expenses
            
        except Exception as e:
            logger.error(f"❌ Error getting monthly data: {e}")
            return []

class MonthlyAnalyzer:
    """Generates monthly expense analysis and charts"""
    
    @staticmethod
    async def generate_monthly_report(year: int, month: int) -> Dict[str, Any]:
        """Generate comprehensive monthly expense report"""
        try:
            expenses = await NotionManager.get_monthly_data(year, month)
            
            if not expenses:
                return {"error": "No expenses found for this month"}
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(expenses)
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
            
            # Basic statistics
            total_spent = df['amount'].sum()
            avg_expense = df['amount'].mean()
            num_transactions = len(df)
            
            # Category analysis
            category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
            
            # Person analysis
            person_totals = df.groupby('person')['amount'].sum().sort_values(ascending=False)
            
            # Person-Category breakdown
            person_category = df.groupby(['person', 'category'])['amount'].sum().unstack(fill_value=0)
            
            # Get previous month and year data for comparison
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            
            # Get data for previous month and year
            prev_month_data = await NotionManager.get_monthly_data(prev_year, prev_month)
            prev_year_data = await NotionManager.get_monthly_data(year - 1, month)
            
            # Calculate spending for previous month and year
            prev_month_spent = sum(item['amount'] for item in prev_month_data)
            prev_year_spent = sum(item['amount'] for item in prev_year_data)
            
            # Calculate growth rates
            month_growth = ((total_spent - prev_month_spent) / prev_month_spent * 100) if prev_month_spent > 0 else 100
            year_growth = ((total_spent - prev_year_spent) / prev_year_spent * 100) if prev_year_spent > 0 else 100
            
            # Trend analysis - compare with last 6 months
            trend_data = []
            for i in range(1, 7):
                past_month = month - i if month - i > 0 else 12 + (month - i)
                past_year = year if month - i > 0 else year - 1
                
                past_month_data = await NotionManager.get_monthly_data(past_year, past_month)
                past_month_spent = sum(item['amount'] for item in past_month_data)
                
                trend_data.append({
                    'month': past_month,
                    'year': past_year,
                    'spent': past_month_spent
                })
            
            # Project next month based on trend
            next_month_projection = total_spent * (1 + month_growth / 100)
            
            report = {
                'month': month,
                'year': year,
                'total_spent': total_spent,
                'avg_expense': avg_expense,
                'num_transactions': num_transactions,
                'category_totals': category_totals.to_dict(),
                'person_totals': person_totals.to_dict(),
                'person_category_breakdown': person_category.to_dict(),
                'raw_data': expenses,
                'prev_month_spent': prev_month_spent,
                'prev_year_spent': prev_year_spent,
                'month_growth': month_growth,
                'year_growth': year_growth,
                'trend_data': trend_data,
                'next_month_projection': next_month_projection
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating monthly report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def create_charts(report: Dict[str, Any]) -> list:
        """Create charts from the monthly report data"""
        try:
            chart_files = []
            month_name = calendar.month_name[report['month']]
            year = report['year']
            
            # Set style for better looking charts
            plt.style.use('default')
            
            # 1. Category Pie Chart
            if report['category_totals']:
                fig, ax = plt.subplots(figsize=(10, 8))
                categories = list(report['category_totals'].keys())
                amounts = list(report['category_totals'].values())
                
                colors = plt.cm.Set3(range(len(categories)))
                wedges, texts, autotexts = ax.pie(amounts, labels=categories, autopct='%1.1f%%', 
                                                 colors=colors, startangle=90)
                
                ax.set_title(f'Expenses by Category - {month_name} {year}', fontsize=16, fontweight='bold')
                plt.tight_layout()
                
                chart_file = f'category_pie_{year}_{report["month"]:02d}.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                chart_files.append(chart_file)
                plt.close()
            
            # 2. Person Spending Bar Chart
            if report['person_totals']:
                fig, ax = plt.subplots(figsize=(10, 6))
                persons = list(report['person_totals'].keys())
                amounts = list(report['person_totals'].values())
                
                bars = ax.bar(persons, amounts, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
                ax.set_title(f'Total Spending by Person - {month_name} {year}', fontsize=16, fontweight='bold')
                ax.set_ylabel('Amount (€)', fontsize=12)
                ax.set_xlabel('Person', fontsize=12)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'€{height:.2f}', ha='center', va='bottom', fontweight='bold')
                
                plt.tight_layout()
                chart_file = f'person_spending_{year}_{report["month"]:02d}.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                chart_files.append(chart_file)
                plt.close()
            
            # 3. Person-Category Heatmap
            if report['person_category_breakdown']:
                person_category_df = pd.DataFrame(report['person_category_breakdown']).fillna(0)
                
                if not person_category_df.empty:
                    fig, ax = plt.subplots(figsize=(12, 8))
                    im = ax.imshow(person_category_df.values, cmap='YlOrRd', aspect='auto')
                    
                    # Set ticks and labels
                    ax.set_xticks(range(len(person_category_df.columns)))
                    ax.set_yticks(range(len(person_category_df.index)))
                    ax.set_xticklabels(person_category_df.columns, rotation=45, ha='right')
                    ax.set_yticklabels(person_category_df.index)
                    
                    # Add text annotations
                    for i in range(len(person_category_df.index)):
                        for j in range(len(person_category_df.columns)):
                            value = person_category_df.iloc[i, j]
                            if value > 0:
                                text = ax.text(j, i, f'€{value:.0f}', ha="center", va="center", 
                                             color="black" if value < person_category_df.values.max()/2 else "white",
                                             fontweight='bold')
                    
                    ax.set_title(f'Spending by Person & Category - {month_name} {year}', 
                               fontsize=16, fontweight='bold')
                    
                    # Add colorbar
                    cbar = plt.colorbar(im)
                    cbar.set_label('Amount (€)', rotation=270, labelpad=20)
                    
                    plt.tight_layout()
                    chart_file = f'person_category_heatmap_{year}_{report["month"]:02d}.png'
                    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                    chart_files.append(chart_file)
                    plt.close()
            
            # 4. Trend Graph (last 12 months)
            if report.get('trend_data'):
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Prepare data for the trend graph
                months = [calendar.month_name[data['month']] for data in report['trend_data']]
                spent = [data['spent'] for data in report['trend_data']]
                
                ax.plot(months, spent, marker='o', color='#4ECDC4')
                
                ax.set_title(f'Spending Trend - Last 12 Months', fontsize=16, fontweight='bold')
                ax.set_ylabel('Amount (€)', fontsize=12)
                ax.set_xlabel('Month', fontsize=12)
                ax.set_xticklabels(months, rotation=45, ha='right')
                
                plt.tight_layout()
                chart_file = f'trend_graph_{year}_{report["month"]:02d}.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                chart_files.append(chart_file)
                plt.close()
            
            # 5. Projection Graph
            if report.get('trend_data') and len(report['trend_data']) > 1:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Prepare data for projection
                months = [data['month'] for data in report['trend_data']]
                spent = [data['spent'] for data in report['trend_data']]
                
                # Linear regression for projection
                from sklearn.linear_model import LinearRegression
                import numpy as np
                
                X = np.array(months).reshape(-1, 1)
                y = np.array(spent)
                
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict next month
                next_month = months[-1] + 1
                predicted_spent = model.predict(np.array([[next_month]]))[0]
                
                # Plot historical data
                ax.plot(months, spent, marker='o', label='Actual', color='#4ECDC4')
                
                # Plot projection
                ax.plot(next_month, predicted_spent, marker='o', label='Projected', color='#FF6B6B')
                
                ax.set_title(f'Spending Projection - Next Month', fontsize=16, fontweight='bold')
                ax.set_ylabel('Amount (€)', fontsize=12)
                ax.set_xlabel('Month', fontsize=12)
                ax.legend()
                
                plt.tight_layout()
                chart_file = f'projection_graph_{year}_{report["month"]:02d}.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                chart_files.append(chart_file)
                plt.close()
            
            logger.info(f"Generated {len(chart_files)} charts")
            return chart_files
            
        except Exception as e:
            logger.error(f"❌ Error creating charts: {e}")
            return []
    
    @staticmethod
    def format_report_message(report: Dict[str, Any]) -> str:
        """Format the report data into a Discord message"""
        if 'error' in report:
            return f"❌ Error generating report: {report['error']}"
        
        month_name = calendar.month_name[report['month']]
        year = report['year']
        
        message = f"📊 **Monthly Expense Report - {month_name} {year}** 📊\n\n"
        
        # Summary
        message += f"💰 **Total Spent:** €{report['total_spent']:.2f}\n"
        message += f"🧾 **Transactions:** {report['num_transactions']}\n"
        message += f"📈 **Average per Transaction:** €{report['avg_expense']:.2f}\n\n"
        
        # Top categories
        message += "🏷️ **Top Categories:**\n"
        for category, amount in list(report['category_totals'].items())[:5]:
            percentage = (amount / report['total_spent']) * 100
            message += f"• {category}: €{amount:.2f} ({percentage:.1f}%)\n"
        
        message += "\n👥 **Spending by Person:**\n"
        for person, amount in report['person_totals'].items():
            percentage = (amount / report['total_spent']) * 100
            message += f"• {person}: €{amount:.2f} ({percentage:.1f}%)\n"
        
        return message

@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f"🤖 {bot.user} is now online!")
    logger.info(f"📍 Monitoring money channel ID: {MONEY_CHANNEL_ID}")
    
    # Send startup notification to the money channel
    try:
        channel = bot.get_channel(MONEY_CHANNEL_ID)
        if channel:
            startup_message = (
                "💰 **Money Bot is now online!** 🤖\n\n"
                "I'm ready to help you track your expenses! Here's what I can do:\n"
                "• 📝 Analyze text messages for money amounts and categories\n"
                "• 📸 Process receipt images and extract expense information\n"
                "• 💾 Automatically save entries to your Notion database\n"
                "• ✅ Provide instant feedback with reactions\n"
                "• 📊 Generate monthly expense reports with charts\n\n"
                "**Commands:**\n"
                "• `!status` - Check bot status\n"
                "• `!analysis [month] [year]` - Generate expense analysis\n\n"
                "Just send me your expenses as text or upload receipt images and I'll handle the rest!\n"
                "Monthly reports are automatically generated on the 1st of each month."
            )
            await channel.send(startup_message)
            logger.info("✅ Startup notification sent to money channel")
        else:
            logger.warning(f"❌ Could not find money channel with ID: {MONEY_CHANNEL_ID}")
    except Exception as e:
        logger.error(f"❌ Error sending startup notification: {e}")
    
    # Start monthly check task
    asyncio.create_task(monthly_check())
    logger.info("📅 Monthly check task started")

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    # Only process messages in the target channel
    if message.channel.id != MONEY_CHANNEL_ID:
        return
    
    # Don't process our own messages (prevent infinite loops)
    if message.author.id == bot.user.id:
        return
    
    # Ignore command messages (but process everything else)
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # Process ALL other messages (user messages, webhook messages, bot messages)
    await process_money_entry(message)

async def process_money_entry(message):
    """Process a money entry from Discord - SINGLE PROCESSING ONLY"""
    try:
        # Get author name - always use display name, no matter the source
        author = str(message.author.display_name)
        logger.info(f"📥 Processing message from: {author} (ID: {message.id})")
        
        # Determine what to process - IMAGE takes priority over TEXT
        has_images = bool(message.attachments and any(
            attachment.filename.lower().endswith(ext) 
            for attachment in message.attachments 
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        ))
        
        has_text = bool(message.content.strip())
        
        # Only process ONE thing per message - no double processing
        if has_images:
            logger.info(f"🖼️ Processing IMAGE from {author}")
            await process_image_entry(message, author)
        elif has_text:
            logger.info(f"📝 Processing TEXT from {author}: {message.content[:50]}...")
            await process_text_entry(message, author)
        else:
            logger.info(f"❓ No processable content from {author}")
    
    except Exception as e:
        logger.error(f"❌ Error processing money entry: {e}")
        await message.add_reaction("❌")

async def process_image_entry(message, author):
    """Process image attachments"""
    try:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                # Add processing reaction
                await message.add_reaction("🔄")
                
                # Analyze image
                analysis = await MoneyAnalyzer.analyze_image(attachment.url, author)
                
                if analysis and analysis["amount"] > 0:
                    # Save to Notion
                    success = await NotionManager.save_money_entry(analysis)
                    
                    if success:
                        await message.add_reaction("✅")
                        await message.reply(f"💰 Saved: €{analysis['amount']:.2f} - {analysis['category']}")
                        return  # Successfully processed - stop here
                    else:
                        await message.add_reaction("❌")
                        return
                else:
                    await message.add_reaction("❓")
                    return
    except Exception as e:
        logger.error(f"❌ Error processing image: {e}")
        await message.add_reaction("❌")

async def process_text_entry(message, author):
    """Process text content"""
    try:
        # Analyze text
        analysis = await MoneyAnalyzer.analyze_text(message.content, author)
        
        if analysis and analysis["amount"] > 0:
            # Save to Notion
            success = await NotionManager.save_money_entry(analysis)
            
            if success:
                await message.add_reaction("✅")
                await message.reply(f"💰 Saved: €{analysis['amount']:.2f} - {analysis['category']}")
            else:
                await message.add_reaction("❌")
        else:
            logger.info(f"💭 No money amount detected in text from {author}")
    except Exception as e:
        logger.error(f"❌ Error processing text: {e}")
        await message.add_reaction("❌")

@bot.command()
async def status(ctx):
    """Check bot status"""
    if ctx.channel.id == MONEY_CHANNEL_ID:
        await ctx.send("💰 Money Bot is running and monitoring this channel!")

@bot.command()
async def analysis(ctx, month: int = None, year: int = None):
    """Generate monthly expense analysis"""
    if ctx.channel.id != MONEY_CHANNEL_ID:
        return
    
    try:
        # Use current month/year if not specified
        now = datetime.now()
        if month is None:
            month = now.month
        if year is None:
            year = now.year
        
        # Validate month
        if month < 1 or month > 12:
            await ctx.send("❌ Month must be between 1 and 12")
            return
        
        await ctx.send(f"📊 Generating expense analysis for {calendar.month_name[month]} {year}...")
        
        # Generate report
        report = await MonthlyAnalyzer.generate_monthly_report(year, month)
        
        if 'error' in report:
            await ctx.send(f"❌ {report['error']}")
            return
        
        # Create charts
        chart_files = await MonthlyAnalyzer.create_charts(report)
        
        # Send text report
        report_message = MonthlyAnalyzer.format_report_message(report)
        await ctx.send(report_message)
        
        # Send charts
        for chart_file in chart_files:
            if os.path.exists(chart_file):
                with open(chart_file, 'rb') as f:
                    discord_file = discord.File(f, filename=chart_file)
                    await ctx.send(file=discord_file)
                
                # Clean up file
                try:
                    os.remove(chart_file)
                except:
                    pass
        
        logger.info(f"✅ Monthly analysis completed for {month}/{year}")
        
    except Exception as e:
        logger.error(f"❌ Error in analysis command: {e}")
        await ctx.send(f"❌ Error generating analysis: {str(e)}")

async def monthly_check():
    """Check if it's the first day of the month and send analysis"""
    while True:
        try:
            now = datetime.now()
            
            # Check if it's the first day of the month at 9 AM
            if now.day == 1 and now.hour == 9 and now.minute < 5:
                channel = bot.get_channel(MONEY_CHANNEL_ID)
                if channel:
                    # Get previous month data
                    if now.month == 1:
                        prev_month = 12
                        prev_year = now.year - 1
                    else:
                        prev_month = now.month - 1
                        prev_year = now.year
                    
                    await channel.send("🗓️ **Monthly Expense Report** - Automatically generated!")
                    
                    # Generate and send analysis
                    report = await MonthlyAnalyzer.generate_monthly_report(prev_year, prev_month)
                    
                    if 'error' not in report:
                        chart_files = await MonthlyAnalyzer.create_charts(report)
                        report_message = MonthlyAnalyzer.format_report_message(report)
                        
                        await channel.send(report_message)
                        
                        for chart_file in chart_files:
                            if os.path.exists(chart_file):
                                with open(chart_file, 'rb') as f:
                                    discord_file = discord.File(f, filename=chart_file)
                                    await channel.send(file=discord_file)
                                
                                try:
                                    os.remove(chart_file)
                                except:
                                    pass
                    
                    logger.info(f"✅ Automatic monthly analysis sent for {prev_month}/{prev_year}")
            
            # Wait 5 minutes before checking again
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"❌ Error in monthly check: {e}")
            await asyncio.sleep(300)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in environment!")
        exit(1)
    
    if not NOTION_TOKEN:
        logger.error("❌ NOTION_TOKEN not found in environment!")
        exit(1)
    
    if not OPENROUTER_API_KEY:
        logger.error("❌ OPENROUTER_API_KEY not found in environment!")
        exit(1)
    
    logger.info("🚀 Starting Money Bot...")
    bot.run(DISCORD_TOKEN)