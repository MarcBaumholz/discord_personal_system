import discord
import logging
from datetime import datetime

logger = logging.getLogger('finance_bot.notification_service')

class NotificationService:
    """Handles notifications and alerts for the finance bot"""
    
    def __init__(self, bot, channel_id):
        """
        Initialize notification service
        
        Args:
            bot: Discord bot instance
            channel_id: Channel ID for notifications
        """
        self.bot = bot
        self.channel_id = channel_id
        logger.info(f"Notification service initialized with channel ID: {channel_id}")
    
    async def send_message(self, message):
        """
        Send a simple text message
        
        Args:
            message: Message text
            
        Returns:
            bool: Success status
        """
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                await channel.send(message)
                return True
            else:
                logger.error(f"Channel not found: {self.channel_id}")
                return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def send_budget_alert(self, over_budget_categories):
        """
        Send alert about categories over budget
        
        Args:
            over_budget_categories: List of dicts with category info
            
        Returns:
            bool: Success status
        """
        if not over_budget_categories:
            return True
        
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Channel not found: {self.channel_id}")
                return False
            
            # Create embed
            embed = discord.Embed(
                title="⚠️ Budget Alert",
                description="The following categories are over budget:",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            # Add fields for each category
            for category in over_budget_categories:
                embed.add_field(
                    name=f"{category['category']} ({category['percentage']:.1f}%)",
                    value=f"Budget: €{category['budget']:.2f}\nSpent: €{category['spent']:.2f}\nOver by: €{category['spent'] - category['budget']:.2f}",
                    inline=True
                )
            
            # Add footer
            embed.set_footer(text="Consider adjusting your spending in these categories")
            
            # Send the embed
            await channel.send(embed=embed)
            return True
            
        except Exception as e:
            logger.error(f"Error sending budget alert: {e}")
            return False
    
    async def send_transaction_alert(self, transaction):
        """
        Send alert about a new transaction
        
        Args:
            transaction: Transaction data
            
        Returns:
            bool: Success status
        """
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Channel not found: {self.channel_id}")
                return False
            
            # Determine color based on amount
            color = discord.Color.green() if transaction['amount'] > 0 else discord.Color.red()
            
            # Create embed
            embed = discord.Embed(
                title="💰 New Transaction",
                description=transaction['description'],
                color=color,
                timestamp=transaction['date']
            )
            
            # Add transaction details
            embed.add_field(name="Amount", value=f"€{abs(transaction['amount']):.2f}", inline=True)
            embed.add_field(name="Account", value=transaction['account'], inline=True)
            embed.add_field(name="Category", value=transaction['category'], inline=True)
            
            # Send the embed
            await channel.send(embed=embed)
            return True
            
        except Exception as e:
            logger.error(f"Error sending transaction alert: {e}")
            return False
    
    async def send_weekly_report(self, spending, budgets):
        """
        Send weekly spending report
        
        Args:
            spending: Dict of spending by category
            budgets: Dict of budgets by category
            
        Returns:
            bool: Success status
        """
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Channel not found: {self.channel_id}")
                return False
            
            # Create embed
            embed = discord.Embed(
                title="📊 Weekly Spending Report",
                description="Your spending for the past week:",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Add total spending
            total_spent = sum(spending.values())
            embed.add_field(name="Total Spent", value=f"€{total_spent:.2f}", inline=False)
            
            # Add spending by category
            for category, amount in spending.items():
                budget = budgets.get(category, {}).get('amount', 0)
                percentage = (amount / budget * 100) if budget > 0 else 0
                status = "✅" if percentage <= 100 else "⚠️"
                
                embed.add_field(
                    name=f"{category} {status}",
                    value=f"€{amount:.2f} / €{budget:.2f} ({percentage:.1f}%)",
                    inline=True
                )
            
            # Send the embed
            await channel.send(embed=embed)
            return True
            
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
            return False 