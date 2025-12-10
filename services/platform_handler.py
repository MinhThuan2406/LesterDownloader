"""
Comprehensive platform handler for all major social media platforms
"""

import yt_dlp
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, List
from urllib.parse import urlparse
import re

from core.logging import get_logger
from core.config import BotConfig, PlatformSettings, EthicalGuidelines, ContentPolicies
from utils.platforms import PlatformDetector

logger = get_logger(__name__)

class PlatformHandler:
    """Comprehensive platform handler with ethical and legal compliance"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.platform_settings = config.platform_settings
        self.ethical_guidelines = config.ethical_guidelines
        self.content_policies = config.content_policies
    
    async def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate URL and check if it's supported and allowed
        
        Args:
            url: URL to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            logger.info(f"Starting validate_url for: {url}")
            
            # Check if URL is from supported platform
            platform = PlatformDetector.get_platform(url)
            logger.info(f"Platform detected: {platform}")
            
            if not platform or platform == "unknown":
                logger.info(f"Unsupported platform: {platform}")
                return {
                    'valid': False,
                    'error': 'Unsupported platform',
                    'platform': None
                }
        
            # Check content policies
            logger.info(f"Checking content policies for platform: {platform}")
            if not self.config.is_content_allowed(url):
                logger.info(f"Content not allowed by policy for: {url}")
                return {
                    'valid': False,
                    'error': 'Content not allowed by policy',
                    'platform': platform
                }
            
            # Get platform settings
            platform_settings = self.config.get_platform_settings(platform)
            logger.debug(f"Platform settings for {platform}: {platform_settings}")
            if not platform_settings:
                return {
                    'valid': False,
                    'error': f'Platform {platform} not configured',
                    'platform': platform
                }
            
            # Check if URL pattern suggests private content
            if self._is_private_content(url, platform):
                return {
                    'valid': False,
                    'error': f'Private content not supported for {platform}',
                    'platform': platform,
                    'reason': 'private_content'
                }
            
            return {
                'valid': True,
                'platform': platform,
                'settings': platform_settings
            }
        except Exception as e:
            logger.error(f"Error in validate_url for {url}: {e}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}',
                'platform': None
            }
    
    def _is_private_content(self, url: str, platform: str) -> bool:
        """
        Check if URL suggests private content based on patterns
        
        Args:
            url: URL to check
            platform: Platform name
            
        Returns:
            True if content appears to be private
        """
        url_lower = url.lower()
        
        if platform == 'facebook':
            # Facebook private content patterns
            private_patterns = [
                '/friends/', '/family/', '/private/',
                'story_fbid', 'permalink', 'photo.php'
            ]
            return any(pattern in url_lower for pattern in private_patterns)
        
        elif platform == 'instagram':
            # Instagram private content patterns
            private_patterns = [
                '/stories/', '/story/', '/highlights/',
                'private', 'close_friends'
            ]
            return any(pattern in url_lower for pattern in private_patterns)
        
        elif platform == 'twitter':
            # Twitter private content patterns
            private_patterns = [
                '/status/', 'protected', 'private'
            ]
            return any(pattern in url_lower for pattern in private_patterns)
        
        elif platform == 'tiktok':
            # TikTok private content patterns
            private_patterns = [
                '/private/', 'private_video'
            ]
            return any(pattern in url_lower for pattern in private_patterns)
        
        return False
    
    async def get_content_info(self, url: str) -> Dict[str, Any]:
        """
        Get comprehensive content information
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary with content information
        """
        # Validate URL first
        validation = await self.validate_url(url)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['error'],
                'platform': validation.get('platform'),
                'reason': validation.get('reason')
            }
        
        platform = validation['platform']
        platform_settings = validation['settings']
        
        # Configure yt-dlp for this platform
        ydl_opts = self._get_platform_ydl_opts(platform, platform_settings)
        
        try:
            logger.info(f"Attempting to extract info from {url} with platform {platform}")
            logger.debug(f"yt-dlp options: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info without downloading
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                
                if not info:
                    logger.warning(f"No info extracted from {url}")
                    return {
                        'success': False,
                        'error': 'Could not extract information',
                        'platform': platform,
                        'reason': 'extraction_failed'
                    }
                
                # Analyze content type and metadata
                content_analysis = self._analyze_content(info, platform)
                
                # Check content policies
                if not self._check_content_policies(info, content_analysis):
                    return {
                        'success': False,
                        'error': 'Content violates policies',
                        'platform': platform,
                        'reason': 'policy_violation'
                    }
                
                return {
                    'success': True,
                    'platform': platform,
                    'content_type': content_analysis['content_type'],
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration'),
                    'formats': info.get('formats', []),
                    'thumbnail': info.get('thumbnail'),
                    'view_count': info.get('view_count'),
                    'upload_date': info.get('upload_date'),
                    'description': info.get('description', ''),
                    'confidence': content_analysis['confidence'],
                    'metadata': content_analysis['metadata']
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error getting content info for {url}: {error_msg}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Handle platform-specific errors
            return self._handle_platform_error(url, platform, error_msg)
    
    def _get_platform_ydl_opts(self, platform: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Get yt-dlp options for specific platform"""
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'no_color': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'cookiesfrombrowser': None,
            'cookiefile': None,
            'cookies': None,
            'no_cookies': True
        }
        
        # Platform-specific options
        if platform == 'facebook':
            base_opts.update({
                'user_agent': settings.get('user_agent'),
                'http_headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                'extractor_args': {
                    'facebook': {
                        'skip': ['dash', 'hls'],
                    }
                }
            })
        
        elif platform == 'instagram':
            base_opts.update({
                'user_agent': settings.get('user_agent'),
                'extractor_args': {
                    'instagram': {
                        'skip': ['stories', 'highlights'],
                    }
                }
            })
        
        elif platform == 'twitter':
            base_opts.update({
                'user_agent': settings.get('user_agent'),
                'extractor_args': {
                    'twitter': {
                        'skip': ['spaces'],
                    }
                }
            })
        
        elif platform == 'tiktok':
            base_opts.update({
                'user_agent': settings.get('user_agent'),
                'extractor_args': {
                    'tiktok': {
                        'skip': ['live'],
                    }
                }
            })
        
        elif platform == 'youtube':
            base_opts.update({
                'user_agent': settings.get('user_agent'),
                'http_headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Referer': 'https://www.youtube.com/',
                    'Origin': 'https://www.youtube.com',
                },
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash'],
                        'player_client': ['android', 'web'],
                        'player_skip': ['webpage', 'configs'],
                    }
                },
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'extractor_retries': 3,
                'fragment_retries': 3,
                'retries': 3,
                'file_access_retries': 3,
                'sleep_interval': 1,
                'max_sleep_interval': 5,
                'sleep_interval_requests': 1,
                'max_sleep_interval_requests': 5,
                'cookiesfrombrowser': None,
                'cookiefile': None,
                'cookies': None,
                'no_cookies': True
            })
        
        elif platform == 'reddit':
            base_opts.update({
                'user_agent': settings.get('user_agent'),
                'extractor_args': {
                    'reddit': {
                        'skip': ['nsfw'],
                    }
                }
            })
        
        return base_opts
    
    def _analyze_content(self, info: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Analyze content type and extract metadata"""
        formats = info.get('formats', []) or []  # Ensure formats is never None
        duration = info.get('duration')
        title = info.get('title', '').lower()
        description = info.get('description', '').lower()
        
        # Determine content type
        content_type = self._determine_content_type(platform, title, description, duration, formats)
        
        # Calculate confidence
        confidence = self._calculate_confidence(info, content_type)
        
        # Extract metadata
        metadata = {
            'platform': platform,
            'content_type': content_type,
            'duration': duration,
            'file_size': info.get('filesize'),
            'resolution': self._get_best_resolution(formats),
            'format_count': len(formats),
            'has_audio': any(f.get('acodec') != 'none' for f in formats),
            'has_video': any(f.get('vcodec') != 'none' for f in formats),
            'uploader': info.get('uploader'),
            'view_count': info.get('view_count'),
            'like_count': info.get('like_count'),
            'comment_count': info.get('comment_count'),
            'upload_date': info.get('upload_date'),
            'tags': info.get('tags', []) or [],
            'categories': info.get('categories', []) or []
        }
        
        return {
            'content_type': content_type,
            'confidence': confidence,
            'metadata': metadata
        }
    
    def _determine_content_type(self, platform: str, title: str, description: str, duration: Optional[int], formats: list) -> str:
        """Determine content type based on platform and metadata"""
        
        if platform == 'instagram':
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
        
        elif platform == 'facebook':
            if any(keyword in title for keyword in ['album', 'gallery', 'photos']):
                return 'gallery'
            elif any(keyword in title for keyword in ['reel', 'reels']):
                return 'reel'
            elif duration and duration > 0:
                return 'video'
            else:
                return 'image'
        
        elif platform == 'twitter':
            if duration and duration > 0:
                return 'video'
            else:
                return 'image'
        
        elif platform == 'tiktok':
            return 'video'  # TikTok is primarily video
        
        elif platform == 'youtube':
            if duration and duration > 0:
                return 'video'
            else:
                return 'unknown'
        
        elif platform == 'reddit':
            if duration and duration > 0:
                return 'video'
            elif any(keyword in title for keyword in ['gallery', 'album']):
                return 'gallery'
            else:
                return 'image'
        
        else:
            # Generic detection
            if duration and duration > 0:
                return 'video'
            else:
                return 'image'
    
    def _calculate_confidence(self, info: Dict[str, Any], content_type: str) -> float:
        """Calculate confidence level for content type detection"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on available information
        formats = info.get('formats', []) or []
        if formats:
            confidence += 0.2
        
        if info.get('duration') and content_type == 'video':
            confidence += 0.2
        
        if info.get('title') and info.get('title') != 'Unknown':
            confidence += 0.1
        
        if info.get('description'):
            confidence += 0.1
        
        # Platform-specific confidence
        platform = info.get('extractor', '').lower()
        if platform in ['facebook', 'instagram', 'twitter', 'tiktok', 'youtube', 'reddit']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_best_resolution(self, formats: list) -> str:
        """Get the best available resolution"""
        if not formats:
            return 'Unknown'
        
        # Find formats with resolution info
        video_formats = [f for f in formats if f.get('resolution') and f.get('resolution') != 'audio only']
        
        if not video_formats:
            return 'Unknown'
        
        # Sort by resolution (height)
        video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
        
        best_format = video_formats[0]
        width = best_format.get('width', 0)
        height = best_format.get('height', 0)
        
        if width and height:
            return f"{width}x{height}"
        elif height:
            return f"{height}p"
        else:
            return 'Unknown'
    
    def _check_content_policies(self, info: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Check if content complies with policies"""
        title = info.get('title', '').lower()
        description = info.get('description', '').lower()
        tags = [tag.lower() for tag in (info.get('tags', []) or [])]
        
        # Check for blocked keywords
        all_text = f"{title} {description} {' '.join(tags)}"
        
        for keyword in self.content_policies.BLOCKED_KEYWORDS:
            if keyword in all_text:
                return False
        
        # Check content type
        content_type = analysis['content_type']
        if content_type in self.content_policies.BLOCKED_CONTENT_TYPES:
            return False
        
        # Check duration limits
        duration = info.get('duration', 0)
        if duration > self.content_policies.MAX_VIDEO_DURATION:
            return False
        
        return True
    
    def _handle_platform_error(self, url: str, platform: str, error_msg: str) -> Dict[str, Any]:
        """Handle platform-specific errors"""
        
        if platform == 'facebook':
            if 'No video formats found' in error_msg:
                return {
                    'success': False,
                    'error': 'This Facebook post could not be downloaded due to technical limitations.',
                    'platform': platform,
                    'reason': 'technical_limitation',
                    'details': 'The post may be using a format not supported by the downloader, or there may be temporary access issues.'
                }
            elif 'pfbid' in error_msg:
                return {
                    'success': False,
                    'error': 'This Facebook post format is not currently supported.',
                    'platform': platform,
                    'reason': 'unsupported_format',
                    'details': 'Facebook occasionally uses new formats that the downloader has not yet implemented.'
                }
            elif 'Login required' in error_msg or 'private' in error_msg.lower():
                return {
                    'success': False,
                    'error': 'This Facebook post requires authentication or is private.',
                    'platform': platform,
                    'reason': 'private_content',
                    'details': 'Only public posts are supported. Private posts, friends-only posts, and posts requiring login cannot be downloaded.'
                }
        
        elif platform == 'instagram':
            if 'Login required' in error_msg:
                return {
                    'success': False,
                    'error': 'This Instagram content requires login or is private.',
                    'platform': platform,
                    'reason': 'private_content'
                }
        
        elif platform == 'twitter':
            if 'protected' in error_msg:
                return {
                    'success': False,
                    'error': 'This Twitter account is protected.',
                    'platform': platform,
                    'reason': 'protected_account'
                }
        
        elif platform == 'youtube':
            if 'Could not copy Chrome cookie database' in error_msg:
                return {
                    'success': False,
                    'error': 'Browser cookie access failed. This is a technical limitation.',
                    'platform': platform,
                    'reason': 'technical_limitation',
                    'details': 'The downloader cannot access browser cookies. This is normal and should not affect most downloads.'
                }
            elif 'HTTP Error 403' in error_msg or 'Forbidden' in error_msg:
                return {
                    'success': False,
                    'error': 'YouTube is blocking this request. This may be due to rate limiting or anti-bot measures.',
                    'platform': platform,
                    'reason': 'rate_limited',
                    'details': 'Try again later or use a different YouTube URL. YouTube occasionally blocks requests to prevent automated access.'
                }
            elif 'Video unavailable' in error_msg:
                return {
                    'success': False,
                    'error': 'This YouTube video is unavailable or has been removed.',
                    'platform': platform,
                    'reason': 'content_unavailable'
                }
            elif 'Private video' in error_msg:
                return {
                    'success': False,
                    'error': 'This YouTube video is private and cannot be accessed.',
                    'platform': platform,
                    'reason': 'private_content'
                }
        
        # Generic error handling
        return {
            'success': False,
            'error': f'Download failed: {error_msg}',
            'platform': platform,
            'reason': 'generic_error'
        }
    
    def get_platform_help(self, platform: str) -> Dict[str, Any]:
        """Get help information for a specific platform"""
        platform_settings = self.config.get_platform_settings(platform)
        
        if not platform_settings:
            return {
                'supported': False,
                'error': f'Platform {platform} not configured'
            }
        
        return {
            'supported': True,
            'platform': platform,
            'settings': platform_settings,
            'limitations': self._get_platform_limitations(platform),
            'tips': self._get_platform_tips(platform)
        }
    
    def _get_platform_limitations(self, platform: str) -> List[str]:
        """Get limitations for a specific platform"""
        limitations = {
            'facebook': [
                'Only public posts are supported',
                'Private posts (Friends Only) are not supported',
                'Posts from private groups are not supported',
                'Stories are not supported',
                'Posts requiring login are not supported'
            ],
            'instagram': [
                'Only public posts are supported',
                'Private accounts are not supported',
                'Stories are not supported',
                'Highlights are not supported',
                'Posts requiring login are not supported'
            ],
            'twitter': [
                'Only public posts are supported',
                'Protected accounts are not supported',
                'Spaces (live audio) are not supported',
                'Posts requiring login are not supported'
            ],
            'tiktok': [
                'Only public videos are supported',
                'Private videos are not supported',
                'Live streams are not supported',
                'Videos requiring login are not supported'
            ],
            'youtube': [
                'Only public videos are supported',
                'Private videos are not supported',
                'Age-restricted content may not work',
                'Videos requiring login are not supported'
            ],
            'reddit': [
                'Only public posts are supported',
                'Private subreddits are not supported',
                'NSFW content is blocked',
                'Posts requiring login are not supported'
            ]
        }
        
        return limitations.get(platform, ['Platform limitations not specified'])
    
    def _get_platform_tips(self, platform: str) -> List[str]:
        """Get tips for a specific platform"""
        tips = {
            'facebook': [
                'Use public posts only',
                'Try posts from public pages',
                'Use direct links to media when possible',
                'Check if the post is still available'
            ],
            'instagram': [
                'Use public accounts only',
                'Try posts from public profiles',
                'Use direct links to media when possible',
                'Check if the post is still available'
            ],
            'twitter': [
                'Use public accounts only',
                'Try posts from public profiles',
                'Use direct links to media when possible',
                'Check if the post is still available'
            ],
            'tiktok': [
                'Use public videos only',
                'Try videos from public accounts',
                'Use direct links to videos when possible',
                'Check if the video is still available'
            ],
            'youtube': [
                'Use public videos only',
                'Try videos from public channels',
                'Use direct links to videos when possible',
                'Check if the video is still available'
            ],
            'reddit': [
                'Use public subreddits only',
                'Try posts from public communities',
                'Use direct links to media when possible',
                'Check if the post is still available'
            ]
        }
        
        return tips.get(platform, ['Tips not available for this platform'])
