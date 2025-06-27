"""
Discord Publisher for Personal RSS News Bot.
Handles Discord bot functionality, message formatting, and channel publishing.
"""

import discord
from discord.ext import commands
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import os
import json
import re

logger = logging.getLogger(__name__)


class DiscordPublisher:
    """Handles Discord bot operations and message publishing."""
    
    def __init__(self, bot_token: str, target_channel_id: int, 
                 command_prefix: str = '!', max_embed_length: int = 4096):
        """Initialize Discord publisher with bot configuration."""
        self.bot_token = bot_token
        self.target_channel_id = target_channel_id
        self.command_prefix = command_prefix
        self.max_embed_length = max_embed_length
        
        # Configure Discord bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        # Initialize bot
        self.bot = commands.Bot(command_prefix=command_prefix, intents=intents)
        self.target_channel = None
        self.is_ready = False
        
        # Set up event handlers
        self._setup_event_handlers()
        self._setup_commands()
    
    def _setup_event_handlers(self):
        """Set up Discord bot event handlers."""
        
        @self.bot.event
        async def on_ready():
            logger.info(f'{self.bot.user} has connected to Discord!')
            
            # Get target channel
            self.target_channel = self.bot.get_channel(self.target_channel_id)
            if self.target_channel:
                logger.info(f'Target channel found: {self.target_channel.name}')
                self.is_ready = True
                
                # Send simple "bot is running" message immediately
                try:
                    simple_embed = discord.Embed(
                        title="🟢 Bot Connected",
                        description="RSS News Bot is now online and ready!",
                        color=0x00ff00,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await self.target_channel.send(embed=simple_embed)
                    logger.info("Simple startup message sent")
                except Exception as e:
                    logger.error(f"Error sending simple startup message: {e}")
                    
            else:
                logger.error(f'Target channel with ID {self.target_channel_id} not found')
            
            # Set bot status
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="RSS feeds for weekly updates"
            )
            await self.bot.change_presence(activity=activity)
        
        @self.bot.event
        async def on_error(event, *args, **kwargs):
            logger.error(f'Discord bot error in {event}: {args}')
    
    def _setup_commands(self):
        """Set up Discord bot commands."""
        
        @self.bot.command(name='status')
        async def status_command(ctx):
            """Check bot status and configuration."""
            embed = discord.Embed(
                title="RSS News Bot Status",
                color=0x00ff00 if self.is_ready else 0xff0000,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="Status", 
                value="✅ Ready" if self.is_ready else "❌ Not Ready",
                inline=True
            )
            embed.add_field(
                name="Target Channel",
                value=f"#{self.target_channel.name}" if self.target_channel else "Not Found",
                inline=True
            )
            embed.add_field(
                name="Bot User",
                value=f"{self.bot.user.name}#{self.bot.user.discriminator}",
                inline=True
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='test')
        async def test_command(ctx):
            """Test message posting."""
            test_embed = self.create_test_embed()
            await ctx.send(embed=test_embed)
        
        @self.bot.command(name='commands')
        async def commands_command(ctx):
            """Show available bot commands."""
            embed = discord.Embed(
                title="🤖 RSS News Bot Commands",
                description="Available commands for the Personal RSS News Bot",
                color=0x2196F3,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="📰 `!news`",
                value="Generate a fresh personalized news summary (fetches new articles)",
                inline=False
            )
            embed.add_field(
                name="⚡ `!quicknews [days]`",
                value="Quick summary from recent articles (default: 3 days)",
                inline=False
            )
            embed.add_field(
                name="📊 `!status`",
                value="Check bot status and configuration",
                inline=False
            )
            embed.add_field(
                name="🔧 `!test`",
                value="Test bot functionality",
                inline=False
            )
            embed.add_field(
                name="👀 `!preview`",
                value="Preview how summaries look",
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ About",
                value="This bot curates content from 20+ RSS sources covering AI, productivity, cognitive science, automation, and performance.",
                inline=False
            )
            
            embed.set_footer(text="Use !commands to see this message again")
            await ctx.send(embed=embed)
        
        @self.bot.command(name='preview')
        async def preview_command(ctx, *, content: str = None):
            """Preview how a summary would look."""
            if not content:
                content = "This is a preview of how your weekly summary would appear in Discord."
            
            preview_embed = self.create_summary_embed(
                "Weekly Summary Preview",
                content,
                article_count=5,
                categories=["AI_LLM", "PRODUCTIVITY", "COGNITIVE_SCIENCE"]
            )
            await ctx.send(embed=preview_embed)
        
        @self.bot.command(name='news')
        async def news_command(ctx):
            """Generate and post an on-demand news summary."""
            await ctx.send("🔄 Generating your personalized news summary... This may take a moment.")
            
            try:
                # Import here to avoid circular imports
                from main import RSSNewsBot
                
                # Create a temporary bot instance to use the processing methods
                if hasattr(self, '_rss_bot_instance'):
                    bot_instance = self._rss_bot_instance
                else:
                    await ctx.send("❌ Bot instance not available. Please restart the bot.")
                    return
                
                # Run the full processing workflow
                await ctx.send("📡 Fetching latest articles from RSS feeds...")
                new_articles = await bot_instance.fetch_and_process_articles()
                
                await ctx.send("🤖 Analyzing article relevance with AI...")
                analyzed_articles = await bot_instance.analyze_article_relevance()
                
                await ctx.send("📝 Generating personalized summary...")
                summary = await bot_instance.generate_weekly_summary()
                
                if summary:
                    # Get metadata for the summary
                    articles = bot_instance.db_manager.get_recent_articles(
                        days=bot_instance.config['days_to_process'],
                        min_relevance=bot_instance.config['min_relevance_score'],
                        limit=bot_instance.config['max_articles_per_week']
                    )
                    categories = list(set(article['category'] for article in articles))
                    
                    # Post the summary
                    message_ids = await self.publish_long_summary(
                        summary_content=summary,
                        title="📰 On-Demand News Summary",
                        article_count=len(articles),
                        categories=categories
                    )
                    
                    if message_ids:
                        await ctx.send(f"✅ Summary generated! Found {new_articles} new articles, analyzed {analyzed_articles} articles.")
                    else:
                        await ctx.send("❌ Failed to publish summary.")
                else:
                    await ctx.send("❌ No relevant articles found for summary generation.")
                    
            except Exception as e:
                logger.error(f"Error in news command: {e}")
                await ctx.send(f"❌ Error generating news summary: {str(e)}")
        
        @self.bot.command(name='quicknews')
        async def quicknews_command(ctx, days: int = 3):
            """Quick news summary from recent high-relevance articles (no new fetching)."""
            try:
                await ctx.send(f"📰 Fetching news summary from the last {days} days...")
                
                # Import here to avoid circular imports
                if hasattr(self, '_rss_bot_instance'):
                    bot_instance = self._rss_bot_instance
                else:
                    await ctx.send("❌ Bot instance not available. Please restart the bot.")
                    return
                
                # Get recent high-relevance articles without fetching new ones
                articles = bot_instance.db_manager.get_recent_articles(
                    days=days,
                    min_relevance=0.6,  # Slightly lower threshold for quick news
                    limit=15  # Fewer articles for quick summary
                )
                
                if not articles:
                    await ctx.send(f"📭 No high-relevance articles found in the last {days} days.")
                    return
                
                # Generate summary
                summary = await bot_instance.llm_processor.generate_weekly_summary(articles)
                
                if summary:
                    categories = list(set(article['category'] for article in articles))
                    
                    message_ids = await self.publish_long_summary(
                        summary_content=summary,
                        title=f"⚡ Quick News Summary ({days} days)",
                        article_count=len(articles),
                        categories=categories
                    )
                    
                    if message_ids:
                        await ctx.send(f"✅ Quick summary generated from {len(articles)} articles!")
                    else:
                        await ctx.send("❌ Failed to publish quick summary.")
                else:
                    await ctx.send("❌ Failed to generate quick summary.")
                    
            except Exception as e:
                logger.error(f"Error in quicknews command: {e}")
                await ctx.send(f"❌ Error generating quick news: {str(e)}")
    
    async def start_bot(self):
        """Start the Discord bot."""
        try:
            await self.bot.start(self.bot_token)
        except discord.LoginFailure:
            logger.error("Failed to login to Discord. Check bot token.")
            raise
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}")
            raise
    
    async def stop_bot(self):
        """Stop the Discord bot gracefully."""
        if self.bot:
            await self.bot.close()
    
    def create_summary_embed(self, title: str, content: str, 
                           article_count: int = 0, categories: List[str] = None,
                           week_start: str = None) -> discord.Embed:
        """Create a rich embed for weekly summary."""
        
        # Truncate content if too long
        if len(content) > self.max_embed_length:
            content = content[:self.max_embed_length-3] + "..."
        
        embed = discord.Embed(
            title=f"📰 {title}",
            description=content,
            color=0x2196F3,  # Blue color
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add metadata
        if article_count > 0:
            embed.add_field(
                name="📊 Articles Processed",
                value=str(article_count),
                inline=True
            )
        
        if categories:
            category_names = [cat.replace('_', ' ').title() for cat in categories]
            embed.add_field(
                name="🏷️ Categories Covered",
                value=", ".join(category_names),
                inline=True
            )
        
        if week_start:
            embed.add_field(
                name="📅 Week Starting",
                value=week_start,
                inline=True
            )
        
        # Add footer
        embed.set_footer(
            text="Personal RSS News Bot • Curated with AI",
            icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"  # Optional bot icon
        )
        
        return embed
    
    def create_article_embed(self, article: Dict) -> discord.Embed:
        """Create an embed for a single article."""
        embed = discord.Embed(
            title=article.get('title', 'Untitled Article'),
            url=article.get('url', ''),
            description=article.get('content_summary', '')[:300] + "..." if len(article.get('content_summary', '')) > 300 else article.get('content_summary', ''),
            color=0x4CAF50,  # Green color
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add metadata
        if article.get('source'):
            embed.add_field(
                name="📖 Source",
                value=article['source'],
                inline=True
            )
        
        if article.get('category'):
            embed.add_field(
                name="🏷️ Category",
                value=article['category'].replace('_', ' ').title(),
                inline=True
            )
        
        if article.get('relevance_score'):
            score = article['relevance_score']
            score_emoji = "🔥" if score >= 0.8 else "⭐" if score >= 0.6 else "📌"
            embed.add_field(
                name=f"{score_emoji} Relevance",
                value=f"{score:.1f}/1.0",
                inline=True
            )
        
        return embed
    
    def create_test_embed(self) -> discord.Embed:
        """Create a test embed for bot verification."""
        embed = discord.Embed(
            title="🤖 RSS Bot Test",
            description="This is a test message to verify the bot is working correctly.",
            color=0xFF9800,  # Orange color
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="✅ Connection Status",
            value="Successfully connected to Discord",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Target Channel",
            value=f"#{self.target_channel.name}" if self.target_channel else "Not configured",
            inline=True
        )
        
        embed.add_field(
            name="🕒 Test Time",
            value=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            inline=True
        )
        
        embed.set_footer(text="If you see this message, the bot is working! 🎉")
        
        return embed
    
    async def publish_weekly_summary(self, summary_content: str, 
                                   article_count: int = 0,
                                   categories: List[str] = None,
                                   week_start: str = None) -> Optional[int]:
        """
        Publish weekly summary to Discord channel.
        Returns message ID if successful, None otherwise.
        """
        if not self.is_ready or not self.target_channel:
            logger.error("Bot not ready or target channel not found")
            return None
        
        try:
            # Create embed
            embed = self.create_summary_embed(
                "Weekly RSS Summary",
                summary_content,
                article_count,
                categories,
                week_start
            )
            
            # Send message
            message = await self.target_channel.send(embed=embed)
            
            logger.info(f"Weekly summary published successfully. Message ID: {message.id}")
            return message.id
            
        except discord.HTTPException as e:
            logger.error(f"HTTP error publishing summary: {e}")
            return None
        except Exception as e:
            logger.error(f"Error publishing weekly summary: {e}")
            return None
    
    async def publish_article(self, article: Dict) -> Optional[int]:
        """
        Publish a single article to Discord channel.
        Returns message ID if successful, None otherwise.
        """
        if not self.is_ready or not self.target_channel:
            logger.error("Bot not ready or target channel not found")
            return None
        
        try:
            embed = self.create_article_embed(article)
            message = await self.target_channel.send(embed=embed)
            
            logger.info(f"Article published: {article.get('title', 'Untitled')} (Message ID: {message.id})")
            return message.id
            
        except discord.HTTPException as e:
            logger.error(f"HTTP error publishing article: {e}")
            return None
        except Exception as e:
            logger.error(f"Error publishing article: {e}")
            return None
    
    async def send_notification(self, title: str, message: str, 
                              color: int = 0xFFEB3B) -> Optional[int]:
        """Send a notification message to the channel."""
        if not self.is_ready or not self.target_channel:
            logger.error("Bot not ready or target channel not found")
            return None
        
        try:
            embed = discord.Embed(
                title=f"🔔 {title}",
                description=message,
                color=color,
                timestamp=datetime.now(timezone.utc)
            )
            
            message_obj = await self.target_channel.send(embed=embed)
            return message_obj.id
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return None
    
    def split_long_content(self, content: str, max_length: int = 4000) -> List[str]:
        """Split long content into multiple parts for Discord limits."""
        if len(content) <= max_length:
            return [content]
        
        parts = []
        current_part = ""
        
        # Try to split at natural break points (paragraphs, sentences)
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_part + paragraph) <= max_length:
                current_part += paragraph + '\n\n'
            else:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = paragraph + '\n\n'
                else:
                    # Paragraph is too long, split by sentences
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_part + sentence) <= max_length:
                            current_part += sentence + '. '
                        else:
                            if current_part:
                                parts.append(current_part.strip())
                            current_part = sentence + '. '
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts
    
    async def publish_long_summary(self, summary_content: str, 
                                 title: str = "Weekly RSS Summary",
                                 article_count: int = 0,
                                 categories: List[str] = None) -> List[int]:
        """
        Publish a long summary, splitting into multiple messages if needed.
        Returns list of message IDs.
        """
        if not self.is_ready or not self.target_channel:
            logger.error("Bot not ready or target channel not found")
            return []
        
        parts = self.split_long_content(summary_content)
        message_ids = []
        
        for i, part in enumerate(parts):
            part_title = f"{title} (Part {i+1}/{len(parts)})" if len(parts) > 1 else title
            
            embed = self.create_summary_embed(
                part_title,
                part,
                article_count if i == 0 else 0,
                categories if i == 0 else None
            )
            
            try:
                message = await self.target_channel.send(embed=embed)
                message_ids.append(message.id)
                
                # Small delay between messages
                if i < len(parts) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error publishing part {i+1}: {e}")
                break
        
        logger.info(f"Published summary in {len(message_ids)} parts")
        return message_ids


