import aiosqlite
import logging
from datetime import datetime
from typing import List, Dict, Optional
import os

from core.logging import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Database manager for storing download history and user preferences"""
    
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
    
    async def init_db(self):
        """Initialize database tables"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Downloads table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS downloads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username TEXT NOT NULL,
                        url TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        title TEXT,
                        file_size INTEGER,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User preferences table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        preferred_quality TEXT DEFAULT 'best[height<=720]',
                        max_duration INTEGER DEFAULT 600,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Platform stats table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS platform_stats (
                        platform TEXT PRIMARY KEY,
                        total_downloads INTEGER DEFAULT 0,
                        successful_downloads INTEGER DEFAULT 0,
                        failed_downloads INTEGER DEFAULT 0,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                await db.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def log_download(self, user_id: int, username: str, url: str, platform: str, 
                          title: str = None, file_size: int = None, success: bool = True, 
                          error_message: str = None):
        """Log a download attempt"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO downloads (user_id, username, url, platform, title, file_size, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, url, platform, title, file_size, success, error_message))
                
                # Update platform stats
                await self._update_platform_stats(db, platform, success)
                
                await db.commit()
                logger.debug(f"Logged download: user={user_id}, platform={platform}, success={success}")
                
        except Exception as e:
            logger.error(f"Failed to log download: {e}")
    
    async def _update_platform_stats(self, db, platform: str, success: bool):
        """Update platform statistics"""
        try:
            if success:
                await db.execute('''
                    INSERT INTO platform_stats (platform, total_downloads, successful_downloads, last_updated)
                    VALUES (?, 1, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(platform) DO UPDATE SET
                        total_downloads = total_downloads + 1,
                        successful_downloads = successful_downloads + 1,
                        last_updated = CURRENT_TIMESTAMP
                ''', (platform,))
            else:
                await db.execute('''
                    INSERT INTO platform_stats (platform, total_downloads, failed_downloads, last_updated)
                    VALUES (?, 1, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(platform) DO UPDATE SET
                        total_downloads = total_downloads + 1,
                        failed_downloads = failed_downloads + 1,
                        last_updated = CURRENT_TIMESTAMP
                ''', (platform,))
                
        except Exception as e:
            logger.error(f"Failed to update platform stats: {e}")
    
    async def get_user_downloads(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent downloads for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM downloads 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get user downloads: {e}")
            return []
    
    async def get_platform_stats(self) -> List[Dict]:
        """Get platform statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM platform_stats 
                    ORDER BY total_downloads DESC
                ''')
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get platform stats: {e}")
            return []
    
    async def get_user_preferences(self, user_id: int) -> Optional[Dict]:
        """Get user preferences"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM user_preferences WHERE user_id = ?
                ''', (user_id,))
                
                row = await cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return None
    
    async def update_user_preferences(self, user_id: int, username: str, 
                                    preferred_quality: str = None, max_duration: int = None):
        """Update user preferences"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Check if user exists
                cursor = await db.execute('''
                    SELECT user_id FROM user_preferences WHERE user_id = ?
                ''', (user_id,))
                
                exists = await cursor.fetchone()
                
                if exists:
                    # Update existing user
                    update_fields = []
                    params = []
                    
                    if preferred_quality is not None:
                        update_fields.append("preferred_quality = ?")
                        params.append(preferred_quality)
                    
                    if max_duration is not None:
                        update_fields.append("max_duration = ?")
                        params.append(max_duration)
                    
                    if update_fields:
                        update_fields.append("updated_at = CURRENT_TIMESTAMP")
                        params.append(user_id)
                        
                        await db.execute(f'''
                            UPDATE user_preferences 
                            SET {', '.join(update_fields)}
                            WHERE user_id = ?
                        ''', params)
                else:
                    # Insert new user
                    await db.execute('''
                        INSERT INTO user_preferences (user_id, username, preferred_quality, max_duration)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, username, preferred_quality or 'best[height<=720]', max_duration or 600))
                
                await db.commit()
                logger.debug(f"Updated preferences for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
    
    async def get_total_downloads(self) -> int:
        """Get total number of downloads"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT COUNT(*) FROM downloads')
                result = await cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Failed to get total downloads: {e}")
            return 0
    
    async def get_successful_downloads(self) -> int:
        """Get number of successful downloads"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT COUNT(*) FROM downloads WHERE success = 1')
                result = await cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Failed to get successful downloads: {e}")
            return 0
    
    async def cleanup_old_downloads(self, days: int = 30) -> int:
        """Clean up old download records"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    DELETE FROM downloads 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                await db.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Failed to cleanup old downloads: {e}")
            return 0
    
    async def get_download_stats(self) -> Dict:
        """Get comprehensive download statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Total downloads
                cursor = await db.execute('SELECT COUNT(*) FROM downloads')
                total = (await cursor.fetchone())[0]
                
                # Successful downloads
                cursor = await db.execute('SELECT COUNT(*) FROM downloads WHERE success = 1')
                successful = (await cursor.fetchone())[0]
                
                # Failed downloads
                cursor = await db.execute('SELECT COUNT(*) FROM downloads WHERE success = 0')
                failed = (await cursor.fetchone())[0]
                
                # Success rate
                success_rate = (successful / total * 100) if total > 0 else 0
                
                # Top platforms
                cursor = await db.execute('''
                    SELECT platform, COUNT(*) as count 
                    FROM downloads 
                    GROUP BY platform 
                    ORDER BY count DESC 
                    LIMIT 5
                ''')
                top_platforms = await cursor.fetchall()
                
                return {
                    'total': total,
                    'successful': successful,
                    'failed': failed,
                    'success_rate': success_rate,
                    'top_platforms': top_platforms
                }
                
        except Exception as e:
            logger.error(f"Failed to get download stats: {e}")
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0,
                'top_platforms': []
            } 