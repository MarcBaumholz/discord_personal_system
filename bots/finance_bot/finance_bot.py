import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import logging
import asyncio

# Import our modules
from bank_connector import BankDataManager
from budget_manager import BudgetManager
from notification_service import NotificationService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('finance_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
FINANCE_CHANNEL_ID = int(os.getenv("FINANCE_CHANNEL_ID", "0"))

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize our services (will be created later)
bank_manager = None
budget_manager = None
notification_service = None

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    global bank_manager, budget_manager, notification_service
    
    logger.info(f"Logged in as {bot.user}")
    logger.info(f"Using finance channel ID: {FINANCE_CHANNEL_ID}")
    
    # Initialize our services
    try:
        bank_manager = BankDataManager()
        budget_manager = BudgetManager()
        notification_service = NotificationService(bot, FINANCE_CHANNEL_ID)
        
        # Start background tasks
        check_budget.start()
        
        logger.info("Finance Bot is ready!")
        
        # Send welcome message
        channel = bot.get_channel(FINANCE_CHANNEL_ID)
        if channel:
            await channel.send("💰 Finance Bot is online! Type `!finance_help` for commands.")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

@tasks.loop(hours=24)
async def check_budget():
    """Daily check if any budget categories are over limit"""
    try:
        # This will be implemented later with actual logic
        logger.info("Running daily budget check")
        
        # Example notification (to be replaced with actual implementation)
        over_budget = budget_manager.check_budgets()
        if over_budget:
            await notification_service.send_budget_alert(over_budget)
    except Exception as e:
        logger.error(f"Error in budget check: {e}")

@check_budget.before_loop
async def before_check_budget():
    """Wait until the bot is ready before starting the task"""
    await bot.wait_until_ready()

@bot.command(name="balance")
async def get_balance(ctx):
    """Get current balance for all accounts"""
    if ctx.channel.id != FINANCE_CHANNEL_ID:
        await ctx.send("Please use this command in the finance channel.")
        return
    
    # This will be implemented later with actual bank connection
    await ctx.send("Fetching your account balances... This feature will be implemented soon.")

@bot.command(name="set_budget")
async def set_budget(ctx, category: str, amount: float):
    """Set budget for a specific category"""
    if ctx.channel.id != FINANCE_CHANNEL_ID:
        await ctx.send("Please use this command in the finance channel.")
        return
    
    # This will be implemented later with actual budget setting
    await ctx.send(f"Setting budget for {category} to €{amount:.2f}... This feature will be implemented soon.")

@bot.command(name="finance_help")
async def finance_help(ctx):
    """Show help for finance bot commands"""
    if ctx.channel.id != FINANCE_CHANNEL_ID:
        await ctx.send("Please use this command in the finance channel.")
        return
    
    help_text = """
💰 **Finance Bot Help**

**Commands:**
- `!balance` - View your current account balances
- `!set_budget [category] [amount]` - Set budget for a category
- `!report` - Generate monthly spending report
- `!transactions [days=7]` - View recent transactions
- `!finance_help` - Show this help message

The bot will automatically notify you when you exceed your budget limits.
    """
    await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN) 