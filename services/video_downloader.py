import yt_dlp
import asyncio
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import aiofiles
import re

from core.config import DiscordLimits, Platforms
from core.logging import get_logger
from utils.platforms import PlatformDetector

logger = get_logger(__name__)

class VideoDownloader:
    """Core video downloader service using yt-dlp"""
    
    def __init__(self, download_path: str = "downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        self.max_file_size = DiscordLimits.MAX_FILE_SIZE
        self.supported_platforms = Platforms.SUPPORTED_PLATFORMS
    
    def is_supported_url(self, url: str) -> bool:
        """Check if URL is from a supported platform"""
        return PlatformDetector.is_supported_url(url)
    
    def get_platform(self, url: str) -> str:
        """Get the platform from URL"""
        return PlatformDetector.get_platform(url)
    
    async def download_video(self, url: str, quality: str = "best[height<=720]") -> Tuple[Optional[str], str, Optional[str]]:
        """
        Download video from supported platforms
        
        Args:
            url: Video URL
            quality: Video quality preference
            
        Returns:
            Tuple of (filepath, title, error_message)
        """
        if not self.is_supported_url(url):
            return None, "Unknown", "Unsupported platform"
        
        platform = self.get_platform(url)
        logger.info(f"Downloading from {platform}: {url}")
        
        # Configure yt-dlp options with platform-specific settings
        ydl_opts = {
            'outtmpl': str(self.download_path / f'{platform}_%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'audioformat': 'mp3',
            'postprocessors': [],
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_color': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US'
        }
        
        # Platform-specific format selection with enhanced quality options
        if quality == 'small':
            # Optimized for Discord (under 8MB)
            if platform == 'tiktok':
                ydl_opts['format'] = 'best[height<=480]/best[height<=720]/best'
            else:
                ydl_opts['format'] = 'best[height<=480]/best[height<=720]/best'
        elif quality in ['720p', '480p', '360p']:
            # Specific resolution
            height = quality.replace('p', '')
            ydl_opts['format'] = f'best[height<={height}]/best'
        elif platform == 'tiktok':
            # TikTok often has issues with specific formats, use best available
            ydl_opts['format'] = 'best[height<=720]/best'
        elif platform == 'instagram':
            # Instagram works better with best quality
            ydl_opts['format'] = 'best[height<=720]/best'
        elif platform == 'facebook':
            # Facebook often has issues, try multiple formats and add user-agent
            ydl_opts['format'] = 'best[height<=720]/best[ext=mp4]/best'
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ydl_opts['extractor_args'] = {
                'facebook': {
                    'skip': ['dash', 'hls'],  # Skip problematic formats
                }
            }
            # Add additional headers for better Facebook compatibility
            ydl_opts['http_headers'] = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        else:
            # Default quality setting
            ydl_opts['format'] = quality
        
        try:
            # Create yt-dlp instance
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            
            # Get video info first
            info = await asyncio.get_event_loop().run_in_executor(
                None, ydl.extract_info, url, False
            )
            
            if not info:
                return None, "Unknown", "Failed to extract video information"
            
            # Download the video
            result = await asyncio.get_event_loop().run_in_executor(
                None, ydl.download, [url]
            )
            
            if result != 0:
                return None, info.get('title', 'Unknown'), "Download failed"
            
            # Find the downloaded file
            downloaded_file = None
            for file in self.download_path.iterdir():
                if file.is_file() and platform in file.name:
                    downloaded_file = file
                    break
            
            if not downloaded_file or not downloaded_file.exists():
                return None, info.get('title', 'Unknown'), "Downloaded file not found"
            
            # Check file size
            file_size = downloaded_file.stat().st_size
            if file_size > self.max_file_size:
                # Clean up oversized file
                downloaded_file.unlink()
                return None, info.get('title', 'Unknown'), f"File too large ({file_size} bytes, max {self.max_file_size})"
            
            return str(downloaded_file), info.get('title', 'Unknown'), None
            
        except Exception as e:
            logger.error(f"Error downloading video from {platform}: {e}")
            return None, "Unknown", str(e)
    
    async def cleanup_file(self, filepath: str):
        """Clean up downloaded file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Cleaned up file: {filepath}")
        except Exception as e:
            logger.error(f"Error cleaning up file {filepath}: {e}")
    
    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get video information without downloading
        
        Args:
            url: Video URL
            
        Returns:
            Dictionary with video information
        """
        if not self.is_supported_url(url):
            return {}
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_color': True
        }
        
        try:
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = await asyncio.get_event_loop().run_in_executor(
                None, ydl.extract_info, url, False
            )
            
            if not info:
                return {}
            
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'filesize': info.get('filesize', 0),
                'platform': self.get_platform(url),
                'thumbnail': info.get('thumbnail'),
                'description': info.get('description', ''),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
    
    def get_supported_platforms(self) -> Dict[str, str]:
        """Get supported platforms"""
        return self.supported_platforms
    
    async def get_available_formats(self, url: str) -> Dict[str, Any]:
        """
        Get available formats for a video
        
        Args:
            url: Video URL
            
        Returns:
            Dictionary with available formats
        """
        if not self.is_supported_url(url):
            return {}
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'listformats': True
        }
        
        try:
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = await asyncio.get_event_loop().run_in_executor(
                None, ydl.extract_info, url, False
            )
            
            if not info:
                return {}
            
            formats = info.get('formats', [])
            if not formats:
                return {}
            
            # Filter and format the formats
            available_formats = []
            for fmt in formats:
                if fmt.get('format_id') and fmt.get('ext'):
                    available_formats.append({
                        'format_id': fmt['format_id'],
                        'ext': fmt['ext'],
                        'resolution': fmt.get('resolution', 'N/A'),
                        'filesize': fmt.get('filesize', 0),
                        'fps': fmt.get('fps'),
                        'vcodec': fmt.get('vcodec'),
                        'acodec': fmt.get('acodec')
                    })
            
            return {
                'title': info.get('title', 'Unknown'),
                'formats': available_formats
            }
            
        except Exception as e:
            logger.error(f"Error getting available formats: {e}")
            return {} 