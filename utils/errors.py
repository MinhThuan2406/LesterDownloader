"""
Error handling utilities
"""

import discord
from typing import Optional
from core.config import Colors

class BotError(Exception):
    """Custom exception for bot errors with embed color"""
    def __init__(self, message: str, embed_color: int = Colors.ERROR):
        self.message = message
        self.embed_color = embed_color
        super().__init__(self.message)

class ValidationError(BotError):
    """Error for validation failures"""
    def __init__(self, message: str):
        super().__init__(message, Colors.WARNING)

class DownloadError(BotError):
    """Error for download failures"""
    def __init__(self, message: str):
        super().__init__(message, Colors.ERROR)

class PlatformError(BotError):
    """Error for unsupported platforms"""
    def __init__(self, message: str):
        super().__init__(message, Colors.ERROR)

def create_error_embed(error: BotError, title: str = "❌ Error") -> discord.Embed:
    """
    Create a standardized error embed
    
    Args:
        error: BotError instance
        title: Embed title
        
    Returns:
        Discord embed for the error
    """
    return discord.Embed(
        title=title,
        description=error.message,
        color=error.embed_color
    )

def create_validation_error_embed(message: str, valid_options: list = None) -> discord.Embed:
    """
    Create a validation error embed
    
    Args:
        message: Error message
        valid_options: List of valid options to display
        
    Returns:
        Discord embed for validation error
    """
    embed = discord.Embed(
        title="❌ Invalid Input",
        description=message,
        color=Colors.WARNING
    )
    
    if valid_options:
        embed.add_field(
            name="Valid Options",
            value="\n".join([f"• `{option}`" for option in valid_options]),
            inline=False
        )
    
    return embed

def handle_bot_error(ctx, error: Exception) -> Optional[discord.Embed]:
    """
    Handle bot errors and return appropriate embed
    
    Args:
        ctx: Discord context
        error: Exception that occurred
        
    Returns:
        Discord embed for error or None if not handled
    """
    if isinstance(error, BotError):
        return create_error_embed(error)
    
    # Handle other common errors
    if isinstance(error, ValueError):
        return create_error_embed(ValidationError(str(error)))
    
    if isinstance(error, TypeError):
        return create_error_embed(ValidationError("Invalid argument type"))
    
    # Return None for unhandled errors
    return None 