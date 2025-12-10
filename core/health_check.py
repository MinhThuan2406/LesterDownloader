"""
Health check endpoint for monitoring
"""

from aiohttp import web
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class HealthCheckServer:
    """Simple HTTP server for health checks"""
    
    def __init__(self, bot, port: int = 8080):
        self.bot = bot
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/metrics', self.metrics)
        self.app.router.add_get('/', self.root)
    
    async def root(self, request):
        """Root endpoint"""
        return web.json_response({
            "service": "Lester Discord Bot",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "metrics": "/metrics"
            }
        })
    
    async def health_check(self, request):
        """Health check endpoint"""
        try:
            # Check if bot is connected
            if not self.bot.is_ready():
                return web.json_response({
                    "status": "unhealthy",
                    "reason": "Bot not ready"
                }, status=503)
            
            # Check if bot has guilds
            if len(self.bot.guilds) == 0:
                return web.json_response({
                    "status": "unhealthy",
                    "reason": "Not connected to any guilds"
                }, status=503)
            
            return web.json_response({
                "status": "healthy",
                "uptime": self.bot.get_uptime(),
                "guilds": len(self.bot.guilds),
                "latency_ms": round(self.bot.latency * 1000, 2)
            })
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def metrics(self, request):
        """Metrics endpoint for monitoring"""
        try:
            from services.database import DatabaseManager
            db = DatabaseManager()
            
            stats = await db.get_download_stats()
            
            # Prometheus-style metrics
            metrics = f"""# HELP lester_uptime_seconds Bot uptime in seconds
# TYPE lester_uptime_seconds gauge
lester_uptime_seconds {self._get_uptime_seconds()}

# HELP lester_guilds_total Total number of guilds
# TYPE lester_guilds_total gauge
lester_guilds_total {len(self.bot.guilds)}

# HELP lester_downloads_total Total downloads
# TYPE lester_downloads_total counter
lester_downloads_total {stats['total']}

# HELP lester_downloads_successful Successful downloads
# TYPE lester_downloads_successful counter
lester_downloads_successful {stats['successful']}

# HELP lester_downloads_failed Failed downloads
# TYPE lester_downloads_failed counter
lester_downloads_failed {stats['failed']}

# HELP lester_success_rate Download success rate
# TYPE lester_success_rate gauge
lester_success_rate {stats['success_rate']}

# HELP lester_latency_milliseconds Bot latency in milliseconds
# TYPE lester_latency_milliseconds gauge
lester_latency_milliseconds {round(self.bot.latency * 1000, 2)}
"""
            
            return web.Response(text=metrics, content_type='text/plain')
        
        except Exception as e:
            logger.error(f"Metrics failed: {e}")
            return web.Response(text=f"# Error: {e}", content_type='text/plain', status=500)
    
    def _get_uptime_seconds(self) -> int:
        """Get uptime in seconds"""
        if not self.bot.start_time:
            return 0
        from discord.utils import utcnow
        uptime = utcnow() - self.bot.start_time
        return int(uptime.total_seconds())
    
    async def start(self):
        """Start the health check server"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await site.start()
            logger.info(f"Health check server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
    
    async def stop(self):
        """Stop the health check server"""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Health check server stopped")
