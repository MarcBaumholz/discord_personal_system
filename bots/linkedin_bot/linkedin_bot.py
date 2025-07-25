#!/usr/bin/env python3
"""
LinkedIn Network Analysis Bot
Analyzes LinkedIn connections, categorizes by topics, ranks by followers,
and stores top contacts per category in Notion database.

Due to LinkedIn API restrictions, this bot works with:
1. LinkedIn data export (CSV files)
2. Manual profile enrichment through OpenAI
3. Notion database storage and management
"""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json
import asyncio
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

# API Clients
from notion_client import Client as NotionClient
from openai import OpenAI

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LINKEDIN_CHANNEL_ID = int(os.getenv("LINKEDIN_CHANNEL_ID", "0"))
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
LINKEDIN_CONTACTS_DB_ID = os.getenv("LINKEDIN_CONTACTS_DB_ID")
OPENAI_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize clients
notion = NotionClient(auth=NOTION_TOKEN)
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Topic categories for classification
TOPIC_CATEGORIES = [
    "Artificial Intelligence & Machine Learning",
    "Software Development & Engineering",
    "Data Science & Analytics", 
    "Product Management",
    "Digital Marketing & Growth",
    "Finance & Investment",
    "Entrepreneurship & Startups",
    "Consulting & Strategy",
    "Sales & Business Development",
    "Human Resources & Recruiting",
    "Design & UX/UI",
    "Content Creation & Media",
    "Healthcare & Life Sciences",
    "Education & Training",
    "Other"
]

class LinkedInContact:
    """Represents a LinkedIn contact with enriched data"""
    
    def __init__(self, name: str, position: str = "", company: str = "", 
                 profile_url: str = "", email: str = ""):
        self.name = name
        self.position = position
        self.company = company
        self.profile_url = profile_url
        self.email = email
        self.follower_count = 0
        self.topic_category = "Other"
        self.importance_score = 0
        self.last_interaction = None
        self.notes = ""
        
    def to_dict(self):
        return {
            "name": self.name,
            "position": self.position,
            "company": self.company,
            "profile_url": self.profile_url,
            "email": self.email,
            "follower_count": self.follower_count,
            "topic_category": self.topic_category,
            "importance_score": self.importance_score,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "notes": self.notes
        }

