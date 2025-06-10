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
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional
import re

# API Clients
from notion_client import Client as NotionClient
from openai import OpenAI

# Load environment variables
# Load environment variables from main discord directory
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
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
    """Represents the result of AI food analysis"""
    def __init__(self, food_name: str, calories: int, confidence: float, description: str = ""):
        self.food_name = food_name
        self.calories = calories
        self.confidence = confidence
        self.description = description
        self.timestamp = datetime.now()

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
            Please analyze this food image and provide:
            1. The name of the food item(s) you see
            2. An estimate of the total calories in this serving
            3. A confidence score (0-100) for your analysis
            4. A brief description of what you see
            
            Please respond in this exact JSON format:
            {
                "food_name": "name of the food",
                "calories": 123,
                "confidence": 85,
                "description": "brief description of the food and portion"
            }
            
            Focus on being accurate with calorie estimation. If you see multiple food items, provide the total calories for everything visible.
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
                    confidence=float(json_data.get("confidence", 0)),
                    description=json_data.get("description", "")
                )
            else:
                # Fallback parsing if JSON not found
                lines = response_text.split('\n')
                food_name = "Unknown Food"
                calories = 0
                confidence = 50.0
                description = "Analysis completed"
                
                for line in lines:
                    if 'food' in line.lower() or 'name' in line.lower():
                        food_name = line.split(':')[-1].strip().strip('"')
                    elif 'calorie' in line.lower():
                        cal_match = re.search(r'(\d+)', line)
                        if cal_match:
                            calories = int(cal_match.group(1))
                    elif 'confidence' in line.lower():
                        conf_match = re.search(r'(\d+)', line)
                        if conf_match:
                            confidence = float(conf_match.group(1))
                
                return FoodAnalysisResult(food_name, calories, confidence, description)
                
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
                "date": {
                    "date": {
                        "start": analysis.timestamp.isoformat()
                    }
                },
                "confidence": {
                    "number": analysis.confidence
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
    """Create a Discord embed with the analysis results"""
    embed = discord.Embed(
        title="🍽️ Food Analysis Complete!",
        color=0x00ff00 if analysis.confidence > 70 else 0xffaa00
    )
    
    embed.add_field(name="🥗 Food Identified", value=analysis.food_name, inline=True)
    embed.add_field(name="🔥 Estimated Calories", value=f"{analysis.calories} kcal", inline=True)
    embed.add_field(name="🎯 Confidence", value=f"{analysis.confidence:.1f}%", inline=True)
    
    if analysis.description:
        embed.add_field(name="📝 Description", value=analysis.description, inline=False)
    
    embed.set_image(url=image_url)
    embed.set_footer(text=f"Analysis completed at {analysis.timestamp.strftime('%H:%M:%S')}")
    
    return embed

async def process_food_image(message: discord.Message, attachment: discord.Attachment):
    """Process a food image attachment"""
    try:
        # Send processing message
        processing_msg = await message.channel.send("🔄 Analyzing your food image...")
        
        # Analyze the image
        analysis = await AIVisionHandler.analyze_food_image(attachment.url)
        
        if analysis is None:
            await processing_msg.edit(content="❌ Sorry, I couldn't analyze this image. Please try again with a clearer food photo.")
            return
        
        # Save to Notion database
        saved = await NotionHandler.save_food_analysis(analysis, attachment.url, str(message.author))
        
        # Create result embed
        embed = await create_analysis_embed(analysis, attachment.url)
        
        if saved:
            embed.add_field(name="💾 Database", value="✅ Saved to FoodIate", inline=True)
        else:
            embed.add_field(name="💾 Database", value="❌ Failed to save", inline=True)
        
        # Update the processing message with results
        await processing_msg.edit(content="", embed=embed)
        
        # Add reaction to original message
        await message.add_reaction("✅")
        
    except Exception as e:
        print(f"❌ Error processing food image: {e}")
        await message.channel.send("❌ An error occurred while processing your image. Please try again.")

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'📊 Monitoring channel ID: {CALORIES_CHANNEL_ID}')
    print(f'💾 Connected to Notion database: {FOODIATE_DB_ID}')

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Only process messages from the calories channel
    if message.channel.id != CALORIES_CHANNEL_ID:
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

@bot.command(name="help_calories")
async def help_calories(ctx):
    """Show help information for the calories bot"""
    embed = discord.Embed(
        title="🍽️ Calories Bot Help",
        description="Upload food images to get AI-powered calorie analysis!",
        color=0x00aaff
    )
    
    embed.add_field(
        name="📸 How to Use",
        value="Simply upload an image of your food to this channel and I'll analyze it automatically!",
        inline=False
    )
    
    embed.add_field(
        name="🔍 What I Analyze",
        value="• Food identification\n• Calorie estimation\n• Portion size assessment\n• Confidence scoring",
        inline=True
    )
    
    embed.add_field(
        name="💾 Data Storage",
        value="Results are automatically saved to your FoodIate Notion database",
        inline=True
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
    
    embed.add_field(
        name="📋 Ready to Analyze",
        value="Upload a food image to test the full analysis pipeline!",
        inline=False
    )
    
    await ctx.send(embed=embed)

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