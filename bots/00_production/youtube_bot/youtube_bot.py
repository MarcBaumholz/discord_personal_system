#!/usr/bin/env python3
"""
YouTube Bot - Discord YouTube Subscription Bot
Automatically fetches videos from YouTube subscriptions from the previous day and posts them to Discord.
"""

import discord
from discord.ext import commands, tasks
import os
import logging
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from typing import List, Dict, Any
import pickle
from youtube_transcript_api import YouTubeTranscriptApi
import pytz

# Load environment variables from main discord directory
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_CHANNEL_ID = 1397292430239469669  # YouTube bot channel ID
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # Correct YouTube Data API key
GOOGLE_CLIENT_ID = os.getenv("GoogleClientID")
GOOGLE_CLIENT_SECRET = os.getenv("GoogleClientkey")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('youtube_bot')

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class YouTubeManager:
    """Manages YouTube API interactions"""
    
    def __init__(self):
        self.api_key = YOUTUBE_API_KEY
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.youtube = None
        self.youtube_oauth = None
        self.scopes = ['https://www.googleapis.com/auth/youtube.readonly']
        self._initialize_client()
        self._initialize_oauth_client()
    
    def _initialize_client(self):
        """Initialize YouTube API client with API key"""
        try:
            if not self.api_key:
                logger.error("❌ YouTube API key not found!")
                return
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("✅ YouTube API client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize YouTube API client: {e}")
    
    def _initialize_oauth_client(self):
        """Initialize OAuth client for personal subscriptions"""
        try:
            creds = None
            # Token file stores the user's access and refresh tokens
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Create OAuth config
                    oauth_config = {
                        "installed": {
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost"]
                        }
                    }
                    
                    flow = InstalledAppFlow.from_client_config(oauth_config, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            self.youtube_oauth = build('youtube', 'v3', credentials=creds)
            logger.info("✅ YouTube OAuth client initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OAuth client: {e}")
            self.youtube_oauth = None

    async def get_my_subscriptions(self):
        """Get user's personal YouTube subscriptions using OAuth"""
        if not self.youtube_oauth:
            logger.error("❌ OAuth client not initialized. Cannot access personal subscriptions.")
            return []
        
        try:
            subscriptions = []
            next_page_token = None
            
            while True:
                request = self.youtube_oauth.subscriptions().list(
                    part='snippet',
                    mine=True,
                    maxResults=50,
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                for item in response.get('items', []):
                    channel_info = {
                        'channel_id': item['snippet']['resourceId']['channelId'],
                        'channel_title': item['snippet']['title'],
                        'thumbnail': item['snippet']['thumbnails']['default']['url']
                    }
                    subscriptions.append(channel_info)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"✅ Found {len(subscriptions)} subscriptions")
            return subscriptions
            
        except Exception as e:
            logger.error(f"❌ Error fetching subscriptions: {e}")
            return []

    async def get_latest_videos_from_subscriptions(self, max_videos_per_channel=3):
        """Get latest videos from all subscribed channels with a maximum limit of 3 videos per channel"""
        subscriptions = await self.get_my_subscriptions()
        
        if not subscriptions:
            logger.warning("⚠️ No subscriptions found or OAuth not configured")
            return []
        
        all_videos = []
        
        for subscription in subscriptions:
            try:
                # Get latest videos from this channel
                start_time, end_time = self.get_yesterday_timeframe()
                
                request = self.youtube.search().list(
                    part='snippet',
                    channelId=subscription['channel_id'],
                    publishedAfter=start_time,
                    publishedBefore=end_time,
                    type='video',
                    order='date',
                    maxResults=max_videos_per_channel,
                    videoDuration='medium'  # Excludes shorts (< 4 minutes)
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    video_data = {
                        'videoId': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'][:500] + '...' if len(item['snippet']['description']) > 500 else item['snippet']['description'],
                        'channelTitle': subscription['channel_title'],
                        'publishedAt': item['snippet']['publishedAt'],
                        'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                        'url': f"https://youtu.be/{item['id']['videoId']}"
                    }
                    all_videos.append(video_data)
                    
            except Exception as e:
                logger.error(f"❌ Error getting videos for {subscription['channel_title']}: {e}")
                continue
        
        # Sort by published date (newest first)
        all_videos.sort(key=lambda x: x['publishedAt'], reverse=True)
        
        return all_videos
    
    def get_yesterday_timeframe(self) -> tuple:
        """Get yesterday's start and end timestamps in UTC"""
        # Get current time in UTC
        now_utc = datetime.utcnow()
        
        # Calculate yesterday
        yesterday = now_utc - timedelta(days=1)
        
        # Get start and end of yesterday
        yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Format as ISO strings
        start_time = yesterday_start.isoformat() + 'Z'
        end_time = yesterday_end.isoformat() + 'Z'
        
        return start_time, end_time
    
    def get_subscribed_channels(self) -> List[str]:
        """Get list of subscribed channel IDs (requires OAuth - fallback to popular channels)"""
        # Since we don't have OAuth setup, we'll use some popular tech/educational channels
        # In a full implementation, you'd use OAuth to get actual subscriptions
        popular_channels = [
            'UC_x5XG1OV2P6uZZ5FSM9Ttw',  # Google Developers
            'UCsBjURrPoezykLs9EqgamOA',  # Fireship
            'UC8butISFwT-Wl7EV0hUK0BQ',  # freeCodeCamp
            'UCWv7vMbMWH4-V0ZXdmDpPBA',  # Programming with Mosh
            'UCJbPGzawDH1njbqV-D5HqKw',  # Ben Eater
        ]
        return popular_channels
    
    def search_videos_from_yesterday(self) -> List[Dict[str, Any]]:
        """Search for videos from subscribed channels published yesterday"""
        try:
            start_time, end_time = self.get_yesterday_timeframe()
            subscribed_channels = self.get_subscribed_channels()
            
            all_videos = []
            
            for channel_id in subscribed_channels:
                try:
                    # Search for videos from this channel published yesterday
                    request = self.youtube.search().list(
                        part='snippet',
                        channelId=channel_id,
                        publishedAfter=start_time,
                        publishedBefore=end_time,
                        type='video',
                        order='date',
                        maxResults=10,
                        videoDuration='medium'  # Excludes shorts (< 4 minutes)
                    )
                    response = request.execute()
                    
                    for item in response.get('items', []):
                        video_data = {
                            'videoId': item['id']['videoId'],
                            'title': item['snippet']['title'],
                            'description': item['snippet']['description'][:500] + '...' if len(item['snippet']['description']) > 500 else item['snippet']['description'],
                            'channelTitle': item['snippet']['channelTitle'],
                            'publishedAt': item['snippet']['publishedAt'],
                            'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                            'url': f"https://youtu.be/{item['id']['videoId']}"
                        }
                        all_videos.append(video_data)
                        
                except HttpError as e:
                    logger.error(f"❌ Error fetching videos from channel {channel_id}: {e}")
                    continue
            
            logger.info(f"✅ Found {len(all_videos)} videos from yesterday")
            return all_videos
            
        except Exception as e:
            logger.error(f"❌ Error searching videos: {e}")
            return []
    
    def get_trending_videos(self) -> List[Dict[str, Any]]:
        """Fallback: Get trending videos if no subscription videos found"""
        try:
            request = self.youtube.videos().list(
                part='snippet,statistics',
                chart='mostPopular',
                regionCode='DE',  # Germany
                videoCategoryId='28',  # Science & Technology
                maxResults=5
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video_data = {
                    'videoId': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:500] + '...' if len(item['snippet']['description']) > 500 else item['snippet']['description'],
                    'channelTitle': item['snippet']['channelTitle'],
                    'publishedAt': item['snippet']['publishedAt'],
                    'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'url': f"https://youtu.be/{item['id']}",
                    'viewCount': item['statistics'].get('viewCount', '0')
                }
                videos.append(video_data)
            
            logger.info(f"✅ Found {len(videos)} trending videos")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Error fetching trending videos: {e}")
            return []

    def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Get detailed information about a video including transcript"""
        try:
            # Get video details
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                return {}
            
            video = response['items'][0]
            
            # Get transcript
            transcript_text = ""
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'de'])
                transcript_text = " ".join([entry['text'] for entry in transcript])
                transcript_text = transcript_text[:2000] + "..." if len(transcript_text) > 2000 else transcript_text
            except Exception as e:
                logger.warning(f"⚠️ Could not get transcript for {video_id}: {e}")
                transcript_text = "Transcript not available"
            
            # Extract tags (they might be in snippet)
            tags = video['snippet'].get('tags', [])
            
            video_details = {
                'videoId': video_id,
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'channelTitle': video['snippet']['channelTitle'],
                'publishedAt': video['snippet']['publishedAt'],
                'thumbnail': video['snippet']['thumbnails'].get('maxres', video['snippet']['thumbnails'].get('high', {})).get('url', ''),
                'url': f"https://youtu.be/{video_id}",
                'duration': video['contentDetails']['duration'],
                'viewCount': video['statistics'].get('viewCount', '0'),
                'likeCount': video['statistics'].get('likeCount', '0'),
                'commentCount': video['statistics'].get('commentCount', '0'),
                'tags': tags,
                'transcript': transcript_text
            }
            
            return video_details
            
        except Exception as e:
            logger.error(f"❌ Error getting video details for {video_id}: {e}")
            return {}

    async def get_latest_videos_from_subscriptions_detailed(self, max_videos_per_channel=1):
        """Get latest videos with full details including transcript"""
        subscriptions = await self.get_my_subscriptions()
        
        if not subscriptions:
            logger.warning("⚠️ No subscriptions found or OAuth not configured")
            return []
        
        all_videos = []
        
        for subscription in subscriptions:
            try:
                # Get latest videos from this channel
                start_time, end_time = self.get_yesterday_timeframe()
                
                request = self.youtube.search().list(
                    part='snippet',
                    channelId=subscription['channel_id'],
                    publishedAfter=start_time,
                    publishedBefore=end_time,
                    type='video',
                    order='date',
                    maxResults=max_videos_per_channel,
                    videoDuration='medium'  # Excludes shorts
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    video_id = item['id']['videoId']
                    # Get detailed information for each video
                    video_details = self.get_video_details(video_id)
                    if video_details:
                        video_details['channelTitle'] = subscription['channel_title']
                        all_videos.append(video_details)
                    
            except Exception as e:
                logger.error(f"❌ Error getting detailed videos for {subscription['channel_title']}: {e}")
                continue
        
        # Sort by published date (newest first)
        all_videos.sort(key=lambda x: x['publishedAt'], reverse=True)
        
        return all_videos

    async def get_latest_10_videos_from_subscriptions(self):
        """Get latest 10 videos from all subscribed channels (not time-restricted)"""
        subscriptions = await self.get_my_subscriptions()
        
        if not subscriptions:
            logger.warning("⚠️ No subscriptions found or OAuth not configured")
            return []
        
        all_videos = []
        
        for subscription in subscriptions:
            try:
                # Get latest videos from this channel (no time restriction)
                request = self.youtube.search().list(
                    part='snippet',
                    channelId=subscription['channel_id'],
                    type='video',
                    order='date',
                    maxResults=2,  # Get 2 per channel to ensure we get 10 total
                    videoDuration='medium'  # Excludes shorts
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    video_data = {
                        'videoId': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'][:500] + '...' if len(item['snippet']['description']) > 500 else item['snippet']['description'],
                        'channelTitle': subscription['channel_title'],
                        'publishedAt': item['snippet']['publishedAt'],
                        'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                        'url': f"https://youtu.be/{item['id']['videoId']}"
                    }
                    all_videos.append(video_data)
                    
            except Exception as e:
                logger.error(f"❌ Error getting latest videos for {subscription['channel_title']}: {e}")
                continue
        
        # Sort by published date (newest first) and limit to 10
        all_videos.sort(key=lambda x: x['publishedAt'], reverse=True)
        
        return all_videos[:10]

class VideoCategorizer:
    """Categorizes videos based on their content"""
    
    CATEGORIES = {
        'Productivity': [
            'productivity', 'efficiency', 'time management', 'organization', 'workflow', 
            'task management', 'planning', 'calendar', 'schedule', 'notion', 'obsidian',
            'productivity tips', 'work from home', 'remote work', 'focus', 'concentration',
            'getting things done', 'gtd', 'bullet journal', 'habit', 'routine'
        ],
        'AI/LLMs/Machine Learning': [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'ai', 'ml', 'llm', 'large language model', 'chatgpt', 'gpt', 'openai', 'claude',
            'transformer', 'bert', 'nlp', 'natural language processing', 'computer vision',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'data science', 'algorithm',
            'model training', 'fine tuning', 'prompt engineering', 'generative ai'
        ],
        'Biohacking': [
            'biohacking', 'health optimization', 'longevity', 'anti-aging', 'nutrition',
            'supplements', 'fitness', 'workout', 'exercise', 'meditation', 'mindfulness',
            'sleep optimization', 'circadian rhythm', 'intermittent fasting', 'cold therapy',
            'heat therapy', 'sauna', 'red light therapy', 'nootropics', 'wellness',
            'health tracking', 'quantified self', 'recovery', 'stress management'
        ]
    }
    
    @staticmethod
    def categorize_video(video: Dict[str, Any]) -> str:
        """Categorize a video based on its title, description, and tags"""
        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        tags = [tag.lower() for tag in video.get('tags', [])]
        
        # Combine all text for analysis
        content = f"{title} {description} {' '.join(tags)}"
        
        # Check each category
        for category, keywords in VideoCategorizer.CATEGORIES.items():
            for keyword in keywords:
                if keyword in content:
                    return category
        
        return None  # No category found
    
    @staticmethod
    def categorize_videos(videos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize a list of videos"""
        categorized = {category: [] for category in VideoCategorizer.CATEGORIES.keys()}
        
        for video in videos:
            category = VideoCategorizer.categorize_video(video)
            if category:
                categorized[category].append(video)
        
        return categorized

class DiscordManager:
    """Manages Discord message formatting and sending"""
    
    @staticmethod
    def create_video_embeds(videos: List[Dict[str, Any]]) -> List[discord.Embed]:
        """Create Discord embeds for videos"""
        embeds = []
        
        for video in videos[:10]:  # Limit to 10 embeds per message
            embed = discord.Embed(
                title=video['title'][:256],  # Discord title limit
                url=video['url'],
                description=video['description'][:4096] if video['description'] else 'No description available',
                color=0xff0000  # YouTube red
            )
            
            embed.set_author(
                name=video['channelTitle'],
                icon_url="https://www.youtube.com/favicon.ico"
            )
            
            if video.get('thumbnail'):
                embed.set_image(url=video['thumbnail'])
            
            # Parse and format publish date
            try:
                pub_date = datetime.fromisoformat(video['publishedAt'].replace('Z', '+00:00'))
                embed.timestamp = pub_date
            except:
                pass
            
            embed.set_footer(text="YouTube", icon_url="https://www.youtube.com/favicon.ico")
            
            embeds.append(embed)
        
        return embeds
    
    @staticmethod
    def create_detailed_video_embeds(videos: List[Dict[str, Any]]) -> List[discord.Embed]:
        """Create detailed Discord embeds for videos with full information"""
        embeds = []
        
        for video in videos[:5]:  # Limit to 5 detailed embeds per message due to size
            embed = discord.Embed(
                title=video['title'][:256],  # Discord title limit
                url=video['url'],
                description=video['description'][:1000] + '...' if len(video['description']) > 1000 else video['description'],
                color=0xff0000  # YouTube red
            )
            
            embed.set_author(
                name=video['channelTitle'],
                icon_url="https://www.youtube.com/favicon.ico"
            )
            
            if video.get('thumbnail'):
                embed.set_image(url=video['thumbnail'])
            
            # Parse and format publish date
            try:
                pub_date = datetime.fromisoformat(video['publishedAt'].replace('Z', '+00:00'))
                embed.timestamp = pub_date
            except:
                pass
            
            # Add detailed information
            details = []
            if video.get('viewCount'):
                details.append(f"👁️ {int(video['viewCount']):,} views")
            if video.get('likeCount'):
                details.append(f"👍 {int(video['likeCount']):,} likes")
            if video.get('commentCount'):
                details.append(f"💬 {int(video['commentCount']):,} comments")
            if video.get('duration'):
                details.append(f"⏱️ {video['duration']}")
            
            if details:
                embed.add_field(name="📊 Statistics", value=" | ".join(details), inline=False)
            
            # Add tags if available
            if video.get('tags') and len(video['tags']) > 0:
                tags_text = ", ".join(video['tags'][:10])  # Show first 10 tags
                if len(tags_text) > 200:
                    tags_text = tags_text[:200] + "..."
                embed.add_field(name="🏷️ Tags", value=tags_text, inline=False)
            
            # Add transcript preview
            if video.get('transcript') and video['transcript'] != "Transcript not available":
                transcript_preview = video['transcript'][:500] + "..." if len(video['transcript']) > 500 else video['transcript']
                embed.add_field(name="📝 Transcript Preview", value=transcript_preview, inline=False)
            
            embed.set_footer(text="YouTube", icon_url="https://www.youtube.com/favicon.ico")
            
            embeds.append(embed)
        
        return embeds
    
    @staticmethod
    def create_category_embed(category: str, videos: List[Dict[str, Any]]) -> discord.Embed:
        """Create an embed for a specific category of videos"""
        # Category emojis
        category_emojis = {
            'Productivity': '⚡',
            'AI/LLMs/Machine Learning': '🤖',
            'Biohacking': '🧬'
        }
        
        emoji = category_emojis.get(category, '📺')
        
        embed = discord.Embed(
            title=f"{emoji} {category} Videos ({len(videos)} found)",
            color=0xff0000,
            description=f"Yesterday's videos in the {category} category"
        )
        
        # Add each video as a field
        for i, video in enumerate(videos[:10], 1):  # Limit to 10 videos per category
            video_title = video['title'][:100] + '...' if len(video['title']) > 100 else video['title']
            channel_title = video['channelTitle'][:30] + '...' if len(video['channelTitle']) > 30 else video['channelTitle']
            
            embed.add_field(
                name=f"{i}. {video_title}",
                value=f"[🔗 Watch Video]({video['url']}) | 📺 {channel_title}",
                inline=False
            )
        
        if len(videos) > 10:
            embed.add_field(
                name="📋 Note",
                value=f"Showing first 10 of {len(videos)} videos in this category",
                inline=False
            )
        
        embed.set_footer(text="YouTube", icon_url="https://www.youtube.com/favicon.ico")
        
        return embed
    
    @staticmethod
    async def send_categorized_videos_to_channel(channel, videos: List[Dict[str, Any]]):
        """Send categorized videos to Discord channel"""
        if not videos:
            await channel.send("📺 No videos found to categorize today.")
            return
        
        # Categorize videos
        categorized = VideoCategorizer.categorize_videos(videos)
        
        # Count total categorized videos
        total_categorized = sum(len(vids) for vids in categorized.values())
        
        if total_categorized == 0:
            await channel.send("📺 No videos found in the relevant categories (Productivity, AI/ML, Biohacking).")
            return
        
        # Send intro message
        intro_message = (
            f"📺 **Yesterday's Categorized YouTube Videos** 🗂️\n\n"
            f"Found {total_categorized} videos in relevant categories out of {len(videos)} total videos\n"
            f"Categories: Productivity, AI/LLMs/Machine Learning, Biohacking\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await channel.send(intro_message)
        
        # Send categories in order of priority
        category_order = ['Productivity', 'AI/LLMs/Machine Learning', 'Biohacking']
        
        for category in category_order:
            category_videos = categorized[category]
            if category_videos:
                try:
                    embed = DiscordManager.create_category_embed(category, category_videos)
                    await channel.send(embed=embed)
                    await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.error(f"❌ Error sending {category} category: {e}")
        
        # Send summary
        summary_lines = []
        for category in category_order:
            count = len(categorized[category])
            if count > 0:
                emoji = {'Productivity': '⚡', 'AI/LLMs/Machine Learning': '🤖', 'Biohacking': '🧬'}[category]
                summary_lines.append(f"{emoji} {category}: {count} videos")
        
        if summary_lines:
            summary_message = "📊 **Summary:**\n" + "\n".join(summary_lines)
            await channel.send(summary_message)
    
    @staticmethod
    async def send_videos_to_channel(channel, videos: List[Dict[str, Any]], video_type: str = "yesterday's"):
        """Send video embeds to Discord channel"""
        if not videos:
            await channel.send(f"📺 No {video_type} videos found to share today.")
            return
        
        embeds = DiscordManager.create_video_embeds(videos)
        
        # Send intro message
        intro_message = f"📺 **{video_type.title()} YouTube Videos** ({len(videos)} found)\n\n"
        await channel.send(intro_message)
        
        # Send embeds in batches (Discord limit: 10 embeds per message)
        for i in range(0, len(embeds), 10):
            batch = embeds[i:i+10]
            try:
                await channel.send(embeds=batch)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"❌ Error sending video batch: {e}")

@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f"🤖 {bot.user} is now online!")
    logger.info(f"📺 Monitoring YouTube channel ID: {YOUTUBE_CHANNEL_ID}")
    
    # Send startup notification
    try:
        channel = bot.get_channel(YOUTUBE_CHANNEL_ID)
        if channel:
            startup_message = (
                "📺 **YouTube Bot is now online!** 🤖\n\n"
                "I'm ready to share YouTube videos! Here's what I can do:\n"
                "• 📅 Automatically fetch and categorize videos from subscriptions\n"
                "• 🗂️ Organize videos by: Productivity, AI/ML, Biohacking\n"
                "• 🔥 Get trending tech videos\n"
                "• 🔍 Search for specific videos\n"
                "• 📋 Show your subscription list\n"
                "• 📝 Get detailed video info with transcripts\n\n"
                "**Commands:**\n"
                "• `!status` - Check bot status\n"
                "• `!subscribers` - Show your subscription list\n"
                "• `!latest` - Get latest 10 videos from subscriptions\n"
                "• `!yesterday` - Get yesterday's videos categorized by topic\n"
                "• `!yesterday_detailed` - Get yesterday's videos with full details\n"
                "• `!trending` - Get trending tech videos\n"
                "• `!search <query>` - Search for videos\n"
                "• `!subscriptions` - Test OAuth functionality\n"
                "• `!oauth_videos` - Get videos from personal subscriptions\n\n"
                "🗂️ **Categories:** Productivity ⚡, AI/LLMs/ML 🤖, Biohacking 🧬\n"
                "Daily categorized video updates will be posted automatically at 9 AM!\n"
                "🚫 **Shorts are automatically filtered out** - only real videos!"
            )
            await channel.send(startup_message)
            logger.info("✅ Startup notification sent to YouTube channel")
        else:
            logger.warning(f"❌ Could not find YouTube channel with ID: {YOUTUBE_CHANNEL_ID}")
    except Exception as e:
        logger.error(f"❌ Error sending startup notification: {e}")
    
    # Start daily task
    if not daily_video_check.is_running():
        daily_video_check.start()
        logger.info("📅 Daily video check task started")

@tasks.loop(hours=24)
async def daily_video_check():
    """Daily task to post yesterday's videos"""
    try:
        # Run at 9 AM
        now = datetime.now()
        if now.hour != 9:
            return
        
        logger.info("🔄 Running daily video check...")
        
        channel = bot.get_channel(YOUTUBE_CHANNEL_ID)
        if not channel:
            logger.error("❌ Could not find YouTube channel")
            return
        
        youtube_manager = YouTubeManager()
        
        # Try OAuth subscriptions first
        oauth_videos = await youtube_manager.get_latest_videos_from_subscriptions()
        
        if oauth_videos:
            await DiscordManager.send_categorized_videos_to_channel(channel, oauth_videos)
            logger.info(f"✅ Daily video check completed - {len(oauth_videos)} videos from OAuth subscriptions categorized and posted")
        else:
            # Fallback to predefined channels
            videos = youtube_manager.search_videos_from_yesterday()
            
            if not videos:
                # Final fallback to trending videos
                videos = youtube_manager.get_trending_videos()
                await DiscordManager.send_videos_to_channel(channel, videos, "trending")
            else:
                await DiscordManager.send_categorized_videos_to_channel(channel, videos)
            
            logger.info(f"✅ Daily video check completed - {len(videos)} fallback videos categorized and posted")
        
    except Exception as e:
        logger.error(f"❌ Error in daily video check: {e}")

@bot.command()
async def status(ctx):
    """Check bot status"""
    if ctx.channel.id == YOUTUBE_CHANNEL_ID:
        await ctx.send("📺 YouTube Bot is running and ready to share videos!")

@bot.command()
async def subscriptions(ctx):
    """Test OAuth and show subscription count"""
    if ctx.channel.id == YOUTUBE_CHANNEL_ID:
        youtube_manager = YouTubeManager()
        
        if not youtube_manager.youtube_oauth:
            await ctx.send("❌ OAuth not configured. Using fallback channels only.")
            return
        
        try:
            subs = await youtube_manager.get_my_subscriptions()
            if subs:
                await ctx.send(f"✅ Found {len(subs)} subscriptions via OAuth!")
                # Show first 5 subscription names
                sub_names = [sub['channel_title'] for sub in subs[:5]]
                await ctx.send(f"📺 Sample channels: {', '.join(sub_names)}")
            else:
                await ctx.send("❌ No subscriptions found or OAuth failed.")
        except Exception as e:
            await ctx.send(f"❌ Error testing OAuth: {str(e)}")

@bot.command()
async def oauth_videos(ctx):
    """Get videos from OAuth subscriptions"""
    if ctx.channel.id == YOUTUBE_CHANNEL_ID:
        youtube_manager = YouTubeManager()
        
        try:
            videos = await youtube_manager.get_latest_videos_from_subscriptions()
            
            if videos:
                await DiscordManager.send_videos_to_channel(ctx.channel, videos, "your subscriptions (yesterday's)")
            else:
                await ctx.send("❌ No videos found from subscriptions. OAuth might not be configured.")
        except Exception as e:
            await ctx.send(f"❌ Error fetching subscription videos: {str(e)}")

@bot.command()
async def subscribers(ctx):
    """Print current subscriber list"""
    if ctx.channel.id != YOUTUBE_CHANNEL_ID:
        return
    
    try:
        await ctx.send("🔄 Fetching your YouTube subscriptions...")
        
        youtube_manager = YouTubeManager()
        
        if not youtube_manager.youtube_oauth:
            await ctx.send("❌ OAuth not configured. Cannot access personal subscriptions.")
            return
        
        subscriptions = await youtube_manager.get_my_subscriptions()
        
        if not subscriptions:
            await ctx.send("❌ No subscriptions found or OAuth failed.")
            return
        
        # Create embed for subscriber list
        embed = discord.Embed(
            title=f"📺 Your YouTube Subscriptions ({len(subscriptions)} channels)",
            color=0xff0000
        )
        
        # Group subscriptions into chunks for fields (Discord field value limit)
        chunk_size = 20
        for i in range(0, len(subscriptions), chunk_size):
            chunk = subscriptions[i:i+chunk_size]
            field_value = "\n".join([f"• {sub['channel_title']}" for sub in chunk])
            
            embed.add_field(
                name=f"Channels {i+1}-{min(i+chunk_size, len(subscriptions))}",
                value=field_value,
                inline=True
            )
        
        embed.set_footer(text="YouTube", icon_url="https://www.youtube.com/favicon.ico")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"❌ Error in subscribers command: {e}")
        await ctx.send(f"❌ Error fetching subscriptions: {str(e)}")

