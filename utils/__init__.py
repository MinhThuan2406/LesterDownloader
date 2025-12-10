"""
Utility modules for the Discord bot
"""

from .platforms import PlatformDetector
from .decorators import auto_delete, error_handler
from .errors import BotError, ValidationError, DownloadError, PlatformError, create_error_embed, create_validation_error_embed, handle_bot_error
from .embeds import EmbedBuilder
from .command_base import BaseCommand

__all__ = [
    'PlatformDetector',
    'auto_delete',
    'error_handler',
    'BotError',
    'ValidationError',
    'DownloadError',
    'PlatformError',
    'create_error_embed',
    'create_validation_error_embed',
    'handle_bot_error',
    'EmbedBuilder',
    'BaseCommand'
] 