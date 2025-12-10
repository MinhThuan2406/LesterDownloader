#!/usr/bin/env python3
"""
Startup script for LesterDownloader Discord Bot
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import BotConfig
from core.logging import setup_logging

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'discord.py',
        'yt-dlp',
        'requests',
        'python-dotenv',
        'aiosqlite',
        'aiofiles'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please run: python -m pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """Check if environment variables are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['DISCORD_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False
    
    return True

def main():
    """Main startup function"""
    print("Starting LesterDownloader Discord Bot...")
    
    # Setup logging
    logger = setup_logging(
        log_file="bot.log",
        log_level="INFO",
        enable_console=True,
        enable_file=True
    )
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("Dependencies OK")
    
    # Check environment
    print("Checking environment...")
    if not check_environment():
        sys.exit(1)
    print("Environment OK")
    
    # Initialize configuration
    try:
        config = BotConfig()
        config.validate()
        print("Configuration OK")
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create downloads directory
    downloads_dir = Path(config.DOWNLOAD_PATH)
    downloads_dir.mkdir(exist_ok=True)
    print("Downloads directory ready")
    
    # Import and run the bot
    try:
        print("Starting bot...")
        from main import main as run_bot
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\nBot shutdown by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        print(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 