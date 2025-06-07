import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up minimal intents (no privileged intents)
intents = discord.Intents.default()
intents.message_content = True  # Enable message content to read emoji reactions

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Channel IDs - from environment variables
HAUSHALTSPLAN_CHANNEL_ID = int(os.getenv("HAUSHALTSPLAN_CHANNEL_ID"))
EINKAUFSLISTE_CHANNEL_ID = int(os.getenv("EINKAUFSLISTE_CHANNEL_ID"))

# Storage for todos
todos = []

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Using haushaltsplan channel ID: {HAUSHALTSPLAN_CHANNEL_ID}")
    print(f"Using einkaufsliste channel ID: {EINKAUFSLISTE_CHANNEL_ID}")
    
    haushaltsplan = bot.get_channel(HAUSHALTSPLAN_CHANNEL_ID)
    if haushaltsplan:
        await haushaltsplan.send("🤖 Bot is now online! Use `!todo [task]` to create reminders or use 🔥 emoji to view your todos.")
    
    einkaufsliste = bot.get_channel(EINKAUFSLISTE_CHANNEL_ID)
    if einkaufsliste:
        await einkaufsliste.send("🤖 Bot is now online! Use `!add [item1, item2]` to add items to your shopping list.")
    
    print("Bot is ready to receive commands!")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check for fire emoji in haushaltsplan channel
    if message.channel.id == HAUSHALTSPLAN_CHANNEL_ID:
        if "🔥" in message.content or ":fire:" in message.content:
            await list_todos_emoji(message)
    
    # Allow command processing to continue
    await bot.process_commands(message)

async def list_todos_emoji(message):
    """Show todos when triggered by fire emoji"""
    if not todos:
        await message.channel.send("No TODOs found! Add some with `!todo [task]`")
        return
    
    # Create a nice embed
    embed = discord.Embed(
        title="🔥 Your TODO List",
        color=discord.Color.orange()
    )
    
    for i, todo in enumerate(todos, 1):
        embed.add_field(name=f"TODO #{i}", value=todo, inline=False)
    
    await message.channel.send(embed=embed)

@bot.command(name="todo")
async def add_todo(ctx, *, text):
    """Add a TODO item when used in the haushaltsplan channel"""
    if ctx.channel.id == HAUSHALTSPLAN_CHANNEL_ID:
        todos.append(text)
        await ctx.reply(f"📝 **Reminder created**: {text}")
    else:
        await ctx.send("This command only works in the haushaltsplan channel.")

@bot.command(name="add")
async def add_item(ctx, *, text):
    """Add an item when used in the einkaufsliste channel"""
    if ctx.channel.id == EINKAUFSLISTE_CHANNEL_ID:
        items = text.split(",")
        if len(items) > 1:
            await ctx.reply(f"✅ Added {len(items)} items to shopping list")
        else:
            await ctx.reply(f"✅ Added \"{text}\" to shopping list")
    else:
        await ctx.send("This command only works in the einkaufsliste channel.")

@bot.command(name="todos")
async def list_todos(ctx):
    """List all saved todos"""
    if not todos:
        await ctx.send("No TODOs found!")
        return
    
    # Create a nice embed
    embed = discord.Embed(
        title="📋 Your TODO List",
        color=discord.Color.blue()
    )
    
    for i, todo in enumerate(todos, 1):
        embed.add_field(name=f"TODO #{i}", value=todo, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="clear_todos")
async def clear_todos(ctx):
    """Clear all todos"""
    global todos
    todos = []
    await ctx.send("✅ All TODOs have been cleared!")

@bot.command(name="help_bot")
async def help_bot(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="🤖 Bot Help",
        description="Here are the commands you can use:",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="!todo [task]", value="Add a TODO item (in haushaltsplan channel)", inline=False)
    embed.add_field(name="!add [item1, item2, ...]", value="Add items to shopping list (in einkaufsliste channel)", inline=False)
    embed.add_field(name="!todos", value="List all saved TODOs", inline=False)
    embed.add_field(name="!clear_todos", value="Clear all saved TODOs", inline=False)
    embed.add_field(name="!help_bot", value="Show this help message", inline=False)
    
    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN) 