@bot.command()
async def latest(ctx):
    """Get latest 10 videos from subscriptions"""
    if ctx.channel.id != YOUTUBE_CHANNEL_ID:
        return
    
    try:
        await ctx.send("🔄 Fetching latest 10 videos from your subscriptions...")
        
        youtube_manager = YouTubeManager()
        videos = await youtube_manager.get_latest_10_videos_from_subscriptions()
        
        if not videos:
            await ctx.send("❌ No recent videos found from subscriptions. OAuth might not be configured.")
            return
        
        await DiscordManager.send_videos_to_channel(ctx.channel, videos, f"latest {len(videos)}")
        
    except Exception as e:
        logger.error(f"❌ Error in latest command: {e}")
        await ctx.send(f"❌ Error fetching latest videos: {str(e)}")

@bot.command()
async def yesterday(ctx):
    """Get yesterday's videos categorized by topic (Productivity, AI/ML, Biohacking)"""
    if ctx.channel.id != YOUTUBE_CHANNEL_ID:
        return
    
    try:
        await ctx.send("🔄 Fetching and categorizing yesterday's videos...")
        
        youtube_manager = YouTubeManager()
        
        # Try OAuth subscriptions first for detailed info
        videos = await youtube_manager.get_latest_videos_from_subscriptions_detailed()
        
        if not videos:
            # Fallback to regular search
            videos = youtube_manager.search_videos_from_yesterday()
            if not videos:
                await ctx.send("❌ No videos found from yesterday.")
                return
        
        # Send categorized videos
        await DiscordManager.send_categorized_videos_to_channel(ctx.channel, videos)
        
    except Exception as e:
        logger.error(f"❌ Error in yesterday command: {e}")
        await ctx.send(f"❌ Error fetching yesterday's videos: {str(e)}")

