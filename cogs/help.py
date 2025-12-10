import discord
from discord.ext import commands
from utils.command_base import BaseCommand
from utils.embeds import EmbedBuilder

class HelpCog(BaseCommand):
    """Custom help command"""
    
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command(name='help')
    async def help_command(self, ctx, command_name: str = None):
        """Show help information for commands"""
        if command_name:
            await self._show_command_help(ctx, command_name)
        else:
            await self._show_general_help(ctx)
    
    async def _show_general_help(self, ctx):
        """Show general help information"""
        embed = EmbedBuilder.info(
            title="Video Downloader Bot Help",
            description="A Discord bot for downloading videos and images from popular social media platforms.",
            fields=[
                {
                    'name': 'Download Commands',
                    'value': "`!download <url> [quality]` - Download a video or image\n`!info <url>` - Get media information\n`!queue` - Check download queue status\n`!cancel` - Cancel your pending downloads",
                    'inline': False
                },
                {
                    'name': 'Information Commands',
                    'value': "`!history [limit]` - Show your download history\n`!stats` - Show platform statistics\n`!platforms` - List supported platforms\n`!formats <url>` - Show available formats",
                    'inline': False
                },
                {
                    'name': 'Settings Commands',
                    'value': "`!quality <quality>` - Set your preferred video quality\n`!qualities` - Show available quality options\n`!ping` - Check bot latency",
                    'inline': False
                },
                {
                    'name': 'Troubleshooting',
                    'value': "`!facebook-help` - Facebook download help and limitations\n`!platform-help` - Comprehensive platform help\n`!ethical-guidelines` - Bot's ethical guidelines and policies\n`!support` - Get support information",
                    'inline': False
                },
                {
                    'name': 'Examples',
                    'value': "`!download https://youtube.com/watch?v=...`\n`!download https://tiktok.com/@user/video/... best[height<=480]`\n`!info https://instagram.com/p/...`\n`!quality best[height<=720]`",
                    'inline': False
                },
                {
                    'name': 'Supported Platforms',
                    'value': "**Video:** YouTube, TikTok, Instagram, Facebook, Twitter, Reddit, Twitch, Vimeo, Dailymotion\n**Images:** Instagram, Facebook, Twitter, Reddit, Imgur, DeviantArt, Pinterest, Flickr, 500px, Unsplash, Pexels",
                    'inline': False
                },
                {
                    'name': 'Important Notes',
                    'value': "• Facebook: Only public posts are supported\n• Instagram: Some content may require login\n• Twitter: Rate limits may apply\n• All downloads must comply with platform terms of service",
                    'inline': False
                }
            ]
        )
        
        await self.send_embed(ctx, embed, auto_delete=True, delete_delay=60)
    
    async def _show_command_help(self, ctx, command_name: str):
        """Show detailed help for a specific command"""
        command = self.bot.get_command(command_name)
        
        if not command:
            embed = EmbedBuilder.error(
                title="Command Not Found",
                description=f"The command `{command_name}` was not found."
            )
            await self.send_embed(ctx, embed, auto_delete=True, delete_delay=20)
            return
        
        # Get command help information
        help_info = self._get_command_help_info(command_name)
        
        embed = EmbedBuilder.info(
            title=f"Help: {command_name}",
            description=help_info['description'],
            fields=help_info['fields']
        )
        
        await self.send_embed(ctx, embed, auto_delete=True, delete_delay=60)
    
    def _get_command_help_info(self, command_name: str) -> dict:
        """Get detailed help information for a command"""
        help_data = {
            'download': {
                'description': 'Download a video or image from supported platforms',
                'fields': [
                    {
                        'name': 'Usage',
                        'value': '`!download <url> [quality]`',
                        'inline': False
                    },
                    {
                        'name': 'Arguments',
                        'value': '**url** - The URL to download from\n**quality** - (Optional) Video quality preference',
                        'inline': False
                    },
                    {
                        'name': 'Quality Options',
                        'value': '• `best` - Best quality available\n• `best[height<=720]` - Best up to 720p (default)\n• `best[height<=480]` - Best up to 480p\n• `worst` - Lowest quality\n• `small` - Discord-optimized (under 8MB)\n• `720p`, `480p`, `360p` - Specific resolutions',
                        'inline': False
                    },
                    {
                        'name': 'Examples',
                        'value': '`!download https://youtube.com/watch?v=dQw4w9WgXcQ`\n`!download https://tiktok.com/@user/video/123 best[height<=480]`',
                        'inline': False
                    }
                ]
            },
            'facebook-help': {
                'description': 'Get help with Facebook downloads and common issues',
                'fields': [
                    {
                        'name': 'Supported Content',
                        'value': '• Public Facebook posts\n• Public photos and videos\n• Public reels and stories\n• Posts from public groups',
                        'inline': False
                    },
                    {
                        'name': 'Not Supported',
                        'value': '• Private posts (Friends Only)\n• Posts from private groups\n• Posts requiring login\n• Deleted posts\n• Posts with restricted access',
                        'inline': False
                    },
                    {
                        'name': 'Common Issues',
                        'value': '• "No video formats found" = Private post\n• "pfbid" errors = Unsupported format\n• "Could not extract" = Post not accessible',
                        'inline': False
                    }
                ]
            },
            'quality': {
                'description': 'Set your preferred video quality for downloads',
                'fields': [
                    {
                        'name': 'Usage',
                        'value': '`!quality <quality>`',
                        'inline': False
                    },
                    {
                        'name': 'Available Qualities',
                        'value': '• `best` - Best quality available\n• `best[height<=720]` - Best up to 720p\n• `best[height<=480]` - Best up to 480p\n• `worst` - Lowest quality\n• `small` - Discord-optimized\n• `720p`, `480p`, `360p` - Specific resolutions',
                        'inline': False
                    },
                    {
                        'name': 'Examples',
                        'value': '`!quality best[height<=720]`\n`!quality small`',
                        'inline': False
                    }
                ]
            }
        }
        
        return help_data.get(command_name, {
            'description': f'Help information for {command_name} command',
            'fields': [
                {
                    'name': 'Usage',
                    'value': f'`!{command_name}`',
                    'inline': False
                }
            ]
        })
    
    @commands.command(name='about')
    async def about(self, ctx):
        """Show information about the bot"""
        embed = EmbedBuilder.info(
            title="About LesterDownloader",
            description="A powerful Discord bot for downloading videos and images from various social media platforms.",
            fields=[
                {
                    'name': 'Features',
                    'value': "• Multi-platform support\n• Queue system for multiple downloads\n• Quality control options\n• Auto-delete messages for privacy\n• Download history tracking\n• Rate limiting and error handling",
                    'inline': False
                },
                {
                    'name': 'Supported Platforms',
                    'value': "**Video:** YouTube, TikTok, Instagram, Facebook, Twitter, Reddit, Twitch, Vimeo, Dailymotion\n**Images:** Instagram, Facebook, Twitter, Reddit, Imgur, DeviantArt, Pinterest, Flickr, 500px, Unsplash, Pexels",
                    'inline': False
                },
                {
                    'name': 'Technical Details',
                    'value': "• Built with discord.py\n• Uses yt-dlp for downloads\n• SQLite database for tracking\n• Asynchronous architecture\n• Modular design for maintainability",
                    'inline': False
                },
                {
                    'name': 'Limitations',
                    'value': "• Facebook: Only public posts supported\n• Instagram: Some content may require login\n• Twitter: Rate limits may apply\n• All downloads must comply with platform terms of service",
                    'inline': False
                },
                {
                    'name': 'Commands',
                    'value': "Use `!help` to see all available commands\nUse `!facebook-help` for Facebook-specific help",
                    'inline': False
                }
            ]
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'about')

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(HelpCog(bot)) 