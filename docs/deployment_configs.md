# Deployment Configuration Files

This document contains ready-to-use configuration files for deploying the LesterDownloader bot to various platforms.

---

## 1. Oracle Cloud - systemd Service Configuration

### File: `/etc/systemd/system/lester-bot.service`

```ini
[Unit]
Description=Lester Discord Bot - Media Downloader
After=network.target network-online.target
Wants=network-online.target
Documentation=https://github.com/yourusername/LesterTheDownloader

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/lester-bot
Environment="PATH=/home/ubuntu/lester-bot/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

# Main process
ExecStart=/home/ubuntu/lester-bot/.venv/bin/python start.py

# Restart configuration
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryLimit=1G
CPUQuota=90%

# Logging
StandardOutput=append:/home/ubuntu/lester-bot/logs/bot.log
StandardError=append:/home/ubuntu/lester-bot/logs/error.log
SyslogIdentifier=lester-bot

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/ubuntu/lester-bot/downloads /home/ubuntu/lester-bot/logs /home/ubuntu/lester-bot/bot_data.db
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
```

### Setup Script: `setup_systemd.sh`

```bash
#!/bin/bash

# Oracle Cloud systemd setup script
set -e

echo "Setting up Lester Bot on Oracle Cloud..."

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "Installing system dependencies..."
sudo apt install -y python3.11 python3.11-venv python3-pip ffmpeg git sqlite3

# Create directory structure
echo "Creating directory structure..."
mkdir -p /home/ubuntu/lester-bot/logs
mkdir -p /home/ubuntu/lester-bot/downloads

# Clone or update repository
if [ -d "/home/ubuntu/lester-bot/.git" ]; then
    echo "Updating existing repository..."
    cd /home/ubuntu/lester-bot
    git pull
else
    echo "Cloning repository..."
    git clone <YOUR_REPO_URL> /home/ubuntu/lester-bot
    cd /home/ubuntu/lester-bot
fi

# Create virtual environment
echo "Creating virtual environment..."
python3.11 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
DISCORD_TOKEN=your_token_here
GUILD_ID=your_guild_id_optional
EOF
    echo "⚠️  Don't forget to edit .env with your Discord token!"
fi

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/lester-bot.service > /dev/null << 'EOF'
[Unit]
Description=Lester Discord Bot - Media Downloader
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/lester-bot
Environment="PATH=/home/ubuntu/lester-bot/.venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/ubuntu/lester-bot/.venv/bin/python start.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/lester-bot/logs/bot.log
StandardError=append:/home/ubuntu/lester-bot/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling lester-bot service..."
sudo systemctl enable lester-bot

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /home/ubuntu/lester-bot/.env with your Discord token"
echo "2. Start the bot with: sudo systemctl start lester-bot"
echo "3. Check status with: sudo systemctl status lester-bot"
echo "4. View logs with: tail -f /home/ubuntu/lester-bot/logs/bot.log"
```

---

## 2. Fly.io Configuration

### File: `fly.toml`

```toml
# Fly.io deployment configuration
app = "lester-downloader-bot"
primary_region = "sjc"  # San Jose - change to your preferred region

[build]
  [build.args]
    PYTHON_VERSION = "3.11"

[env]
  PORT = "8080"
  PYTHONUNBUFFERED = "1"
  DOWNLOAD_PATH = "/data/downloads"

[mounts]
  source = "lester_data"
  destination = "/data"

[[services]]
  internal_port = 8080
  protocol = "tcp"
  auto_stop_machines = false  # Keep running 24/7
  auto_start_machines = true
  min_machines_running = 1

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.tcp_checks]]
    interval = "15s"
    timeout = "2s"
    grace_period = "10s"

[metrics]
  port = 9091
  path = "/metrics"

# Resource limits
[experimental]
  auto_rollback = true

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

### File: `Dockerfile` (for Fly.io)

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/downloads /data/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DOWNLOAD_PATH=/data/downloads

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import discord; print('healthy')" || exit 1

# Run the bot
CMD ["python", "start.py"]
```

### File: `.dockerignore`

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.env
.venv/
venv/
downloads/
logs/
bot.log
bot_data.db
.git/
.gitignore
README.md
*.md
.DS_Store
```

### Deployment Script: `deploy_flyio.sh`

```bash
#!/bin/bash

