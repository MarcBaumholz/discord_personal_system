#!/usr/bin/env python3
"""
Enhanced Weekly Planning Bot Setup Script
This script sets up the enhanced bot with all new features.
"""

import os
import sys
import subprocess
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('setup_enhanced')

def run_command(command, description):
    """Run a system command with error handling"""
    try:
        logger.info(f"🔄 {description}...")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("❌ Python 3.8+ is required. Current version: {}.{}.{}".format(
            version.major, version.minor, version.micro))
        return False
    
    logger.info(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_virtual_environment():
    """Set up virtual environment for enhanced bot"""
    if os.path.exists("weekly_env"):
        logger.info("📦 Virtual environment already exists")
        return True
    
    return run_command("python -m venv weekly_env", "Creating virtual environment")

def install_dependencies():
    """Install enhanced dependencies"""
    # Activate virtual environment and install
    if os.name == 'nt':  # Windows
        pip_cmd = "weekly_env\\Scripts\\pip install -r requirements_enhanced.txt"
    else:  # Unix/Linux/MacOS
        pip_cmd = "source weekly_env/bin/activate && pip install -r requirements_enhanced.txt"
    
    return run_command(pip_cmd, "Installing enhanced dependencies")

def create_data_directory():
    """Create data directory for database and files"""
    try:
        os.makedirs("data", exist_ok=True)
        logger.info("✅ Data directory created")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating data directory: {e}")
        return False

def setup_database():
    """Initialize SQLite database"""
    try:
        # Import and initialize database
        sys.path.append('.')
        from core.database import get_database
        
        db = get_database()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False

def check_environment_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists('.env'):
        logger.warning("⚠️ .env file not found. Creating template...")
        
        template_env = """# Enhanced Weekly Planning Bot Environment Variables

# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
WEEKLY_PLANNING_CHANNEL_ID=your_channel_id_here

# Notion Configuration (optional - bot works without it)
NOTION_TOKEN=your_notion_integration_token_here
WEEKLY_PLANNING_DATABASE_ID=your_notion_database_id_here

# OpenRouter AI Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Google Calendar Configuration (optional)
GOOGLE_CALENDAR_CREDENTIALS_FILE=data/google_credentials.json
"""
        
        try:
            with open('.env', 'w') as f:
                f.write(template_env)
            logger.info("✅ .env template created - please fill in your API keys")
            return False  # Needs configuration
        except Exception as e:
            logger.error(f"❌ Error creating .env template: {e}")
            return False
    
    logger.info("✅ .env file exists")
    return True

def run_basic_tests():
    """Run basic functionality tests"""
    try:
        logger.info("🧪 Running basic functionality tests...")
        
        # Test imports
        sys.path.append('.')
        
        # Test database
        from core.database import get_database
        db = get_database()
        
        # Test models
        from core.models import User, Task, WeeklyPlan
        
        # Test services (these might fail without API keys, which is OK)
        try:
            from notion_manager import NotionManager
            from openrouter_service import OpenRouterService
            logger.info("✅ Core services can be imported")
        except Exception as e:
            logger.warning(f"⚠️ Some services need configuration: {e}")
        
        # Test enhanced features
        try:
            from features.task_manager import TaskManagerCog
            from features.analytics import AnalyticsCog
            from integrations.google_calendar import GoogleCalendarIntegration
            logger.info("✅ Enhanced features can be imported")
        except Exception as e:
            logger.error(f"❌ Enhanced features import failed: {e}")
            return False
        
        logger.info("✅ All basic tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic tests failed: {e}")
        return False

def display_next_steps():
    """Display next steps for user"""
    print("\n" + "="*60)
    print("🎉 ENHANCED WEEKLY PLANNING BOT SETUP COMPLETE!")
    print("="*60)
    print("\n📋 NEXT STEPS:")
    print("\n1. 🔑 Configure API Keys:")
    print("   - Edit .env file with your Discord bot token")
    print("   - Add OpenRouter API key for AI features")
    print("   - (Optional) Add Notion integration tokens")
    print("   - (Optional) Set up Google Calendar credentials")
    
    print("\n2. 🚀 Start the Enhanced Bot:")
    if os.name == 'nt':
        print("   weekly_env\\Scripts\\activate")
    else:
        print("   source weekly_env/bin/activate")
    print("   python weekly_planning_bot_enhanced.py")
    
    print("\n3. 🎯 Try New Features:")
    print("   !plan          - Enhanced weekly planning")
    print("   !tasks         - Interactive task management")
    print("   !analytics     - Advanced productivity insights")
    print("   !calendar      - Google Calendar integration")
    print("   !help enhanced - Complete feature guide")
    
    print("\n4. 📊 Enhanced Features Available:")
    print("   ✅ SQLite database for data persistence")
    print("   ✅ Interactive task management with buttons")
    print("   ✅ Advanced analytics with visual charts")
    print("   ✅ Google Calendar synchronization")
    print("   ✅ Productivity trend tracking")
    print("   ✅ Historical data analysis")
    
    print("\n💡 TIPS:")
    print("   - All your data is now automatically saved")
    print("   - Use !analytics chart to see visual trends")
    print("   - React with emojis for quick interactions")
    print("   - Set up Google Calendar for full synchronization")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("   - Check .env file has correct API keys")
    print("   - Ensure Discord bot has proper permissions")
    print("   - Install missing dependencies with pip")
    print("   - Check logs for detailed error information")
    
    print("\n" + "="*60)

def main():
    """Main setup function"""
    print("🚀 Enhanced Weekly Planning Bot Setup")
    print("="*40)
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Setup steps
    setup_steps = [
        ("Virtual Environment", setup_virtual_environment),
        ("Enhanced Dependencies", install_dependencies),
        ("Data Directory", create_data_directory),
        ("Database", setup_database),
        ("Environment File", check_environment_file),
        ("Basic Tests", run_basic_tests),
    ]
    
    success_count = 0
    for step_name, step_function in setup_steps:
        logger.info(f"\n📝 Step: {step_name}")
        if step_function():
            success_count += 1
        else:
            logger.error(f"❌ Step failed: {step_name}")
            if step_name in ["Database", "Basic Tests"]:
                logger.error("⚠️ Critical step failed. Please fix errors before proceeding.")
                return False
    
    # Display results
    print(f"\n📊 Setup Results: {success_count}/{len(setup_steps)} steps completed")
    
    if success_count == len(setup_steps):
        logger.info("🎉 Enhanced setup completed successfully!")
        display_next_steps()
        return True
    else:
        logger.warning("⚠️ Setup completed with warnings. Check the steps above.")
        display_next_steps()
        return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during setup: {e}")
        sys.exit(1) 