@bot.command()
async def yesterday_detailed(ctx):
    """Get yesterday's videos with detailed information including transcript"""
    if ctx.channel.id != YOUTUBE_CHANNEL_ID:
        return
    
    try:
        await ctx.send("🔄 Fetching yesterday's videos with detailed information...")
        
        youtube_manager = YouTubeManager()
        
        # Try OAuth subscriptions first for detailed info
        videos = await youtube_manager.get_latest_videos_from_subscriptions_detailed()
        
        if not videos:
            # Fallback to regular search
            videos = youtube_manager.search_videos_from_yesterday()
            if videos:
                await DiscordManager.send_videos_to_channel(ctx.channel, videos, "yesterday's (basic info)")
            else:
                await ctx.send("❌ No videos found from yesterday.")
            return
        
        # Send detailed videos
        if not videos:
            await ctx.send("📺 No detailed videos found from yesterday.")
            return
        
        embeds = DiscordManager.create_detailed_video_embeds(videos)
        
        # Send intro message
        intro_message = f"📺 **Yesterday's YouTube Videos (Detailed)** ({len(videos)} found)\n\n"
        await ctx.send(intro_message)
        
        # Send embeds in batches (Discord limit: 10 embeds per message, but detailed embeds are larger)
        for i in range(0, len(embeds), 3):
            batch = embeds[i:i+3]
            try:
                await ctx.send(embeds=batch)
                await asyncio.sleep(2)  # Longer delay for detailed embeds
            except Exception as e:
                logger.error(f"❌ Error sending detailed video batch: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error in yesterday_detailed command: {e}")
        await ctx.send(f"❌ Error fetching yesterday's detailed videos: {str(e)}")