# Utility functions
def load_discord_config() -> Dict:
    """Load Discord configuration from environment variables."""
    return {
        'bot_token': os.getenv('DISCORD_TOKEN'),
        'target_channel_id': int(os.getenv('DISCORD_CHANNEL_ID', '0')),
        'command_prefix': os.getenv('DISCORD_COMMAND_PREFIX', '!'),
        'max_embed_length': int(os.getenv('DISCORD_MAX_EMBED_LENGTH', '4096'))
    }


async def test_discord_publisher():
    """Test function for Discord publisher."""
    logging.basicConfig(level=logging.INFO)
    
    config = load_discord_config()
    
    if not config['bot_token'] or not config['target_channel_id']:
        logger.error("Discord configuration missing. Set DISCORD_TOKEN and DISCORD_CHANNEL_ID environment variables.")
        return
    
    publisher = DiscordPublisher(**config)
    
    try:
        # This would start the bot (commented out for testing)
        # await publisher.start_bot()
        
        # Test embed creation
        test_embed = publisher.create_test_embed()
        logger.info(f"Test embed created: {test_embed.title}")
        
        # Test article embed
        test_article = {
            'title': 'Test Article about AI and Productivity',
            'url': 'https://example.com/article',
            'content_summary': 'This is a test article about how AI can improve productivity...',
            'source': 'Test Source',
            'category': 'AI_LLM',
            'relevance_score': 0.85
        }
        
        article_embed = publisher.create_article_embed(test_article)
        logger.info(f"Article embed created: {article_embed.title}")
        
        logger.info("Discord publisher test completed successfully")
        
    except Exception as e:
        logger.error(f"Discord publisher test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_discord_publisher()) 