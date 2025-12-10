"""
Base command class for common command functionality
"""

import discord
from discord.ext import commands
from typing import Optional, Any, Dict
import asyncio

from core.logging import get_logger
from utils.embeds import EmbedBuilder

logger = get_logger(__name__)

class BaseCommand(commands.Cog):
    """Base class for all command cogs with common functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(self.__class__.__name__)
    
    async def send_embed(
        self,
        ctx,
        embed: discord.Embed,
        auto_delete: bool = False,
        delete_delay: int = 30
    ) -> discord.Message:
        """
        Send an embed with optional auto-delete
        
        Args:
            ctx: Command context
            embed: Discord embed to send
            auto_delete: Whether to auto-delete the message
            delete_delay: Delay before deletion in seconds
            
        Returns:
            Sent message object
        """
        try:
            message = await ctx.send(embed=embed)
            
            # Auto-deletion feature disabled
            # if auto_delete:
            #     await self.schedule_auto_delete(message, delete_delay)
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to send embed: {e}")
            await ctx.send("Failed to send message.")
            return None
    
    async def send_error(
        self,
        ctx,
        title: str,
        description: str,
        auto_delete: bool = True,
        delete_delay: int = 20
    ) -> Optional[discord.Message]:
        """Send an error embed"""
        embed = EmbedBuilder.error(title, description)
        return await self.send_embed(ctx, embed, auto_delete, delete_delay)
    
    async def send_success(
        self,
        ctx,
        title: str,
        description: str,
        auto_delete: bool = False,
        delete_delay: int = 30
    ) -> Optional[discord.Message]:
        """Send a success embed"""
        embed = EmbedBuilder.success(title, description)
        return await self.send_embed(ctx, embed, auto_delete, delete_delay)
    
    async def send_info(
        self,
        ctx,
        title: str,
        description: str,
        auto_delete: bool = False,
        delete_delay: int = 30
    ) -> Optional[discord.Message]:
        """Send an info embed"""
        embed = EmbedBuilder.info(title, description)
        return await self.send_embed(ctx, embed, auto_delete, delete_delay)
    
    async def schedule_auto_delete(
        self,
        message: discord.Message,
        delay_seconds: int
    ) -> None:
        """
        Schedule a message for auto-deletion
        
        Args:
            message: Message to delete
            delay_seconds: Delay before deletion
        """
        try:
            await asyncio.sleep(delay_seconds)
            await message.delete()
        except discord.NotFound:
            # Message was already deleted
            pass
        except Exception as e:
            self.logger.error(f"Failed to auto-delete message: {e}")
    
    async def check_permissions(
        self,
        ctx,
        required_permissions: list
    ) -> bool:
        """
        Check if user has required permissions
        
        Args:
            ctx: Command context
            required_permissions: List of required permissions
            
        Returns:
            True if user has permissions, False otherwise
        """
        if not ctx.guild:
            return True  # DM context, allow
        
        for permission in required_permissions:
            if not getattr(ctx.author.guild_permissions, permission, False):
                await self.send_error(
                    ctx,
                    "Insufficient Permissions",
                    f"You need the `{permission}` permission to use this command."
                )
                return False
        
        return True
    
    async def check_rate_limit(
        self,
        ctx,
        max_requests: int = 3,
        window_seconds: int = 60
    ) -> bool:
        """
        Check rate limiting for user
        
        Args:
            ctx: Command context
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
            
        Returns:
            True if within rate limit, False otherwise
        """
        # Simple in-memory rate limiting
        # In production, consider using Redis or database
        user_id = ctx.author.id
        current_time = discord.utils.utcnow()
        
        if not hasattr(self, '_rate_limit_data'):
            self._rate_limit_data = {}
        
        if user_id not in self._rate_limit_data:
            self._rate_limit_data[user_id] = []
        
        # Clean old entries
        self._rate_limit_data[user_id] = [
            timestamp for timestamp in self._rate_limit_data[user_id]
            if (current_time - timestamp).total_seconds() < window_seconds
        ]
        
        # Check if user has exceeded rate limit
        if len(self._rate_limit_data[user_id]) >= max_requests:
            await self.send_error(
                ctx,
                "Rate Limit Exceeded",
                f"You can only make {max_requests} requests per {window_seconds} seconds."
            )
            return False
        
        # Add current request
        self._rate_limit_data[user_id].append(current_time)
        return True
    
    def log_command_usage(
        self,
        ctx,
        command_name: str,
        **kwargs
    ) -> None:
        """
        Log command usage for analytics
        
        Args:
            ctx: Command context
            command_name: Name of the command
            **kwargs: Additional data to log
        """
        user_info = {
            'user_id': ctx.author.id,
            'username': ctx.author.name,
            'guild_id': ctx.guild.id if ctx.guild else None,
            'guild_name': ctx.guild.name if ctx.guild else None,
            'channel_id': ctx.channel.id,
            'channel_name': ctx.channel.name if hasattr(ctx.channel, 'name') else None
        }
        
        self.logger.info(
            f"Command used: {command_name} by {ctx.author.name} ({ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'} - {kwargs}"
        )
    
    async def handle_command_error(
        self,
        ctx,
        error: Exception
    ) -> None:
        """
        Handle command errors consistently
        
        Args:
            ctx: Command context
            error: The error that occurred
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await self.send_error(
                ctx,
                "Missing Argument",
                f"Missing required argument: `{error.param}`"
            )
        elif isinstance(error, commands.BadArgument):
            await self.send_error(
                ctx,
                "Invalid Argument",
                "One or more arguments provided are invalid."
            )
        elif isinstance(error, commands.CommandOnCooldown):
            await self.send_error(
                ctx,
                "Command on Cooldown",
                f"Please wait {error.retry_after:.1f} seconds before trying again."
            )
        elif isinstance(error, commands.MissingPermissions):
            await self.send_error(
                ctx,
                "Insufficient Permissions",
                "You don't have permission to use this command."
            )
        else:
            self.logger.error(f"Unhandled command error in {ctx.command}: {error}")
            await self.send_error(
                ctx,
                "Unexpected Error",
                "An unexpected error occurred. Please try again later."
            )
    
    def format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to human-readable string
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            remaining_seconds = seconds % 60
            return f"{hours}h {minutes}m {remaining_seconds}s"
    
    def format_file_size(self, bytes_size: int) -> str:
        """
        Format file size in bytes to human-readable string
        
        Args:
            bytes_size: Size in bytes
            
        Returns:
            Formatted file size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
