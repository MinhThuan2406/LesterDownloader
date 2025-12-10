import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio

from utils.command_base import BaseCommand
from utils.embeds import EmbedBuilder
from core.config import AutoDeleteSettings, DatabaseLimits, Colors

class UtilsCog(BaseCommand):
    """Utility commands for the bot"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.start_time = datetime.now()
        self.auto_delete_enabled = False  # Global auto-delete setting - disabled by default
        self.auto_delete_delay = 300  # Default delay in seconds (5 minutes if enabled)
    
    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """Show bot uptime"""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = EmbedBuilder.info(
            title="Bot Uptime",
            description=f"**Uptime:** {days}d {hours}h {minutes}m {seconds}s\n"
                       f"**Started:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'uptime')
    
    @commands.command(name='status')
    async def status(self, ctx):
        """Show detailed bot status"""
        status_info = self.bot.get_status_info()
        
        fields = [
            {
                'name': 'Servers',
                'value': str(status_info['guilds']),
                'inline': True
            },
            {
                'name': 'Users',
                'value': str(status_info['users']),
                'inline': True
            },
            {
                'name': 'Latency',
                'value': f"{status_info['latency']}ms",
                'inline': True
            }
        ]
        
        if status_info['uptime']:
            fields.append({
                'name': 'Uptime',
                'value': status_info['uptime'],
                'inline': True
            })
        
        # Memory usage (if available)
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            fields.append({
                'name': 'Memory',
                'value': f"{memory_mb:.1f} MB",
                'inline': True
            })
        except ImportError:
            pass
        
        embed = EmbedBuilder.create_embed(
            title="Bot Status",
            description="Detailed bot status information",
            color=Colors.SUCCESS,
            fields=fields
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'status')
    
    @commands.command(name='invite')
    async def invite(self, ctx):
        """Get bot invite link"""
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot"
        
        embed = EmbedBuilder.info(
            title="Bot Invite Link",
            description=f"[Click here to invite the bot to your server]({invite_url})\n\n"
                       f"**Required Permissions:**\n"
                       f"• Send Messages\n"
                       f"• Embed Links\n"
                       f"• Attach Files\n"
                       f"• Manage Messages (for auto-delete feature)"
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'invite')
    
    @commands.command(name='support')
    async def support(self, ctx):
        """Get support information"""
        embed = EmbedBuilder.info(
            title="Support Information",
            description="Need help with the bot? Here's how to get support:",
            fields=[
                {
                    'name': 'Commands',
                    'value': "Use `!help` to see all available commands",
                    'inline': False
                },
                {
                    'name': 'Issues',
                    'value': "If you encounter any issues, please report them with:\n"
                             "• The command you used\n"
                             "• The error message\n"
                             "• The URL you tried to download",
                    'inline': False
                },
                {
                    'name': 'Features',
                    'value': "• Download videos from multiple platforms\n"
                             "• Download images and galleries\n"
                             "• Quality selection for videos\n"
                             "• Queue system for multiple downloads\n"
                             "• Auto-delete messages for privacy",
                    'inline': False
                }
            ]
        )
        
        await self.send_embed(ctx, embed)
        self.log_command_usage(ctx, 'support')
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check bot latency"""
        latency = round(self.bot.latency * 1000)
        
        embed = EmbedBuilder.success(
            title="Pong!",
            description=f"Bot latency: {latency}ms"
        )
        
        message = await self.send_embed(ctx, embed, auto_delete=True, delete_delay=10)
        self.log_command_usage(ctx, 'ping', latency=latency)
    
    @commands.command(name='guildid')
    async def guildid(self, ctx):
        """Get the current server's Guild ID"""
        if not ctx.guild:
            await self.send_error(ctx, "Error", "This command can only be used in a server.")
            return
        
        guild_id = ctx.guild.id
        
        embed = EmbedBuilder.info(
            title="Server Information",
            description=f"**Guild ID:** `{guild_id}`\n\n"
                       f"Copy this ID and add it to your `.env` file as `GUILD_ID={guild_id}`"
        )
        
        await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
        self.log_command_usage(ctx, 'guildid', guild_id=guild_id)
    
    @commands.command(name='listguilds')
    async def listguilds(self, ctx):
        """List all servers the bot is in (for debugging)"""
        if not await self.bot.is_owner(ctx.author):
            await self.send_error(ctx, "Access Denied", "This command is only available to the bot owner.")
            return
        
        guilds_info = []
        for guild in self.bot.guilds:
            guilds_info.append(f"**{guild.name}** - `{guild.id}`")
        
        embed = EmbedBuilder.info(
            title="Servers Bot is In",
            description="\n".join(guilds_info)
        )
        
        await self.send_embed(ctx, embed, auto_delete=True, delete_delay=30)
        self.log_command_usage(ctx, 'listguilds', guild_count=len(self.bot.guilds))
    
    @commands.command(name='autodelete')
    async def auto_delete_settings(self, ctx, action: str = None, delay: int = None):
        """Configure auto-delete settings"""
        if action is None:
            # Show current settings
            status = "enabled" if self.auto_delete_enabled else "disabled"
            embed = EmbedBuilder.info(
                title="Auto-Delete Settings",
                description=f"**Status:** {status}\n"
                           f"**Default Delay:** {self.auto_delete_delay} seconds\n\n"
                           f"**Usage:**\n"
                           f"• `!autodelete on [delay]` - Enable auto-delete\n"
                           f"• `!autodelete off` - Disable auto-delete\n"
                           f"• `!autodelete delay <seconds>` - Set default delay"
            )
            await self.send_embed(ctx, embed)
            return
        
        if action.lower() == 'on':
            self.auto_delete_enabled = True
            if delay:
                self.auto_delete_delay = max(AutoDeleteSettings.MIN_DELAY, 
                                           min(delay, AutoDeleteSettings.MAX_DELAY))
            
            embed = EmbedBuilder.success(
                title="Auto-Delete Enabled",
                description=f"Auto-delete is now enabled with {self.auto_delete_delay} second delay."
            )
            await self.send_embed(ctx, embed)
            
        elif action.lower() == 'off':
            self.auto_delete_enabled = False
            embed = EmbedBuilder.success(
                title="Auto-Delete Disabled",
                description="Auto-delete is now disabled."
            )
            await self.send_embed(ctx, embed)
            
        elif action.lower() == 'delay' and delay:
            if delay < AutoDeleteSettings.MIN_DELAY or delay > AutoDeleteSettings.MAX_DELAY:
                await self.send_error(
                    ctx,
                    "Invalid Delay",
                    f"Delay must be between {AutoDeleteSettings.MIN_DELAY} and {AutoDeleteSettings.MAX_DELAY} seconds."
                )
                return
            
            self.auto_delete_delay = delay
            embed = EmbedBuilder.success(
                title="Delay Updated",
                description=f"Auto-delete delay set to {delay} seconds."
            )
            await self.send_embed(ctx, embed)
            
        else:
            await self.send_error(
                ctx,
                "Invalid Action",
                "Valid actions: `on`, `off`, `delay <seconds>`"
            )
        
        self.log_command_usage(ctx, 'autodelete', action=action, delay=delay)
    
    @commands.command(name='cleanup')
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, amount: int = 10):
        """Clean up bot messages (requires Manage Messages permission)"""
        if amount > DatabaseLimits.MAX_CLEANUP_AMOUNT:
            amount = DatabaseLimits.MAX_CLEANUP_AMOUNT
        
        def check(message):
            return message.author == self.bot.user
        
        try:
            deleted = await ctx.channel.purge(limit=amount, check=check)
            embed = EmbedBuilder.success(
                title="Cleanup Complete",
                description=f"Deleted {len(deleted)} bot messages."
            )
            await self.send_embed(ctx, embed, auto_delete=True, delete_delay=10)
            
        except discord.Forbidden:
            await self.send_error(
                ctx,
                "Permission Error",
                "I don't have permission to delete messages in this channel."
            )
        except Exception as e:
            await self.send_error(
                ctx,
                "Cleanup Failed",
                f"An error occurred: {str(e)}"
            )
        
        self.log_command_usage(ctx, 'cleanup', amount=amount, deleted=len(deleted))
    
    @commands.command(name='echo')
    @commands.has_permissions(manage_messages=True)
    async def echo(self, ctx, *, message: str):
        """Echo a message (requires Manage Messages permission)"""
        await ctx.send(message)
        self.log_command_usage(ctx, 'echo', message_length=len(message))
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        await self.handle_command_error(ctx, error)

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(UtilsCog(bot)) 