class NotionLinkedInHandler:
    """Handles Notion database operations for LinkedIn contacts"""
    
    @staticmethod
    async def create_contacts_database():
        """Create the LinkedIn Contacts database structure in Notion"""
        database_properties = {
            "Name": {"title": {}},
            "Position": {"rich_text": {}},
            "Company": {"rich_text": {}},
            "Profile URL": {"url": {}},
            "Email": {"email": {}},
            "Follower Count": {"number": {"format": "number"}},
            "Topic Category": {
                "select": {
                    "options": [{"name": category, "color": "default"} for category in TOPIC_CATEGORIES]
                }
            },
            "Importance Score": {"number": {"format": "number"}},
            "Last Interaction": {"date": {}},
            "Notes": {"rich_text": {}},
            "Top 10 Flag": {"checkbox": {}},
            "Created Date": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}}
        }
        
        try:
            response = notion.databases.create(
                parent={"type": "page_id", "page_id": "your_parent_page_id"},
                title=[{"type": "text", "text": {"content": "LinkedIn Network Analysis"}}],
                properties=database_properties
            )
            print(f"✅ Created LinkedIn Contacts database: {response['id']}")
            return response['id']
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return None
    
    @staticmethod
    async def add_contact_to_notion(contact: LinkedInContact):
        """Add a LinkedIn contact to the Notion database"""
        try:
            properties = {
                "Name": {"title": [{"text": {"content": contact.name}}]},
                "Position": {"rich_text": [{"text": {"content": contact.position}}]},
                "Company": {"rich_text": [{"text": {"content": contact.company}}]},
                "Profile URL": {"url": contact.profile_url if contact.profile_url else None},
                "Email": {"email": contact.email if contact.email else None},
                "Follower Count": {"number": contact.follower_count},
                "Topic Category": {"select": {"name": contact.topic_category}},
                "Importance Score": {"number": contact.importance_score},
                "Notes": {"rich_text": [{"text": {"content": contact.notes}}]},
                "Top 10 Flag": {"checkbox": False}
            }
            
            if contact.last_interaction:
                properties["Last Interaction"] = {"date": {"start": contact.last_interaction.isoformat()}}
            
            response = notion.pages.create(
                parent={"database_id": LINKEDIN_CONTACTS_DB_ID},
                properties=properties
            )
            
            return response['id']
        except Exception as e:
            print(f"❌ Error adding contact to Notion: {e}")
            return None
    
    @staticmethod
    async def update_top_10_flags(top_contacts_by_category: Dict[str, List[LinkedInContact]]):
        """Update the Top 10 flags in Notion for the highest-ranked contacts"""
        try:
            # First, clear all Top 10 flags
            response = notion.databases.query(database_id=LINKEDIN_CONTACTS_DB_ID)
            
            for page in response.get("results", []):
                notion.pages.update(
                    page_id=page["id"],
                    properties={"Top 10 Flag": {"checkbox": False}}
                )
            
            # Set Top 10 flags for the highest-ranked contacts in each category
            for category, contacts in top_contacts_by_category.items():
                for contact in contacts[:10]:  # Top 10 per category
                    # Find the page for this contact and update the flag
                    query_response = notion.databases.query(
                        database_id=LINKEDIN_CONTACTS_DB_ID,
                        filter={
                            "and": [
                                {"property": "Name", "title": {"equals": contact.name}},
                                {"property": "Topic Category", "select": {"equals": category}}
                            ]
                        }
                    )
                    
                    if query_response.get("results"):
                        page_id = query_response["results"][0]["id"]
                        notion.pages.update(
                            page_id=page_id,
                            properties={"Top 10 Flag": {"checkbox": True}}
                        )
            
            print("✅ Updated Top 10 flags in Notion")
        except Exception as e:
            print(f"❌ Error updating Top 10 flags: {e}")

