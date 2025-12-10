"""
Core bot class for LesterDownloader Discord Bot
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import List, Optional

from .config import BotConfig
from .logging import get_logger

logger = get_logger(__name__)

class LesterBot(commands.Bot):
    """Main bot class with enhanced functionality"""
    
    def __init__(self, config: BotConfig):
        """Initialize the bot with configuration"""
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        # Initialize bot
        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None  # Disable default help command
        )
        
        # Store configuration
        self.config = config
        self.start_time = None
        self.download_path = Path(config.DOWNLOAD_PATH)
        
        # Setup event handlers
        self.setup_events()
        
        # Start cleanup task
        self.cleanup_old_files.start()
    
    def setup_events(self):
        """Setup bot event handlers"""
        
        @self.event
        async def on_ready():
            """Called when the bot is ready"""
            self.start_time = discord.utils.utcnow()
            logger.info(f'{self.user} has connected to Discord!')
            logger.info(f'Bot is in {len(self.guilds)} guilds')
            
            # Set bot status
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="!help for commands"
                )
            )
        
        @self.event
        async def on_command_error(ctx, error):
            """Global error handler"""
            if isinstance(error, commands.CommandNotFound):
                return  # Ignore command not found errors
            
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"Missing required argument: {error.param}")
                return
            
            if isinstance(error, commands.BadArgument):
                await ctx.send("Invalid argument provided.")
                return
            
            # Log the error
            logger.error(f"Command error in {ctx.command}: {error}")
            await ctx.send("An error occurred while processing your command.")
    
    async def load_extensions(self, extensions: List[str]):
        """Load all cog extensions"""
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
    
    async def start_bot(self):
        """Start the bot with proper initialization"""
        try:
            # Validate configuration
            self.config.validate()
            
            # Load extensions
            extensions = [
                'cogs.video_downloader',
                'cogs.utils',
                'cogs.help'
            ]
            await self.load_extensions(extensions)
            
            # Start the bot
            await self.start(self.config.DISCORD_TOKEN)
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    @tasks.loop(hours=1)
    async def cleanup_old_files(self):
        """Clean up downloaded files older than 1 hour"""
        try:
            if not self.download_path.exists():
                return
            
            cutoff_time = time.time() - 3600  # 1 hour ago
            deleted_count = 0
            
            for file_path in self.download_path.iterdir():
                if file_path.is_file():
                    try:
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old files from downloads directory")
        
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
    
    @cleanup_old_files.before_loop
    async def before_cleanup(self):
        """Wait until bot is ready before starting cleanup task"""
        await self.wait_until_ready()
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.cleanup_old_files.cancel()
    
    def get_uptime(self) -> Optional[str]:
        """Get bot uptime as formatted string"""
        if not self.start_time:
            return None
        
        uptime = discord.utils.utcnow() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_status_info(self) -> dict:
        """Get comprehensive bot status information"""
        return {
            'guilds': len(self.guilds),
            'users': len(self.users),
            'latency': round(self.latency * 1000),
            'uptime': self.get_uptime(),
            'start_time': self.start_time.isoformat() if self.start_time else None
        }
