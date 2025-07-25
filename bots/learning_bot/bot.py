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
import random
import asyncio
import json
import hashlib

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
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # Disable default help

# Initialize components
document_processor = DocumentProcessor()
vector_store = VectorStore()
llm_service = LLMService()

# Create uploads directory
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Metadata file to track processed documents
METADATA_FILE = Path("vector_store/processed_files.json")

scheduler = AsyncIOScheduler()

def get_file_hash(file_path: Path) -> str:
    """Generate a hash for a file to detect changes."""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    except Exception:
        return ""

def load_processed_files_metadata() -> dict:
    """Load metadata about already processed files."""
    try:
        if METADATA_FILE.exists():
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load processed files metadata: {e}")
    return {}

def save_processed_files_metadata(metadata: dict):
    """Save metadata about processed files."""
    try:
        METADATA_FILE.parent.mkdir(exist_ok=True)
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save processed files metadata: {e}")

def truncate_content(text: str, max_length: int = 1500) -> str:
    """Truncate content to fit within limits while preserving structure."""
    if len(text) <= max_length:
        return text
    
    # Find a good breaking point
    truncated = text[:max_length]
    last_newline = truncated.rfind('\n')
    if last_newline > max_length * 0.8:  # If newline is reasonably close to end
        return truncated[:last_newline] + "\n[Content truncated for length...]"
    else:
        return truncated + "\n[Content truncated for length...]"

