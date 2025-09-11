#!/usr/bin/env python3
"""
Test Discord connection for WHOOP bot
"""

import os
import asyncio
import discord
from discord.ext import commands

async def test_discord_connection():
    """Test if we can connect to Discord"""
    print("🤖 Testing Discord Connection...")
    
    # Get Discord token from environment
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        print("❌ DISCORD_TOKEN not found in environment variables")
        return False
    
    # Create bot instance
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Bot connected as {bot.user}")
        print(f"✅ Bot is in {len(bot.guilds)} guilds")
        
        # Test channel access
        channel_id = 1415625361106014348
        channel = bot.get_channel(channel_id)
        
        if channel:
            print(f"✅ Found target channel: {channel.name} in {channel.guild.name}")
            
            # Send test message
            try:
                embed = discord.Embed(
                    title="🏃‍♂️ WHOOP Bot Test",
                    description="This is a test message from the WHOOP bot!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="Status",
                    value="✅ Bot is working correctly!",
                    inline=False
                )
                embed.set_footer(text="WHOOP Discord Bot • Test Message")
                
                await channel.send(embed=embed)
                print("✅ Test message sent successfully!")
                
            except Exception as e:
                print(f"❌ Error sending test message: {e}")
                return False
        else:
            print(f"❌ Could not find channel with ID {channel_id}")
            return False
        
        # Close bot
        await bot.close()
        return True
    
    try:
        await bot.start(discord_token)
        return True
    except Exception as e:
        print(f"❌ Error connecting to Discord: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Discord Connection Test...\n")
    
    success = await test_discord_connection()
    
    if success:
        print("\n🎉 Discord connection test passed!")
        print("✅ The WHOOP bot is ready to run in production!")
    else:
        print("\n❌ Discord connection test failed!")
        print("Please check your DISCORD_TOKEN and channel ID.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
