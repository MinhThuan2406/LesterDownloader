"""
Automated download testing script for multiple platforms
Tests YouTube Shorts, TikTok, and Instagram downloads
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from services.video_downloader import VideoDownloader
from services.image_downloader import ImageDownloader
from core.logging import get_logger

# Setup logging
logger = get_logger(__name__)

# Test URLs
TEST_URLS = {
    'youtube_short': 'https://youtube.com/shorts/uLROGEeCtZs?si=CDQHPSSM7MxYT5mm',
    'youtube_regular': 'https://www.youtube.com/watch?v=5e7e_KZINA4',
    'tiktok': 'https://www.tiktok.com/@thanglootro/video/7580767234939882773?is_from_webapp=1&sender_device=pc',
    'instagram': 'https://www.instagram.com/reel/DSCSUiYiZ1Z/?utm_source=ig_web_copy_link&igsh=NTc4MTIwNjQ2YQ=='
}

class DownloadTester:
    def __init__(self):
        self.video_downloader = VideoDownloader()
        self.image_downloader = ImageDownloader()
        self.results = {}
        self.log_file = Path('bot.log')
        
    async def test_download(self, platform: str, url: str):
        """Test downloading from a specific platform"""
        print(f"\n{'='*60}")
        print(f"Testing {platform.upper()} download...")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        start_time = datetime.now()
        
        try:
            # Try video download
            print(f"Attempting video download...")
            filepath, title, error = await self.video_downloader.download_video(url, quality='best[height<=720]')
            
            if filepath:
                file_size = Path(filepath).stat().st_size
                duration = (datetime.now() - start_time).total_seconds()
                
                result = {
                    'status': 'SUCCESS',
                    'filepath': filepath,
                    'title': title,
                    'file_size': file_size,
                    'file_size_mb': round(file_size / 1024 / 1024, 2),
                    'duration': f"{duration:.2f}s",
                    'error': None
                }
                
                print(f"✅ SUCCESS!")
                print(f"   Title: {title}")
                print(f"   File: {filepath}")
                print(f"   Size: {result['file_size_mb']} MB")
                print(f"   Time: {result['duration']}")
                
            else:
                # Extract recent errors from log
                recent_errors = self.get_recent_errors(platform)
                
                result = {
                    'status': 'FAILED',
                    'filepath': None,
                    'title': title,
                    'file_size': 0,
                    'file_size_mb': 0,
                    'duration': f"{(datetime.now() - start_time).total_seconds():.2f}s",
                    'error': error,
                    'log_errors': recent_errors
                }
                
                print(f"❌ FAILED!")
                print(f"   Error: {error}")
                print(f"\n   Recent log errors:")
                for log_error in recent_errors:
                    print(f"   - {log_error}")
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            recent_errors = self.get_recent_errors(platform)
            
            result = {
                'status': 'ERROR',
                'filepath': None,
                'title': 'Unknown',
                'file_size': 0,
                'file_size_mb': 0,
                'duration': f"{duration:.2f}s",
                'error': str(e),
                'log_errors': recent_errors
            }
            
            print(f"💥 ERROR!")
            print(f"   Exception: {e}")
            print(f"\n   Recent log errors:")
            for log_error in recent_errors:
                print(f"   - {log_error}")
        
        self.results[platform] = result
        return result
    
    def get_recent_errors(self, platform: str, lines: int = 20):
        """Get recent error messages from log file"""
        if not self.log_file.exists():
            return ["Log file not found"]
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
            # Get last N lines
            recent_lines = all_lines[-lines:]
            
            # Filter for ERROR/WARNING messages related to this platform
            errors = []
            for line in recent_lines:
                if ('ERROR' in line or 'WARNING' in line) and platform in line.lower():
                    # Clean up the line
                    errors.append(line.strip())
            
            # If no platform-specific errors, get general errors
            if not errors:
                for line in recent_lines:
                    if 'ERROR' in line or 'WARNING' in line:
                        errors.append(line.strip())
            
            return errors[-5:] if errors else ["No recent errors found"]
            
        except Exception as e:
            return [f"Error reading log: {e}"]
    
    def print_summary(self):
        """Print summary of all test results"""
        print(f"\n\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}\n")
        
        total = len(self.results)
        successful = sum(1 for r in self.results.values() if r['status'] == 'SUCCESS')
        failed = total - successful
        
        print(f"Total Tests: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(successful/total*100):.1f}%\n")
        
        for platform, result in self.results.items():
            status_emoji = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"{status_emoji} {platform.upper()}: {result['status']}")
            if result['status'] == 'SUCCESS':
                print(f"   └─ {result['file_size_mb']} MB in {result['duration']}")
            else:
                print(f"   └─ {result['error']}")
        
        print(f"\n{'='*60}")
        
        # Diagnostics section
        if failed > 0:
            print("\n📋 DIAGNOSTICS")
            print(f"{'='*60}\n")
            
            for platform, result in self.results.items():
                if result['status'] != 'SUCCESS':
                    print(f"\n{platform.upper()} Failed:")
                    print(f"Error: {result['error']}")
                    
                    # Analyze common issues
                    error_str = str(result['error']).lower()
                    if 'ffmpeg' in error_str:
                        print("\n💡 SOLUTION: Install ffmpeg")
                        print("   - Download: https://ffmpeg.org/download.html")
                        print("   - Or use: choco install ffmpeg (if you have Chocolatey)")
                    elif 'format' in error_str and 'not available' in error_str:
                        print("\n💡 SOLUTION: Try different quality settings")
                        print("   - The script will auto-retry with format 18 (360p)")
                        print("   - Check if yt-dlp is up to date: pip install -U yt-dlp")
                    elif 'private' in error_str or 'authentication' in error_str:
                        print("\n💡 SOLUTION: Content may be private or require login")
                        print("   - Verify the URL is for ​public content")
                        print("   - Try a different video from the same platform")
                    
                    if result.get('log_errors'):
                        print("\n📝 Recent log entries:")
                        for log_line in result['log_errors'][-3:]:
                            print(f"   {log_line}")
    
    async def run_all_tests(self):
        """Run tests for all platforms"""
        print("🚀 Starting automated download tests...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for platform, url in TEST_URLS.items():
            await self.test_download(platform, url)
            await asyncio.sleep(1)  # Brief pause between tests
        
        self.print_summary()
        
        # Return exit code based on results
        return 0 if all(r['status'] == 'SUCCESS' for r in self.results.values()) else 1


async def main():
    """Main entry point"""
    tester = DownloadTester()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
