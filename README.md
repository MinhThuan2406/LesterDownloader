# LesterDownloader Discord Bot

A powerful Discord bot for downloading videos and images from various social media platforms. Built with a clean, modular architecture for maintainability and extensibility.

## Features

- **Multi-Platform Support**: Download from YouTube, TikTok, Instagram, Facebook, Twitter, Reddit, and more
- **Queue System**: Efficient download queue with rate limiting and user management
- **Quality Control**: Customizable video quality settings with Discord-friendly presets
- **Auto-Delete**: Configurable message auto-deletion for privacy
- **Statistics**: Track download history and platform statistics
- **Error Handling**: Robust error handling with user-friendly messages
- **Modular Design**: Clean separation of concerns with reusable components

## Architecture

The bot follows a clean, modular architecture:

```
LesterDownloader/
├── core/                    # Core bot functionality
│   ├── bot.py              # Main bot class
│   ├── config.py           # Configuration management
│   └── logging.py          # Centralized logging
├── cogs/                   # Discord command modules
│   ├── video_downloader.py # Download commands
│   ├── utils.py            # Utility commands
│   └── help.py             # Help system
├── services/               # Business logic services
│   ├── video_downloader.py # Video download logic
│   ├── image_downloader.py # Image download logic
│   ├── database.py         # Database operations
│   ├── download_queue.py   # Queue management
│   └── content_detector.py # Content type detection
├── utils/                  # Utility modules
│   ├── embeds.py          # Embed creation utilities
│   ├── command_base.py    # Base command class
│   ├── platforms.py       # Platform detection
│   ├── errors.py          # Error handling
│   └── decorators.py      # Command decorators
├── downloads/              # Downloaded files (auto-created)
├── main.py                 # Entry point
├── start.py                # Startup script
└── requirements.txt        # Dependencies
```

## Key Improvements

### 1. Centralized Configuration
- All configuration moved to `core/config.py`
- Environment-based settings with validation
- Type-safe configuration with dataclasses

### 2. Modular Command System
- Base command class with common functionality
- Consistent error handling and logging
- Rate limiting and permission checking

### 3. Reusable Components
- Centralized embed creation utilities
- Common error handling patterns
- Shared utility functions

### 4. Improved Error Handling
- Comprehensive error catching and logging
- User-friendly error messages
- Graceful degradation

### 5. Better Logging
- Centralized logging configuration
- Consistent log format across modules
- Debug and error tracking

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LesterDownloader
   ```

2. **Install dependencies**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file with:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   GUILD_ID=your_guild_id (optional)
   ```

4. **Run the bot**
   ```bash
   python start.py
   ```

## Configuration

The bot uses a centralized configuration system in `core/config.py`:

- **Discord Settings**: Token, guild ID, command prefix
- **Download Settings**: File size limits, quality presets
- **Queue Settings**: Concurrent downloads, rate limiting
- **Auto-Delete**: Message deletion timing
- **Feature Flags**: Debug mode, auto-delete toggle

## Commands

### Download Commands
- `!download <url> [quality]` - Download video/image
- `!info <url>` - Get media information
- `!formats <url>` - Show available formats

### Queue Management
- `!queue` - Check queue status
- `!cancel` - Cancel pending downloads

### User Preferences
- `!quality <setting>` - Set preferred quality
- `!qualities` - Show available qualities

### Statistics
- `!history [limit]` - View download history
- `!stats` - Platform statistics

### Utility Commands
- `!ping` - Check bot latency
- `!status` - Bot status information
- `!uptime` - Bot uptime
- `!platforms` - Supported platforms

## Supported Platforms

### Video Platforms
- YouTube
- TikTok
- Instagram (Reels)
- Facebook
- Twitter/X
- Reddit
- Twitch
- Vimeo
- Dailymotion

### Image Platforms
- Instagram
- Facebook
- Twitter/X
- Reddit
- Imgur
- DeviantArt
- Pinterest
- Flickr
- 500px
- Unsplash
- Pexels

## Quality Options

- `best` - Best quality available
- `best[height<=720]` - Best up to 720p (default)
- `best[height<=480]` - Best up to 480p
- `worst` - Lowest quality (smallest file)
- `small` - Discord-optimized (under 8MB)
- `720p`, `480p`, `360p` - Specific resolutions

## Development

### Code Structure
- **Core Module**: Centralized bot functionality and configuration
- **Cogs**: Discord command modules with shared base class
- **Services**: Business logic separated from commands
- **Utils**: Reusable utility functions and classes

### Adding New Features
1. Create new service in `services/` for business logic
2. Add commands in appropriate cog in `cogs/`
3. Use base classes and utilities for consistency
4. Update configuration if needed

### Testing
```bash
python test_bot.py
```

## Error Handling

The bot includes comprehensive error handling:
- Platform validation
- File size limits
- Rate limiting
- Network timeouts
- User permission checks

## Logging

Logs are written to `bot.log` with the following levels:
- **INFO**: General bot activity
- **DEBUG**: Detailed debugging information
- **ERROR**: Error conditions
- **WARNING**: Warning conditions

## Performance

- Asynchronous operations throughout
- Efficient queue system
- File cleanup after downloads
- Memory-conscious design

## Security

- Rate limiting per user
- File size validation
- Platform URL validation
- Permission checking

## Contributing

1. Follow the existing code structure
2. Use the base command class for new commands
3. Add proper error handling and logging
4. Update documentation as needed
5. Test thoroughly before submitting

## License

This project is licensed under the MIT License - see the LICENSE file for details.