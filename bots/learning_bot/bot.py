import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands
from document_processor import DocumentProcessor
from vector_store import VectorStore
from llm_service import LLMService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data_loader import get_random_learning

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize components
document_processor = DocumentProcessor()
vector_store = VectorStore()
llm_service = LLMService()

# Create uploads directory
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

scheduler = AsyncIOScheduler()

async def send_learning(channel):
    title, content, actions = get_random_learning()
    msg = f"**{title}**\n\n{content}"
    if actions:
        msg += f"\n\n**Action Steps:**\n{actions}"
    await channel.send(msg)

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('------')
    # Schedule daily learning
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            scheduler.add_job(lambda: bot.loop.create_task(send_learning(channel)), 'cron', hour=8, minute=0)
            scheduler.start()

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use !help to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. Please check the command usage.")
    else:
        logger.error(f"An error occurred: {error}")
        await ctx.send("An error occurred while processing your command.")

@bot.command(name='ping')
async def ping(ctx):
    """Simple command to check if the bot is responsive."""
    await ctx.send('Pong! 🏓')

@bot.command(name='help')
async def help_command(ctx):
    """Display available commands and their usage."""
    help_text = """
**Available Commands:**
`!ping` - Check if the bot is responsive
`!help` - Display this help message
`!learn` - Upload a document for learning (PDF or DOCX)
`!ask <question>` - Ask a question about the learned content
`!clear` - Clear all learned content

**How to use:**
1. Upload a document using `!learn` command
2. Ask questions about the content using `!ask`
3. Use `!clear` to start fresh with new documents
"""
    await ctx.send(help_text)

@bot.command(name='learn')
async def learn(ctx):
    """Handle document uploads for learning."""
    if not ctx.message.attachments:
        await ctx.send("Please attach a PDF or DOCX file to learn from.")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.filename.lower().endswith(('.pdf', '.docx')):
        await ctx.send("Please upload a PDF or DOCX file.")
        return
    
    try:
        # Download the file
        file_path = UPLOADS_DIR / attachment.filename
        await attachment.save(file_path)
        
        # Process the document
        text = document_processor.load_document(str(file_path))
        if not text:
            await ctx.send("Failed to process the document. Please try again.")
            return
        
        # Add to vector store
        docs = document_processor.process_document(text)
        if vector_store.add_documents(docs):
            await ctx.send(f"Successfully learned from {attachment.filename}! You can now ask questions about it.")
        else:
            await ctx.send("Failed to store the document. Please try again.")
        
        # Clean up
        file_path.unlink()
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await ctx.send("An error occurred while processing the document. Please try again.")

@bot.command(name='ask')
async def ask(ctx, *, question: str):
    """Answer questions about the learned content."""
    try:
        # Search for relevant documents
        docs = vector_store.similarity_search(question)
        if not docs:
            await ctx.send("I don't have enough context to answer your question. Please upload some documents first.")
            return
        
        # Generate response
        response = llm_service.generate_response(question, docs)
        await ctx.send(response)
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        await ctx.send("An error occurred while processing your question. Please try again.")

@bot.command(name='clear')
async def clear(ctx):
    """Clear all learned content."""
    try:
        if vector_store.clear():
            await ctx.send("All learned content has been cleared. You can start fresh with new documents.")
        else:
            await ctx.send("Failed to clear the content. Please try again.")
    except Exception as e:
        logger.error(f"Error clearing content: {e}")
        await ctx.send("An error occurred while clearing the content. Please try again.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    if channel_id and message.channel.id == int(channel_id) and 'learn' in message.content.lower():
        await send_learning(message.channel)
    await bot.process_commands(message)

def main():
    """Main function to run the bot."""
    if not DISCORD_TOKEN:
        logger.error("No Discord token found. Please set DISCORD_TOKEN in .env file")
        return

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main() 