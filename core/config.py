"""
Configuration management for the Discord bot
"""

import os
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class DiscordLimits:
    """Discord-specific limits and constraints"""
    MAX_FILE_SIZE: int = 8 * 1024 * 1024  # 8MB Discord file size limit
    MAX_DURATION: int = 600  # 10 minutes max video duration
    MAX_MESSAGE_LENGTH: int = 2000  # Discord message character limit

@dataclass
class QueueSettings:
    """Download queue configuration"""
    MAX_CONCURRENT: int = 3  # Maximum concurrent downloads
    MAX_QUEUE_SIZE: int = 50  # Maximum items in queue
    RATE_LIMIT_REQUESTS: int = 3  # Max requests per user per window
    RATE_LIMIT_WINDOW: int = 60  # Rate limit window in seconds

@dataclass
class AutoDeleteSettings:
    """Auto-delete message configuration"""
    DEFAULT_DELAY: int = 300  # Default auto-delete delay in seconds (5 minutes)
    MIN_DELAY: int = 30  # Minimum auto-delete delay (30 seconds)
    MAX_DELAY: int = 1800  # Maximum auto-delete delay (30 minutes)

@dataclass
class QualityPresets:
    """Video quality presets"""
    VALID_QUALITIES: list = None
    DEFAULT_QUALITY: str = 'best[height<=720]'
    DISCORD_FRIENDLY: str = 'small'
    
    def __post_init__(self):
        if self.VALID_QUALITIES is None:
            self.VALID_QUALITIES = [
                'best', 'worst', 'small',
                'best[height<=720]', 'best[height<=480]', 'best[height<=360]',
                '720p', '480p', '360p'
            ]

@dataclass
class DatabaseLimits:
    """Database query limits"""
    MAX_HISTORY_LIMIT: int = 20  # Maximum history items to show
    MAX_CLEANUP_AMOUNT: int = 100  # Maximum messages to cleanup

@dataclass
class Colors:
    """Discord embed colors"""
    SUCCESS: int = 0x00ff00  # Green
    ERROR: int = 0xff0000    # Red
    WARNING: int = 0xffa500  # Orange
    INFO: int = 0xffff00     # Yellow
    NEUTRAL: int = 0x808080  # Gray

@dataclass
class Platforms:
    """Supported video and image platforms"""
    SUPPORTED_VIDEO_PLATFORMS: Dict[str, str] = None
    SUPPORTED_IMAGE_PLATFORMS: Dict[str, str] = None
    SUPPORTED_PLATFORMS: Dict[str, str] = None
    
    def __post_init__(self):
        if self.SUPPORTED_VIDEO_PLATFORMS is None:
            self.SUPPORTED_VIDEO_PLATFORMS = {
                'youtube': r'(youtube\.com|youtu\.be)',
                'tiktok': r'tiktok\.com',
                'instagram': r'instagram\.com',
                'facebook': r'facebook\.com',
                'twitter': r'twitter\.com|x\.com',
                'reddit': r'reddit\.com',
                'twitch': r'twitch\.tv',
                'vimeo': r'vimeo\.com',
                'dailymotion': r'dailymotion\.com'
            }
        
        if self.SUPPORTED_IMAGE_PLATFORMS is None:
            self.SUPPORTED_IMAGE_PLATFORMS = {
                'instagram': r'instagram\.com',
                'facebook': r'facebook\.com',
                'twitter': r'twitter\.com|x\.com',
                'reddit': r'reddit\.com',
                'imgur': r'imgur\.com',
                'deviantart': r'deviantart\.com',
                'pinterest': r'pinterest\.com',
                'flickr': r'flickr\.com',
                '500px': r'500px\.com',
                'unsplash': r'unsplash\.com',
                'pexels': r'pexels\.com'
            }
        
        if self.SUPPORTED_PLATFORMS is None:
            self.SUPPORTED_PLATFORMS = {**self.SUPPORTED_VIDEO_PLATFORMS, **self.SUPPORTED_IMAGE_PLATFORMS}

