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
from enhanced_data_loader import load_all_md_content, get_random_learning_content
from langchain.schema import Document as LangchainDocument

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
    """Send a random learning snippet to the channel."""
    try:
        title, content = get_random_learning_content()
        
        # Format the message nicely
        embed = discord.Embed(
            title=f"📚 Daily Learning: {title}",
            description=content,
            color=0x3498db
        )
        embed.set_footer(text="Ask me questions about this content using !ask")
        
        await channel.send(embed=embed)
        logger.info(f"Sent learning content: {title}")
        
    except Exception as e:
        logger.error(f"Error sending learning content: {e}")
        await channel.send("Sorry, I encountered an error while getting your learning content.")

async def load_knowledge_base():
    """Load all MD files into the RAG system at startup."""
    try:
        logger.info("Loading knowledge base from MD files...")
        all_content = load_all_md_content()
        
        if not all_content:
            logger.warning("No content found in MD files")
            return
        
        # Convert to LangChain documents
        documents = []
        for title, content in all_content:
            doc = LangchainDocument(
                page_content=content,
                metadata={"title": title, "source": "knowledge_base"}
            )
            documents.append(doc)
        
        # Add to vector store
        success = vector_store.add_documents(documents)
        if success:
            logger.info(f"Successfully loaded {len(documents)} documents into knowledge base")
        else:
            logger.error("Failed to load documents into vector store")
            
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('------')
    
    # Load knowledge base
    await load_knowledge_base()
    
    # Schedule daily learning
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            scheduler.add_job(lambda: bot.loop.create_task(send_learning(channel)), 'cron', hour=8, minute=0)
            scheduler.start()
            logger.info("Daily learning scheduled for 08:00")

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
    await ctx.send('Pong! 🏓 Learning Bot is ready!')

@bot.command(name='help')
async def help_command(ctx):
    """Display available commands and their usage."""
    embed = discord.Embed(
        title="🤖 Learning Bot Commands",
        color=0x3498db
    )
    embed.add_field(
        name="!ping", 
        value="Check if the bot is responsive", 
        inline=False
    )
    embed.add_field(
        name="!help", 
        value="Display this help message", 
        inline=False
    )
    embed.add_field(
        name="!learn", 
        value="Upload a document for learning (PDF or DOCX) or get random learning content", 
        inline=False
    )
    embed.add_field(
        name="!ask <question>", 
        value="Ask a question about the learned content", 
        inline=False
    )
    embed.add_field(
        name="!clear", 
        value="Clear all learned content", 
        inline=False
    )
    embed.add_field(
        name="💡 Pro Tip", 
        value="Just type 'learn' in chat to get random learning content!", 
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='learn')
async def learn(ctx):
    """Handle document uploads or provide random learning content."""
    if ctx.message.attachments:
        # Handle file upload
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
                embed = discord.Embed(
                    title="✅ Document Learned Successfully!",
                    description=f"I've learned from **{attachment.filename}**! You can now ask questions about it.",
                    color=0x2ecc71
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("Failed to store the document. Please try again.")
            
            # Clean up
            file_path.unlink()
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await ctx.send("An error occurred while processing the document. Please try again.")
    else:
        # Provide random learning content
        await send_learning(ctx.channel)

@bot.command(name='ask')
async def ask(ctx, *, question: str):
    """Answer questions about the learned content."""
    try:
        # Search for relevant documents
        docs = vector_store.similarity_search(question, k=5)
        if not docs:
            await ctx.send("I don't have enough context to answer your question. Please upload some documents first or wait for the knowledge base to load.")
            return
        
        # Generate response
        response = llm_service.generate_response(question, docs)
        
        # Create embed for response
        embed = discord.Embed(
            title="🧠 AI Response",
            description=response,
            color=0x9b59b6
        )
        embed.set_footer(text=f"Based on {len(docs)} relevant documents")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        await ctx.send("An error occurred while processing your question. Please try again.")

@bot.command(name='clear')
async def clear(ctx):
    """Clear all learned content."""
    try:
        if vector_store.clear():
            # Reload the knowledge base
            await load_knowledge_base()
            embed = discord.Embed(
                title="🔄 Content Cleared & Reloaded",
                description="All uploaded content has been cleared. The original knowledge base has been reloaded.",
                color=0xf39c12
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Failed to clear the content. Please try again.")
    except Exception as e:
        logger.error(f"Error clearing content: {e}")
        await ctx.send("An error occurred while clearing the content. Please try again.")

@bot.event
async def on_message(message):
    """Handle messages, including the 'learn' trigger."""
    if message.author == bot.user:
        return
    
    # Check if message contains 'learn' (case insensitive)
    if 'learn' in message.content.lower() and not message.content.startswith('!'):
        await send_learning(message.channel)
        return
    
    # Process commands
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