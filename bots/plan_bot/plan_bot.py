import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # We need message content intent to process messages

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Channel ID for the todoliste
TODOLISTE_CHANNEL_ID = int(os.getenv("TODOLISTE_CHANNEL_ID"))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Using todoliste channel ID: {TODOLISTE_CHANNEL_ID}")
    print("Plan Bot is ready to receive messages!")
    
    channel = bot.get_channel(TODOLISTE_CHANNEL_ID)
    if channel:
        await channel.send("📝 Plan Bot is now online! Type `plan` followed by your items to generate a plan.")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Only process messages in the todoliste channel
    if message.channel.id == TODOLISTE_CHANNEL_ID:
        # Check if the message starts with "plan"
        if message.content.lower().startswith("plan"):
            # Extract the items after "plan"
            items_text = message.content[4:].strip()
            
            # Split the items by comma or new line
            items = re.split(r',|\n', items_text)
            items = [item.strip() for item in items if item.strip()]
            
            if items:
                # Generate the plan with the prefilled template
                plan_text = generate_plan(items)
                await message.reply(plan_text)
            else:
                await message.reply("Please provide items for your plan! Example: `plan item1, item2, item3`")
    
    # Process commands (if any)
    await bot.process_commands(message)

def generate_plan(items):
    """Generate a formatted plan with the given items"""
    plan = "📋 **Your Plan**\n\n"
    
    plan += "**Today's Tasks:**\n"
    for i, item in enumerate(items, 1):
        plan += f"{i}. {item}\n"
    
    plan += "\n**Timeline:**\n"
    plan += "- Morning: Start with the first tasks\n"
    plan += "- Afternoon: Continue with middle tasks\n"
    plan += "- Evening: Complete remaining tasks\n"
    
    plan += "\n**Notes:**\n"
    plan += "- Remember to take breaks between tasks\n"
    plan += "- Mark each item as complete when done\n"
    
    return plan

@bot.command(name="help_plan")
async def help_plan(ctx):
    """Show help information for the plan bot"""
    if ctx.channel.id == TODOLISTE_CHANNEL_ID:
        help_text = """
📋 **Plan Bot Help**

To create a plan, simply type:
`plan item1, item2, item3`

You can also list items on separate lines:
```
plan
item1
item2
item3
```

The bot will organize your items into a formatted plan.
        """
        await ctx.send(help_text)

# Run the bot
bot.run(TOKEN) 