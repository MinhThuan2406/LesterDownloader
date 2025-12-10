"""
Graceful shutdown handler for the bot
"""

import asyncio
import signal
import logging
import sys
from typing import Callable, List

logger = logging.getLogger(__name__)

class ShutdownHandler:
    """Handles graceful shutdown of the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.shutdown_hooks: List[Callable] = []
        self._shutdown_initiated = False
    
    def register_hook(self, hook: Callable):
        """Register a shutdown hook"""
        self.shutdown_hooks.append(hook)
        logger.debug(f"Registered shutdown hook: {hook.__name__}")
    
    async def shutdown(self, signal_name: str = "SIGTERM"):
        """Perform graceful shutdown"""
        if self._shutdown_initiated:
            logger.warning("Shutdown already in progress")
            return
        
        self._shutdown_initiated = True
        logger.info(f"Received exit signal {signal_name}")
        logger.info("Starting graceful shutdown...")
        
        try:
            # Run shutdown hooks
            logger.info(f"Running {len(self.shutdown_hooks)} shutdown hooks...")
            for hook in self.shutdown_hooks:
                try:
                    logger.info(f"Running shutdown hook: {hook.__name__}")
                    if asyncio.iscoroutinefunction(hook):
                        await hook()
                    else:
                        hook()
                except Exception as e:
                    logger.error(f"Error in shutdown hook {hook.__name__}: {e}")
            
            # Close bot connection
            logger.info("Closing bot connection...")
            if not self.bot.is_closed():
                await self.bot.close()
            
            logger.info("✅ Graceful shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            # Exit the program
            sys.exit(0)
    
    def setup_signals(self):
        """Setup signal handlers for graceful shutdown"""
        # Only set up signal handlers on Unix systems
        if sys.platform == 'win32':
            logger.info("Windows detected - signal handlers limited")
            # On Windows, we can only handle SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        else:
            # Unix systems support more signals
            for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                signal.signal(sig, self._signal_handler)
        
        logger.info("Signal handlers registered")
    
    def _signal_handler(self, signum, frame):
        """Handle received signals"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal: {signal_name}")
        
        # Create shutdown task
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.shutdown(signal_name))
        else:
            loop.run_until_complete(self.shutdown(signal_name))
