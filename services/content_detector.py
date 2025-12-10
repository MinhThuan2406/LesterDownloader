"""
Content type detection service for determining if a URL contains video, image, or other content
"""

import yt_dlp
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
import re

from core.logging import get_logger
from utils.platforms import PlatformDetector

logger = get_logger(__name__)

class ContentDetector:
    """Service for detecting content types from URLs"""
    
    @staticmethod
    async def detect_content_type(url: str) -> Dict[str, Any]:
        """
        Detect the content type of a URL
        
        Args:
            url: The URL to analyze
            
        Returns:
            Dictionary with content type information
        """
        platform = PlatformDetector.get_platform(url)
        
        # Configure yt-dlp for info extraction only
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'no_color': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US'
        }
        
        # Platform-specific settings
        if platform == 'facebook':
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ydl_opts['http_headers'] = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            # Add Facebook-specific extractor arguments
            ydl_opts['extractor_args'] = {
                'facebook': {
                    'skip': ['dash', 'hls'],
                }
            }
        elif platform == 'instagram':
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        elif platform == 'twitter':
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        elif platform == 'reddit':
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info without downloading
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                
                if not info:
                    # For Facebook, try fallback detection based on URL patterns
                    if platform == 'facebook':
                        return ContentDetector._facebook_fallback_detection(url)
                    return {
                        'content_type': 'unknown',
                        'platform': platform,
                        'error': 'Could not extract information'
                    }
                
                # Analyze the content type based on available formats and metadata
                content_type = ContentDetector._analyze_content_type(info, platform)
                
                return {
                    'content_type': content_type,
                    'platform': platform,
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration'),
                    'formats': info.get('formats', []),
                    'thumbnail': info.get('thumbnail'),
                    'view_count': info.get('view_count'),
                    'upload_date': info.get('upload_date'),
                    'description': info.get('description', ''),
                    'confidence': ContentDetector._calculate_confidence(info, content_type)
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error detecting content type for {url}: {error_msg}")
            
            # For Facebook, provide specific error handling
            if platform == 'facebook':
                return ContentDetector._handle_facebook_error(url, error_msg)
            
            # For other platforms, try fallback detection
            if platform == 'facebook':
                return ContentDetector._facebook_fallback_detection(url)
            
            return {
                'content_type': 'unknown',
                'platform': platform,
                'error': error_msg,
                'confidence': 0.0
            }
    
    @staticmethod
    def _handle_facebook_error(url: str, error_msg: str) -> Dict[str, Any]:
        """
        Handle Facebook-specific errors and provide better error messages
        
        Args:
            url: Facebook URL
            error_msg: Error message from yt-dlp
            
        Returns:
            Dictionary with error information and fallback detection
        """
        # Check for specific Facebook error patterns
        if 'No video formats found' in error_msg:
            # This usually means the post is private or requires authentication
            return {
                'content_type': 'unknown',
                'platform': 'facebook',
                'title': 'Facebook Post',
                'uploader': 'Unknown',
                'duration': None,
                'formats': [],
                'thumbnail': None,
                'view_count': None,
                'upload_date': None,
                'description': '',
                'confidence': 0.0,
                'fallback_detection': True,
                'error': 'This Facebook post may be private, deleted, or require authentication. Only public posts can be downloaded.',
                'error_type': 'private_post'
            }
        elif 'pfbid' in error_msg:
            # Facebook post ID format error
            return {
                'content_type': 'unknown',
                'platform': 'facebook',
                'title': 'Facebook Post',
                'uploader': 'Unknown',
                'duration': None,
                'formats': [],
                'thumbnail': None,
                'view_count': None,
                'upload_date': None,
                'description': '',
                'confidence': 0.0,
                'fallback_detection': True,
                'error': 'This Facebook post format is not supported or the post may be private.',
                'error_type': 'unsupported_format'
            }
        else:
            # Generic Facebook error
            return {
                'content_type': 'unknown',
                'platform': 'facebook',
                'title': 'Facebook Post',
                'uploader': 'Unknown',
                'duration': None,
                'formats': [],
                'thumbnail': None,
                'view_count': None,
                'upload_date': None,
                'description': '',
                'confidence': 0.0,
                'fallback_detection': True,
                'error': f'Facebook download failed: {error_msg}',
                'error_type': 'generic_error'
            }
    
    @staticmethod
    def _facebook_fallback_detection(url: str) -> Dict[str, Any]:
        """
        Fallback content detection for Facebook when yt-dlp fails
        
        Args:
            url: Facebook URL
            
        Returns:
            Dictionary with fallback content type information
        """
        # Analyze URL patterns to make educated guesses
        url_lower = url.lower()
        
        # Check for common Facebook URL patterns
        if '/photos/' in url_lower or '/photo/' in url_lower:
            content_type = 'gallery'
            confidence = 0.7
        elif '/videos/' in url_lower or '/video/' in url_lower:
            content_type = 'video'
            confidence = 0.7
        elif '/reels/' in url_lower or '/reel/' in url_lower:
            content_type = 'reel'
            confidence = 0.8
        elif '/stories/' in url_lower or '/story/' in url_lower:
            content_type = 'story'
            confidence = 0.8
        else:
            # Default to image for general posts
            content_type = 'image'
            confidence = 0.5
        
        return {
            'content_type': content_type,
            'platform': 'facebook',
            'title': 'Facebook Post',
            'uploader': 'Unknown',
            'duration': None,
            'formats': [],
            'thumbnail': None,
            'view_count': None,
            'upload_date': None,
            'description': '',
            'confidence': confidence,
            'fallback_detection': True,
            'error': 'yt-dlp extraction failed, using URL pattern analysis'
        }
    
    @staticmethod
    def _analyze_content_type(info: Dict[str, Any], platform: str) -> str:
        """
        Analyze the content type based on available information
        
        Args:
            info: yt-dlp info dictionary
            platform: Platform name
            
        Returns:
            Content type: 'video', 'image', 'gallery', 'story', 'reel', 'unknown'
        """
        formats = info.get('formats', [])
        duration = info.get('duration')
        title = info.get('title', '').lower()
        description = info.get('description', '').lower()
        
        # Platform-specific detection
        if platform == 'instagram':
            return ContentDetector._detect_instagram_content(title, description, duration, formats)
        elif platform == 'facebook':
            return ContentDetector._detect_facebook_content(title, description, duration, formats)
        elif platform == 'twitter':
            return ContentDetector._detect_twitter_content(title, description, duration, formats)
        elif platform == 'reddit':
            return ContentDetector._detect_reddit_content(title, description, duration, formats)
        else:
            return ContentDetector._detect_generic_content(duration, formats)
    
    @staticmethod
    def _detect_instagram_content(title: str, description: str, duration: Optional[int], formats: list) -> str:
        """Detect Instagram content type"""
        # Instagram-specific keywords
        if any(keyword in title for keyword in ['story', 'stories']):
            return 'story'
        elif any(keyword in title for keyword in ['reel', 'reels']):
            return 'reel'
        elif any(keyword in title for keyword in ['carousel', 'gallery', 'multiple']):
            return 'gallery'
        elif duration and duration > 0:
            return 'video'
        else:
            return 'image'
    
    @staticmethod
    def _detect_facebook_content(title: str, description: str, duration: Optional[int], formats: list) -> str:
        """Detect Facebook content type"""
        # Facebook-specific keywords
        if any(keyword in title for keyword in ['album', 'gallery', 'photos']):
            return 'gallery'
        elif duration and duration > 0:
            return 'video'
        else:
            return 'image'
    
    @staticmethod
    def _detect_twitter_content(title: str, description: str, duration: Optional[int], formats: list) -> str:
        """Detect Twitter content type"""
        # Twitter-specific keywords
        if duration and duration > 0:
            return 'video'
        else:
            return 'image'
    
    @staticmethod
    def _detect_reddit_content(title: str, description: str, duration: Optional[int], formats: list) -> str:
        """Detect Reddit content type"""
        # Reddit-specific keywords
        if duration and duration > 0:
            return 'video'
        else:
            return 'image'
    
    @staticmethod
    def _detect_generic_content(duration: Optional[int], formats: list) -> str:
        """Detect generic content type"""
        if duration and duration > 0:
            return 'video'
        else:
            return 'image'
    
    @staticmethod
    def _calculate_confidence(info: Dict[str, Any], content_type: str) -> float:
        """
        Calculate confidence level for content type detection
        
        Args:
            info: yt-dlp info dictionary
            content_type: Detected content type
            
        Returns:
            Confidence level (0.0 to 1.0)
        """
        formats = info.get('formats', [])
        duration = info.get('duration')
        title = info.get('title', '')
        description = info.get('description', '')
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on available information
        if formats:
            confidence += 0.2
        
        if duration and duration > 0:
            confidence += 0.1
        
        if title and title != 'Unknown':
            confidence += 0.1
        
        if description:
            confidence += 0.1
        
        # Platform-specific confidence adjustments
        platform = info.get('extractor', '').lower()
        if platform in ['facebook', 'instagram', 'twitter', 'reddit']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    @staticmethod
    def get_content_type_emoji(content_type: str) -> str:
        """Get emoji for content type"""
        emoji_map = {
            'video': '🎥',
            'image': '🖼️',
            'gallery': '📷',
            'story': '📱',
            'reel': '🎬',
            'unknown': '❓'
        }
        return emoji_map.get(content_type, '❓')
    
    @staticmethod
    def get_content_type_name(content_type: str) -> str:
        """Get human-readable name for content type"""
        name_map = {
            'video': 'Video',
            'image': 'Image',
            'gallery': 'Gallery',
            'story': 'Story',
            'reel': 'Reel',
            'unknown': 'Unknown'
        }
        return name_map.get(content_type, 'Unknown')
