import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # Need this to detect emoji reactions
intents.reactions = True  # Need this to handle reactions

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Channel ID for haushaltsplan
HAUSHALTSPLAN_CHANNEL_ID = int(os.getenv("HAUSHALTSPLAN_CHANNEL_ID"))

# Default daily todos
DEFAULT_TODOS = [
    "Clean bathroom",
    "Clean bedroom",
    "Take out trash",
    "Do laundry",
    "Vacuum living room",
    "Wash dishes",
    "Make bed"
]

# Store active todo messages
active_todo_messages = {}

# File to save completed todos
COMPLETED_TODOS_FILE = "completed_todos.json"

def load_completed_todos():
    """Load the completed todos from file"""
    if os.path.exists(COMPLETED_TODOS_FILE):
        with open(COMPLETED_TODOS_FILE, 'r') as f:
            return json.load(f)
    return {"date": datetime.now().strftime("%Y-%m-%d"), "completed": []}

def save_completed_todos(completed_todos):
    """Save the completed todos to file"""
    with open(COMPLETED_TODOS_FILE, 'w') as f:
        json.dump(completed_todos, f)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Using haushaltsplan channel ID: {HAUSHALTSPLAN_CHANNEL_ID}")
    print("Daily Todo Bot is ready to receive messages!")
    
    # Send welcome message
    channel = bot.get_channel(HAUSHALTSPLAN_CHANNEL_ID)
    if channel:
        await channel.send("✅ Daily Todo Bot is now online! Type `:white_check_mark:` to see your daily todos.")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Only process messages in the haushaltsplan channel
    if message.channel.id == HAUSHALTSPLAN_CHANNEL_ID:
        # Check if the message contains the white check mark emoji
        if "✅" in message.content or ":white_check_mark:" in message.content:
            await send_daily_todos(message.channel)
    
    # Process commands
    await bot.process_commands(message)

async def send_daily_todos(channel):
    """Send the daily todos list to the channel"""
    # Check if todos need to be reset for a new day
    completed_todos = load_completed_todos()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if completed_todos["date"] != today:
        # Reset for new day
        completed_todos = {"date": today, "completed": []}
        save_completed_todos(completed_todos)
    
    # Create the embed with todos
    embed = discord.Embed(
        title="📋 Daily Todos",
        description="React with the number to mark a todo as complete.",
        color=discord.Color.blue()
    )
    
    # Add todos to the embed
    for i, todo in enumerate(DEFAULT_TODOS, 1):
        status = "✅" if todo in completed_todos["completed"] else "⬜"
        embed.add_field(
            name=f"{i}. {todo}",
            value=f"Status: {status}",
            inline=False
        )
    
    # Add footer with date
    embed.set_footer(text=f"Today: {today}")
    
    # Send the message and store it
    todo_message = await channel.send(embed=embed)
    active_todo_messages[todo_message.id] = True
    
    # Add number reactions for selection
    for i in range(1, min(10, len(DEFAULT_TODOS) + 1)):
        await todo_message.add_reaction(f"{i}\u20e3")  # Adding keycap digit reactions

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reactions to mark todos as complete"""
    # Ignore bot's own reactions
    if user == bot.user:
        return
    
    # Check if this is a todo message
    if reaction.message.id in active_todo_messages:
        # Check if it's a number reaction
        if str(reaction.emoji)[0].isdigit() and str(reaction.emoji).endswith('\u20e3'):
            # Get the todo index (1-based)
            todo_index = int(str(reaction.emoji)[0]) - 1
            
            if 0 <= todo_index < len(DEFAULT_TODOS):
                # Toggle the todo completion
                completed_todos = load_completed_todos()
                todo_item = DEFAULT_TODOS[todo_index]
                
                if todo_item in completed_todos["completed"]:
                    completed_todos["completed"].remove(todo_item)
                else:
                    completed_todos["completed"].append(todo_item)
                
                save_completed_todos(completed_todos)
                
                # Update the message
                await update_todo_message(reaction.message)

async def update_todo_message(message):
    """Update the todo message with current status"""
    completed_todos = load_completed_todos()
    
    # Create updated embed
    embed = discord.Embed(
        title="📋 Daily Todos",
        description="React with the number to mark a todo as complete.",
        color=discord.Color.blue()
    )
    
    # Add todos to the embed
    for i, todo in enumerate(DEFAULT_TODOS, 1):
        status = "✅" if todo in completed_todos["completed"] else "⬜"
        embed.add_field(
            name=f"{i}. {todo}",
            value=f"Status: {status}",
            inline=False
        )
    
    # Add footer with date
    embed.set_footer(text=f"Today: {completed_todos['date']}")
    
    # Update the message
    await message.edit(embed=embed)

@bot.command(name="help_todo")
async def help_todo(ctx):
    """Show help information for the daily todo bot"""
    if ctx.channel.id == HAUSHALTSPLAN_CHANNEL_ID:
        help_text = """
✅ **Daily Todo Bot Help**

To see your daily todos, simply type:
`:white_check_mark:` or `✅`

To mark a todo as complete:
1. React with the number of the todo
2. React again to toggle it back to incomplete

Your todo status is saved for the day and will reset tomorrow.
        """
        await ctx.send(help_text)

# Run the bot
bot.run(TOKEN) 