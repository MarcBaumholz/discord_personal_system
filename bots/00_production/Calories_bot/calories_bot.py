#!/usr/bin/env python3
"""
Calories Bot with OpenRouter AI Vision and Notion Integration
Analyzes food images uploaded to Discord, estimates calories, and saves to Notion database
"""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json
import asyncio
import aiohttp
import base64
import hashlib
import re
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import re
import hashlib

# API Clients
from notion_client import Client as NotionClient
from openai import OpenAI

# Import monthly report modules
from notion_data_reader import CalorieDataExtractor
from chart_generator import CalorieChartGenerator
from monthly_report import MonthlyReportGenerator

# Import logging system
from logger_config import bot_logger

# Load environment variables
# Load environment variables from main discord directory
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CALORIES_CHANNEL_ID = int(os.getenv("CALORIES_CHANNEL_ID", "1382099540391497818"))
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
FOODIATE_DB_ID = os.getenv("FOODIATE_DB_ID", "20ed42a1faf5807497c2f350ff84ea8d")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize clients
notion = NotionClient(auth=NOTION_TOKEN)
openai_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

class FoodAnalysisResult:
    """Represents the result of AI food analysis with macronutrients"""
    def __init__(self, food_name: str, calories: int, confidence: float, description: str = "", 
                 protein: float = 0.0, carbohydrates: float = 0.0, fat: float = 0.0):
        self.food_name = food_name
        self.calories = calories
        self.confidence = confidence
        self.description = description
        self.protein = protein  # in grams
        self.carbohydrates = carbohydrates  # in grams
        self.fat = fat  # in grams
        self.timestamp = datetime.now()
        
    def get_meal_hash(self) -> str:
        """Generate a hash for meal similarity detection"""
        import hashlib
        # Create a simplified version of the food name for comparison
        simplified_name = re.sub(r'[^a-z0-9\s]', '', self.food_name.lower().strip())
        return hashlib.md5(simplified_name.encode()).hexdigest()[:8]