@dataclass
class PlatformSettings:
    """Platform-specific configuration and limitations"""
    
    # Public content only - ethical and legal compliance
    PUBLIC_CONTENT_ONLY: bool = True
    
    # Platform-specific settings
    FACEBOOK: Dict[str, Any] = None
    INSTAGRAM: Dict[str, Any] = None
    TWITTER: Dict[str, Any] = None
    TIKTOK: Dict[str, Any] = None
    YOUTUBE: Dict[str, Any] = None
    REDDIT: Dict[str, Any] = None
    TWITCH: Dict[str, Any] = None
    VIMEO: Dict[str, Any] = None
    DAILYMOTION: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.FACEBOOK is None:
            self.FACEBOOK = {
                'supports_public_posts': True,
                'supports_private_posts': False,  # Ethical limitation
                'supports_groups': True,
                'supports_pages': True,
                'supports_reels': True,
                'supports_stories': False,  # Stories are typically private
                'max_duration': 600,  # 10 minutes
                'rate_limit': 10,  # requests per minute
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        if self.INSTAGRAM is None:
            self.INSTAGRAM = {
                'supports_public_posts': True,
                'supports_private_posts': False,  # Ethical limitation
                'supports_stories': False,  # Stories are typically private
                'supports_reels': True,
                'supports_igtv': True,
                'max_duration': 600,
                'rate_limit': 5,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        if self.TWITTER is None:
            self.TWITTER = {
                'supports_public_posts': True,
                'supports_private_posts': False,  # Ethical limitation
                'supports_spaces': False,  # Live audio spaces
                'max_duration': 600,
                'rate_limit': 15,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        if self.TIKTOK is None:
            self.TIKTOK = {
                'supports_public_videos': True,
                'supports_private_videos': False,  # Ethical limitation
                'supports_live_streams': False,  # Live streams are complex
                'max_duration': 600,
                'rate_limit': 20,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        if self.YOUTUBE is None:
            self.YOUTUBE = {
                'supports_public_videos': True,
                'supports_private_videos': False,  # Ethical limitation
                'supports_live_streams': True,
                'supports_shorts': True,
                'max_duration': 3600,  # 1 hour for public content
                'rate_limit': 30,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        if self.REDDIT is None:
            self.REDDIT = {
                'supports_public_posts': True,
                'supports_private_posts': False,  # Ethical limitation
                'supports_nsfw': False,  # Content policy compliance
                'max_duration': 600,
                'rate_limit': 25,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        if self.TWITCH is None:
            self.TWITCH = {
                'supports_public_videos': True,
                'supports_private_videos': False,  # Ethical limitation
                'supports_clips': True,
                'supports_live_streams': False,  # Complex to handle
                'max_duration': 3600,
                'rate_limit': 10,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        if self.VIMEO is None:
            self.VIMEO = {
                'supports_public_videos': True,
                'supports_private_videos': False,  # Ethical limitation
                'max_duration': 3600,
                'rate_limit': 15,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        if self.DAILYMOTION is None:
            self.DAILYMOTION = {
                'supports_public_videos': True,
                'supports_private_videos': False,  # Ethical limitation
                'max_duration': 3600,
                'rate_limit': 20,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

@dataclass
class EthicalGuidelines:
    """Ethical guidelines and content policies"""
    
    # Content policies
    RESPECT_PRIVACY: bool = True
    PUBLIC_CONTENT_ONLY: bool = True
    RESPECT_COPYRIGHT: bool = True
    NO_NSFW_CONTENT: bool = True
    NO_HARASSMENT_CONTENT: bool = True
    
    # Rate limiting to be respectful
    RESPECT_RATE_LIMITS: bool = True
    MINIMIZE_SERVER_LOAD: bool = True
    
    # User education
    EDUCATE_USERS: bool = True
    CLEAR_LIMITATIONS: bool = True
    
    # Legal compliance
    COMPLY_WITH_TOS: bool = True
    RESPECT_PLATFORM_POLICIES: bool = True

@dataclass
class ContentPolicies:
    """Content filtering and policy enforcement"""
    
    # Content types to block
    BLOCKED_CONTENT_TYPES: list = None
    BLOCKED_KEYWORDS: list = None
    BLOCKED_DOMAINS: list = None
    
    # File size and duration limits
    MAX_FILE_SIZE: int = 8 * 1024 * 1024  # 8MB
    MAX_VIDEO_DURATION: int = 600  # 10 minutes
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    def __post_init__(self):
        if self.BLOCKED_CONTENT_TYPES is None:
            self.BLOCKED_CONTENT_TYPES = [
                'nsfw', 'adult', 'explicit', 'violence', 'harassment'
            ]
        
        if self.BLOCKED_KEYWORDS is None:
            self.BLOCKED_KEYWORDS = [
                'nsfw', 'adult', 'explicit', 'violence', 'harassment',
                'hate', 'discrimination', 'illegal'
            ]
        
        if self.BLOCKED_DOMAINS is None:
            self.BLOCKED_DOMAINS = [
                'onlyfans.com', 'pornhub.com', 'xvideos.com'
            ]

class BotConfig:
    """Centralized bot configuration"""
    
    def __init__(self):
        # Discord settings
        self.DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
        self.GUILD_ID = os.getenv('GUILD_ID')
        self.COMMAND_PREFIX = '!'
        
        # Bot settings
        self.DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', 'downloads')
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_data.db')
        self.LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
        
        # Feature flags
        self.AUTO_DELETE_ENABLED = os.getenv('AUTO_DELETE_ENABLED', 'false').lower() == 'true'
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        # Initialize configuration objects
        self.discord_limits = DiscordLimits()
        self.queue_settings = QueueSettings()
        self.auto_delete_settings = AutoDeleteSettings()
        self.quality_presets = QualityPresets()
        self.database_limits = DatabaseLimits()
        self.colors = Colors()
        self.platforms = Platforms()
        self.platform_settings = PlatformSettings()
        self.ethical_guidelines = EthicalGuidelines()
        self.content_policies = ContentPolicies()
    
    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        return True
    
    def get_download_path(self) -> str:
        """Get the download path, creating it if necessary"""
        import os
        os.makedirs(self.DOWNLOAD_PATH, exist_ok=True)
        return self.DOWNLOAD_PATH
    
    def get_platform_settings(self, platform: str) -> Dict[str, Any]:
        """Get settings for a specific platform"""
        platform_attr = platform.upper()
        if hasattr(self.platform_settings, platform_attr):
            return getattr(self.platform_settings, platform_attr)
        return {}
    
    def is_content_allowed(self, url: str, content_type: str = None) -> bool:
        """Check if content is allowed based on policies"""
        # Check blocked domains
        for blocked_domain in self.content_policies.BLOCKED_DOMAINS:
            if blocked_domain in url.lower():
                return False
        
        # Check content type
        if content_type and content_type.lower() in self.content_policies.BLOCKED_CONTENT_TYPES:
            return False
        
        return True
