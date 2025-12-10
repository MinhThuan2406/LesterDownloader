"""
Centralized embed creation utilities
"""

import discord
from typing import Optional, List, Dict, Any
from core.config import Colors

class EmbedBuilder:
    """Utility class for creating consistent Discord embeds"""
    
    @staticmethod
    def create_embed(
        title: str,
        description: Optional[str] = None,
        color: int = Colors.SUCCESS,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[str] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        timestamp: Optional[discord.utils.utcnow] = None
    ) -> discord.Embed:
        """
        Create a standardized embed
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color (from Colors class)
            fields: List of field dictionaries with 'name', 'value', 'inline' keys
            footer: Footer text
            thumbnail: Thumbnail URL
            image: Image URL
            timestamp: Timestamp for embed
            
        Returns:
            discord.Embed object
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=timestamp or discord.utils.utcnow()
        )
        
        # Add fields
        if fields:
            for field in fields:
                embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', True)
                )
        
        # Add footer
        if footer:
            embed.set_footer(text=footer)
        
        # Add thumbnail
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        # Add image
        if image:
            embed.set_image(url=image)
        
        return embed
    
    @staticmethod
    def success(title: str, description: str, **kwargs) -> discord.Embed:
        """Create a success embed"""
        return EmbedBuilder.create_embed(
            title=title,
            description=description,
            color=Colors.SUCCESS,
            **kwargs
        )
    
    @staticmethod
    def error(title: str, description: str, **kwargs) -> discord.Embed:
        """Create an error embed"""
        return EmbedBuilder.create_embed(
            title=title,
            description=description,
            color=Colors.ERROR,
            **kwargs
        )
    
    @staticmethod
    def warning(title: str, description: str, **kwargs) -> discord.Embed:
        """Create a warning embed"""
        return EmbedBuilder.create_embed(
            title=title,
            description=description,
            color=Colors.WARNING,
            **kwargs
        )
    
    @staticmethod
    def info(title: str, description: str, **kwargs) -> discord.Embed:
        """Create an info embed"""
        return EmbedBuilder.create_embed(
            title=title,
            description=description,
            color=Colors.INFO,
            **kwargs
        )
    
    @staticmethod
    def neutral(title: str, description: str, **kwargs) -> discord.Embed:
        """Create a neutral embed"""
        return EmbedBuilder.create_embed(
            title=title,
            description=description,
            color=Colors.NEUTRAL,
            **kwargs
        )
    
    @staticmethod
    def download_progress(
        platform: str,
        title: str,
        progress: str,
        status: str = "Downloading..."
    ) -> discord.Embed:
        """Create a download progress embed"""
        return EmbedBuilder.create_embed(
            title=f"Downloading from {platform}",
            description=f"**{title}**\n\n{progress}\n\n{status}",
            color=Colors.INFO,
            fields=[
                {
                    'name': 'Platform',
                    'value': platform.capitalize(),
                    'inline': True
                },
                {
                    'name': 'Status',
                    'value': status,
                    'inline': True
                }
            ]
        )
    
    @staticmethod
    def download_complete(
        platform: str,
        title: str,
        file_size: Optional[str] = None,
        duration: Optional[str] = None
    ) -> discord.Embed:
        """Create a download complete embed"""
        fields = [
            {
                'name': 'Platform',
                'value': platform.capitalize(),
                'inline': True
            }
        ]
        
        if file_size:
            fields.append({
                'name': 'File Size',
                'value': file_size,
                'inline': True
            })
        
        if duration:
            fields.append({
                'name': 'Duration',
                'value': duration,
                'inline': True
            })
        
        return EmbedBuilder.success(
            title="Download Complete",
            description=f"**{title}**\n\nYour download is ready!",
            fields=fields
        )
    
    @staticmethod
    def download_error(
        platform: str,
        title: str,
        error_message: str
    ) -> discord.Embed:
        """Create a download error embed"""
        return EmbedBuilder.error(
            title="Download Failed",
            description=f"**{title}**\n\nError: {error_message}",
            fields=[
                {
                    'name': 'Platform',
                    'value': platform.capitalize(),
                    'inline': True
                },
                {
                    'name': 'Error',
                    'value': error_message,
                    'inline': False
                }
            ]
        )
    
    @staticmethod
    def queue_status(
        queue_size: int,
        active_downloads: int,
        user_position: Optional[int] = None
    ) -> discord.Embed:
        """Create a queue status embed"""
        fields = [
            {
                'name': 'Queue Size',
                'value': str(queue_size),
                'inline': True
            },
            {
                'name': 'Active Downloads',
                'value': str(active_downloads),
                'inline': True
            }
        ]
        
        if user_position is not None:
            fields.append({
                'name': 'Your Position',
                'value': f"#{user_position}" if user_position > 0 else "Downloading now",
                'inline': True
            })
        
        return EmbedBuilder.info(
            title="Download Queue Status",
            description="Current download queue information",
            fields=fields
        )
    
    @staticmethod
    def platform_list(
        video_platforms: Dict[str, str],
        image_platforms: Dict[str, str]
    ) -> discord.Embed:
        """Create a platform list embed"""
        video_list = "\n".join([f"• {platform}" for platform in video_platforms.keys()])
        image_list = "\n".join([f"• {platform}" for platform in image_platforms.keys()])
        
        return EmbedBuilder.info(
            title="Supported Platforms",
            description="Platforms supported by this bot",
            fields=[
                {
                    'name': 'Video Platforms',
                    'value': video_list,
                    'inline': True
                },
                {
                    'name': 'Image Platforms',
                    'value': image_list,
                    'inline': True
                }
            ]
        )
    
    @staticmethod
    def quality_list(qualities: List[str], current_quality: str) -> discord.Embed:
        """Create a quality options embed"""
        quality_list = "\n".join([f"• {quality}" for quality in qualities])
        
        return EmbedBuilder.info(
            title="Available Quality Options",
            description="Video quality options for downloads",
            fields=[
                {
                    'name': 'Current Quality',
                    'value': current_quality,
                    'inline': True
                },
                {
                    'name': 'Available Options',
                    'value': quality_list,
                    'inline': False
                }
            ]
        )