# Fly.io deployment script
set -e

echo "Deploying Lester Bot to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Installing..."
    curl -L https://fly.io/install.sh | sh
    echo "✅ flyctl installed. Please run this script again."
    exit 1
fi

# Login to Fly.io
echo "Logging in to Fly.io..."
fly auth login

# Create app if it doesn't exist
if ! fly apps list | grep -q "lester-downloader-bot"; then
    echo "Creating new Fly.io app..."
    fly apps create lester-downloader-bot
fi

# Create volume for persistent storage
if ! fly volumes list | grep -q "lester_data"; then
    echo "Creating persistent volume..."
    fly volumes create lester_data --region sjc --size 1
fi

# Set secrets
echo "Setting Discord token..."
echo "Please enter your Discord token:"
read -s DISCORD_TOKEN
fly secrets set DISCORD_TOKEN="$DISCORD_TOKEN"

# Deploy
echo "Deploying application..."
fly deploy

# Check status
echo "Checking deployment status..."
fly status

# View logs
echo "Viewing logs (Ctrl+C to exit)..."
fly logs

echo "✅ Deployment complete!"
echo "Your bot should now be running on Fly.io"
```

---

## 3. Railway Configuration

### File: `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python start.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300
  }
}
```

### File: `nixpacks.toml`

```toml
[phases.setup]
nixPkgs = ["python311", "ffmpeg"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = ["echo 'Build complete'"]

[start]
cmd = "python start.py"
```

---

## 4. Render.com Configuration

### File: `render.yaml`

```yaml
services:
  - type: web
    name: lester-discord-bot
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python start.py
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DISCORD_TOKEN
        sync: false
      - key: PYTHONUNBUFFERED
        value: 1
    disk:
      name: lester-data
      mountPath: /opt/render/project/src/downloads
      sizeGB: 1
```

---

## 5. Docker Compose (Local Development)

### File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: lester-bot
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - GUILD_ID=${GUILD_ID}
      - PYTHONUNBUFFERED=1
    volumes:
      - ./downloads:/app/downloads
      - ./logs:/app/logs
      - ./bot_data.db:/app/bot_data.db
    networks:
      - lester-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "python", "-c", "import discord; print('healthy')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  lester-network:
    driver: bridge

volumes:
  downloads:
  logs:
```

### Development Commands

```bash
# Start bot
docker-compose up -d

# View logs
docker-compose logs -f

# Restart bot
docker-compose restart

# Stop bot
docker-compose down

# Rebuild and start
docker-compose up -d --build
```

---

## 6. Health Check Endpoint (Add to bot)

### File: `health_check.py` (New file to create)

```python
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
            metrics = f"""
# HELP lester_uptime_seconds Bot uptime in seconds
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
```

### Update `main.py` to include health check:

```python
# Add to imports
from health_check import HealthCheckServer

# In main() function, before bot.start_bot():
# Start health check server
health_server = HealthCheckServer(bot)
asyncio.create_task(health_server.start())
```

---

## 7. Graceful Shutdown Handler

### File: `shutdown_handler.py` (New file to create)

```python
"""
Graceful shutdown handler for the bot
"""

import asyncio
import signal
import logging
from typing import Callable, List

logger = logging.getLogger(__name__)

class ShutdownHandler:
    """Handles graceful shutdown of the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.shutdown_hooks: List[Callable] = []
    
    def register_hook(self, hook: Callable):
        """Register a shutdown hook"""
        self.shutdown_hooks.append(hook)
    
    async def shutdown(self, signal_name: str):
        """Perform graceful shutdown"""
        logger.info(f"Received exit signal {signal_name}")
        
        try:
            # Run shutdown hooks
            for hook in self.shutdown_hooks:
                try:
                    logger.info(f"Running shutdown hook: {hook.__name__}")
                    await hook()
                except Exception as e:
                    logger.error(f"Error in shutdown hook {hook.__name__}: {e}")
            
            # Close bot connection
            logger.info("Closing bot connection...")
            await self.bot.close()
            
            logger.info("Graceful shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def setup_signals(self, loop):
        """Setup signal handlers"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(
                    self.shutdown(s.name)
                )
            )
        logger.info("Signal handlers registered")
```

### Update `main.py` to use shutdown handler:

```python
# Add to imports
from shutdown_handler import ShutdownHandler

# In main() function:
# Setup shutdown handler
shutdown_handler = ShutdownHandler(bot)

# Register cleanup hooks
shutdown_handler.register_hook(bot.close)  # Close bot
# Add more hooks as needed

# Setup signal handlers
loop = asyncio.get_event_loop()
shutdown_handler.setup_signals(loop)
```

---

## 8. Automated Update Script

### File: `update_bot.sh`

```bash
#!/bin/bash

# Automated update script
set -e

echo "Updating Lester Bot..."

# Go to bot directory
cd /home/ubuntu/lester-bot

# Backup database
echo "Backing up database..."
cp bot_data.db bot_data.db.backup.$(date +%Y%m%d_%H%M%S)

# Pull latest changes
echo "Pulling latest changes..."
git pull

# Activate virtual environment
source .venv/bin/activate

# Update dependencies
echo "Updating dependencies..."
pip install --upgrade -r requirements.txt

# Update yt-dlp
echo "Updating yt-dlp..."
pip install --upgrade yt-dlp

# Restart service
echo "Restarting bot..."
sudo systemctl restart lester-bot

# Wait for bot to start
sleep 5

# Check status
echo "Checking status..."
sudo systemctl status lester-bot --no-pager

echo "✅ Update complete!"
echo "View logs with: journalctl -u lester-bot -f"
```

---

## 9. Monitoring Script

### File: `monitor.sh`

```bash
#!/bin/bash

# Bot monitoring script
# Run via cron every 5 minutes

LOG_FILE="/home/ubuntu/lester-bot/logs/monitor.log"
BOT_SERVICE="lester-bot"

# Check if service is running
if ! systemctl is-active --quiet $BOT_SERVICE; then
    echo "$(date): Bot is not running! Attempting restart..." >> $LOG_FILE
    sudo systemctl start $BOT_SERVICE
    
    # Wait and check again
    sleep 10
    if systemctl is-active --quiet $BOT_SERVICE; then
        echo "$(date): Bot restarted successfully" >> $LOG_FILE
    else
        echo "$(date): CRITICAL: Failed to restart bot!" >> $LOG_FILE
        # Send alert (e.g., email, Discord webhook)
    fi
else
    echo "$(date): Bot is running normally" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df /home/ubuntu/lester-bot | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): WARNING: Disk usage is ${DISK_USAGE}%" >> $LOG_FILE
    # Clean up old downloads
    find /home/ubuntu/lester-bot/downloads -type f -mtime +1 -delete
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "$(date): WARNING: Memory usage is ${MEM_USAGE}%" >> $LOG_FILE
fi
```

### Setup cron job:

```bash
# Edit crontab
crontab -e

# Add this line to run every 5 minutes:
*/5 * * * * /home/ubuntu/lester-bot/monitor.sh
```

---

## 10. Environment Variables Reference

### Required Variables

```bash
# .env file
DISCORD_TOKEN=your_discord_bot_token_here
```

### Optional Variables

```bash
# Guild ID for faster command registration (optional)
GUILD_ID=your_guild_id_here

# Download path (default: downloads/)
DOWNLOAD_PATH=./downloads

# Database path (default: bot_data.db)
DATABASE_PATH=./bot_data.db

# Log level (default: INFO)
LOG_LEVEL=INFO

# Health check port (default: 8080)
HEALTH_CHECK_PORT=8080
```

---

## Usage Instructions

### For Oracle Cloud:
1. Copy `setup_systemd.sh` to server
2. Run: `bash setup_systemd.sh`
3. Edit `.env` with your token
4. Start: `sudo systemctl start lester-bot`

### For Fly.io:
1. Add `fly.toml` and `Dockerfile` to your repo
2. Run: `bash deploy_flyio.sh`
3. Follow prompts

### For Railway:
1. Add `railway.json` to your repo
2. Connect repo in Railway dashboard
3. Add environment variables
4. Deploy

### For Render:
1. Add `render.yaml` to your repo
2. Connect repo in Render dashboard
3. Add environment variables
4. Deploy

---

All configuration files are production-ready and include security best practices!