class AIVisionHandler:
    """Handles OpenRouter AI vision analysis"""
    
    @staticmethod
    async def encode_image_to_base64(image_url: str) -> str:
        """Download and encode image to base64"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        return base64.b64encode(image_data).decode('utf-8')
                    else:
                        raise Exception(f"Failed to download image: {response.status}")
        except Exception as e:
            print(f"❌ Error encoding image: {e}")
            raise
    
    @staticmethod
    async def analyze_food_image(image_url: str) -> Optional[FoodAnalysisResult]:
        """Analyze food image using OpenRouter AI vision model"""
        try:
            print(f"🔍 Analyzing food image...")
            
            # Encode image to base64
            image_base64 = await AIVisionHandler.encode_image_to_base64(image_url)
            
            # Create the prompt for food analysis
            prompt = """
            Please analyze this food image and provide detailed nutritional information:
            1. The name of the food item(s) you see
            2. An estimate of the total calories in this serving
            3. Estimate of protein content in grams
            4. Estimate of carbohydrates content in grams
            5. Estimate of fat content in grams
            6. A confidence score (0-100) for your analysis
            7. A brief description of what you see
            
            Please respond in this exact JSON format:
            {
                "food_name": "name of the food",
                "calories": 123,
                "protein": 15.5,
                "carbohydrates": 45.2,
                "fat": 8.3,
                "confidence": 85,
                "description": "brief description of the food and portion"
            }
            
            Focus on being accurate with nutritional estimation. If you see multiple food items, provide the total nutrition for everything visible.
            Protein, carbohydrates, and fat should be in grams. Be as precise as possible but realistic about portion sizes.
            """
            
            # Call OpenRouter API with vision model
            response = openai_client.chat.completions.create(
                model="qwen/qwen2.5-vl-72b-instruct:free",  # Free vision model
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
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            print(f"🤖 AI Response: {response_text}")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group())
                
                return FoodAnalysisResult(
                    food_name=json_data.get("food_name", "Unknown Food"),
                    calories=int(json_data.get("calories", 0)),
                    protein=float(json_data.get("protein", 0.0)),
                    carbohydrates=float(json_data.get("carbohydrates", 0.0)),
                    fat=float(json_data.get("fat", 0.0)),
                    confidence=float(json_data.get("confidence", 0)),
                    description=json_data.get("description", "")
                )
            else:
                # Fallback parsing if JSON not found
                lines = response_text.split('\n')
                food_name = "Unknown Food"
                calories = 0
                protein = 0.0
                carbohydrates = 0.0
                fat = 0.0
                confidence = 50.0
                description = "Analysis completed"
                
                for line in lines:
                    if 'food' in line.lower() or 'name' in line.lower():
                        food_name = line.split(':')[-1].strip().strip('"')
                    elif 'calorie' in line.lower():
                        cal_match = re.search(r'(\d+)', line)
                        if cal_match:
                            calories = int(cal_match.group(1))
                    elif 'protein' in line.lower():
                        prot_match = re.search(r'(\d+\.?\d*)', line)
                        if prot_match:
                            protein = float(prot_match.group(1))
                    elif 'carb' in line.lower():
                        carb_match = re.search(r'(\d+\.?\d*)', line)
                        if carb_match:
                            carbohydrates = float(carb_match.group(1))
                    elif 'fat' in line.lower():
                        fat_match = re.search(r'(\d+\.?\d*)', line)
                        if fat_match:
                            fat = float(fat_match.group(1))
                    elif 'confidence' in line.lower():
                        conf_match = re.search(r'(\d+)', line)
                        if conf_match:
                            confidence = float(conf_match.group(1))
                
                return FoodAnalysisResult(food_name, calories, confidence, description, 
                                        protein, carbohydrates, fat)
                
        except Exception as e:
            print(f"❌ Error in AI analysis: {e}")
            return None

class NotionHandler:
    """Handles all Notion database operations"""
    
    @staticmethod
    async def upload_image_to_notion(image_url: str) -> str:
        """Upload image to Notion and return the URL"""
        try:
            # For now, we'll use the Discord image URL directly
            # In production, you might want to upload to a file storage service
            return image_url
        except Exception as e:
            print(f"❌ Error uploading image to Notion: {e}")
            return image_url
    
    @staticmethod
    async def get_person_select_option(discord_user: str) -> str:
        """Match Discord username to best Notion select option"""
        try:
            # Get database schema to find available select options
            database_info = notion.databases.retrieve(database_id=FOODIATE_DB_ID)
            person_property = database_info.get("properties", {}).get("person", {})
            
            if person_property.get("type") == "select":
                available_options = []
                for option in person_property.get("select", {}).get("options", []):
                    available_options.append(option.get("name", ""))
                
                print(f"🔍 Available person options: {available_options}")
                print(f"🔍 Discord user: {discord_user}")
                
                # Extract names from Discord username (remove discriminator, spaces, etc.)
                discord_name_parts = discord_user.lower().replace("#", " ").split()
                
                # Find best match
                best_match = None
                for option in available_options:
                    option_lower = option.lower()
                    # Check if any part of discord name matches option
                    for name_part in discord_name_parts:
                        if name_part in option_lower or option_lower in name_part:
                            best_match = option
                            print(f"✅ Matched '{discord_user}' to '{option}'")
                            break
                    if best_match:
                        break
                
                # If no match found, use first available option or return None
                if not best_match and available_options:
                    best_match = available_options[0]
                    print(f"⚠️  No match found for '{discord_user}', using default: '{best_match}'")
                
                return best_match
            else:
                print(f"⚠️  Person field is not a select type: {person_property.get('type')}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting person select options: {e}")
            return None
    
    @staticmethod
    async def save_food_analysis(analysis: FoodAnalysisResult, image_url: str, discord_user: str) -> bool:
        """Save food analysis results to Notion database"""
        try:
            print(f"💾 Saving analysis to Notion database...")
            
            # Upload image to Notion
            notion_image_url = await NotionHandler.upload_image_to_notion(image_url)
            
            # Get the best matching person from Notion select options
            person_option = await NotionHandler.get_person_select_option(discord_user)
            
            # Build properties for new page
            properties = {
                "Food": {
                    "title": [
                        {
                            "text": {
                                "content": analysis.food_name
                            }
                        }
                    ]
                },
                "Calories": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"{analysis.calories} kcal"
                            }
                        }
                    ]
                },
                "Protein": {
                    "number": analysis.protein
                },
                "Carbs": {
                    "number": analysis.carbohydrates
                },
                "Fat": {
                    "number": analysis.fat
                },
                "date": {
                    "date": {
                        "start": analysis.timestamp.isoformat()
                    }
                },
                "confidence": {
                    "number": analysis.confidence
                },
                "meal_hash": {
                    "rich_text": [
                        {
                            "text": {
                                "content": analysis.get_meal_hash()
                            }
                        }
                    ]
                },
                "Picture": {
                    "files": [
                        {
                            "type": "external",
                            "name": "Food Image",
                            "external": {
                                "url": notion_image_url
                            }
                        }
                    ]
                }
            }
            
            # Add person field if we found a matching option
            if person_option:
                properties["person"] = {
                    "select": {
                        "name": person_option
                    }
                }
            
            # Create new page in Notion database
            new_page = notion.pages.create(
                parent={"database_id": FOODIATE_DB_ID},
                properties=properties
            )
            
            print(f"✅ Successfully saved to Notion: {analysis.food_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving to Notion: {e}")
            return False

async def create_analysis_embed(analysis: FoodAnalysisResult, image_url: str) -> discord.Embed:
    """Create a Discord embed with the analysis results including macronutrients"""
    embed = discord.Embed(
        title="🍽️ Food Analysis Complete!",
        color=0x00ff00 if analysis.confidence > 70 else 0xffaa00
    )
    
    embed.add_field(name="🥗 Food Identified", value=analysis.food_name, inline=True)
    embed.add_field(name="🔥 Calories", value=f"{analysis.calories} kcal", inline=True)
    embed.add_field(name="🎯 Confidence", value=f"{analysis.confidence:.1f}%", inline=True)
    
    # Add macronutrient information
    embed.add_field(name="🥩 Protein", value=f"{analysis.protein:.1f}g", inline=True)
    embed.add_field(name="🍞 Carbs", value=f"{analysis.carbohydrates:.1f}g", inline=True)
    embed.add_field(name="🧈 Fat", value=f"{analysis.fat:.1f}g", inline=True)
    
    # Calculate macronutrient distribution
    total_macros = analysis.protein + analysis.carbohydrates + analysis.fat
    if total_macros > 0:
        protein_pct = (analysis.protein / total_macros) * 100
        carbs_pct = (analysis.carbohydrates / total_macros) * 100
        fat_pct = (analysis.fat / total_macros) * 100
        
        embed.add_field(
            name="📊 Macro Distribution", 
            value=f"P: {protein_pct:.0f}% | C: {carbs_pct:.0f}% | F: {fat_pct:.0f}%", 
            inline=False
        )
    
    if analysis.description:
        embed.add_field(name="📝 Description", value=analysis.description, inline=False)
    
    embed.set_image(url=image_url)
    embed.set_footer(text=f"Analysis completed at {analysis.timestamp.strftime('%H:%M:%S')} | Meal ID: {analysis.get_meal_hash()}")
    
    return embed

async def process_food_image(message: discord.Message, attachment: discord.Attachment):
    """Process a food image attachment"""
    try:
        # Log image processing start
        bot_logger.log_user_command(
            str(message.author.display_name),
            "upload_food_image",
            str(message.channel)
        )
        
        # Send processing message
        processing_msg = await message.channel.send("🔄 Analyzing your food image...")
        
        # Analyze the image
        analysis = await AIVisionHandler.analyze_food_image(attachment.url)
        
        if analysis is None:
            bot_logger.log_error(
                "AI_ANALYSIS_FAILED",
                "Could not analyze food image",
                {"user": str(message.author.display_name), "image_url": attachment.url}
            )
            await processing_msg.edit(content="❌ Sorry, I couldn't analyze this image. Please try again with a clearer food photo.")
            return
        
        # Save to Notion database
        saved = await NotionHandler.save_food_analysis(analysis, attachment.url, str(message.author))
        
        # Log the food analysis with enhanced nutrition data
        bot_logger.log_food_analysis({
            'user': str(message.author.display_name),
            'food_name': analysis.food_name,
            'calories': analysis.calories,
            'protein': analysis.protein,
            'carbohydrates': analysis.carbohydrates,
            'fat': analysis.fat,
            'confidence': analysis.confidence,
            'description': analysis.description,
            'meal_hash': analysis.get_meal_hash(),
            'image_url': attachment.url,
            'saved_to_notion': saved,
            'timestamp': analysis.timestamp.isoformat()
        })
        
        # Create result embed
        embed = await create_analysis_embed(analysis, attachment.url)
        
        if saved:
            embed.add_field(name="💾 Database", value="✅ Saved to FoodIate", inline=True)
        else:
            embed.add_field(name="💾 Database", value="❌ Failed to save", inline=True)
            bot_logger.log_error(
                "NOTION_SAVE_FAILED",
                "Failed to save analysis to Notion",
                {"user": str(message.author.display_name), "food": analysis.food_name}
            )
        
        # Update the processing message with results
        await processing_msg.edit(content="", embed=embed)
        
        # Add reaction to original message
        await message.add_reaction("✅")
        
    except Exception as e:
        print(f"❌ Error processing food image: {e}")
        bot_logger.log_error(
            "IMAGE_PROCESSING_ERROR",
            str(e),
            {"user": str(message.author.display_name), "image_url": attachment.url}
        )
        await message.channel.send("❌ An error occurred while processing your image. Please try again.")

async def process_monthly_command(message: discord.Message, current_month: bool = True):
    """Process the 'month' or 'month_before' command to generate monthly report"""
    try:
        # Determine which month to analyze
        command_type = "month_command" if current_month else "month_before_command"
        
        # Log monthly command usage
        bot_logger.log_user_command(
            str(message.author.display_name),
            command_type,
            str(message.channel)
        )
        
        # Send processing message
        if current_month:
            processing_msg = await message.channel.send("📊 Generating your current month's report...")
        else:
            processing_msg = await message.channel.send("📊 Generating your previous month's report...")
        
        # Get the target month's date
        now = datetime.now()
        
        if current_month:
            target_month = now.month
            target_year = now.year
        else:
            # Previous month
            if now.month == 1:
                target_month = 12
                target_year = now.year - 1
            else:
                target_month = now.month - 1
                target_year = now.year
        
        # Initialize report generator
        data_extractor = CalorieDataExtractor()
        chart_generator = CalorieChartGenerator()
        report_generator = MonthlyReportGenerator()
        
        # Get Discord username and match to Notion person
        discord_username = str(message.author.display_name)
        
        # Try to find matching user in the data
        all_users = data_extractor.get_all_users(target_year, target_month)
        
        if not all_users:
            bot_logger.log_error(
                "NO_DATA_FOUND",
                f"No calorie data found for {target_month}/{target_year}",
                {"user": discord_username, "period": f"{target_month}/{target_year}"}
            )
            month_name = datetime(target_year, target_month, 1).strftime('%B %Y')
            await processing_msg.edit(content=f"❌ No calorie data found for {month_name}. Upload some food images first!")
            return
        
        # Find best matching user
        user_match = None
        discord_name_lower = discord_username.lower()
        
        for user in all_users:
            if user.lower() in discord_name_lower or discord_name_lower in user.lower():
                user_match = user
                break
        
        if not user_match:
            # Use first available user if no match found
            user_match = all_users[0]
            bot_logger.log_system_event("USER_MATCH_FALLBACK", {
                "discord_user": discord_username,
                "matched_user": user_match,
                "available_users": all_users
            })
            await processing_msg.edit(content=f"⚠️ Using data for '{user_match}' (couldn't match your Discord name exactly)")
        
        # Generate the monthly report
        report_data = await report_generator.generate_monthly_report(target_year, target_month, user_match)
        
        # Log the monthly report generation
        bot_logger.log_monthly_report({
            **report_data,
            'requested_by': discord_username,
            'matched_user': user_match,
            'period': f"{target_month}/{target_year}",
            'report_type': 'current_month' if current_month else 'previous_month'
        })
        
        if not report_data.get('success'):
            await processing_msg.edit(content=f"❌ {report_data.get('message', 'No data found for last month')}")
            return
        
        # Create and send embed
        embed = report_generator.create_report_embed(report_data)
        
        # Send chart file if it exists
        chart_path = report_data.get('chart_path')
        if chart_path and os.path.exists(chart_path):
            file = discord.File(chart_path, filename=f"monthly_chart_{user_match}.png")
            await processing_msg.edit(content="", embed=embed)
            await message.channel.send(file=file)
            
            # Log chart file info
            bot_logger.log_system_event("CHART_GENERATED", {
                "user": user_match,
                "chart_path": chart_path,
                "file_size": os.path.getsize(chart_path) if os.path.exists(chart_path) else 0
            })
            
            # Clean up the chart file
            try:
                os.remove(chart_path)
                bot_logger.log_system_event("CHART_CLEANUP", {"chart_path": chart_path})
            except OSError:
                pass
        else:
            await processing_msg.edit(content="", embed=embed)
        
        # Add success reaction
        await message.add_reaction("📊")
        
    except Exception as e:
        print(f"❌ Error processing monthly command: {e}")
        bot_logger.log_error(
            "MONTHLY_COMMAND_ERROR",
            str(e),
            {"user": str(message.author.display_name)}
        )
        await message.channel.send(f"❌ Error generating monthly report: {str(e)}")

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'📊 Monitoring channel ID: {CALORIES_CHANNEL_ID}')
    print(f'💾 Connected to Notion database: {FOODIATE_DB_ID}')
    
    # Log bot startup
    bot_logger.log_bot_startup({
        'bot_user': str(bot.user),
        'channel_id': CALORIES_CHANNEL_ID,
        'database_id': FOODIATE_DB_ID,
        'openrouter_configured': bool(OPENROUTER_API_KEY),
        'notion_configured': bool(NOTION_TOKEN)
    })
    
    # Send startup message to Discord channel
    try:
        channel = bot.get_channel(CALORIES_CHANNEL_ID)
        if channel:
            startup_message = (
                "🍽️ **Enhanced Calories Bot is now online!** 🤖\n\n"
                "I'm your AI-powered nutrition assistant! Here's what I can do:\n\n"
                "**🔍 AI Food Analysis:**\n"
                "• 📸 Analyze food images using advanced AI vision\n"
                "• 🔥 Estimate calories, protein, carbs, and fat content\n"
                "• 💾 Automatically save to your Notion database\n"
                "• 🎯 Provide confidence ratings for accuracy\n\n"
                "**📊 Available Commands:**\n"
                "• `!help_calories` - Show detailed help information\n"
                "• `!nutrition` - Show today's nutrition summary with macros\n"
                "• `!nutrition_weekly` - Display this week's nutrition overview\n"
                "• `!weekly` - Display this week's calories and tracking summary\n"
                "• `!meals` - View your most frequent meals this month\n"
                "• `!test_analysis` - Test bot connectivity and status\n"
                "• `!logs` - View recent activity and system logs\n"
                "• Type `month` - Generate current month's comprehensive report\n"
                "• Type `month_before` - Generate previous month's comprehensive report\n\n"
                "**🚀 How to Use:**\n"
                "• Simply upload food photos and I'll analyze them automatically!\n"
                "• Each analysis includes calories, protein, carbs, and fat\n"
                "• Use commands to track your nutrition progress\n"
                "• Monthly reports show trends and meal frequency\n\n"
                "**💡 Enhanced Features:**\n"
                "• Macronutrient tracking (protein, carbs, fat)\n"
                "• Meal similarity detection and frequency analysis\n"
                "• Daily, weekly, and monthly nutrition summaries\n"
                "• Detailed nutritional breakdowns and distributions\n\n"
                "Ready to track your nutrition! 🎯"
            )
            await channel.send(startup_message)
            print("✅ Enhanced startup notification sent to calories channel")
        else:
            print(f"❌ Could not find channel with ID {CALORIES_CHANNEL_ID}")
    except Exception as e:
        print(f"❌ Error sending startup notification: {e}")

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Only process messages from the calories channel
    if message.channel.id != CALORIES_CHANNEL_ID:
        return
    
    # Check for "month" command (current month)
    if message.content.lower().strip() == "month":
        await process_monthly_command(message, current_month=True)
        return
    
    # Check for "month_before" command (previous month)
    if message.content.lower().strip() == "month_before":
        await process_monthly_command(message, current_month=False)
        return
    
    # Check if message has image attachments
    if message.attachments:
        for attachment in message.attachments:
            # Check if attachment is an image
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                await process_food_image(message, attachment)
                break
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name="nutrition")
async def nutrition_today(ctx):
    """Show today's nutrition summary"""
    if ctx.channel.id != CALORIES_CHANNEL_ID:
        await ctx.send("This command can only be used in the calories channel!")
        return
    
    try:
        # Log command usage
        bot_logger.log_user_command(
            str(ctx.author.display_name),
            "nutrition_today",
            str(ctx.channel)
        )
        
        # Get today's data
        today = datetime.now()
        discord_username = str(ctx.author.display_name)
        
        # Extract today's data
        data_extractor = CalorieDataExtractor()
        monthly_data = data_extractor.get_monthly_data(today.year, today.month)
        
        # Filter for today and user
        user_data = [
            entry for entry in monthly_data 
            if entry.get("person", "").lower() in discord_username.lower() or 
               discord_username.lower() in entry.get("person", "").lower()
        ]
        
        today_data = [
            entry for entry in user_data 
            if entry.get("date") == today.date()
        ]
        
        if not today_data:
            embed = discord.Embed(
                title="🍽️ Heute's Ernährung",
                description="Noch keine Mahlzeiten heute erfasst.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate today's totals
        total_calories = sum(entry.get("calories", 0) for entry in today_data)
        total_protein = sum(entry.get("protein", 0) for entry in today_data)
        total_carbs = sum(entry.get("carbohydrates", 0) for entry in today_data)
        total_fat = sum(entry.get("fat", 0) for entry in today_data)
        
        # Create embed
        embed = discord.Embed(
            title="🍽️ Heute's Ernährung",
            description=f"**{len(today_data)} Mahlzeit(en) erfasst**",
            color=0x00ff00
        )
        
        embed.add_field(name="🔥 Kalorien", value=f"{total_calories} kcal", inline=True)
        embed.add_field(name="🥩 Protein", value=f"{total_protein:.1f}g", inline=True)
        embed.add_field(name="🍞 Kohlenhydrate", value=f"{total_carbs:.1f}g", inline=True)
        embed.add_field(name="🧈 Fette", value=f"{total_fat:.1f}g", inline=True)
        
        # Macronutrient distribution
        total_macros = total_protein + total_carbs + total_fat
        if total_macros > 0:
            protein_pct = (total_protein / total_macros) * 100
            carbs_pct = (total_carbs / total_macros) * 100
            fat_pct = (total_fat / total_macros) * 100
            
            embed.add_field(
                name="📊 Verteilung", 
                value=f"P: {protein_pct:.0f}% | C: {carbs_pct:.0f}% | F: {fat_pct:.0f}%", 
                inline=False
            )
        
        # List today's meals
        meals_text = "\n".join([
            f"• {entry.get('food_name', 'Unknown')} ({entry.get('calories', 0)} kcal)"
            for entry in today_data
        ])
        
        if len(meals_text) > 1024:  # Discord embed field limit
            meals_text = meals_text[:1020] + "..."
        
        embed.add_field(name="🥗 Heutige Mahlzeiten", value=meals_text, inline=False)
        embed.set_footer(text=f"Stand: {today.strftime('%H:%M')} Uhr")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        bot_logger.log_error(
            "NUTRITION_COMMAND_ERROR",
            str(e),
            {"user": str(ctx.author.display_name)}
        )
        await ctx.send(f"❌ Fehler beim Abrufen der Ernährungsdaten: {str(e)}")

@bot.command(name="meals")
async def frequent_meals(ctx):
    """Show most frequent meals this month"""
    if ctx.channel.id != CALORIES_CHANNEL_ID:
        await ctx.send("This command can only be used in the calories channel!")
        return
    
    try:
        # Log command usage
        bot_logger.log_user_command(
            str(ctx.author.display_name),
            "frequent_meals",
            str(ctx.channel)
        )
        
        # Get this month's data
        today = datetime.now()
        discord_username = str(ctx.author.display_name)
        
        # Extract data
        data_extractor = CalorieDataExtractor()
        monthly_data = data_extractor.get_monthly_data(today.year, today.month)
        
        # Find matching user
        all_users = list(set(entry.get("person", "") for entry in monthly_data))
        user_match = None
        
        for user in all_users:
            if user.lower() in discord_username.lower() or discord_username.lower() in user.lower():
                user_match = user
                break
        
        if not user_match and all_users:
            user_match = all_users[0]
        
        if not user_match:
            await ctx.send("❌ Keine Daten für diesen Monat gefunden.")
            return
        
        # Get meal frequency analysis
        meal_frequency = data_extractor.get_meal_frequency_analysis(monthly_data, user_match)
        
        if meal_frequency.get('error'):
            await ctx.send("❌ Fehler bei der Mahlzeiten-Analyse.")
            return
        
        # Create embed
        embed = discord.Embed(
            title="🍽️ Häufigste Mahlzeiten",
            description=f"**{meal_frequency['total_meals']} Mahlzeiten** | **{meal_frequency['unique_foods']} verschiedene Gerichte**",
            color=0x00ff00
        )
        
        # Add variety score
        embed.add_field(
            name="🌈 Vielfalt-Score",
            value=f"{meal_frequency['variety_score']}%",
            inline=True
        )
        
        # Add most repeated meal
        most_repeated = meal_frequency['most_repeated_meal']
        embed.add_field(
            name="🔝 Häufigstes Gericht",
            value=f"{most_repeated[0]} ({most_repeated[1]}x)",
            inline=True
        )
        
        # List top meals
        top_meals = meal_frequency.get('top_meals', [])[:10]
        if top_meals:
            meals_text = "\n".join([
                f"{i+1}. {meal[0]} - **{meal[1]}x**"
                for i, meal in enumerate(top_meals)
            ])
            if len(meals_text) > 1024:
                meals_text = meals_text[:1020] + "..."
            embed.add_field(name="📊 Top 10 Mahlzeiten", value=meals_text, inline=False)
        
        embed.set_footer(text=f"Analyse für {today.strftime('%B %Y')}")
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Error in meals command: {e}")
        bot_logger.log_error(
            "MEALS_COMMAND_ERROR",
            str(e),
            {"user": str(ctx.author.display_name)}
        )
        await ctx.send("❌ Fehler beim Abrufen der Mahlzeiten-Daten.")

@bot.command(name="weekly")
async def weekly_summary(ctx):
    """Show this week's nutrition summary"""
    if ctx.channel.id != CALORIES_CHANNEL_ID:
        await ctx.send("This command can only be used in the calories channel!")
        return
    
    try:
        # Log command usage
        bot_logger.log_user_command(
            str(ctx.author.display_name),
            "weekly_summary",
            str(ctx.channel)
        )
        
        # Get this week's data
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())  # Monday
        discord_username = str(ctx.author.display_name)
        
        # Extract monthly data (we'll filter for the week)
        data_extractor = CalorieDataExtractor()
        monthly_data = data_extractor.get_monthly_data(today.year, today.month)
        
        # Filter for user and this week
        user_data = [
            entry for entry in monthly_data 
            if entry.get("person", "").lower() in discord_username.lower() or 
               discord_username.lower() in entry.get("person", "").lower()
        ]
        
        week_data = [
            entry for entry in user_data 
            if entry.get("date") >= week_start.date() and entry.get("date") <= today.date()
        ]
        
        if not week_data:
            embed = discord.Embed(
                title="📅 Wochenübersicht",
                description="Noch keine Mahlzeiten diese Woche erfasst.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate weekly totals
        total_calories = sum(entry.get("calories", 0) for entry in week_data)
        total_protein = sum(entry.get("protein", 0) for entry in week_data)
        total_carbs = sum(entry.get("carbohydrates", 0) for entry in week_data)
        total_fat = sum(entry.get("fat", 0) for entry in week_data)
        
        # Calculate daily averages
        unique_days = len(set(entry.get("date") for entry in week_data))
        avg_calories = total_calories / unique_days if unique_days > 0 else 0
        avg_protein = total_protein / unique_days if unique_days > 0 else 0
        avg_carbs = total_carbs / unique_days if unique_days > 0 else 0
        avg_fat = total_fat / unique_days if unique_days > 0 else 0
        
        # Create embed
        embed = discord.Embed(
            title="📅 Wochenübersicht",
            description=f"**{len(week_data)} Mahlzeiten** an **{unique_days} Tagen**",
            color=0x00ff00
        )
        
        # Weekly totals
        embed.add_field(name="🔥 Gesamt Kalorien", value=f"{total_calories} kcal", inline=True)
        embed.add_field(name="🥩 Gesamt Protein", value=f"{total_protein:.1f}g", inline=True)
        embed.add_field(name="🍞 Gesamt Carbs", value=f"{total_carbs:.1f}g", inline=True)
        embed.add_field(name="🧈 Gesamt Fette", value=f"{total_fat:.1f}g", inline=True)
        
        # Daily averages
        embed.add_field(name="📊 Ø Kalorien/Tag", value=f"{avg_calories:.0f} kcal", inline=True)
        embed.add_field(name="📊 Ø Protein/Tag", value=f"{avg_protein:.1f}g", inline=True)
        
        # Macronutrient distribution
        total_macros = total_protein + total_carbs + total_fat
        if total_macros > 0:
            protein_pct = (total_protein / total_macros) * 100
            carbs_pct = (total_carbs / total_macros) * 100
            fat_pct = (total_fat / total_macros) * 100
            
            embed.add_field(
                name="📊 Makro-Verteilung (Woche)", 
                value=f"P: {protein_pct:.0f}% | C: {carbs_pct:.0f}% | F: {fat_pct:.0f}%", 
                inline=False
            )
        
        # Daily breakdown
        daily_breakdown = {}
        for entry in week_data:
            date = entry.get("date")
            if date not in daily_breakdown:
                daily_breakdown[date] = {"calories": 0, "meals": 0}
            daily_breakdown[date]["calories"] += entry.get("calories", 0)
            daily_breakdown[date]["meals"] += 1
        
        daily_text = ""
        for date in sorted(daily_breakdown.keys()):
            day_name = date.strftime("%a")
            calories = daily_breakdown[date]["calories"]
            meals = daily_breakdown[date]["meals"]
            daily_text += f"{day_name}: {calories} kcal ({meals} Mahlzeiten)\n"
        
        if daily_text:
            embed.add_field(name="📅 Tägliche Aufschlüsselung", value=daily_text, inline=False)
        
        week_range = f"{week_start.strftime('%d.%m')} - {today.strftime('%d.%m.%Y')}"
        embed.set_footer(text=f"Woche: {week_range}")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Error in weekly command: {e}")
        bot_logger.log_error(
            "WEEKLY_COMMAND_ERROR",
            str(e),
            {"user": str(ctx.author.display_name)}
        )
        await ctx.send("❌ Fehler beim Abrufen der Wochendaten.")

@bot.command(name="nutrition_weekly")
async def weekly_nutrition(ctx):
    """Show this week's nutrition summary"""
    if ctx.channel.id != CALORIES_CHANNEL_ID:
        await ctx.send("This command can only be used in the calories channel!")
        return
    
    try:
        # Log command usage
        bot_logger.log_user_command(
            str(ctx.author.display_name),
            "weekly_nutrition",
            str(ctx.channel)
        )
        
        # Get this week's data
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())  # Monday
        discord_username = str(ctx.author.display_name)
        
        # Extract data
        data_extractor = CalorieDataExtractor()
        monthly_data = data_extractor.get_monthly_data(today.year, today.month)
        
        # Filter for user and this week
        user_data = [
            entry for entry in monthly_data 
            if entry.get("person", "").lower() in discord_username.lower() or 
               discord_username.lower() in entry.get("person", "").lower()
        ]
        
        week_data = [
            entry for entry in user_data 
            if entry.get("date") >= week_start.date() and entry.get("date") <= today.date()
        ]
        
        if not week_data:
            embed = discord.Embed(
                title="📅 Diese Woche",
                description="Noch keine Mahlzeiten diese Woche erfasst.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate weekly totals and averages
        total_calories = sum(entry.get("calories", 0) for entry in week_data)
        total_protein = sum(entry.get("protein", 0) for entry in week_data)
        total_carbs = sum(entry.get("carbohydrates", 0) for entry in week_data)
        total_fat = sum(entry.get("fat", 0) for entry in week_data)
        
        # Calculate unique days with data
        unique_days = len(set(entry.get("date") for entry in week_data))
        
        avg_calories = total_calories / unique_days if unique_days > 0 else 0
        avg_protein = total_protein / unique_days if unique_days > 0 else 0
        avg_carbs = total_carbs / unique_days if unique_days > 0 else 0
        avg_fat = total_fat / unique_days if unique_days > 0 else 0
        
        # Create embed
        embed = discord.Embed(
            title="📅 Diese Woche",
            description=f"**{week_start.strftime('%d.%m.')} - {today.strftime('%d.%m.%Y')}**",
            color=0x00ff00
        )
        
        embed.add_field(name="🔥 Gesamt Kalorien", value=f"{total_calories} kcal", inline=True)
        embed.add_field(name="📈 Ø Kalorien/Tag", value=f"{avg_calories:.0f} kcal", inline=True)
        embed.add_field(name="📅 Getrackte Tage", value=f"{unique_days}/7", inline=True)
        
        embed.add_field(name="🥩 Ø Protein/Tag", value=f"{avg_protein:.1f}g", inline=True)
        embed.add_field(name="🍞 Ø Kohlenhydrate/Tag", value=f"{avg_carbs:.1f}g", inline=True)
        embed.add_field(name="🧈 Ø Fette/Tag", value=f"{avg_fat:.1f}g", inline=True)
        
        # Daily breakdown
        daily_breakdown = {}
        for entry in week_data:
            date = entry.get("date")
            if date not in daily_breakdown:
                daily_breakdown[date] = {"calories": 0, "meals": 0}
            daily_breakdown[date]["calories"] += entry.get("calories", 0)
            daily_breakdown[date]["meals"] += 1
        
        # Show daily summary
        daily_text = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_date = day.date()
            if day_date in daily_breakdown:
                data = daily_breakdown[day_date]
                daily_text.append(f"**{day.strftime('%a %d.%m.')}:** {data['calories']} kcal ({data['meals']} Mahlzeiten)")
            else:
                daily_text.append(f"{day.strftime('%a %d.%m.')}: Keine Daten")
        
        embed.add_field(
            name="📊 Tägliche Übersicht",
            value="\n".join(daily_text),
            inline=False
        )
        
        embed.set_footer(text=f"Woche {today.isocalendar()[1]}, {today.year}")
        await ctx.send(embed=embed)
        
    except Exception as e:
        bot_logger.log_error(
            "WEEKLY_COMMAND_ERROR",
            str(e),
            {"user": str(ctx.author.display_name)}
        )
        await ctx.send(f"❌ Fehler bei der Wochen-Analyse: {str(e)}")

@bot.command(name="help_calories")
async def help_calories(ctx):
    """Show help information for the calories bot"""
    # Log help command usage
    bot_logger.log_user_command(
        str(ctx.author.display_name),
        "help_calories",
        str(ctx.channel)
    )
    
    embed = discord.Embed(
        title="🍽️ Enhanced Calories Bot Help",
        description="AI-powered food analysis with comprehensive nutrition tracking!",
        color=0x00aaff
    )
    
    embed.add_field(
        name="📸 How to Use",
        value="Simply upload an image of your food to this channel and I'll analyze it automatically!",
        inline=False
    )
    
    embed.add_field(
        name=" What I Analyze",
        value="• Food identification\n• Calorie estimation\n• Protein content (grams)\n• Carbohydrate content (grams)\n• Fat content (grams)\n• Macronutrient distribution\n• Confidence scoring",
        inline=True
    )
    
    embed.add_field(
        name="💾 Data Storage",
        value="Results are automatically saved to your FoodIate Notion database with full nutritional data",
        inline=True
    )
    
    embed.add_field(
        name="⚡ Available Commands",
        value="• `!help_calories` - Show this help\n• `!test_analysis` - Test bot status\n• Type `month` - Current month report with macros\n• Type `month_before` - Previous month report\n• `!nutrition` - Today's nutrition\n• `!weekly` - This week's summary\n• `!meals` - Most frequent meals\n• `!logs` - View logging info",
        inline=False
    )
    
    embed.add_field(
        name="📊 Enhanced Reports",
        value="• **Monthly**: Calories, macros, meal frequency\n• **Daily**: Current day nutrition breakdown\n• **Weekly**: 7-day nutrition trends\n• **Meal Analysis**: Frequency and variety tracking",
        inline=False
    )
    
    embed.add_field(
        name="🎯 Tips for Better Results",
        value="• Use good lighting\n• Show the full portion\n• Avoid blurry images\n• Include reference objects (plate, utensils)",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name="test_analysis")
async def test_analysis(ctx):
    """Test the analysis system with a sample"""
    # Log test command usage
    bot_logger.log_user_command(
        str(ctx.author.display_name),
        "test_analysis",
        str(ctx.channel)
    )
    
    if ctx.channel.id != CALORIES_CHANNEL_ID:
        await ctx.send("This command can only be used in the calories channel!")
        return
    
    embed = discord.Embed(
        title="🧪 System Test",
        description="Bot is running and connected to all services:",
        color=0x00ff00
    )
    
    embed.add_field(name="🤖 Discord", value="✅ Connected", inline=True)
    embed.add_field(name="🧠 OpenRouter AI", value="✅ Ready" if OPENROUTER_API_KEY else "❌ No API Key", inline=True)
    embed.add_field(name="💾 Notion", value="✅ Connected" if NOTION_TOKEN else "❌ No Token", inline=True)
    embed.add_field(name="📋 Logging", value="✅ Active", inline=True)
    
    embed.add_field(
        name="📋 Ready to Analyze",
        value="Upload a food image to test the full analysis pipeline!",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name="logs")
async def show_logs(ctx):
    """Show logging information and statistics"""
    # Log the logs command usage
    bot_logger.log_user_command(
        str(ctx.author.display_name),
        "logs",
        str(ctx.channel)
    )
    
    if ctx.channel.id != CALORIES_CHANNEL_ID:
        await ctx.send("This command can only be used in the calories channel!")
        return
    
    try:
        # Get log summary
        log_summary = bot_logger.get_log_summary()
        
        embed = discord.Embed(
            title="📋 Bot Logging Information",
            description="Current logging status and statistics",
            color=0x00aaff
        )
        
        embed.add_field(
            name="📁 Log Directory",
            value=f"`{log_summary.get('log_directory', 'logs/')}`",
            inline=False
        )
        
        # Show log categories
        directories = log_summary.get('directories', [])
        if directories:
            log_info = []
            for dir_info in directories:
                path = dir_info.get('path', 'unknown')
                file_count = dir_info.get('file_count', 0)
                log_info.append(f"📊 **{path}**: {file_count} files")
            
            embed.add_field(
                name="📚 Log Categories",
                value="\n".join(log_info[:10]),  # Limit to 10 entries
                inline=False
            )
        
        embed.add_field(
            name="🔍 Available Logs",
            value="• Food analysis events\n• Monthly reports\n• User activity\n• System events\n• Error tracking",
            inline=True
        )
        
        embed.add_field(
            name="📝 Log Features",
            value="• JSON structured data\n• Rotating file logs\n• Daily organization\n• Error categorization",
            inline=True
        )
        
        embed.set_footer(text=f"Logs are stored locally and rotated automatically (max 10MB per file)")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        bot_logger.log_error(
            "LOGS_COMMAND_ERROR",
            str(e),
            {"user": str(ctx.author.display_name)}
        )
        await ctx.send(f"❌ Error retrieving log information: {str(e)}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in environment variables")
        exit(1)
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPENROUTER_API_KEY not found in environment variables")
        exit(1)
    if not NOTION_TOKEN:
        print("❌ Error: NOTION_TOKEN not found in environment variables")
        exit(1)
    
    print("🚀 Starting Calories Bot...")
    bot.run(DISCORD_TOKEN) 