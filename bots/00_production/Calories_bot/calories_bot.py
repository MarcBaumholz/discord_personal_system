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
import sys

# Add log bot directory to path for API monitoring
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'log_bot'))
from api_monitor_shared import track_openrouter_call

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
    """Represents the result of AI food analysis with complete nutritional information"""
    def __init__(self, food_name: str, calories: int, confidence: float, description: str = "", 
                 protein: float = 0.0, carbohydrates: float = 0.0, fat: float = 0.0,
                 vitamins: dict = None, minerals: dict = None, fiber: float = 0.0,
                 sugar: float = 0.0, saturated_fat: float = 0.0, cholesterol: float = 0.0,
                 analysis_source: str = "ai"):
        self.food_name = food_name
        self.calories = calories
        self.confidence = confidence
        self.description = description
        self.protein = protein  # in grams
        self.carbohydrates = carbohydrates  # in grams
        self.fat = fat  # in grams
        self.vitamins = vitamins or {}  # vitamins dict
        self.minerals = minerals or {}  # minerals dict
        self.fiber = fiber  # in grams
        self.sugar = sugar  # in grams
        self.saturated_fat = saturated_fat  # in grams
        self.cholesterol = cholesterol  # in mg
        self.analysis_source = analysis_source  # "ground_truth" or "ai"
        self.timestamp = datetime.now()
        
    def get_meal_hash(self) -> str:
        """Generate a hash for meal similarity detection"""
        import hashlib
        # Create a simplified version of the food name for comparison
        simplified_name = re.sub(r'[^a-z0-9\s]', '', self.food_name.lower().strip())
        return hashlib.md5(simplified_name.encode()).hexdigest()[:8]

