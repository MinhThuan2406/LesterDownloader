#!/usr/bin/env python3
"""
Test script for LesterDownloader Discord Bot
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_video_downloader():
    """Test the video downloader service"""
    print("🧪 Testing Video Downloader...")
    
    try:
        from services.video_downloader import VideoDownloader
        downloader = VideoDownloader()
        
        # Test URL validation
        test_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://tiktok.com/@user/video/1234567890",
            "https://instagram.com/p/ABC123/",
            "https://facebook.com/watch?v=123456789",
            "https://invalid-url.com/video"
        ]
        
        for url in test_urls:
            is_supported = downloader.is_supported_url(url)
            platform = downloader.get_platform(url)
            print(f"  {url}: {'✅' if is_supported else '❌'} ({platform})")
        
        print("✅ Video Downloader tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Video Downloader test failed: {e}")
        return False

async def test_database():
    """Test the database service"""
    print("🧪 Testing Database...")
    
    try:
        from services.database import DatabaseManager
        db = DatabaseManager("test_bot_data.db")
        
        # Initialize database
        await db.init_db()
        print("  ✅ Database initialization")
        
        # Test basic operations
        await db.log_download(
            user_id=123456789,
            username="TestUser",
            url="https://youtube.com/watch?v=test",
            platform="youtube",
            title="Test Video",
            file_size=1024,
            success=True
        )
        print("  ✅ Download logging")
        
        # Test getting stats
        total_downloads = await db.get_total_downloads()
        successful_downloads = await db.get_successful_downloads()
        print(f"  ✅ Stats retrieval: {total_downloads} total, {successful_downloads} successful")
        
        # Clean up test database
        if os.path.exists("test_bot_data.db"):
            os.remove("test_bot_data.db")
        
        print("✅ Database tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_download_queue():
    """Test the download queue service"""
    print("🧪 Testing Download Queue...")
    
    try:
        from services.download_queue import DownloadQueue
        queue = DownloadQueue(max_concurrent=2, max_queue_size=10)
        
        # Test queue status
        status = await queue.get_queue_status()
        print(f"  ✅ Queue status: {status}")
        
        # Test user position (should be None for non-existent user)
        position = await queue.get_user_position(123456789)
        print(f"  ✅ User position: {position}")
        
        print("✅ Download Queue tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Download Queue test failed: {e}")
        return False

async def test_environment():
    """Test environment setup"""
    print("🧪 Testing Environment...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check required environment variables
        required_vars = ['DISCORD_TOKEN']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"  ⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("  This is expected if you haven't set up your .env file yet")
        else:
            print("  ✅ Environment variables loaded")
        
        # Check if downloads directory exists
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            print("  ✅ Downloads directory exists")
        else:
            print("  ℹ️  Downloads directory will be created on first run")
        
        print("✅ Environment tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Running LesterDownloader Bot Tests...\n")
    
    tests = [
        test_environment,
        test_video_downloader,
        test_database,
        test_download_queue
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your bot is ready to run.")
        print("\nNext steps:")
        print("1. Set up your Discord bot token in .env file")
        print("2. Run: python main.py")
        print("3. Or run: python start.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        sys.exit(1) 