import discord
from discord.ext import commands
import asyncio
from typing import Optional, Dict, Any

from utils.command_base import BaseCommand
from utils.embeds import EmbedBuilder
from utils.platforms import PlatformDetector
from services.video_downloader import VideoDownloader
from services.image_downloader import ImageDownloader
from services.database import DatabaseManager
from services.download_queue import DownloadQueue
from services.content_detector import ContentDetector
from services.platform_handler import PlatformHandler
from core.config import QualityPresets, DatabaseLimits

class VideoDownloaderCog(BaseCommand):
    """Cog for video downloading commands"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.video_downloader = VideoDownloader()
        self.image_downloader = ImageDownloader()
        self.db = DatabaseManager()
        self.queue = DownloadQueue()
        self.content_detector = ContentDetector()
        self.platform_handler = PlatformHandler(bot.config)
        
        # Initialize database
        asyncio.create_task(self.db.init_db())
    
    @commands.command(name='download', aliases=['dl', 'get'])
    async def download_video(self, ctx, url: str, quality: str = None):
        """
        Download a video or image from supported platforms
        
        Usage: !download <url> [quality]
        
        Quality Options (for videos):
        • best - Best quality available
        • best[height<=720] - Best up to 720p (default)
        • best[height<=480] - Best up to 480p (smaller file)
        • worst - Lowest quality (smallest file)
        • 720p, 480p, 360p - Specific resolution
        • small - Optimized for Discord (under 8MB)
        """
        # Check rate limiting
        if not await self.check_rate_limit(ctx):
            return
        
        # Validate URL using platform handler
        try:
            self.logger.info(f"Starting validation for URL: {url}")
            validation = await self.platform_handler.validate_url(url)
            
            # Debug logging
            self.logger.info(f"Validation result type: {type(validation)}")
            self.logger.info(f"Validation result: {validation}")
            
            # Check if validation is a string (error case)
            if isinstance(validation, str):
                self.logger.error(f"Validation returned string instead of dict: {validation}")
                embed = EmbedBuilder.error(
                    title="Validation Error",
                    description=f"An error occurred while validating the URL: {validation}",
                    fields=[
                        {
                            'name': 'What to Try',
                            'value': "• Check if the URL is correct\n• Try a different URL\n• Use `!platform-help` for supported platforms",
                            'inline': False
                        }
                    ]
                )
                await self.send_embed(ctx, embed, auto_delete=True, delete_delay=20)
                return
            
            if not validation['valid']:
                if validation.get('reason') == 'private_content':
                    embed = EmbedBuilder.error(
                    title="Private Content Not Supported",
                    description=f"This {validation['platform']} content appears to be private or restricted.",
                    fields=[
                        {
                            'name': 'Why This Happens',
                            'value': "• The content is set to private/friends only\n• The content requires authentication\n• The content is from a private group/account\n• The content has restricted access",
                            'inline': False
                        },
                        {
                            'name': 'Solutions',
                            'value': "• Try public content from the same platform\n• Ask the content creator to make it public\n• Use a direct link to public content\n• Check if the content is still available",
                            'inline': False
                        }
                    ]
                )
                    await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
                    return
                else:
                    embed = EmbedBuilder.error(
                        title="URL Validation Failed",
                        description=validation.get('error', 'Unknown validation error'),
                        fields=[
                            {
                                'name': 'Supported Platforms',
                                'value': "Use `!platform-help` to see all supported platforms and their limitations",
                                'inline': False
                            }
                        ]
                    )
                    await self.send_embed(ctx, embed, auto_delete=True, delete_delay=20)
                    return
            
            # If we get here, validation was successful, proceed with download
            self.logger.info(f"URL validation successful for {url}, proceeding with download")
            
        except Exception as e:
            self.logger.error(f"Error validating URL {url}: {e}")
            embed = EmbedBuilder.error(
                title="Validation Error",
                description=f"An error occurred while validating the URL: {str(e)}",
                fields=[
                    {
                        'name': 'What to Try',
                        'value': "• Check if the URL is correct\n• Try a different URL\n• Use `!platform-help` for supported platforms",
                        'inline': False
                    }
                ]
            )
            await self.send_embed(ctx, embed, auto_delete=True, delete_delay=20)
            return
        
        # Get content information using platform handler
        try:
            content_info = await self.platform_handler.get_content_info(url)
            self.logger.info(f"Received content_info: type={type(content_info)}, keys={list(content_info.keys()) if isinstance(content_info, dict) else 'N/A'}")
            self.logger.info(f"content_info['success'] = {content_info.get('success')}")
            if 'error' in content_info:
                self.logger.info(f"content_info['error'] = {content_info['error']}")
            if not content_info['success']:
                # Handle different error types with appropriate messages
                if content_info.get('reason') == 'private_content':
                    embed = EmbedBuilder.error(
                    title="Private Content Not Supported",
                    description=content_info['error'],
                    fields=[
                        {
                            'name': 'Why This Happens',
                            'value': "• The content is set to private/friends only\n• The content requires authentication\n• The content is from a private group/account\n• The content has restricted access",
                            'inline': False
                        },
                        {
                            'name': 'Solutions',
                            'value': "• Try public content from the same platform\n• Ask the content creator to make it public\n• Use a direct link to public content\n• Check if the content is still available",
                            'inline': False
                        }
                    ]
                )
                    await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
                    return
                elif content_info.get('reason') == 'technical_limitation':
                    embed = EmbedBuilder.error(
                        title="Technical Limitation",
                        description=content_info['error'],
                        fields=[
                            {
                                'name': 'Details',
                                'value': content_info.get('details', 'The content could not be processed due to technical limitations.'),
                                'inline': False
                            },
                            {
                                'name': 'What to Try',
                                'value': "• Try the download again later\n• Check if the content is still available\n• Try a different post from the same user\n• Use `!platform-help facebook` for more information",
                                'inline': False
                            }
                        ]
                    )
                    await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
                    return
                elif content_info.get('reason') == 'unsupported_format':
                    embed = EmbedBuilder.error(
                        title="Unsupported Format",
                        description=content_info['error'],
                        fields=[
                            {
                                'name': 'Details',
                                'value': content_info.get('details', 'This content uses a format that is not currently supported.'),
                                'inline': False
                            },
                            {
                                'name': 'What to Try',
                                'value': "• Try a different post from the same platform\n• The format may be supported in future updates\n• Use `!platform-help` for platform-specific guidance",
                                'inline': False
                            }
                        ]
                    )
                    await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
                    return
                elif content_info.get('reason') == 'rate_limited':
                    embed = EmbedBuilder.error(
                        title="Rate Limited",
                        description=content_info['error'],
                        fields=[
                            {
                                'name': 'Details',
                                'value': content_info.get('details', 'The platform is temporarily blocking requests due to rate limiting.'),
                                'inline': False
                            },
                            {
                                'name': 'What to Try',
                                'value': "• Wait a few minutes and try again\n• Try a different URL from the same platform\n• The platform may be experiencing high traffic\n• Try again later when traffic is lower",
                                'inline': False
                            }
                        ]
                    )
                    await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
                    return
                elif content_info.get('reason') == 'content_unavailable':
                    embed = EmbedBuilder.error(
                        title="Content Unavailable",
                        description=content_info['error'],
                        fields=[
                            {
                                'name': 'Details',
                                'value': content_info.get('details', 'The requested content cannot be accessed.'),
                                'inline': False
                            },
                            {
                                'name': 'What to Try',
                                'value': "• Check if the URL is correct\n• The content may have been deleted or made private\n• Try a different URL from the same platform\n• The content may be region-restricted",
                                'inline': False
                            }
                        ]
                    )
                    await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
                    return
                else:
                    # Generic error fallback for unhandled error reasons
                    embed = EmbedBuilder.error(
                        title="Content Analysis Failed",
                        description=content_info.get('error', 'Unknown error occurred'),
                        fields=[
                            {
                                'name': 'Possible Reasons',
                                'value': "• Content may have been deleted\n• Content requires authentication\n• Content violates platform policies\n• Temporary technical issues",
                                'inline': False
                            },
                            {
                                'name': 'What to Try',
                                'value': "• Check if the content is still available\n• Try a different URL from the same platform\n• Use `!platform-help` for platform-specific guidance\n• Try again later",
                                'inline': False
                            }
                        ]
                    )
                    await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
                    return
        except Exception as e:
            self.logger.error(f"Error getting content info for {url}: {e}")
            embed = EmbedBuilder.error(
                title="Content Analysis Error",
                description=f"An error occurred while analyzing the content: {str(e)}",
                fields=[
                    {
                        'name': 'What to Try',
                        'value': "• Check if the content is still available\n• Try a different URL\n• Use `!platform-help` for supported platforms",
                        'inline': False
                    }
                ]
            )
            await self.send_embed(ctx, embed, auto_delete=True, delete_delay=20)
            return
        
        # Extract content information
        platform = content_info['platform']
        content_type = content_info['content_type']
        title = content_info['title']
        
        # Set quality based on content type
        if content_type in ['image', 'gallery']:
            quality = None  # Images don't need quality settings
        elif content_type in ['video', 'reel', 'story', 'thread']:
            # Get user's preferred quality if not specified
            if quality is None:
                user_prefs = await self.db.get_user_preferences(ctx.author.id)
                quality = user_prefs.get('preferred_quality', QualityPresets.DEFAULT_QUALITY) if user_prefs else QualityPresets.DEFAULT_QUALITY
            
            # Validate quality parameter for videos
            if quality not in QualityPresets.VALID_QUALITIES:
                embed = EmbedBuilder.error(
                    title="Invalid Quality",
                    description=f"Invalid quality: `{quality}`",
                    fields=[
                        {
                            'name': 'Valid Qualities',
                            'value': "\n".join([f"• {q}" for q in QualityPresets.VALID_QUALITIES]),
                            'inline': False
                        }
                    ]
                )
                await self.send_embed(ctx, embed, auto_delete=True, delete_delay=20)
                return
        
        # Add to download queue
        queue_item = {
            'user_id': ctx.author.id,
            'username': ctx.author.name,
            'url': url,
            'platform': platform,
            'quality': quality,
            'content_type': content_type,
            'ctx': ctx
        }
        
        # Check queue status
        queue_status = await self.queue.get_queue_status()
        if queue_status['queue_size'] >= self.queue.max_queue_size:
            await self.send_error(
                ctx,
                "Queue Full",
                "The download queue is full. Please try again later."
            )
            return
        
        # Add to queue
        result = await self.queue.add_download(ctx, url, quality)
        if result['status'] != 'queued':
            await self.send_error(
                ctx,
                "Queue Error",
                result['message']
            )
            return
        
        position = result['position']
        
        # Send confirmation
        embed = EmbedBuilder.info(
            title="Download Queued",
            description=f"Your download has been added to the queue.",
            fields=[
                {
                    'name': 'Platform',
                    'value': platform.capitalize(),
                    'inline': True
                },
                {
                    'name': 'Content Type',
                    'value': content_type.capitalize(),
                    'inline': True
                },
                {
                    'name': 'Position',
                    'value': f"#{position}" if position > 1 else "Downloading now",
                    'inline': True
                },
                {
                    'name': 'Quality',
                    'value': quality or "N/A (image)",
                    'inline': True
                }
            ]
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'download', url=url, quality=quality, platform=platform, content_type=content_type)
        
        # Process queue
        asyncio.create_task(self._process_download_queue())
    
    async def _process_download_queue(self):
        """Process the download queue"""
        while True:
            try:
                # Get next item from queue
                item = await self.queue.get_next_item()
                if not item:
                    await asyncio.sleep(1)
                    continue
                
                ctx = item['ctx']
                url = item['url']
                platform = item['platform']
                quality = item['quality']
                content_type = item['content_type']
                
                # Send progress message
                progress_embed = EmbedBuilder.download_progress(
                    platform=platform,
                    title="Processing...",
                    progress="Starting download...",
                    status="Downloading..."
                )
                
                progress_message = await self.send_embed(ctx, progress_embed)
                
                try:
                    # Download based on content type
                    if content_type in ['image', 'gallery']:
                        filepath, title, error = await self.image_downloader.download_image(url)
                    else:
                        filepath, title, error = await self.video_downloader.download_video(url, quality)
                    
                    if error:
                        # Check for specific Facebook errors
                        if platform == 'facebook' and 'No video formats found' in error:
                            error_embed = EmbedBuilder.error(
                                title="Facebook Download Failed",
                                description="This Facebook post could not be downloaded due to technical limitations.",
                                fields=[
                                    {
                                        'name': 'Reason',
                                        'value': "The post may be using a format not supported by the downloader, or there may be temporary access issues.",
                                        'inline': False
                                    },
                                    {
                                        'name': 'What to Try',
                                        'value': "• Try the download again later\n• Check if the post is still available\n• Try a different post from the same user\n• Use `!platform-help facebook` for more information",
                                        'inline': False
                                    }
                                ]
                            )
                            await self.send_embed(ctx, error_embed, auto_delete=True, delete_delay=30)
                        elif platform == 'facebook' and 'pfbid' in error:
                            error_embed = EmbedBuilder.error(
                                title="Facebook Format Not Supported",
                                description="This Facebook post format is not currently supported.",
                                fields=[
                                    {
                                        'name': 'Reason',
                                        'value': "Facebook occasionally uses new formats that the downloader has not yet implemented.",
                                        'inline': False
                                    },
                                    {
                                        'name': 'What to Try',
                                        'value': "• Try a different Facebook post\n• The format may be supported in future updates\n• Use `!platform-help facebook` for more information",
                                        'inline': False
                                    }
                                ]
                            )
                            await self.send_embed(ctx, error_embed, auto_delete=True, delete_delay=30)
                        else:
                            # Log error
                            await self.db.log_download(
                                user_id=item['user_id'],
                                username=item['username'],
                                url=url,
                                platform=platform,
                                title=title,
                                success=False,
                                error_message=error
                            )
                            
                            # Send error message
                            error_embed = EmbedBuilder.download_error(
                                platform=platform,
                                title=title or "Unknown",
                                error_message=error
                            )
                            await self.send_embed(ctx, error_embed, auto_delete=True, delete_delay=30)
                        
                        # Delete progress message
                        if progress_message:
                            try:
                                await progress_message.delete()
                            except:
                                pass
                        
                        continue
                    
                    # Get file info
                    import os
                    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                    file_size_str = self.format_file_size(file_size)
                    
                    # Log successful download
                    await self.db.log_download(
                        user_id=item['user_id'],
                        username=item['username'],
                        url=url,
                        platform=platform,
                        title=title,
                        file_size=file_size,
                        success=True
                    )
                    
                    # Send file
                    try:
                        with open(filepath, 'rb') as f:
                            file = discord.File(f, filename=os.path.basename(filepath))
                            
                            complete_embed = EmbedBuilder.download_complete(
                                platform=platform,
                                title=title,
                                file_size=file_size_str
                            )
                            
                            await ctx.send(embed=complete_embed, file=file)
                    
                    except Exception as e:
                        await self.send_error(
                            ctx,
                            "File Send Error",
                            f"Download completed but failed to send file: {str(e)}"
                        )
                    
                    finally:
                        # Clean up file
                        try:
                            os.remove(filepath)
                        except:
                            pass
                    
                    # Delete progress message
                    if progress_message:
                        try:
                            await progress_message.delete()
                        except:
                            pass
                
                except Exception as e:
                    self.logger.error(f"Error processing download: {e}")
                    await self.send_error(
                        ctx,
                        "Download Error",
                        f"An unexpected error occurred: {str(e)}"
                    )
                    
                    # Delete progress message
                    if progress_message:
                        try:
                            await progress_message.delete()
                        except:
                            pass
                
                # Mark as complete
                await self.queue.mark_complete(item)
                
            except Exception as e:
                self.logger.error(f"Error in download queue processor: {e}")
                await asyncio.sleep(5)
    
    @commands.command(name='info')
    async def get_video_info(self, ctx, url: str):
        """Get information about a video or image"""
        if not await self.check_rate_limit(ctx):
            return
        
        if not PlatformDetector.is_supported_url(url):
            await self.send_error(
                ctx,
                "Unsupported Platform",
                "This URL is not from a supported platform."
            )
            return
        
        try:
            # Get video info
            info = await self.video_downloader.get_video_info(url)
            
            if not info:
                await self.send_error(
                    ctx,
                    "Info Unavailable",
                    "Could not retrieve information for this URL."
                )
                return
            
            # Format info
            platform = PlatformDetector.get_platform(url)
            duration = self.format_duration(info.get('duration', 0))
            file_size = self.format_file_size(info.get('filesize', 0))
            
            fields = [
                {
                    'name': 'Platform',
                    'value': platform.capitalize(),
                    'inline': True
                },
                {
                    'name': 'Title',
                    'value': info.get('title', 'Unknown'),
                    'inline': False
                }
            ]
            
            if info.get('duration'):
                fields.append({
                    'name': 'Duration',
                    'value': duration,
                    'inline': True
                })
            
            if info.get('filesize'):
                fields.append({
                    'name': 'File Size',
                    'value': file_size,
                    'inline': True
                })
            
            if info.get('uploader'):
                fields.append({
                    'name': 'Uploader',
                    'value': info.get('uploader'),
                    'inline': True
                })
            
            embed = EmbedBuilder.info(
                title="Media Information",
                description="Information about the requested media",
                fields=fields
            )
            
            await self.send_embed(ctx, embed)
            self.log_command_usage(ctx, 'info', url=url, platform=platform)
            
        except Exception as e:
            await self.send_error(
                ctx,
                "Info Error",
                f"Failed to get information: {str(e)}"
            )
    
    @commands.command(name='queue')
    async def queue_status(self, ctx):
        """Show current download queue status"""
        queue_status = await self.queue.get_queue_status()
        user_position = await self.queue.get_user_position(ctx.author.id)
        
        embed = EmbedBuilder.queue_status(
            queue_size=queue_status['queue_size'],
            active_downloads=queue_status['active_downloads'],
            user_position=user_position
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'queue')
    
    @commands.command(name='cancel')
    async def cancel_downloads(self, ctx):
        """Cancel your pending downloads"""
        cancelled = await self.queue.cancel_user_downloads(ctx.author.id)
        
        if cancelled > 0:
            embed = EmbedBuilder.success(
                title="Downloads Cancelled",
                description=f"Cancelled {cancelled} pending download(s)."
            )
        else:
            embed = EmbedBuilder.info(
                title="No Downloads to Cancel",
                description="You don't have any pending downloads to cancel."
            )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'cancel', cancelled=cancelled)
    
    @commands.command(name='history')
    async def download_history(self, ctx, limit: int = 5):
        """Show your download history"""
        if limit > DatabaseLimits.MAX_HISTORY_LIMIT:
            limit = DatabaseLimits.MAX_HISTORY_LIMIT
        
        downloads = await self.db.get_user_downloads(ctx.author.id, limit)
        
        if not downloads:
            embed = EmbedBuilder.info(
                title="No Download History",
                description="You haven't downloaded anything yet."
            )
            await self.send_embed(ctx, embed)
            return
        
        # Format history
        history_lines = []
        for download in downloads:
            status = "✅" if download['success'] else "❌"
            platform = download['platform'].capitalize()
            title = download['title'] or "Unknown"
            date = download['timestamp'][:10]  # Just the date part
            
            history_lines.append(f"{status} **{platform}** - {title} ({date})")
        
        embed = EmbedBuilder.info(
            title="Download History",
            description="\n".join(history_lines),
            fields=[
                {
                    'name': 'Total Downloads',
                    'value': str(len(downloads)),
                    'inline': True
                }
            ]
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'history', limit=limit)
    
    @commands.command(name='stats')
    async def platform_stats(self, ctx):
        """Show platform download statistics"""
        stats = await self.db.get_platform_stats()
        
        if not stats:
            embed = EmbedBuilder.info(
                title="No Statistics",
                description="No download statistics available yet."
            )
            await self.send_embed(ctx, embed)
            return
        
        # Format stats
        stats_lines = []
        for stat in stats:
            platform = stat['platform'].capitalize()
            total = stat['total_downloads']
            successful = stat['successful_downloads']
            failed = stat['failed_downloads']
            success_rate = (successful / total * 100) if total > 0 else 0
            
            stats_lines.append(
                f"**{platform}** - {total} total, {successful} successful "
                f"({success_rate:.1f}% success rate)"
            )
        
        embed = EmbedBuilder.info(
            title="Platform Statistics",
            description="\n".join(stats_lines)
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'stats')
    
    @commands.command(name='quality')
    async def set_quality(self, ctx, quality: str):
        """Set your preferred video quality"""
        if quality not in QualityPresets.VALID_QUALITIES:
            embed = EmbedBuilder.error(
                title="Invalid Quality",
                description=f"Invalid quality: `{quality}`",
                fields=[
                    {
                        'name': 'Valid Qualities',
                        'value': "\n".join([f"• {q}" for q in QualityPresets.VALID_QUALITIES]),
                        'inline': False
                    }
                ]
            )
            await self.send_embed(ctx, embed, auto_delete=True, delete_delay=20)
            return
        
        # Update user preferences
        await self.db.update_user_preferences(
            user_id=ctx.author.id,
            username=ctx.author.name,
            preferred_quality=quality
        )
        
        embed = EmbedBuilder.success(
            title="Quality Updated",
            description=f"Your preferred quality has been set to: `{quality}`"
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'quality', quality=quality)
    
    @commands.command(name='qualities')
    async def show_qualities(self, ctx):
        """Show available quality options"""
        # Get user's current quality
        user_prefs = await self.db.get_user_preferences(ctx.author.id)
        current_quality = user_prefs.get('preferred_quality', QualityPresets.DEFAULT_QUALITY) if user_prefs else QualityPresets.DEFAULT_QUALITY
        
        embed = EmbedBuilder.quality_list(
            qualities=QualityPresets.VALID_QUALITIES,
            current_quality=current_quality
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'qualities')
    
    @commands.command(name='formats')
    async def show_formats(self, ctx, url: str):
        """Show available formats for a video"""
        if not await self.check_rate_limit(ctx):
            return
        
        if not PlatformDetector.is_supported_url(url):
            await self.send_error(
                ctx,
                "Unsupported Platform",
                "This URL is not from a supported platform."
            )
            return
        
        try:
            formats = await self.video_downloader.get_available_formats(url)
            
            if not formats:
                await self.send_error(
                    ctx,
                    "Formats Unavailable",
                    "Could not retrieve format information for this URL."
                )
                return
            
            # Format the formats list
            format_lines = []
            for fmt in formats[:10]:  # Limit to first 10 formats
                format_id = fmt.get('format_id', 'N/A')
                ext = fmt.get('ext', 'N/A')
                resolution = fmt.get('resolution', 'N/A')
                filesize = self.format_file_size(fmt.get('filesize', 0))
                
                format_lines.append(f"**{format_id}** - {ext} {resolution} ({filesize})")
            
            embed = EmbedBuilder.info(
                title="Available Formats",
                description="Available download formats for this video",
                fields=[
                    {
                        'name': 'Formats',
                        'value': "\n".join(format_lines),
                        'inline': False
                    }
                ]
            )
            
            await self.send_embed(ctx, embed)
            self.log_command_usage(ctx, 'formats', url=url)
            
        except Exception as e:
            await self.send_error(
                ctx,
                "Formats Error",
                f"Failed to get formats: {str(e)}"
            )
    
    @commands.command(name='platforms')
    async def supported_platforms(self, ctx):
        """Show supported platforms"""
        video_platforms = PlatformDetector.get_video_platforms()
        image_platforms = PlatformDetector.get_image_platforms()
        
        embed = EmbedBuilder.platform_list(
            video_platforms=video_platforms,
            image_platforms=image_platforms
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'platforms')
    
    @commands.command(name='update')
    async def update_ytdlp(self, ctx):
        """Update yt-dlp to the latest version (owner only)"""
        if not await self.bot.is_owner(ctx.author):
            await self.send_error(
                ctx,
                "Access Denied",
                "This command is only available to the bot owner."
            )
            return
        
        try:
            import subprocess
            import sys
            
            # Update yt-dlp
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                embed = EmbedBuilder.success(
                    title="yt-dlp Updated",
                    description="yt-dlp has been updated to the latest version."
                )
            else:
                embed = EmbedBuilder.error(
                    title="Update Failed",
                    description=f"Failed to update yt-dlp: {result.stderr}"
                )
            
            await self.send_embed(ctx, embed)
            self.log_command_usage(ctx, 'update')
            
        except Exception as e:
            await self.send_error(
                ctx,
                "Update Error",
                f"Failed to update yt-dlp: {str(e)}"
            )

    @commands.command(name='facebook-help')
    async def facebook_help(self, ctx):
        """Get help with Facebook downloads and common issues"""
        embed = EmbedBuilder.info(
            title="Facebook Download Help",
            description="Information about Facebook downloads and troubleshooting",
            fields=[
                {
                    'name': 'Supported Content',
                    'value': "• Public Facebook posts\n• Public photos and videos\n• Public reels and stories\n• Posts from public groups",
                    'inline': False
                },
                {
                    'name': 'Not Supported',
                    'value': "• Private posts (Friends Only)\n• Posts from private groups\n• Posts requiring login\n• Deleted posts\n• Posts with restricted access",
                    'inline': False
                },
                {
                    'name': 'Common Error Messages',
                    'value': "• 'No video formats found' = Technical limitation\n• 'pfbid' errors = Unsupported format\n• 'Could not extract' = Post not accessible\n• 'Login required' = Private content",
                    'inline': False
                },
                {
                    'name': 'Troubleshooting Tips',
                    'value': "• Try public posts only\n• Check if the post is still available\n• Use direct links when possible\n• Try downloading again later\n• Some formats may not be supported yet",
                    'inline': False
                },
                {
                    'name': 'Technical Limitations',
                    'value': "• Facebook occasionally uses new formats\n• Some posts may have temporary access issues\n• The downloader may need updates for new formats\n• Rate limiting may affect downloads",
                    'inline': False
                },
                {
                    'name': 'Alternative Solutions',
                    'value': "• Try a different post from the same user\n• Ask the content creator for a direct link\n• Try downloading from other platforms\n• Use screenshots for static content",
                    'inline': False
                }
            ]
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'facebook-help')

    @commands.command(name='platform-help')
    async def platform_help(self, ctx, platform: str = None):
        """Get comprehensive help for all platforms or a specific platform"""
        if platform:
            await self._show_platform_specific_help(ctx, platform.lower())
        else:
            await self._show_all_platforms_help(ctx)
    
    async def _show_platform_specific_help(self, ctx, platform: str):
        """Show detailed help for a specific platform"""
        # Get platform help information
        platform_help = self.platform_handler.get_platform_help(platform)
        
        if not platform_help['supported']:
            embed = EmbedBuilder.error(
                title="Platform Not Supported",
                description=f"Platform '{platform}' is not currently supported."
            )
            await self.send_embed(ctx, embed, auto_delete=True, delete_delay=20)
            return
        
        # Create detailed platform help embed
        settings = platform_help['settings']
        limitations = platform_help['limitations']
        tips = platform_help['tips']
        
        fields = [
            {
                'name': 'Supported Content',
                'value': self._format_supported_content(settings),
                'inline': False
            },
            {
                'name': 'Limitations',
                'value': "\n".join([f"• {limitation}" for limitation in limitations]),
                'inline': False
            },
            {
                'name': 'Tips',
                'value': "\n".join([f"• {tip}" for tip in tips]),
                'inline': False
            }
        ]
        
        # Add technical details
        if settings.get('max_duration'):
            fields.append({
                'name': 'Technical Limits',
                'value': f"• Max duration: {settings['max_duration']} seconds\n• Rate limit: {settings.get('rate_limit', 'N/A')} requests/min",
                'inline': True
            })
        
        embed = EmbedBuilder.info(
            title=f"{platform.capitalize()} Download Help",
            description=f"Comprehensive guide for downloading from {platform.capitalize()}",
            fields=fields
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'platform-help', platform=platform)
    
    def _format_supported_content(self, settings: Dict[str, Any]) -> str:
        """Format supported content information"""
        supported_items = []
        
        if settings.get('supports_public_posts', False):
            supported_items.append("Public posts")
        if settings.get('supports_public_videos', False):
            supported_items.append("Public videos")
        if settings.get('supports_groups', False):
            supported_items.append("Public groups")
        if settings.get('supports_pages', False):
            supported_items.append("Public pages")
        if settings.get('supports_reels', False):
            supported_items.append("Reels")
        if settings.get('supports_igtv', False):
            supported_items.append("IGTV")
        if settings.get('supports_clips', False):
            supported_items.append("Clips")
        if settings.get('supports_shorts', False):
            supported_items.append("Shorts")
        if settings.get('supports_live_streams', False):
            supported_items.append("Live streams")
        
        if not supported_items:
            return "No specific content types listed"
        
        return "\n".join([f"• {item}" for item in supported_items])
    
    async def _show_all_platforms_help(self, ctx):
        """Show help for all supported platforms"""
        platforms = [
            'facebook', 'instagram', 'twitter', 'tiktok', 
            'youtube', 'reddit', 'twitch', 'vimeo', 'dailymotion'
        ]
        
        platform_info = []
        for platform in platforms:
            help_info = self.platform_handler.get_platform_help(platform)
            if help_info['supported']:
                settings = help_info['settings']
                status = "✅ Supported" if settings.get('supports_public_posts') or settings.get('supports_public_videos') else "⚠️ Limited"
                platform_info.append(f"**{platform.capitalize()}** - {status}")
        
        embed = EmbedBuilder.info(
            title="All Supported Platforms",
            description="Overview of all platforms supported by this bot",
            fields=[
                {
                    'name': 'Platforms',
                    'value': "\n".join(platform_info),
                    'inline': False
                },
                {
                    'name': 'How to Use',
                    'value': "Use `!platform-help <platform>` for detailed information about a specific platform.\nExample: `!platform-help facebook`",
                    'inline': False
                },
                {
                    'name': 'Important Notes',
                    'value': "• Only public content is supported\n• Private/restricted content is not supported\n• All downloads must comply with platform terms of service\n• Rate limits apply to prevent abuse",
                    'inline': False
                }
            ]
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'platform-help', all_platforms=True)
    
    @commands.command(name='ethical-guidelines')
    async def ethical_guidelines(self, ctx):
        """Show the bot's ethical guidelines and content policies"""
        embed = EmbedBuilder.info(
            title="Ethical Guidelines & Content Policies",
            description="This bot operates under strict ethical guidelines to ensure legal compliance and respect for privacy.",
            fields=[
                {
                    'name': 'Privacy & Legal Compliance',
                    'value': "• Only public content is supported\n• Private/restricted content is not supported\n• All downloads comply with platform terms of service\n• User privacy is respected",
                    'inline': False
                },
                {
                    'name': 'Content Policies',
                    'value': "• NSFW content is blocked\n• Harassment content is blocked\n• Violence content is blocked\n• Copyright is respected\n• Platform policies are followed",
                    'inline': False
                },
                {
                    'name': 'Rate Limiting',
                    'value': "• Respectful rate limits are enforced\n• Server load is minimized\n• Platform guidelines are followed\n• Abuse prevention measures are in place",
                    'inline': False
                },
                {
                    'name': 'User Education',
                    'value': "• Clear limitations are communicated\n• Users are educated about platform policies\n• Ethical use is encouraged\n• Legal compliance is prioritized",
                    'inline': False
                },
                {
                    'name': 'Why These Limitations?',
                    'value': "• Respects user privacy\n• Complies with platform terms of service\n• Avoids legal issues\n• Prevents abuse and harassment\n• Maintains ethical standards",
                    'inline': False
                }
            ]
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'ethical-guidelines')

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(VideoDownloaderCog(bot)) 