async def check_and_load_new_documents():
    """Check for new or modified documents and load only those."""
    try:
        logger.info("Checking for new or modified documents...")
        uploads_path = Path("uploads")
        
        if not uploads_path.exists():
            logger.warning("Uploads folder does not exist")
            return 0
        
        # Load existing processed files metadata
        processed_files = load_processed_files_metadata()
        
        # Get all markdown files from uploads
        md_files = list(uploads_path.glob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files in uploads")
        
        new_or_modified_files = []
        
        # Check which files are new or modified
        for file_path in md_files:
            file_hash = get_file_hash(file_path)
            file_key = str(file_path.name)
            
            if file_key not in processed_files or processed_files[file_key] != file_hash:
                new_or_modified_files.append((file_path, file_hash))
                logger.info(f"File {file_path.name} is new or modified")
        
        if not new_or_modified_files:
            logger.info("No new or modified documents found")
            return 0
        
        logger.info(f"Processing {len(new_or_modified_files)} new/modified files...")
        
        total_docs_added = 0
        for file_path, file_hash in new_or_modified_files:
            try:
                logger.info(f"Processing {file_path.name}...")
                
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content.strip():
                    # Process the document into chunks
                    docs = document_processor.process_document(content)
                    
                    # Add metadata to identify the source
                    for doc in docs:
                        doc.metadata['source'] = file_path.name
                        doc.metadata['file_type'] = 'learning_content'
                        doc.metadata['file_hash'] = file_hash
                    
                    # Add to vector store
                    if vector_store.add_documents(docs):
                        total_docs_added += len(docs)
                        logger.info(f"Added {len(docs)} chunks from {file_path.name}")
                        
                        # Update processed files metadata
                        processed_files[str(file_path.name)] = file_hash
                    else:
                        logger.error(f"Failed to add documents from {file_path.name}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
        
        # Save updated metadata
        save_processed_files_metadata(processed_files)
        
        logger.info(f"Successfully processed {total_docs_added} total document chunks from new/modified files")
        return total_docs_added
        
    except Exception as e:
        logger.error(f"Error checking for new documents: {e}")
        return 0

async def load_all_uploads():
    """Load all documents from the uploads folder into the vector store - DEPRECATED."""
    logger.warning("load_all_uploads() is deprecated. Use check_and_load_new_documents() instead.")
    return await check_and_load_new_documents()

async def send_daily_learning():
    """Send a daily learning to the configured channel."""
    try:
        if not DISCORD_CHANNEL_ID:
            logger.warning("No Discord channel ID configured for daily learning")
            return
        
        channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
        if not channel:
            logger.error(f"Could not find channel with ID {DISCORD_CHANNEL_ID}")
            return
        
        logger.info("Generating daily learning...")
        
        # Get random documents from vector store
        all_docs = vector_store.get_random_documents(3)
        if not all_docs:
            await channel.send("📚 Good morning! I don't have any documents loaded yet. Please upload some learning materials using `!upload`.")
            return
        
        # Prepare content for LLM (truncate if too long)
        content_parts = []
        total_length = 0
        max_content_length = 1200  # Leave room for prompt structure
        
        for doc in all_docs:
            source = doc.metadata.get('source', 'Unknown')
            doc_content = f"Source: {source}\nContent: {doc.page_content}"
            
            if total_length + len(doc_content) > max_content_length:
                # Truncate this document to fit
                remaining_space = max_content_length - total_length
                if remaining_space > 100:  # Only add if meaningful space left
                    doc_content = truncate_content(doc_content, remaining_space)
                    content_parts.append(doc_content)
                break
            else:
                content_parts.append(doc_content)
                total_length += len(doc_content)
        
        content_text = "\n\n".join(content_parts)
        
        # Create a detailed learning prompt
        learning_prompt = (
            "Based on the following content from the user's knowledge base, "
            "create a comprehensive daily learning summary that includes:\n\n"
            "1. **🎯 Key Action Steps** (3-5 concrete steps the user can take today)\n"
            "2. **📋 Summary** (brief overview of the main concepts)\n"
            "3. **📚 Detailed Learning Steps** (step-by-step breakdown for implementation)\n"
            "4. **📖 Source Information** (where this knowledge comes from)\n"
            "5. **🏷️ Key Topics** (main areas where this knowledge applies)\n"
            "6. **🔑 Keywords** (important terms and concepts)\n\n"
            "Make this actionable and inspiring for starting the day. Focus on practical application.\n\n"
            "Content from knowledge base:\n"
            + content_text
        )
        
        # Generate the comprehensive learning response
        response = llm_service.generate_detailed_learning(learning_prompt)
        
        # Send the response
        morning_greeting = "🌅 **Good Morning! Here's your daily learning:**\n\n"
        
        # Split response into Discord-friendly chunks
        max_chunk_size = 1900  # Leave room for greeting
        if len(response) > max_chunk_size:
            chunks = []
            current_chunk = ""
            
            for line in response.split('\n'):
                if len(current_chunk) + len(line) + 1 > max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    current_chunk += "\n" + line if current_chunk else line
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Send chunks
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await channel.send(f"{morning_greeting}{chunk}")
                else:
                    await channel.send(chunk)
        else:
            await channel.send(f"{morning_greeting}{response}")
        
        logger.info("Daily learning sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending daily learning: {e}")
        if DISCORD_CHANNEL_ID:
            try:
                channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
                if channel:
                    await channel.send("❌ Sorry, I encountered an error while generating your daily learning. Please try the `!learn` command manually.")
            except:
                pass

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('------')
    
    # Send immediate connection notification
    if DISCORD_CHANNEL_ID:
        try:
            channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
            if channel:
                await channel.send("🔄 **Learning Bot connecting...** Loading knowledge base...")
        except Exception as e:
            logger.error(f"Failed to send connection notification: {e}")
    
    # Initialize document loading with error handling
    total_docs = 0
    startup_status = "✅ Ready"
    
    try:
        # Check existing vector store
        existing_doc_count = vector_store.get_document_count()
        logger.info(f"Found {existing_doc_count} documents already in vector store")
        
        # Check for new or modified documents
        new_doc_count = await check_and_load_new_documents()
        if new_doc_count > 0:
            logger.info(f"Processed {new_doc_count} new document chunks")
        else:
            logger.info("No new documents to process - using existing vector store")
        
        total_docs = vector_store.get_document_count()
        logger.info(f"Total documents available: {total_docs}")
        
    except Exception as e:
        logger.error(f"Error during document loading: {e}")
        startup_status = "⚠️ Ready (document loading issues)"
        total_docs = 0
    
    # Schedule daily learning at 8 AM
    if DISCORD_CHANNEL_ID:
        logger.info("Setting up daily learning scheduler for 8:00 AM")
        
        # Only set up scheduler if not already running
        if not scheduler.running:
            scheduler.add_job(
                send_daily_learning,
                'cron',
                hour=8,
                minute=0,
                timezone='Europe/Berlin'  # Adjust timezone as needed
            )
            scheduler.start()
            logger.info("Daily learning scheduler started")
        else:
            logger.info("Daily learning scheduler already running")
    else:
        logger.warning("No Discord channel ID configured - daily learning disabled")
    
    # Send startup notification to Discord channel
    if DISCORD_CHANNEL_ID:
        try:
            channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
            if channel:
                if total_docs > 0:
                    startup_message = f"🤖 **Learning Bot is now running!** {startup_status}\n📚 Ready with {total_docs} documents in knowledge base\n⚡ Performance optimized - fast startup enabled\n\nUse `!help` to see available commands."
                else:
                    startup_message = f"🤖 **Learning Bot is now running!** {startup_status}\n📚 Knowledge base loading encountered issues\n🔧 Use `!reload` or `!rebuild` to fix document loading\n\nUse `!help` to see available commands."
                
                await channel.send(startup_message)
                logger.info(f"Startup notification sent to channel {DISCORD_CHANNEL_ID}")
            else:
                logger.warning(f"Could not find channel with ID {DISCORD_CHANNEL_ID} for startup notification")
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    else:
        logger.info("Bot ready - no startup notification channel configured")

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
    try:
        doc_count = vector_store.get_document_count()
        await ctx.send(f'Pong! 🏓\n📚 I have {doc_count} documents loaded in my knowledge base.')
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
        await ctx.send('Pong! 🏓\n❌ Error checking document count.')

@bot.command(name='help')
async def help_command(ctx):
    """Display available commands and their usage."""
    try:
        doc_count = vector_store.get_document_count()
        help_text = f"""
**Learning Bot Commands:**
`!ping` - Check bot responsiveness and document count
`!help` - Display this help message
`!upload` - Upload a document for learning (PDF or DOCX)
`!ask <question>` - Ask a question about the learned content
`!learn` - Get a random detailed learning from your knowledge base
`!reload` - Check for new/modified documents and load them
`!rebuild` - Force complete rebuild of knowledge base (slow!)

**Current Status:**
📚 **{doc_count} documents** loaded in knowledge base
🕗 **Daily learning** scheduled for 8:00 AM
💾 **Smart loading** - only processes new/modified files on startup

**How to use:**
1. Upload documents using `!upload` command with file attachment
2. Ask questions about the content using `!ask`
3. Get random learnings using `!learn` for structured knowledge review
4. Use `!reload` to check for new files without restarting
5. Daily learnings are automatically sent at 8:00 AM

**Performance:**
✅ Vector store is persistent - no re-processing on restart
✅ Only new/modified files are processed automatically
"""
        await ctx.send(help_text)
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await ctx.send("Error displaying help information.")

@bot.command(name='reload')
async def reload_documents(ctx):
    """Check for new or modified documents and reload only those."""
    try:
        await ctx.send("🔄 Checking for new or modified documents...")
        existing_count = vector_store.get_document_count()
        new_doc_count = await check_and_load_new_documents()
        total_docs = vector_store.get_document_count()
        
        if new_doc_count > 0:
            await ctx.send(f"✅ Reload complete! Added {new_doc_count} new document chunks.\n📚 Total documents in knowledge base: {total_docs}")
        else:
            await ctx.send(f"✅ No new documents found - all {existing_count} documents are up to date.\n📚 Total documents in knowledge base: {total_docs}")
    except Exception as e:
        logger.error(f"Error in reload command: {e}")
        await ctx.send("❌ Error reloading documents. Please try again.")

@bot.command(name='rebuild')
async def rebuild_knowledge_base(ctx):
    """Force a complete rebuild of the knowledge base (use only when needed)."""
    try:
        await ctx.send("🔧 **WARNING**: This will rebuild the entire knowledge base from scratch. This may take several minutes...")
        
        # Clear the vector store
        vector_store.clear()
        
        # Clear the metadata
        save_processed_files_metadata({})
        
        # Reprocess all documents
        await ctx.send("🔄 Processing all documents...")
        doc_count = await check_and_load_new_documents()
        total_docs = vector_store.get_document_count()
        
        await ctx.send(f"✅ Rebuild complete! Processed {doc_count} document chunks.\n📚 Total documents in knowledge base: {total_docs}")
        
    except Exception as e:
        logger.error(f"Error in rebuild command: {e}")
        await ctx.send("❌ Error rebuilding knowledge base. Please try again.")

@bot.command(name='upload')
async def upload(ctx):
    """Handle document uploads for learning."""
    if not ctx.message.attachments:
        await ctx.send("Please attach a PDF or DOCX file to upload.")
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
        # Add metadata
        for doc in docs:
            doc.metadata['source'] = attachment.filename
            doc.metadata['file_type'] = 'uploaded_document'
        
        if vector_store.add_documents(docs):
            total_docs = vector_store.get_document_count()
            await ctx.send(f"Successfully uploaded and processed {attachment.filename}! 📚\nAdded {len(docs)} chunks. Total documents: {total_docs}\nYou can now ask questions about it or get random learnings from it.")
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
            await ctx.send("I don't have enough context to answer your question. Please upload some documents first using `!upload` or use `!reload` to load existing documents.")
            return
        
        # Generate response
        response = llm_service.generate_response(question, docs)
        
        # Add source information
        sources = list(set([doc.metadata.get('source', 'Unknown') for doc in docs]))
        source_text = f"\n\n📖 **Sources:** {', '.join(sources)}"
        
        full_response = response + source_text
        
        if len(full_response) > 2000:
            await ctx.send(response)
            await ctx.send(source_text)
        else:
            await ctx.send(full_response)
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        await ctx.send("An error occurred while processing your question. Please try again.")

@bot.command(name='learn')
async def learn(ctx):
    """Get a random detailed learning from your knowledge base."""
    try:
        await ctx.send("🎓 Generating your learning... This may take a moment.")
        
        # Get random documents from vector store
        all_docs = vector_store.get_random_documents(3)
        if not all_docs:
            await ctx.send("No documents found in your knowledge base. Please upload some documents first using `!upload` or use `!reload` to load existing documents.")
            return
        
        # Prepare content for LLM (truncate if too long)
        content_parts = []
        total_length = 0
        max_content_length = 1200  # Leave room for prompt structure
        
        for doc in all_docs:
            source = doc.metadata.get('source', 'Unknown')
            doc_content = f"Source: {source}\nContent: {doc.page_content}"
            
            if total_length + len(doc_content) > max_content_length:
                # Truncate this document to fit
                remaining_space = max_content_length - total_length
                if remaining_space > 100:  # Only add if meaningful space left
                    doc_content = truncate_content(doc_content, remaining_space)
                    content_parts.append(doc_content)
                break
            else:
                content_parts.append(doc_content)
                total_length += len(doc_content)
        
        content_text = "\n\n".join(content_parts)
        
        # Create a detailed learning prompt
        learning_prompt = (
            "Based on the following content from the user's knowledge base, create a comprehensive learning summary that includes:\n\n"
            "1. **🎯 Key Action Steps** (3-5 concrete steps the user can take immediately)\n"
            "2. **📋 Summary** (brief overview of the main concepts)\n" 
            "3. **📚 Detailed Learning Steps** (step-by-step breakdown for implementation)\n"
            "4. **📖 Source Information** (where this knowledge comes from)\n"
            "5. **🏷️ Key Topics** (main areas where this knowledge applies)\n"
            "6. **🔑 Keywords** (important terms and concepts)\n\n"
            "Format this as a well-structured learning that the user can immediately turn into action.\n\n"
            "Content from knowledge base:\n"
            + content_text
        )
        
        # Generate the comprehensive learning response
        response = llm_service.generate_detailed_learning(learning_prompt)
        
        # Split response into Discord-friendly chunks
        max_chunk_size = 1900
        if len(response) > max_chunk_size:
            chunks = []
            current_chunk = ""
            
            for line in response.split('\n'):
                if len(current_chunk) + len(line) + 1 > max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    current_chunk += "\n" + line if current_chunk else line
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Send chunks
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await ctx.send(f"🎓 **Random Learning from your Knowledge Base:**\n\n{chunk}")
                else:
                    await ctx.send(chunk)
        else:
            await ctx.send(f"🎓 **Random Learning from your Knowledge Base:**\n\n{response}")
        
    except Exception as e:
        logger.error(f"Error generating learning: {e}")
        await ctx.send("An error occurred while generating your learning. Please try again.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
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