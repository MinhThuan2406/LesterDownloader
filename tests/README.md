# Automated Download Tests

This directory contains automated tests for verifying download functionality across multiple platforms.

## Running Tests

### Quick Run
```powershell
# From project root
.\scripts\run_tests.ps1

# Or directly
python tests\test_downloads.py
```

## Test Coverage

The test suite validates:
- YouTube Shorts downloads
- YouTube regular video downloads
- TikTok video downloads
- Instagram Reel downloads

Each test:
1. Attempts to download the content
2. Verifies file was created
3. Checks file size is reasonable
4. Measures download time
5. Captures any errors from logs

## Adding New Tests

Edit `test_downloads.py` and add URLs to the `TEST_URLS` dictionary:

```python
TEST_URLS = {
    'platform_name': 'https://example.com/video/123',
    # ...
}
```

## Test Output

### Success Example
```
✅ SUCCESS!
   Title: Cool Video
   File: downloads/youtube_Cool_Video.mp4
   Size: 2.45 MB
   Time: 5.32s
```

### Failure Example
```
❌ FAILED!
   Error: Format not available
   
   Recent log errors:
   - ERROR: [youtube] Format issue detected
   
💡 SOLUTION: Update yt-dlp
   pip install --upgrade yt-dlp
```

## Interpreting Results

- **100% pass rate** = All platforms working correctly
- **Partial failures** = Check specific platform errors
- **All failures** = Check dependencies (ffmpeg, yt-dlp version)

## Common Issues

| Error | Solution |
|-------|----------|
| ffmpeg not found | `choco install ffmpeg` |
| Format not available | `pip install --upgrade yt-dlp` |
| SSL errors | Use `.\start_bot.ps1` for proper SSL config |
| Module not found | Activate venv: `.\.venv\Scripts\Activate.ps1` |
