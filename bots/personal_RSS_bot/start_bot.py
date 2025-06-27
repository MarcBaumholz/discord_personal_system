#!/usr/bin/env python3
"""
Personal RSS News Bot Starter Script
Handles environment setup and bot launch.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_virtual_environment():
    """Check if we're in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def check_environment_file():
    """Check if .env file exists and has required values."""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📝 Please copy config.example to .env and fill in your credentials:")
        print("   cp config.example .env")
        print("   # Then edit .env with your Discord token and OpenRouter API key")
        return False
    
    # Read .env file
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        # Check for placeholder values
        if 'your_discord_bot_token_here' in content or 'your_openrouter_api_key_here' in content:
            print("⚠️  .env file contains placeholder values!")
            print("📝 Please edit .env and add your actual credentials:")
            print("   - DISCORD_TOKEN=your_actual_discord_token")
            print("   - OPENROUTER_API_KEY=your_actual_openrouter_key")
            return False
            
        print("✅ Environment file looks good!")
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def install_dependencies():
    """Install required dependencies."""
    try:
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def run_tests():
    """Run basic tests before starting the bot."""
    try:
        print("🧪 Running basic tests...")
        result = subprocess.run([sys.executable, 'run_tests.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Basic tests passed!")
            return True
        else:
            print("❌ Tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"⚠️  Could not run tests: {e}")
        print("🚀 Proceeding anyway...")
        return True

def start_bot():
    """Start the RSS bot."""
    try:
        print("🚀 Starting RSS News Bot...")
        print("📱 The bot will:")
        print("   - Connect to Discord")
        print("   - Schedule daily news at 8:30 AM")
        print("   - Schedule weekly summaries on Sundays at 9:00 AM")
        print("   - Respond to !news command for on-demand summaries")
        print("")
        print("🛑 Press Ctrl+C to stop the bot")
        print("="*50)
        
        # Start the bot
        subprocess.run([sys.executable, 'src/main.py'])
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

def main():
    """Main startup routine."""
    print("🤖 Personal RSS News Bot Starter")
    print("="*40)
    
    # Check virtual environment
    if not check_virtual_environment():
        print("⚠️  Not in virtual environment. Consider using one for better isolation.")
        print("   python -m venv rss_env")
        print("   source rss_env/bin/activate  # or rss_env\\Scripts\\activate on Windows")
        print("")
    
    # Check environment configuration
    if not check_environment_file():
        print("🔧 Please set up your environment configuration first.")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("🔧 Please install dependencies manually:")
        print("   pip install -r requirements.txt")
        return
    
    # Run tests
    if not run_tests():
        print("⚠️  Tests failed, but you can still try running the bot.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Start the bot
    start_bot()

if __name__ == "__main__":
    main() 