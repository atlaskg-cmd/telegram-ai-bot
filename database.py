import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

class Database:
    def __init__(self, db_file: str = "bot.db"):
        self.db_file = db_file
        self.init_db()
    
    def get_connection(self):
        """Get database connection with row factory for dict-like access"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Chat history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT NOT NULL,  -- 'user' or 'assistant'
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            ''')
            
            # Contacts table (замена захардкоженным контактам)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    added_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (added_by) REFERENCES users(telegram_id)
                )
            ''')
            
            # User settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    voice_mode INTEGER DEFAULT 0,  -- 0 = off, 1 = on
                    preferred_voice TEXT DEFAULT 'ru-RU-SvetlanaNeural',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            ''')
            
            # News articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE NOT NULL,
                    summary TEXT,
                    category TEXT DEFAULT 'other',
                    source_name TEXT,
                    source_category TEXT,
                    published TIMESTAMP,
                    sentiment TEXT DEFAULT 'neutral',
                    sentiment_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User interests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                    UNIQUE(user_id, category)
                )
            ''')
            
            # User news likes/dislikes for ML
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_news_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    news_id INTEGER,
                    feedback INTEGER,  -- 1 = like, -1 = dislike, 0 = neutral
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (news_id) REFERENCES news_articles(id),
                    UNIQUE(user_id, news_id)
                )
            ''')
            
            # Digest schedule table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS digest_schedules (
                    user_id INTEGER PRIMARY KEY,
                    enabled INTEGER DEFAULT 0,
                    schedule_time TEXT DEFAULT '09:00',
                    last_sent TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            ''')
            
            conn.commit()
            logging.info("Database initialized successfully")
    
    # ========== USERS ==========
    
    def add_or_update_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None):
        """Add new user or update existing"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_active = CURRENT_TIMESTAMP
            ''', (telegram_id, username, first_name, last_name))
            
            # Create default settings for new user
            cursor.execute('''
                INSERT OR IGNORE INTO user_settings (user_id, voice_mode)
                VALUES (?, 0)
            ''', (telegram_id,))
            
            conn.commit()
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]
    
    def get_active_users_today(self) -> int:
        """Get number of active users today"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE date(last_active) = date('now')
            ''')
            return cursor.fetchone()[0]
    
    # ========== CHAT HISTORY ==========
    
    def add_message(self, user_id: int, role: str, content: str):
        """Add message to chat history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (user_id, role, content)
                VALUES (?, ?, ?)
            ''', (user_id, role, content))
            conn.commit()
    
    def get_chat_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get recent chat history for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content FROM chat_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            rows = cursor.fetchall()
            # Reverse to get chronological order
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
    
    def clear_chat_history(self, user_id: int):
        """Clear chat history for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
            conn.commit()
    
    # ========== CONTACTS ==========
    
    def add_contact(self, name: str, phone: str, added_by: int) -> bool:
        """Add new contact"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO contacts (name, phone, added_by)
                    VALUES (?, ?, ?)
                ''', (name, phone, added_by))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding contact: {e}")
            return False
    
    def delete_contact(self, contact_id: int, user_id: int) -> bool:
        """Delete contact (only if added by this user)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM contacts WHERE id = ? AND added_by = ?
            ''', (contact_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts by name or phone"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone FROM contacts
                WHERE name LIKE ? OR phone LIKE ?
                ORDER BY name
            ''', (f'%{query}%', f'%{query}%'))
            return [{"id": row["id"], "name": row["name"], "phone": row["phone"]} 
                    for row in cursor.fetchall()]
    
    def get_all_contacts(self) -> List[Dict]:
        """Get all contacts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, phone FROM contacts ORDER BY name')
            return [{"id": row["id"], "name": row["name"], "phone": row["phone"]} 
                    for row in cursor.fetchall()]
    
    def get_contact_by_id(self, contact_id: int) -> Optional[Dict]:
        """Get single contact by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, phone FROM contacts WHERE id = ?', (contact_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row["id"], "name": row["name"], "phone": row["phone"]}
            return None
    
    # ========== USER SETTINGS ==========
    
    def get_voice_mode(self, user_id: int) -> bool:
        """Get voice mode setting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT voice_mode FROM user_settings WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return bool(row["voice_mode"])
            return False
    
    def set_voice_mode(self, user_id: int, enabled: bool):
        """Set voice mode"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_settings (user_id, voice_mode)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    voice_mode = excluded.voice_mode,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, 1 if enabled else 0))
            conn.commit()
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get stats for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Message count
            cursor.execute('SELECT COUNT(*) FROM chat_history WHERE user_id = ?', (user_id,))
            message_count = cursor.fetchone()[0]
            
            # Contact count
            cursor.execute('SELECT COUNT(*) FROM contacts WHERE added_by = ?', (user_id,))
            contact_count = cursor.fetchone()[0]
            
            return {
                "message_count": message_count,
                "contact_count": contact_count
            }
    
    # ========== ADMIN FUNCTIONS ==========
    
    def get_all_users(self) -> List[Dict]:
        """Get all users for broadcast"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT telegram_id, username, first_name FROM users')
            return [{"telegram_id": row["telegram_id"], "username": row["username"], 
                    "first_name": row["first_name"]} for row in cursor.fetchall()]
    
    def get_admin_stats(self) -> Dict:
        """Get admin statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM contacts')
            total_contacts = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM chat_history')
            total_messages = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE date(last_active) = date('now')
            ''')
            active_today = cursor.fetchone()[0]
            
            return {
                "total_users": total_users,
                "total_contacts": total_contacts,
                "total_messages": total_messages,
                "active_today": active_today
            }
    
    # ========== NEWS FUNCTIONS ==========
    
    def save_news_item(self, item: Dict) -> bool:
        """Save news article to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO news_articles 
                    (title, link, summary, category, source_name, source_category, 
                     published, sentiment, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item['title'], item['link'], item['summary'], 
                    item['category'], item.get('source_name', ''),
                    item.get('source_category', ''), item['published'],
                    item.get('sentiment', 'neutral'), item.get('sentiment_score', 0.0)
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error saving news: {e}")
            return False
    
    def get_news_by_categories(self, categories: List[str], limit: int = 10) -> List[Dict]:
        """Get news by categories (last 3 days)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' for _ in categories)
            cursor.execute(f'''
                SELECT * FROM news_articles 
                WHERE category IN ({placeholders})
                AND date(published) >= date('now', '-3 days')
                ORDER BY published DESC
                LIMIT ?
            ''', (*categories, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_news(self, limit: int = 20) -> List[Dict]:
        """Get latest news regardless of category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM news_articles 
                WHERE date(published) >= date('now', '-3 days')
                ORDER BY published DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== USER INTERESTS ==========
    
    def add_user_interest(self, user_id: int, category: str) -> bool:
        """Add interest category for user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO user_interests (user_id, category)
                    VALUES (?, ?)
                ''', (user_id, category.lower()))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding interest: {e}")
            return False
    
    def remove_user_interest(self, user_id: int, category: str) -> bool:
        """Remove interest category for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM user_interests WHERE user_id = ? AND category = ?
            ''', (user_id, category.lower()))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_user_interests(self, user_id: int) -> List[str]:
        """Get all interests for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category FROM user_interests WHERE user_id = ?
            ''', (user_id,))
            return [row['category'] for row in cursor.fetchall()]
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        return ['tech', 'ai', 'science', 'space', 'finance', 'kyrgyzstan', 'world', 'sports', 'other']
    
    # ========== NEWS FEEDBACK ==========
    
    def add_news_feedback(self, user_id: int, news_id: int, feedback: int):
        """Add user feedback for news (1=like, -1=dislike)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_news_feedback (user_id, news_id, feedback)
                VALUES (?, ?, ?)
            ''', (user_id, news_id, feedback))
            conn.commit()
    
    def get_user_feedback_stats(self, user_id: int) -> Dict:
        """Get feedback statistics for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT feedback, COUNT(*) as count 
                FROM user_news_feedback 
                WHERE user_id = ?
                GROUP BY feedback
            ''', (user_id,))
            stats = {row['feedback']: row['count'] for row in cursor.fetchall()}
            return {
                'likes': stats.get(1, 0),
                'dislikes': stats.get(-1, 0),
                'neutral': stats.get(0, 0)
            }
    
    # ========== DIGEST SCHEDULE ==========
    
    def set_digest_schedule(self, user_id: int, enabled: bool, schedule_time: str = '09:00'):
        """Set digest schedule for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO digest_schedules (user_id, enabled, schedule_time)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    enabled = excluded.enabled,
                    schedule_time = excluded.schedule_time
            ''', (user_id, 1 if enabled else 0, schedule_time))
            conn.commit()
    
    def get_digest_schedule(self, user_id: int) -> Optional[Dict]:
        """Get digest schedule for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM digest_schedules WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'enabled': bool(row['enabled']),
                    'schedule_time': row['schedule_time'],
                    'last_sent': row['last_sent']
                }
            return None
    
    def get_users_for_digest(self, current_time: str) -> List[int]:
        """Get users who should receive digest at current time"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id FROM digest_schedules 
                WHERE enabled = 1 
                AND schedule_time = ?
                AND (last_sent IS NULL OR date(last_sent) < date('now'))
            ''', (current_time,))
            return [row['user_id'] for row in cursor.fetchall()]
    
    def update_last_sent(self, user_id: int):
        """Update last sent timestamp"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE digest_schedules SET last_sent = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
