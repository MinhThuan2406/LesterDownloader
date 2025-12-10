"""
Image downloader service for downloading images from various platforms
"""

import yt_dlp
import asyncio
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import re

from core.logging import get_logger
from core.config import DiscordLimits
from utils.platforms import PlatformDetector

logger = get_logger(__name__)

class ImageDownloader:
    """Core image downloader service using yt-dlp"""
    
    def __init__(self, download_path: str = "downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        self.max_file_size = DiscordLimits.MAX_FILE_SIZE
    
    def is_supported_url(self, url: str) -> bool:
        """Check if URL is from a supported image platform"""
        return PlatformDetector.is_image_platform(url)
    
    def get_platform(self, url: str) -> str:
        """Get the platform from URL"""
        return PlatformDetector.get_platform(url)
    
    async def download_image(self, url: str) -> Tuple[Optional[str], str, Optional[str]]:
        """
        Download image from supported platforms
        
        Args:
            url: Image URL
            
        Returns:
            Tuple of (filepath, title, error_message)
        """
        if not self.is_supported_url(url):
            return None, "Unknown", "Unsupported image platform"
        
        platform = self.get_platform(url)
        logger.info(f"Downloading image from {platform}: {url}")
        
        # Configure yt-dlp options for image download
        ydl_opts = {
            'outtmpl': str(self.download_path / f'{platform}_%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'postprocessors': [],
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_color': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US'
        }
        
        # Platform-specific settings
        if platform == 'facebook':
            # Facebook often has issues, add user-agent and headers
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ydl_opts['http_headers'] = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            # Try to extract images specifically
            ydl_opts['extractor_args'] = {
                'facebook': {
                    'skip': ['dash', 'hls'],
                }
            }
        elif platform == 'instagram':
            # Instagram-specific settings
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ydl_opts['http_headers'] = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        elif platform == 'twitter':
            # Twitter-specific settings
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ydl_opts['http_headers'] = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        elif platform == 'reddit':
            # Reddit-specific settings
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ydl_opts['http_headers'] = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        
        try:
            # Run download in thread to avoid blocking
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                
                if not info:
                    return None, "Unknown", "Could not extract image information"
                
                # Download the image
                await asyncio.to_thread(ydl.download, [url])
                
                # Get the downloaded file path
                filename = ydl.prepare_filename(info)
                
                # Check if file exists and get its size
                if not os.path.exists(filename):
                    return None, "Unknown", "Download failed - file not found"
                
                file_size = os.path.getsize(filename)
                if file_size > self.max_file_size:
                    # Clean up large file
                    os.remove(filename)
                    return None, "Unknown", f"Image too large ({file_size // 1024 // 1024}MB > 8MB)"
                
                title = info.get('title', 'Unknown Title')
                # Clean title for filename
                title = re.sub(r'[<>:"/\\|?*]', '', title)[:100]
                
                return filename, title, None
                
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            logger.error(f"Download error for {url}: {e}")
            
            # Provide more specific error messages for Facebook
            if platform == 'facebook' and 'No video formats found' in error_msg:
                return None, "Unknown", "Facebook content extraction failed. The post may be private, deleted, or require authentication."
            elif platform == 'facebook':
                return None, "Unknown", f"Facebook download failed: {error_msg}"
            else:
                return None, "Unknown", f"Download failed: {error_msg}"
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return None, "Unknown", f"Unexpected error: {str(e)}"
    
    async def cleanup_file(self, filepath: str):
        """Clean up downloaded file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                # Use repr() to safely log the filename with Unicode characters
                logger.info(f"Cleaned up: {repr(filepath)}")
        except Exception as e:
            logger.error(f"Error cleaning up {repr(filepath)}: {e}")
    
    async def get_image_info(self, url: str) -> Dict[str, Any]:
        """Get image information without downloading"""
        if not self.is_supported_url(url):
            return {"error": "Unsupported image platform"}
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                
                if not info:
                    return {"error": "Could not extract image information"}
                
                return {
                    "title": info.get('title', 'Unknown'),
                    "uploader": info.get('uploader', 'Unknown'),
                    "platform": self.get_platform(url),
                    "thumbnail": info.get('thumbnail'),
                    "view_count": info.get('view_count', 0),
                    "upload_date": info.get('upload_date', ''),
                    "description": info.get('description', '')[:200] + "..." if info.get('description', '') else ''
                }
                
        except Exception as e:
            logger.error(f"Error getting info for {url}: {e}")
            return {"error": f"Error getting image info: {str(e)}"}
    
    def get_supported_platforms(self) -> Dict[str, str]:
        """Get list of supported image platforms"""
        return PlatformDetector.get_image_platforms() 