class GroundTruthHandler:
    """Handles ground truth food database for accurate nutrition data"""
    
    def __init__(self):
        self.ground_truth_file = os.path.join(os.path.dirname(__file__), 'ground_truth_foods.json')
        self.foods_db = self._load_ground_truth_db()
    
    def _load_ground_truth_db(self) -> dict:
        """Load the ground truth foods database"""
        try:
            if os.path.exists(self.ground_truth_file):
                with open(self.ground_truth_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                bot_logger.log_error("File not found", "Ground truth database file not found")
                return {"foods": {}}
        except Exception as e:
            bot_logger.log_error("Ground truth error", f"Error loading ground truth database: {e}")
            return {"foods": {}}
    
    def search_ground_truth(self, text: str) -> Optional[FoodAnalysisResult]:
        """Search for food in ground truth database"""
        try:
            text_lower = text.lower().strip()
            
            # Direct match first
            if text_lower in self.foods_db.get("foods", {}):
                return self._create_result_from_ground_truth(text_lower, self.foods_db["foods"][text_lower])
            
            # Keyword matching
            for food_key, food_data in self.foods_db.get("foods", {}).items():
                keywords = food_data.get("keywords", [])
                for keyword in keywords:
                    if keyword.lower() in text_lower or text_lower in keyword.lower():
                        print(f"Ground truth match found: {food_key} (keyword: {keyword})")
                        return self._create_result_from_ground_truth(food_key, food_data)
            
            return None
            
        except Exception as e:
            bot_logger.log_error("Ground truth search error", f"Error searching ground truth: {e}")
            return None
    
    def _create_result_from_ground_truth(self, food_key: str, food_data: dict) -> FoodAnalysisResult:
        """Create FoodAnalysisResult from ground truth data"""
        return FoodAnalysisResult(
            food_name=food_data.get("food_name", food_key),
            calories=food_data.get("calories", 0),
            confidence=food_data.get("confidence", 100.0),
            description=food_data.get("description", ""),
            protein=food_data.get("protein", 0.0),
            carbohydrates=food_data.get("carbohydrates", 0.0),
            fat=food_data.get("fat", 0.0),
            vitamins=food_data.get("vitamins", {}),
            minerals=food_data.get("minerals", {}),
            fiber=food_data.get("fiber", 0.0),
            sugar=food_data.get("sugar", 0.0),
            saturated_fat=food_data.get("saturated_fat", 0.0),
            cholesterol=food_data.get("cholesterol", 0.0),
            analysis_source="ground_truth"
        )
    
    def add_food_to_ground_truth(self, food_text: str, nutrition_data: dict):
        """Add new food to ground truth database"""
        try:
            if "foods" not in self.foods_db:
                self.foods_db["foods"] = {}
            
            self.foods_db["foods"][food_text.lower()] = nutrition_data
            
            # Save to file
            with open(self.ground_truth_file, 'w', encoding='utf-8') as f:
                json.dump(self.foods_db, f, indent=2, ensure_ascii=False)
            
            print(f"Added {food_text} to ground truth database")
            return True
            
        except Exception as e:
            bot_logger.log_error("Ground truth add error", f"Error adding food to ground truth: {e}")
            return False

class AITextHandler:
    """Handles AI text analysis for food descriptions"""
    
    @staticmethod
    async def analyze_food_text(text: str) -> Optional[FoodAnalysisResult]:
        """Analyze food text using AI"""
        try:
            print(f"🔍 Analyzing food text: {text}")
            
            # Enhanced prompt for comprehensive nutrition analysis
            prompt = f"""
            Analyze this food description and provide detailed nutritional information:
            Text: "{text}"
            
            Please identify the food and provide:
            1. Food name (German preferred if applicable)
            2. Estimated calories for typical serving size
            3. Protein content in grams
            4. Carbohydrates content in grams  
            5. Fat content in grams
            6. Confidence score (0-100) for your analysis
            7. Brief description with serving size estimate
            8. Fiber content in grams
            9. Sugar content in grams
            10. Saturated fat in grams
            11. Key vitamins (vitamin_c, vitamin_a, vitamin_b6, etc.) in mg/mcg
            12. Key minerals (calcium, iron, potassium, sodium, etc.) in mg
            
            Respond in this exact JSON format:
            {{
                "food_name": "name of the food with typical serving size",
                "calories": 123,
                "protein": 15.5,
                "carbohydrates": 45.2,
                "fat": 8.3,
                "confidence": 85,
                "description": "detailed description with serving size",
                "fiber": 3.2,
                "sugar": 12.1,
                "saturated_fat": 2.8,
                "vitamins": {{
                    "vitamin_c": 15.2,
                    "vitamin_a": 98,
                    "vitamin_b6": 0.4
                }},
                "minerals": {{
                    "calcium": 120,
                    "iron": 2.1,
                    "potassium": 300,
                    "sodium": 450
                }}
            }}
            
            Base your estimates on typical serving sizes and be realistic about portions.
            """
            
            # Use Kimi model for text analysis - fix: use sync client
            response = openai_client.chat.completions.create(
                model="moonshotai/kimi-k2:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            # Track successful API call
            track_openrouter_call("calories-bot", "moonshotai/kimi-k2:free", True)
            
            response_text = response.choices[0].message.content.strip()
            print(f"🤖 AI Text Response: {response_text}")
            
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
                    description=json_data.get("description", ""),
                    fiber=float(json_data.get("fiber", 0.0)),
                    sugar=float(json_data.get("sugar", 0.0)),
                    saturated_fat=float(json_data.get("saturated_fat", 0.0)),
                    vitamins=json_data.get("vitamins", {}),
                    minerals=json_data.get("minerals", {}),
                    analysis_source="ai"
                )
            else:
                bot_logger.log_warning("AI response parsing", "Could not extract JSON from AI response")
                return None
                
        except Exception as e:
            # Track failed API call
            track_openrouter_call("calories-bot", "moonshotai/kimi-k2:free", False)
            bot_logger.log_error("AI text analysis error", f"Error analyzing food text: {e}")
            return None

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
            
            # Create the enhanced prompt for comprehensive food analysis
            prompt = """
            Please analyze this food image and provide comprehensive nutritional information:
            1. The name of the food item(s) you see
            2. An estimate of the total calories in this serving
            3. Estimate of protein content in grams
            4. Estimate of carbohydrates content in grams
            5. Estimate of fat content in grams
            6. A confidence score (0-100) for your analysis
            7. A brief description of what you see with portion size
            8. Fiber content in grams
            9. Sugar content in grams 
            10. Saturated fat content in grams
            11. Key vitamins (vitamin_c, vitamin_a, vitamin_b6, etc.) in mg/mcg
            12. Key minerals (calcium, iron, potassium, sodium, etc.) in mg
            
            Please respond in this exact JSON format:
            {
                "food_name": "name of the food with serving size",
                "calories": 123,
                "protein": 15.5,
                "carbohydrates": 45.2,
                "fat": 8.3,
                "confidence": 85,
                "description": "detailed description of the food and portion size",
                "fiber": 3.2,
                "sugar": 12.1,
                "saturated_fat": 2.8,
                "vitamins": {
                    "vitamin_c": 15.2,
                    "vitamin_a": 98,
                    "vitamin_b6": 0.4
                },
                "minerals": {
                    "calcium": 120,
                    "iron": 2.1,
                    "potassium": 300,
                    "sodium": 450
                }
            }
            
            Focus on being accurate with nutritional estimation. If you see multiple food items, provide the total nutrition for everything visible.
            All nutrients should be realistic estimates based on typical food composition databases.
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
            
            # Track successful API call
            track_openrouter_call("calories-bot", "qwen/qwen2.5-vl-72b-instruct:free", True)
            
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
                    description=json_data.get("description", ""),
                    fiber=float(json_data.get("fiber", 0.0)),
                    sugar=float(json_data.get("sugar", 0.0)),
                    saturated_fat=float(json_data.get("saturated_fat", 0.0)),
                    vitamins=json_data.get("vitamins", {}),
                    minerals=json_data.get("minerals", {}),
                    analysis_source="ai"
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
            # Track failed API call
            track_openrouter_call("calories-bot", "qwen/qwen2.5-vl-72b-instruct:free", False)
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

async def save_to_notion(analysis: FoodAnalysisResult, discord_user: str, image_url: str = None) -> bool:
    """Wrapper function to save analysis to Notion"""
    try:
        if image_url:
            return await NotionHandler.save_food_analysis(analysis, image_url, discord_user)
        else:
            # For text-based analysis, create a dummy image URL or modify the save function
            return await NotionHandler.save_food_analysis(analysis, "text_analysis", discord_user)
    except Exception as e:
        bot_logger.log_error(f"Error saving to Notion: {e}")
        return False

async def process_food_text(message: discord.Message):
    """Process a text food description"""
    try:
        # Log text processing start
        bot_logger.log_user_command(
            str(message.author.display_name),
            "text_food_analysis",
            str(message.channel)
        )
        
        # Send processing message
        processing_msg = await message.channel.send("🔍 Analyzing your food description...")
        
        food_text = message.content.strip()
        
        # Step 1: Check ground truth database first
        ground_truth_result = ground_truth_handler.search_ground_truth(food_text)
        
        if ground_truth_result:
            # Found in ground truth database
            # Convert FoodAnalysisResult to dict for logging
            ground_truth_dict = {
                'food_name': ground_truth_result.food_name,
                'calories': ground_truth_result.calories,
                'confidence': ground_truth_result.confidence,
                'protein': ground_truth_result.protein,
                'carbohydrates': ground_truth_result.carbohydrates,
                'fat': ground_truth_result.fat,
                'user': message.author.display_name,
                'analysis_source': ground_truth_result.analysis_source
            }
            bot_logger.log_food_analysis(ground_truth_dict)
            
            # Create enhanced embed
            embed = await create_enhanced_analysis_embed(ground_truth_result, source_text=food_text)
            
            # Try to save to Notion
            saved = await save_to_notion(ground_truth_result, message.author.display_name)
            
            # Update embed footer
            if saved:
                embed.set_footer(text=f"✅ Saved to database | Source: Ground Truth | Meal ID: {ground_truth_result.get_meal_hash()}")
            else:
                embed.set_footer(text=f"❌ Failed to save | Source: Ground Truth | Meal ID: {ground_truth_result.get_meal_hash()}")
            
            await processing_msg.edit(content="", embed=embed)
            
        else:
            # Not found in ground truth, use AI analysis
            analysis = await AITextHandler.analyze_food_text(food_text)
            
            if analysis:
                # Convert analysis to dict for logging
                analysis_dict = {
                    'food_name': analysis.food_name,
                    'calories': analysis.calories,
                    'confidence': analysis.confidence,
                    'protein': analysis.protein,
                    'carbohydrates': analysis.carbohydrates,
                    'fat': analysis.fat,
                    'user': message.author.display_name,
                    'analysis_source': analysis.analysis_source
                }
                bot_logger.log_food_analysis(analysis_dict)
                
                # Create enhanced embed
                embed = await create_enhanced_analysis_embed(analysis, source_text=food_text)
                
                # Try to save to Notion
                saved = await save_to_notion(analysis, message.author.display_name)
                
                # Update embed footer
                if saved:
                    embed.set_footer(text=f"✅ Saved to database | Source: AI Analysis | Meal ID: {analysis.get_meal_hash()}")
                else:
                    embed.set_footer(text=f"❌ Failed to save | Source: AI Analysis | Meal ID: {analysis.get_meal_hash()}")
                
                await processing_msg.edit(content="", embed=embed)
                
            else:
                await processing_msg.edit(content="❌ Sorry, I couldn't analyze that food description. Please try again with more details.")
    
    except Exception as e:
        bot_logger.log_error("Text processing error", f"Error processing food text: {e}")
        await message.channel.send(f"❌ Error processing food text: {e}")

async def create_enhanced_analysis_embed(analysis: FoodAnalysisResult, image_url: str = None, source_text: str = None) -> discord.Embed:
    """Create an enhanced Discord embed with complete nutrition analysis"""
    # Color based on confidence and source
    if analysis.analysis_source == "ground_truth":
        color = 0x00AA00  # Green for ground truth
        title = "🍽️ Food Analysis Complete! (Ground Truth Data)"
    else:
        color = 0x00ff00 if analysis.confidence > 70 else 0xffaa00
        title = "🍽️ Food Analysis Complete! (AI Analysis)"
    
    embed = discord.Embed(title=title, color=color)
    
    # Basic info
    embed.add_field(name="🥗 Food Identified", value=analysis.food_name, inline=True)
    embed.add_field(name="🔥 Calories", value=f"{analysis.calories} kcal", inline=True)
    embed.add_field(name="🎯 Confidence", value=f"{analysis.confidence:.1f}%", inline=True)
    
    # Macronutrients
    embed.add_field(name="🥩 Protein", value=f"{analysis.protein:.1f}g", inline=True)
    embed.add_field(name="🍞 Carbs", value=f"{analysis.carbohydrates:.1f}g", inline=True)
    embed.add_field(name="🧈 Fat", value=f"{analysis.fat:.1f}g", inline=True)
    
    # Additional nutrients if available
    if analysis.fiber > 0:
        embed.add_field(name="🌾 Fiber", value=f"{analysis.fiber:.1f}g", inline=True)
    if analysis.sugar > 0:
        embed.add_field(name="🍯 Sugar", value=f"{analysis.sugar:.1f}g", inline=True)
    if analysis.saturated_fat > 0:
        embed.add_field(name="🧈 Sat. Fat", value=f"{analysis.saturated_fat:.1f}g", inline=True)
    
    # Vitamins
    if analysis.vitamins:
        vitamin_text = ""
        for vitamin, amount in analysis.vitamins.items():
            if amount > 0:
                vitamin_text += f"{vitamin.replace('_', ' ').title()}: {amount:.1f}\n"
        if vitamin_text:
            embed.add_field(name="💊 Key Vitamins", value=vitamin_text[:1024], inline=True)
    
    # Minerals  
    if analysis.minerals:
        mineral_text = ""
        for mineral, amount in analysis.minerals.items():
            if amount > 0:
                mineral_text += f"{mineral.replace('_', ' ').title()}: {amount:.1f}mg\n"
        if mineral_text:
            embed.add_field(name="⚡ Key Minerals", value=mineral_text[:1024], inline=True)
    
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
    
    if source_text:
        embed.add_field(name="📥 Your Input", value=f'"{source_text}"', inline=False)
    
    if image_url:
        embed.set_image(url=image_url)
    
    embed.set_footer(text=f"Analysis completed at {analysis.timestamp.strftime('%H:%M:%S')} | Meal ID: {analysis.get_meal_hash()}")
    
    return embed

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
        
        # Create result embed - use enhanced embed function
        embed = await create_enhanced_analysis_embed(analysis, image_url=attachment.url)
        
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

# Initialize handlers after class definitions
ground_truth_handler = GroundTruthHandler()

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
    # Check if message is a text food description (not a command)
    elif message.content and not message.content.startswith('!') and len(message.content.strip()) > 3:
        await process_food_text(message)
    
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

@bot.command(name="add_food")
async def add_food_to_ground_truth(ctx, *, food_description: str = None):
    """Add a food to the ground truth database with detailed nutrition info"""
    if ctx.channel.id != CALORIES_CHANNEL_ID:
        await ctx.send("This command can only be used in the calories channel!")
        return
    
    if not food_description:
        await ctx.send("❌ Please provide a food description!\nUsage: `!add_food butterbrezel mit honig`")
        return
    
    try:
        # Log command usage
        bot_logger.log_user_command(
            str(ctx.author.display_name),
            "add_food_ground_truth",
            str(ctx.channel)
        )
        
        await ctx.send("🔍 Analyzing food for ground truth database... This will be used for future quick lookups!")
        
        # Use AI to analyze the food first
        analysis = await AITextHandler.analyze_food_text(food_description)
        
        if not analysis:
            await ctx.send("❌ Could not analyze this food. Please try again with more details.")
            return
        
        # Create ground truth entry
        ground_truth_entry = {
            "food_name": analysis.food_name,
            "calories": analysis.calories,
            "protein": analysis.protein,
            "carbohydrates": analysis.carbohydrates,
            "fat": analysis.fat,
            "confidence": 100,  # Ground truth is 100% confident
            "description": analysis.description,
            "vitamins": analysis.vitamins,
            "minerals": analysis.minerals,
            "fiber": analysis.fiber,
            "sugar": analysis.sugar,
            "saturated_fat": analysis.saturated_fat,
            "cholesterol": analysis.cholesterol,
            "keywords": [food_description.lower(), analysis.food_name.lower()]
        }
        
        # Add to ground truth database
        success = ground_truth_handler.add_food_to_ground_truth(food_description.lower(), ground_truth_entry)
        
        if success:
            # Create success embed
            embed = discord.Embed(
                title="✅ Food Added to Ground Truth Database!",
                color=0x00ff00
            )
            embed.add_field(name="🥗 Food", value=analysis.food_name, inline=True)
            embed.add_field(name="🔑 Lookup Key", value=f'"{food_description.lower()}"', inline=True)
            embed.add_field(name="🔥 Calories", value=f"{analysis.calories} kcal", inline=True)
            
            embed.add_field(name="📊 Macros", 
                          value=f"P: {analysis.protein}g | C: {analysis.carbohydrates}g | F: {analysis.fat}g", 
                          inline=False)
            
            embed.add_field(name="💡 Usage", 
                          value=f"Next time someone types '{food_description}', this data will be used instantly!", 
                          inline=False)
            
            embed.set_footer(text="Ground truth data provides instant, accurate nutrition info")
            
            await ctx.send(embed=embed)
            
        else:
            await ctx.send("❌ Failed to add food to ground truth database. Please try again.")
    
    except Exception as e:
        bot_logger.log_error(f"Error adding food to ground truth: {e}")
        await ctx.send(f"❌ Error adding food: {e}")

@bot.command(name="list_foods")
async def list_ground_truth_foods(ctx):
    """List all foods in the ground truth database"""
    if ctx.channel.id != CALORIES_CHANNEL_ID:
        await ctx.send("This command can only be used in the calories channel!")
        return
    
    try:
        foods = ground_truth_handler.foods_db.get("foods", {})
        
        if not foods:
            await ctx.send("📭 No foods in ground truth database yet. Use `!add_food <description>` to add some!")
            return
        
        embed = discord.Embed(
            title="🗂️ Ground Truth Food Database",
            description=f"Contains {len(foods)} reliable food entries",
            color=0x00AA00
        )
        
        food_list = []
        for key, data in list(foods.items())[:20]:  # Limit to 20 foods
            food_name = data.get("food_name", key)
            calories = data.get("calories", 0)
            food_list.append(f"• **{food_name}** ({calories} kcal)")
        
        embed.add_field(
            name="🍽️ Available Foods",
            value="\n".join(food_list),
            inline=False
        )
        
        if len(foods) > 20:
            embed.add_field(
                name="📊 More Foods",
                value=f"... and {len(foods) - 20} more foods",
                inline=False
            )
        
        embed.set_footer(text="These foods provide instant, accurate nutrition data when mentioned")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error listing foods: {e}")

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