class LinkedInAnalyzer:
    """Analyzes LinkedIn contacts and categorizes them"""
    
    @staticmethod
    async def analyze_contact_with_ai(contact: LinkedInContact) -> LinkedInContact:
        """Use AI to analyze and categorize a LinkedIn contact"""
        try:
            prompt = f"""
            Analyze this LinkedIn contact and provide:
            1. Estimated follower count (realistic estimate based on position/company)
            2. Topic category from: {', '.join(TOPIC_CATEGORIES)}
            3. Importance score (1-10 based on influence, network, position)
            4. Brief notes about why this person is valuable to connect with
            
            Contact Info:
            Name: {contact.name}
            Position: {contact.position}
            Company: {contact.company}
            
            Respond in JSON format:
            {{
                "estimated_followers": number,
                "topic_category": "category_name",
                "importance_score": number,
                "notes": "brief valuable connection notes"
            }}
            """
            
            response = await openai_client.chat.completions.acreate(
                model="anthropic/claude-3.5-haiku",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            analysis = json.loads(content)
            
            # Update contact with AI analysis
            contact.follower_count = analysis.get("estimated_followers", 0)
            contact.topic_category = analysis.get("topic_category", "Other")
            contact.importance_score = analysis.get("importance_score", 5)
            contact.notes = analysis.get("notes", "")
            
            return contact
            
        except Exception as e:
            print(f"❌ Error analyzing contact with AI: {e}")
            # Return contact with default values
            contact.topic_category = "Other"
            contact.importance_score = 5
            return contact
    
    @staticmethod
    def parse_linkedin_csv(csv_file_path: str) -> List[LinkedInContact]:
        """Parse LinkedIn connections CSV export"""
        contacts = []
        try:
            df = pd.read_csv(csv_file_path)
            
            # LinkedIn CSV typically has columns: First Name, Last Name, Email Address, Company, Position
            for _, row in df.iterrows():
                name = f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip()
                position = row.get('Position', '')
                company = row.get('Company', '')
                email = row.get('Email Address', '')
                
                if name and name != " ":  # Only add contacts with valid names
                    contact = LinkedInContact(
                        name=name,
                        position=position,
                        company=company,
                        email=email
                    )
                    contacts.append(contact)
            
            print(f"✅ Parsed {len(contacts)} contacts from CSV")
            return contacts
            
        except Exception as e:
            print(f"❌ Error parsing CSV: {e}")
            return []
    
    @staticmethod
    def rank_contacts_by_category(contacts: List[LinkedInContact]) -> Dict[str, List[LinkedInContact]]:
        """Group contacts by category and rank by importance score and follower count"""
        categorized = {}
        
        for contact in contacts:
            category = contact.topic_category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(contact)
        
        # Sort each category by importance score and follower count
        for category in categorized:
            categorized[category].sort(
                key=lambda x: (x.importance_score, x.follower_count),
                reverse=True
            )
        
        return categorized

# Discord Bot Commands
@bot.event
async def on_ready():
    print(f'✅ LinkedIn Bot logged in as {bot.user}!')
    if LINKEDIN_CHANNEL_ID:
        channel = bot.get_channel(LINKEDIN_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🔗 LinkedIn Network Analyzer Bot Started",
                description="Ready to analyze your LinkedIn network!",
                color=0x0077B5
            )
            await channel.send(embed=embed)

@bot.command(name='upload_linkedin')
async def upload_linkedin_csv(ctx):
    """Command to upload and process LinkedIn connections CSV"""
    embed = discord.Embed(
        title="📤 Upload LinkedIn Connections",
        description="""
        **How to export your LinkedIn connections:**
        
        1. Go to LinkedIn Settings & Privacy
        2. Click "Data privacy" → "Get a copy of your data"
        3. Select "Connections" and download
        4. Upload the CSV file here with this message
        
        **Supported formats:**
        - LinkedIn connections export (CSV)
        - Manual CSV with columns: Name, Position, Company, Email
        """,
        color=0x0077B5
    )
    await ctx.send(embed=embed)

@bot.command(name='analyze_network')
async def analyze_network(ctx, csv_file_path: str = None):
    """Analyze uploaded LinkedIn network and store in Notion"""
    if not csv_file_path:
        await ctx.send("❌ Please provide the path to your LinkedIn CSV file.")
        return
    
    if not os.path.exists(csv_file_path):
        await ctx.send("❌ CSV file not found. Please check the file path.")
        return
    
    # Show progress message
    progress_embed = discord.Embed(
        title="🔄 Analyzing LinkedIn Network",
        description="Processing your connections...",
        color=0xFFAA00
    )
    progress_msg = await ctx.send(embed=progress_embed)
    
    try:
        # Parse CSV
        contacts = LinkedInAnalyzer.parse_linkedin_csv(csv_file_path)
        
        if not contacts:
            await ctx.send("❌ No valid contacts found in CSV file.")
            return
        
        # Update progress
        await progress_msg.edit(embed=discord.Embed(
            title="🤖 AI Analysis in Progress",
            description=f"Analyzing {len(contacts)} contacts with AI...",
            color=0xFFAA00
        ))
        
        # Analyze each contact with AI (batch process to avoid rate limits)
        analyzed_contacts = []
        for i, contact in enumerate(contacts):
            if i % 10 == 0:  # Update progress every 10 contacts
                await progress_msg.edit(embed=discord.Embed(
                    title="🤖 AI Analysis in Progress",
                    description=f"Analyzed {i}/{len(contacts)} contacts...",
                    color=0xFFAA00
                ))
            
            analyzed_contact = await LinkedInAnalyzer.analyze_contact_with_ai(contact)
            analyzed_contacts.append(analyzed_contact)
            
            # Rate limiting
            await asyncio.sleep(1)
        
        # Categorize and rank
        categorized_contacts = LinkedInAnalyzer.rank_contacts_by_category(analyzed_contacts)
        
        # Update progress
        await progress_msg.edit(embed=discord.Embed(
            title="💾 Storing in Notion",
            description="Saving analyzed contacts to Notion database...",
            color=0xFFAA00
        ))
        
        # Store in Notion
        stored_count = 0
        for contact in analyzed_contacts:
            contact_id = await NotionLinkedInHandler.add_contact_to_notion(contact)
            if contact_id:
                stored_count += 1
        
        # Update Top 10 flags
        await NotionLinkedInHandler.update_top_10_flags(categorized_contacts)
        
        # Show results
        results_embed = discord.Embed(
            title="✅ LinkedIn Network Analysis Complete",
            description=f"Successfully analyzed and stored {stored_count} contacts!",
            color=0x00AA00
        )
        
        # Add category breakdown
        for category, contacts_list in categorized_contacts.items():
            if contacts_list:
                top_3 = contacts_list[:3]
                names = [f"{c.name} ({c.importance_score}/10)" for c in top_3]
                results_embed.add_field(
                    name=f"{category} (Top 3)",
                    value="\n".join(names) if names else "No contacts",
                    inline=False
                )
        
        await progress_msg.edit(embed=results_embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Analysis Error",
            description=f"Error processing network: {str(e)}",
            color=0xFF0000
        )
        await progress_msg.edit(embed=error_embed)

@bot.command(name='top_contacts')
async def show_top_contacts(ctx, category: str = None):
    """Show top contacts by category"""
    try:
        # Query Notion for top contacts
        filter_query = {"property": "Top 10 Flag", "checkbox": {"equals": True}}
        
        if category:
            filter_query = {
                "and": [
                    {"property": "Top 10 Flag", "checkbox": {"equals": True}},
                    {"property": "Topic Category", "select": {"equals": category}}
                ]
            }
        
        response = notion.databases.query(
            database_id=LINKEDIN_CONTACTS_DB_ID,
            filter=filter_query,
            sorts=[
                {"property": "Importance Score", "direction": "descending"},
                {"property": "Follower Count", "direction": "descending"}
            ]
        )
        
        if not response.get("results"):
            await ctx.send("❌ No top contacts found. Run `!analyze_network` first.")
            return
        
        # Group by category
        categorized = {}
        for page in response["results"]:
            props = page["properties"]
            name = props["Name"]["title"][0]["text"]["content"] if props["Name"]["title"] else "Unknown"
            cat = props["Topic Category"]["select"]["name"] if props["Topic Category"]["select"] else "Other"
            score = props["Importance Score"]["number"] or 0
            followers = props["Follower Count"]["number"] or 0
            
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append((name, score, followers))
        
        # Create embed
        embed = discord.Embed(
            title="🏆 Top LinkedIn Contacts",
            description="Your most valuable connections by category",
            color=0x0077B5
        )
        
        for cat, contacts in categorized.items():
            contact_list = [f"{name} (Score: {score}, ~{followers} followers)" 
                          for name, score, followers in contacts[:5]]
            embed.add_field(
                name=cat,
                value="\n".join(contact_list) if contact_list else "No contacts",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error retrieving top contacts: {str(e)}")

@bot.command(name='linkedin_help')
async def linkedin_help(ctx):
    """Show help for LinkedIn bot commands"""
    embed = discord.Embed(
        title="🔗 LinkedIn Network Analyzer Bot Help",
        description="Commands for analyzing your LinkedIn network",
        color=0x0077B5
    )
    
    commands_info = {
        "!upload_linkedin": "Get instructions for uploading LinkedIn CSV",
        "!analyze_network <csv_path>": "Analyze LinkedIn network from CSV file",
        "!top_contacts [category]": "Show top contacts (optionally filtered by category)", 
        "!linkedin_help": "Show this help message"
    }
    
    for cmd, desc in commands_info.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.add_field(
        name="📊 Available Categories",
        value=", ".join(TOPIC_CATEGORIES[:7]) + "\n" + ", ".join(TOPIC_CATEGORIES[7:]),
        inline=False
    )
    
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    embed = discord.Embed(
        title="❌ Command Error",
        description=f"Error: {str(error)}",
        color=0xFF0000
    )
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables")
        exit(1)
    
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN not found in environment variables")
        exit(1)
    
    print("🚀 Starting LinkedIn Network Analyzer Bot...")
    bot.run(DISCORD_TOKEN)
