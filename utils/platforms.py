"""
Platform detection utilities
"""

import re
from typing import Optional
from core.config import Platforms

# Initialize the Platforms instance to ensure __post_init__ is called
_platforms_instance = Platforms()

class PlatformDetector:
    """Utility class for detecting video and image platforms from URLs"""
    
    @classmethod
    def get_platform(cls, url: str) -> str:
        """
        Get the platform from a URL
        
        Args:
            url: The video/image URL
            
        Returns:
            Platform name or 'unknown' if not supported
        """
        for platform, pattern in _platforms_instance.SUPPORTED_PLATFORMS.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        return "unknown"
    
    @classmethod
    def is_supported_url(cls, url: str) -> bool:
        """
        Check if URL is from a supported platform
        
        Args:
            url: The video/image URL
            
        Returns:
            True if supported, False otherwise
        """
        return cls.get_platform(url) != "unknown"
    
    @classmethod
    def is_video_platform(cls, url: str) -> bool:
        """
        Check if URL is from a video platform
        
        Args:
            url: The URL to check
            
        Returns:
            True if it's a video platform, False otherwise
        """
        platform = cls.get_platform(url)
        return platform in _platforms_instance.SUPPORTED_VIDEO_PLATFORMS
    
    @classmethod
    def is_image_platform(cls, url: str) -> bool:
        """
        Check if URL is from an image platform
        
        Args:
            url: The URL to check
            
        Returns:
            True if it's an image platform, False otherwise
        """
        platform = cls.get_platform(url)
        return platform in _platforms_instance.SUPPORTED_IMAGE_PLATFORMS
    
    @classmethod
    def is_dual_platform(cls, url: str) -> bool:
        """
        Check if URL is from a platform that can contain both videos and images
        (like Facebook, Instagram, Twitter, Reddit)
        
        Args:
            url: The URL to check
            
        Returns:
            True if it's a dual platform, False otherwise
        """
        platform = cls.get_platform(url)
        dual_platforms = ['facebook', 'instagram', 'twitter', 'reddit']
        return platform in dual_platforms
    
    @classmethod
    def get_supported_platforms(cls) -> dict:
        """
        Get list of supported platforms with their patterns
        
        Returns:
            Dictionary of platform names to URL patterns
        """
        return {
            platform: pattern.replace(r'\.', '.').replace(r'\.com', '.com').replace(r'\.tv', '.tv')
            for platform, pattern in _platforms_instance.SUPPORTED_PLATFORMS.items()
        }
    
    @classmethod
    def get_video_platforms(cls) -> dict:
        """
        Get list of supported video platforms
        
        Returns:
            Dictionary of video platform names to URL patterns
        """
        return {
            platform: pattern.replace(r'\.', '.').replace(r'\.com', '.com').replace(r'\.tv', '.tv')
            for platform, pattern in _platforms_instance.SUPPORTED_VIDEO_PLATFORMS.items()
        }
    
    @classmethod
    def get_image_platforms(cls) -> dict:
        """
        Get list of supported image platforms
        
        Returns:
            Dictionary of image platform names to URL patterns
        """
        return {
            platform: pattern.replace(r'\.', '.').replace(r'\.com', '.com').replace(r'\.tv', '.tv')
            for platform, pattern in _platforms_instance.SUPPORTED_IMAGE_PLATFORMS.items()
        } 