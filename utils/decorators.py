"""
Decorators for Discord bot commands
"""

import functools
from typing import Optional
from core.config import AutoDeleteSettings

def auto_delete(delay: int = AutoDeleteSettings.DEFAULT_DELAY):
    """
    Decorator to automatically delete bot messages after a delay
    
    Args:
        delay: Delay in seconds before auto-deletion
        
    Usage:
        @auto_delete(30)
        async def my_command(self, ctx, *args):
            message = await ctx.send("This will be auto-deleted")
            return message  # Must return the message to be deleted
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            result = await func(self, ctx, *args, **kwargs)
            
            # Get utils cog for auto-delete functionality
            if hasattr(self, 'bot'):
                utils_cog = self.bot.get_cog('UtilsCog')
                if utils_cog and result:
                    await utils_cog.schedule_auto_delete(result, delay)
            
            return result
        return wrapper
    return decorator

def error_handler(func):
    """
    Decorator to handle errors in commands with auto-delete
    
    Usage:
        @error_handler
        async def my_command(self, ctx, *args):
            # Command logic here
    """
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            # Log the error
            if hasattr(self, 'logger'):
                self.logger.error(f"Error in {func.__name__}: {e}")
            
            # Send error message with auto-delete
            if hasattr(self, 'bot'):
                utils_cog = self.bot.get_cog('UtilsCog')
                if utils_cog:
                    embed = discord.Embed(
                        title="❌ Error",
                        description=f"An error occurred: {str(e)}",
                        color=0xff0000
                    )
                    message = await ctx.send(embed=embed)
                    await utils_cog.schedule_auto_delete(message, 20)
            
            raise  # Re-raise the exception for proper handling
    return wrapper 