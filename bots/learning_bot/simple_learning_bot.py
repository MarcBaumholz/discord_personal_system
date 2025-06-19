import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from enhanced_data_loader import load_all_md_content, get_random_learning_content
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle

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

class SimpleRAG:
    """Simple RAG system using sentence transformers."""
    
    def __init__(self):
        logger.info("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.documents = []
        self.embeddings = []
        self.storage_path = Path("simple_rag_storage.pkl")
    
    def add_documents(self, documents):
        """Add documents to the knowledge base."""
        logger.info(f"Adding {len(documents)} documents to knowledge base...")
        
        # Extract text content
        texts = []
        for title, content in documents:
            texts.append(f"{title}\n\n{content}")
            self.documents.append({"title": title, "content": content})
        
        # Generate embeddings in batches
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch)
            self.embeddings.extend(batch_embeddings)
            logger.info(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} documents")
        
        # Save to storage
        self.save_to_storage()
        logger.info(f"Total documents in knowledge base: {len(self.documents)}")
    
    def search(self, query, k=3):
        """Search for relevant documents."""
        if not self.embeddings:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                results.append({
                    'document': self.documents[idx],
                    'similarity': similarities[idx]
                })
        
        return results
    
    def save_to_storage(self):
        """Save knowledge base to disk."""
        data = {
            'documents': self.documents,
            'embeddings': self.embeddings
        }
        with open(self.storage_path, 'wb') as f:
            pickle.dump(data, f)
    
    def load_from_storage(self):
        """Load knowledge base from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data['documents']
                    self.embeddings = data['embeddings']
                logger.info(f"Loaded {len(self.documents)} documents from storage")
                return True
            except Exception as e:
                logger.error(f"Error loading from storage: {e}")
        return False

# Initialize RAG system
rag = SimpleRAG()

async def send_learning(channel):
    """Send a random learning snippet to the channel."""
    try:
        title, content = get_random_learning_content()
        
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
        # Try to load from storage first
        if rag.load_from_storage():
            return
        
        logger.info("Loading knowledge base from MD files...")
        all_content = load_all_md_content()
        
        if not all_content:
            logger.warning("No content found in MD files")
            return
        
        # Add to RAG system
        rag.add_documents(all_content)
        logger.info(f"Successfully loaded {len(all_content)} documents into knowledge base")
            
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")

def generate_simple_response(query, context_docs):
    """Generate a simple response based on context."""
    if not context_docs:
        return "I don't have enough information to answer your question."
    
    response_parts = []
    response_parts.append(f"**Question:** {query}\n\n")
    
    for i, doc_info in enumerate(context_docs[:2], 1):
        doc = doc_info['document']
        similarity = doc_info['similarity']
        
        content = doc['content']
        if len(content) > 400:
            content = content[:400] + "..."
        
        response_parts.append(f"**{i}. {doc['title']}** *(Relevance: {similarity:.0%})*\n")
        response_parts.append(f"{content}\n\n")
    
    return "".join(response_parts)

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
            scheduler = AsyncIOScheduler()
            scheduler.add_job(lambda: bot.loop.create_task(send_learning(channel)), 'cron', hour=8, minute=0)
            scheduler.start()
            logger.info("Daily learning scheduled for 08:00")

@bot.command(name='ping')
async def ping(ctx):
    """Simple command to check if the bot is responsive."""
    await ctx.send('Pong! 🏓 Simple Learning Bot is ready!')

@bot.command(name='info')
async def info_command(ctx):
    """Display available commands and their usage."""
    embed = discord.Embed(title="🤖 Simple Learning Bot", color=0x3498db)
    embed.add_field(name="!ping", value="Check bot status", inline=False)
    embed.add_field(name="!learn", value="Get random learning content", inline=False)
    embed.add_field(name="!ask <question>", value="Ask about the knowledge base", inline=False)
    embed.add_field(name="!status", value="Show knowledge base stats", inline=False)
    embed.add_field(name="!info", value="Show this help message", inline=False)
    embed.add_field(name="💡 Tip", value="Type 'learn' anywhere in chat!", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='learn')
async def learn(ctx):
    """Provide random learning content."""
    await send_learning(ctx.channel)

@bot.command(name='ask')
async def ask(ctx, *, question: str):
    """Answer questions about the learned content."""
    try:
        results = rag.search(question, k=3)
        
        if not results:
            await ctx.send("I don't have enough context to answer your question. The knowledge base might still be loading.")
            return
        
        response = generate_simple_response(question, results)
        
        if len(response) > 2000:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        await ctx.send("An error occurred while processing your question.")

@bot.command(name='status')
async def status(ctx):
    """Show knowledge base status."""
    embed = discord.Embed(title="📊 Knowledge Base Status", color=0x2ecc71)
    embed.add_field(name="Documents", value=len(rag.documents), inline=True)
    embed.add_field(name="Embeddings", value=len(rag.embeddings), inline=True)
    embed.add_field(name="Model", value="all-MiniLM-L6-v2", inline=True)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    """Handle messages, including the 'learn' trigger."""
    if message.author == bot.user:
        return
    
    if 'learn' in message.content.lower() and not message.content.startswith('!'):
        await send_learning(message.channel)
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