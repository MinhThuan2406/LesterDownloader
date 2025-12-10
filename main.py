"""
Main entry point for LesterDownloader Discord Bot
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.bot import LesterBot
from core.config import BotConfig
from core.logging import setup_logging
from health_check import HealthCheckServer
from shutdown_handler import ShutdownHandler

async def main():
    """Main function to run the bot"""
    # Setup logging
    logger = setup_logging(
        log_file="bot.log",
        log_level="INFO",
        enable_console=True,
        enable_file=True
    )
    
    try:
        logger.info("Starting LesterDownloader Discord Bot...")
        
        # Initialize configuration
        config = BotConfig()
        
        # Create bot instance
        bot = LesterBot(config)
        
        # Setup shutdown handler
        shutdown_handler = ShutdownHandler(bot)
        
        # Register cleanup hooks
        async def cleanup_database():
            """Cleanup database connections"""
            from services.database import DatabaseManager
            logger.info("Closing database connections...")
            # Database cleanup if needed
        
        async def cleanup_health_server():
            """Cleanup health check server"""
            if health_server:
                logger.info("Stopping health check server...")
                await health_server.stop()
        
        shutdown_handler.register_hook(cleanup_database)
        shutdown_handler.register_hook(cleanup_health_server)
        
        # Setup signal handlers for graceful shutdown
        shutdown_handler.setup_signals()
        logger.info("Shutdown handlers configured")
        
        # Start health check server
        health_server = HealthCheckServer(bot, port=8080)
        asyncio.create_task(health_server.start())
        logger.info("Health check server starting on port 8080")
        
        # Start the bot
        logger.info("Connecting to Discord...")
        await bot.start_bot()
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user (Ctrl+C)")
        if 'bot' in locals():
            await bot.close()
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Bot shutdown complete")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
 