@bot.command()
async def trending(ctx):
    """Get trending tech videos"""
    if ctx.channel.id != YOUTUBE_CHANNEL_ID:
        return
    
    try:
        await ctx.send("🔄 Fetching trending videos...")
        
        youtube_manager = YouTubeManager()
        videos = youtube_manager.get_trending_videos()
        
        await DiscordManager.send_videos_to_channel(ctx.channel, videos, "trending")
        
    except Exception as e:
        logger.error(f"❌ Error in trending command: {e}")
        await ctx.send(f"❌ Error fetching trending videos: {str(e)}")

@bot.command()
async def search(ctx, *, query: str):
    """Search for videos"""
    if ctx.channel.id != YOUTUBE_CHANNEL_ID:
        return
    
    try:
        await ctx.send(f"🔍 Searching for: {query}")
        
        youtube_manager = YouTubeManager()
        
        request = youtube_manager.youtube.search().list(
            part='snippet',
            q=query,
            type='video',
            order='relevance',
            maxResults=5,
            videoDuration='medium'  # Excludes shorts (< 4 minutes)
        )
        response = request.execute()
        
        videos = []
        for item in response.get('items', []):
            video_data = {
                'videoId': item['id']['videoId'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'][:500] + '...' if len(item['snippet']['description']) > 500 else item['snippet']['description'],
                'channelTitle': item['snippet']['channelTitle'],
                'publishedAt': item['snippet']['publishedAt'],
                'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                'url': f"https://youtu.be/{item['id']['videoId']}"
            }
            videos.append(video_data)
        
        await DiscordManager.send_videos_to_channel(ctx.channel, videos, f"search results for '{query}'")
        
    except Exception as e:
        logger.error(f"❌ Error in search command: {e}")
        await ctx.send(f"❌ Error searching videos: {str(e)}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in environment!")
        exit(1)
    
    if not YOUTUBE_API_KEY:
        logger.error("❌ YOUTUBE_API_KEY (GoogleClientkey) not found in environment!")
        exit(1)
    
    logger.info("🚀 Starting YouTube Bot...")
    bot.run(DISCORD_TOKEN)