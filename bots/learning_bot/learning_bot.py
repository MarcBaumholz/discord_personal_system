import os
import discord
from discord.ext import commands, tasks
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import json
import aiohttp
import random
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('learning_bot')

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DAILY_LEARNING_CHANNEL_ID"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "deepseek/deepseek-r1-0528-qwen3-8b:free"

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Create necessary directories
DATA_DIR = Path("data")
DOCUMENTS_DIR = DATA_DIR / "documents"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
METADATA_DIR = DATA_DIR / "metadata"

for directory in [DATA_DIR, DOCUMENTS_DIR, EMBEDDINGS_DIR, METADATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class LearningBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.documents = {}
        self.load_documents()
        
    def load_documents(self):
        """Load existing documents from metadata"""
        try:
            metadata_file = METADATA_DIR / "documents.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.documents = json.load(f)
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.documents = {}

    def save_documents(self):
        """Save documents metadata"""
        try:
            metadata_file = METADATA_DIR / "documents.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving documents: {e}")

    async def generate_daily_learning(self):
        """Generate daily learning from random document"""
        try:
            if not self.documents:
                return "No documents available. Please upload some documents first."

            # Select random document
            doc_id = random.choice(list(self.documents.keys()))
            doc_info = self.documents[doc_id]

            # Prepare prompt for the model
            prompt = f"""Create a daily learning from this document:
            Title: {doc_info['title']}
            Content: {doc_info['content'][:1000]}  # First 1000 chars for context

            Please provide:
            1. A main learning point
            2. 3 key takeaways
            3. A practical application
            Format it nicely for Discord with emojis and markdown.
            """

            # Call OpenRouter API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": "You are a learning expert who creates engaging daily learning content."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }

                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        logger.error(f"Error from OpenRouter API: {response.status}")
                        return "Error generating daily learning. Please try again later."

        except Exception as e:
            logger.error(f"Error generating daily learning: {e}")
            return "Error generating daily learning. Please try again later."

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f"Logged in as {bot.user}")
    logger.info(f"Using learning channel ID: {DISCORD_CHANNEL_ID}")
    
    # Start daily learning task
    daily_learning.start()
    
    # Send welcome message
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("📚 Learning Bot is online! I'll help you learn something new every day. Use `!help` to see available commands.")

@tasks.loop(hours=24)
async def daily_learning():
    """Send daily learning at 9:00 AM"""
    try:
        # Get current time in Europe/Berlin
        berlin_tz = pytz.timezone('Europe/Berlin')
        current_time = datetime.now(berlin_tz)
        
        # Check if it's 9:00 AM
        if current_time.hour == 9 and current_time.minute == 0:
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                # Generate and send daily learning
                learning = await bot.generate_daily_learning()
                await channel.send(f"📚 **Daily Learning**\n\n{learning}")
    except Exception as e:
        logger.error(f"Error in daily learning task: {e}")

@daily_learning.before_loop
async def before_daily_learning():
    """Wait until the bot is ready before starting the task"""
    await bot.wait_until_ready()

@bot.command(name="upload")
async def upload_document(ctx, *, title):
    """Upload a new learning document"""
    if not ctx.message.attachments:
        await ctx.send("Please attach a document (PDF, TXT, or DOCX) with your upload command.")
        return

    attachment = ctx.message.attachments[0]
    file_extension = os.path.splitext(attachment.filename)[1].lower()
    
    if file_extension not in ['.pdf', '.txt', '.docx']:
        await ctx.send("Please upload a PDF, TXT, or DOCX file.")
        return

    try:
        # Download the file
        file_path = DOCUMENTS_DIR / f"{len(bot.documents) + 1}{file_extension}"
        await attachment.save(file_path)
        
        # Read file content
        content = ""
        if file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_extension == '.pdf':
            # Add PDF processing here
            content = "PDF content extraction to be implemented"
        elif file_extension == '.docx':
            # Add DOCX processing here
            content = "DOCX content extraction to be implemented"
        
        # Save document metadata
        doc_id = str(len(bot.documents) + 1)
        bot.documents[doc_id] = {
            'title': title,
            'filename': attachment.filename,
            'content': content,
            'upload_date': datetime.now().isoformat()
        }
        bot.save_documents()
        
        await ctx.send(f"✅ Document '{title}' uploaded successfully!")
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        await ctx.send("Error uploading document. Please try again.")

@bot.command(name="learning")
async def get_learning(ctx):
    """Get current daily learning"""
    try:
        learning = await bot.generate_daily_learning()
        await ctx.send(f"📚 **Daily Learning**\n\n{learning}")
    except Exception as e:
        logger.error(f"Error getting learning: {e}")
        await ctx.send("Error generating learning. Please try again.")

@bot.command(name="list")
async def list_documents(ctx):
    """List all uploaded documents"""
    if not bot.documents:
        await ctx.send("No documents available. Use `!upload` to add some.")
        return
    
    doc_list = "📚 **Available Documents:**\n\n"
    for doc_id, doc in bot.documents.items():
        doc_list += f"ID: {doc_id} - {doc['title']}\n"
    
    await ctx.send(doc_list)

@bot.command(name="help")
async def help_command(ctx):
    """Show help information"""
    help_text = """
📚 **Learning Bot Help**

**Commands:**
- `!upload <title>` - Upload a new learning document (PDF, TXT, or DOCX)
- `!learning` - Get the current daily learning
- `!list` - List all uploaded documents
- `!help` - Show this help message

I'll send you a new learning every day at 9:00 AM!
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN) 