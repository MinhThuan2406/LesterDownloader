"""
Download queue management
"""

import asyncio
import logging
from collections import deque
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import os

from core.config import QueueSettings
from core.logging import get_logger
from utils.platforms import PlatformDetector
from services.video_downloader import VideoDownloader
from services.image_downloader import ImageDownloader
from services.content_detector import ContentDetector

logger = get_logger(__name__)

@dataclass
class DownloadRequest:
    """Represents a download request in the queue"""
    user_id: int
    username: str
    url: str
    platform: str
    quality: str
    ctx: Any  # Discord context
    timestamp: datetime
    priority: int = 0  # Higher number = higher priority

class DownloadQueue:
    """Queue system for managing multiple download requests"""
    
    def __init__(self, max_concurrent: int = QueueSettings.MAX_CONCURRENT, max_queue_size: int = QueueSettings.MAX_QUEUE_SIZE):
        self.queue = deque()
        self.active_downloads = 0
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.download_history = {}  # Track recent downloads per user
        self.lock = asyncio.Lock()
        self.video_downloader = VideoDownloader()
        self.image_downloader = ImageDownloader()
        
    async def add_download(self, ctx, url: str, quality: str = "best[height<=720]", 
                          priority: int = 0) -> Dict[str, Any]:
        """Add a download request to the queue"""
        async with self.lock:
            # Check if user has too many recent downloads
            user_id = ctx.author.id
            if await self._is_user_spamming(user_id):
                return {
                    "status": "rate_limited",
                    "message": f"You're downloading too frequently. Please wait {QueueSettings.RATE_LIMIT_WINDOW} seconds."
                }
            
            # Check queue size
            if len(self.queue) >= self.max_queue_size:
                return {
                    "status": "queue_full",
                    "message": f"Download queue is full (max {self.max_queue_size}). Please try again later."
                }
            
            # Create download request
            request = DownloadRequest(
                user_id=user_id,
                username=ctx.author.display_name,
                url=url,
                platform=self._get_platform_from_url(url),
                quality=quality,
                ctx=ctx,
                timestamp=datetime.now(),
                priority=priority
            )
            
            # Add to queue (sorted by priority)
            self._insert_sorted(request)
            
            # Update user history
            await self._update_user_history(user_id)
            
            # Process queue if we can start more downloads
            if self.active_downloads < self.max_concurrent:
                asyncio.create_task(self._process_queue())
            
            return {
                "status": "queued",
                "position": len(self.queue),
                "message": f"Added to download queue (position: {len(self.queue)})"
            }
    
    def _insert_sorted(self, request: DownloadRequest):
        """Insert request into queue sorted by priority"""
        # Find position to insert based on priority
        insert_pos = 0
        for i, existing_request in enumerate(self.queue):
            if request.priority > existing_request.priority:
                insert_pos = i
                break
            elif request.priority == existing_request.priority:
                # Same priority, insert after existing ones
                insert_pos = i + 1
        
        # Insert at the found position
        self.queue.insert(insert_pos, request)
    
    def _get_platform_from_url(self, url: str) -> str:
        """Extract platform from URL"""
        return PlatformDetector.get_platform(url)
    
    async def _is_user_spamming(self, user_id: int) -> bool:
        """Check if user is making too many requests"""
        if user_id not in self.download_history:
            return False
        
        recent_requests = self.download_history[user_id]
        now = datetime.now()
        
        # Remove requests older than rate limit window
        recent_requests = [req for req in recent_requests 
                         if (now - req).total_seconds() < QueueSettings.RATE_LIMIT_WINDOW]
        
        # Update history
        self.download_history[user_id] = recent_requests
        
        # Check rate limit
        return len(recent_requests) >= QueueSettings.RATE_LIMIT_REQUESTS
    
    async def _update_user_history(self, user_id: int):
        """Update user's download history"""
        if user_id not in self.download_history:
            self.download_history[user_id] = []
        
        self.download_history[user_id].append(datetime.now())
    
    async def _process_queue(self):
        """Process the download queue"""
        while True:
            async with self.lock:
                if not self.queue or self.active_downloads >= self.max_concurrent:
                    break
                
                request = self.queue.popleft()
                self.active_downloads += 1
            
            try:
                # Start download process
                await self._handle_download(request)
            except Exception as e:
                logger.error(f"Error processing download for {request.username}: {e}")
                await request.ctx.send(f"❌ Error processing your download: {str(e)}")
            finally:
                async with self.lock:
                    self.active_downloads -= 1
    
    async def _handle_download(self, request: DownloadRequest):
        """Handle a single download request"""
        # Send initial status
        embed = self._create_status_embed("🔄 Processing", 
                                        f"Analyzing content from {request.platform}...", 
                                        position=0)
        message = await request.ctx.send(embed=embed)
        
        try:
            # Detect content type first
            content_info = await ContentDetector.detect_content_type(request.url)
            content_type = content_info.get('content_type', 'unknown')
            confidence = content_info.get('confidence', 0.0)
            
            # Update status with content type detection
            content_emoji = ContentDetector.get_content_type_emoji(content_type)
            content_name = ContentDetector.get_content_type_name(content_type)
            
            embed = self._create_status_embed("📊 Content Detected", 
                                            f"Detected: {content_emoji} {content_name}\nConfidence: {confidence:.1%}", 
                                            position=0)
            await message.edit(embed=embed)
            
            filename = None
            title = None
            downloader = None
            final_content_type = None
            
            # Handle different content types
            if content_type in ['image', 'gallery']:
                # Try image download first
                logger.info(f"Attempting image download for {content_type}: {request.url}")
                filename, title, error = await self.image_downloader.download_image(request.url)
                if filename:
                    downloader = self.image_downloader
                    final_content_type = content_type
                else:
                    # Fallback to video if image fails
                    logger.info(f"Image download failed, trying video: {request.url}")
                    filename, title, error = await self.video_downloader.download_video(request.url, request.quality)
                    if filename:
                        downloader = self.video_downloader
                        final_content_type = 'video'
            
            elif content_type in ['video', 'reel', 'story']:
                # Try video download
                logger.info(f"Attempting video download for {content_type}: {request.url}")
                filename, title, error = await self.video_downloader.download_video(request.url, request.quality)
                if filename:
                    downloader = self.video_downloader
                    final_content_type = content_type
                else:
                    # Fallback to image if video fails
                    logger.info(f"Video download failed, trying image: {request.url}")
                    filename, title, error = await self.image_downloader.download_image(request.url)
                    if filename:
                        downloader = self.image_downloader
                        final_content_type = 'image'
            
            elif content_type == 'thread':
                # For threads, try both approaches
                logger.info(f"Attempting thread download: {request.url}")
                filename, title, error = await self.video_downloader.download_video(request.url, request.quality)
                if filename:
                    downloader = self.video_downloader
                    final_content_type = 'thread'
                else:
                    filename, title, error = await self.image_downloader.download_image(request.url)
                    if filename:
                        downloader = self.image_downloader
                        final_content_type = 'thread'
            
            else:
                # For unknown content, try both approaches
                logger.info(f"Unknown content type, trying both approaches: {request.url}")
                filename, title, error = await self.image_downloader.download_image(request.url)
                if filename:
                    downloader = self.image_downloader
                    final_content_type = 'image'
                else:
                    filename, title, error = await self.video_downloader.download_video(request.url, request.quality)
                    if filename:
                        downloader = self.video_downloader
                        final_content_type = 'video'
            
            if filename:
                # Send the file
                with open(filename, 'rb') as f:
                    import discord
                    file = discord.File(f, filename=os.path.basename(filename))
                    
                    # Create detailed success message
                    final_emoji = ContentDetector.get_content_type_emoji(final_content_type)
                    final_name = ContentDetector.get_content_type_name(final_content_type)
                    
                    embed = self._create_status_embed(
                        f"✅ {final_emoji} {final_name} Download Complete", 
                        f"**{title}**\n\nPlatform: {request.platform.title()}\nContent Type: {final_name}\nDetected: {content_name}"
                    )
                    await message.edit(embed=embed)
                    await request.ctx.send(file=file)
                
                # Clean up
                await downloader.cleanup_file(filename)
                
            else:
                # Download failed - provide more specific error messages
                error_message = f"Could not download {content_name} from {request.platform.title()}"
                
                # Add platform-specific error details
                if request.platform == 'facebook':
                    if content_info.get('fallback_detection'):
                        error_message += "\n\n**Note:** This Facebook post may be private, deleted, or require authentication."
                    else:
                        error_message += "\n\n**Note:** Facebook content extraction failed. The post may be private or unavailable."
                elif request.platform == 'instagram':
                    error_message += "\n\n**Note:** Instagram content may be private or require authentication."
                elif request.platform == 'twitter':
                    error_message += "\n\n**Note:** Twitter content may be private or require authentication."
                
                embed = self._create_status_embed("❌ Download Failed", error_message)
                await message.edit(embed=embed)
                
        except Exception as e:
            logger.error(f"Download failed for {request.username}: {e}")
            embed = self._create_status_embed("❌ Error", f"Download failed: {str(e)}")
            await message.edit(embed=embed)
    
    def _create_status_embed(self, title: str, description: str, position: int = None):
        """Create a status embed"""
        import discord
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x00ff00 if "Complete" in title else 0xff0000 if "Failed" in title or "Error" in title else 0xffff00
        )
        
        if position is not None:
            embed.add_field(name="Queue Position", value=f"#{position}", inline=True)
        
        return embed
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        async with self.lock:
            return {
                "active_downloads": self.active_downloads,
                "queue_size": len(self.queue),
                "max_concurrent": self.max_concurrent,
                "max_queue_size": self.max_queue_size
            }
    
    async def get_user_position(self, user_id: int) -> Optional[int]:
        """Get user's position in queue"""
        async with self.lock:
            for i, request in enumerate(self.queue):
                if request.user_id == user_id:
                    return i + 1
            return None
    
    async def get_next_item(self) -> Optional[Dict[str, Any]]:
        """Get the next item from the queue"""
        async with self.lock:
            if not self.queue:
                return None
            
            request = self.queue.popleft()
            return {
                'user_id': request.user_id,
                'username': request.username,
                'url': request.url,
                'platform': request.platform,
                'quality': request.quality,
                'ctx': request.ctx,
                'content_type': getattr(request, 'content_type', 'unknown')
            }
    
    async def cancel_user_downloads(self, user_id: int) -> int:
        """Cancel all downloads for a user"""
        async with self.lock:
            original_length = len(self.queue)
            self.queue = deque([req for req in self.queue if req.user_id != user_id])
            return original_length - len(self.queue) 