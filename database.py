"""
Database module - supports SQLite (local) and PostgreSQL (Railway)
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json

# Try to import psycopg2 for PostgreSQL (Railway)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
    logging.info("psycopg2 imported successfully")
except ImportError as e:
    POSTGRES_AVAILABLE = False
    logging.warning(f"psycopg2 not available: {e}")

# SQLite for local development
import sqlite3


class Database:
    def __init__(self):
        # Check if Railway PostgreSQL is available
        self.database_url = os.environ.get("DATABASE_URL")
        self.use_postgres = False
        
        logging.info(f"DATABASE_URL exists: {bool(self.database_url)}")
        if self.database_url:
            logging.info(f"DATABASE_URL starts with: {self.database_url[:20]}...")
        logging.info(f"POSTGRES_AVAILABLE: {POSTGRES_AVAILABLE}")
        
        if POSTGRES_AVAILABLE and self.database_url:
            try:
                # Test connection
                conn = psycopg2.connect(self.database_url, sslmode='require')
                conn.close()
                self.use_postgres = True
                logging.info("✅ PostgreSQL connection successful")
            except Exception as e:
                logging.error(f"❌ PostgreSQL connection failed: {e}")
                self.use_postgres = False
        
        if self.use_postgres:
            logging.info("Using PostgreSQL database (Railway)")
        else:
            self.db_file = "bot.db"
            logging.info(f"Using SQLite database: {self.db_file}")
        
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        if self.use_postgres:
            # Railway requires SSL
            conn = psycopg2.connect(self.database_url, sslmode='require')
            return conn
        else:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            return conn
    
    def _execute(self, cursor, query: str, params: tuple = ()):
        """Execute query with automatic ? to %s conversion for PostgreSQL"""
        if self.use_postgres:
            # Convert ? to %s for PostgreSQL
            query = query.replace('?', '%s')
        cursor.execute(query, params)
    
    def init_db(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        telegram_id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Chat history table
                if self.use_postgres:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS chat_history (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                        )
                    ''')
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS chat_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                        )
                    ''')
                
                # Contacts table
                if self.use_postgres:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS contacts (
                            id SERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            phone TEXT NOT NULL,
                            added_by BIGINT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (added_by) REFERENCES users(telegram_id)
                        )
                    ''')
                else:
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
                        user_id BIGINT PRIMARY KEY,
                        voice_mode INTEGER DEFAULT 0,
                        preferred_voice TEXT DEFAULT 'ru-RU-SvetlanaNeural',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                    )
                ''')
                
                # News articles table
                if self.use_postgres:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS news_articles (
                            id SERIAL PRIMARY KEY,
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
                else:
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
                if self.use_postgres:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_interests (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT,
                            category TEXT NOT NULL,
                            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                            UNIQUE(user_id, category)
                        )
                    ''')
                else:
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
                
                # User news feedback table
                if self.use_postgres:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_news_feedback (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT,
                            news_id INTEGER,
                            feedback INTEGER,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                            FOREIGN KEY (news_id) REFERENCES news_articles(id),
                            UNIQUE(user_id, news_id)
                        )
                    ''')
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_news_feedback (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            news_id INTEGER,
                            feedback INTEGER,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                            FOREIGN KEY (news_id) REFERENCES news_articles(id),
                            UNIQUE(user_id, news_id)
                        )
                    ''')
                
                # Digest schedule table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS digest_schedules (
                        user_id BIGINT PRIMARY KEY,
                        enabled INTEGER DEFAULT 0,
                        schedule_time TEXT DEFAULT '09:00',
                        last_sent TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                    )
                ''')
                
                # Admins table
                if self.use_postgres:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS admins (
                            id SERIAL PRIMARY KEY,
                            telegram_id BIGINT UNIQUE NOT NULL,
                            username TEXT,
                            role TEXT DEFAULT 'admin',
                            added_by BIGINT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (added_by) REFERENCES users(telegram_id)
                        )
                    ''')
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS admins (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id BIGINT UNIQUE NOT NULL,
                            username TEXT,
                            role TEXT DEFAULT 'admin',
                            added_by INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (added_by) REFERENCES users(telegram_id)
                        )
                    ''')
                
                # Banned users table
                if self.use_postgres:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS banned_users (
                            id SERIAL PRIMARY KEY,
                            telegram_id BIGINT UNIQUE NOT NULL,
                            username TEXT,
                            reason TEXT,
                            banned_by BIGINT,
                            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (banned_by) REFERENCES users(telegram_id)
                        )
                    ''')
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS banned_users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id BIGINT UNIQUE NOT NULL,
                            username TEXT,
                            reason TEXT,
                            banned_by INTEGER,
                            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (banned_by) REFERENCES users(telegram_id)
                        )
                    ''')
                
                conn.commit()
                logging.info(f"✅ Database initialized successfully (PostgreSQL: {self.use_postgres})")
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            raise
    
    # ========== USERS ==========
    
    def add_or_update_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None):
        """Add new user or update existing"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO users (telegram_id, username, first_name, last_name)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (telegram_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        last_active = CURRENT_TIMESTAMP
                ''', (telegram_id, username, first_name, last_name))
            else:
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
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO user_settings (user_id, voice_mode)
                    VALUES (%s, 0)
                    ON CONFLICT (user_id) DO NOTHING
                ''', (telegram_id,))
            else:
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
            if self.use_postgres:
                cursor.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE DATE(last_active) = CURRENT_DATE
                ''')
            else:
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
            self._execute(cursor, '''
                INSERT INTO chat_history (user_id, role, content)
                VALUES (?, ?, ?)
            ''', (user_id, role, content))
            conn.commit()
    
    def get_chat_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get recent chat history for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, '''
                SELECT role, content FROM chat_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            rows = cursor.fetchall()
            if self.use_postgres:
                return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
            else:
                return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
    
    def clear_chat_history(self, user_id: int):
        """Clear chat history for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, 'DELETE FROM chat_history WHERE user_id = ?', (user_id,))
            conn.commit()
    
    # ========== CONTACTS ==========
    
    def add_contact(self, name: str, phone: str, added_by: int) -> bool:
        """Add new contact"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                self._execute(cursor, '''
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
            self._execute(cursor, '''
                DELETE FROM contacts WHERE id = ? AND added_by = ?
            ''', (contact_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts by name or phone"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgres:
                cursor.execute('''
                    SELECT id, name, phone FROM contacts
                    WHERE name ILIKE %s OR phone ILIKE %s
                    ORDER BY name
                ''', (f'%{query}%', f'%{query}%'))
            else:
                cursor.execute('''
                    SELECT id, name, phone FROM contacts
                    WHERE name LIKE ? OR phone LIKE ?
                    ORDER BY name
                ''', (f'%{query}%', f'%{query}%'))
            
            rows = cursor.fetchall()
            if self.use_postgres:
                return [{"id": row[0], "name": row[1], "phone": row[2]} for row in rows]
            else:
                return [{"id": row["id"], "name": row["name"], "phone": row["phone"]} for row in rows]
    
    def get_all_contacts(self) -> List[Dict]:
        """Get all contacts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, phone FROM contacts ORDER BY name')
            rows = cursor.fetchall()
            if self.use_postgres:
                return [{"id": row[0], "name": row[1], "phone": row[2]} for row in rows]
            else:
                return [{"id": row["id"], "name": row["name"], "phone": row["phone"]} for row in rows]
    
    def get_contact_by_id(self, contact_id: int) -> Optional[Dict]:
        """Get single contact by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, 'SELECT id, name, phone FROM contacts WHERE id = ?', (contact_id,))
            row = cursor.fetchone()
            if row:
                if self.use_postgres:
                    return {"id": row[0], "name": row[1], "phone": row[2]}
                else:
                    return {"id": row["id"], "name": row["name"], "phone": row["phone"]}
            return None
    
    # ========== USER SETTINGS ==========
    
    def get_voice_mode(self, user_id: int) -> bool:
        """Get voice mode setting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, 'SELECT voice_mode FROM user_settings WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return bool(row[0] if self.use_postgres else row["voice_mode"])
            return False
    
    def set_voice_mode(self, user_id: int, enabled: bool):
        """Set voice mode"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO user_settings (user_id, voice_mode)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        voice_mode = EXCLUDED.voice_mode,
                        updated_at = CURRENT_TIMESTAMP
                ''', (user_id, 1 if enabled else 0))
            else:
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
            
            self._execute(cursor, 'SELECT COUNT(*) FROM chat_history WHERE user_id = ?', (user_id,))
            message_count = cursor.fetchone()[0]
            
            self._execute(cursor, 'SELECT COUNT(*) FROM contacts WHERE added_by = ?', (user_id,))
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
            rows = cursor.fetchall()
            if self.use_postgres:
                return [{"telegram_id": row[0], "username": row[1], "first_name": row[2]} for row in rows]
            else:
                return [{"telegram_id": row["telegram_id"], "username": row["username"],
                        "first_name": row["first_name"]} for row in rows]
    
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
            
            if self.use_postgres:
                cursor.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE DATE(last_active) = CURRENT_DATE
                ''')
            else:
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
                
                if self.use_postgres:
                    cursor.execute('''
                        INSERT INTO news_articles 
                        (title, link, summary, category, source_name, source_category, 
                         published, sentiment, sentiment_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (link) DO NOTHING
                    ''', (
                        item['title'], item['link'], item['summary'], 
                        item['category'], item.get('source_name', ''),
                        item.get('source_category', ''), item['published'],
                        item.get('sentiment', 'neutral'), item.get('sentiment_score', 0.0)
                    ))
                else:
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
        # Handle empty categories list
        if not categories:
            return []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                placeholders = ','.join('%s' for _ in categories)
                cursor.execute(f'''
                    SELECT * FROM news_articles 
                    WHERE category IN ({placeholders})
                    AND DATE(published) >= CURRENT_DATE - INTERVAL '3 days'
                    ORDER BY published DESC
                    LIMIT %s
                ''', (*categories, limit))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
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
            
            if self.use_postgres:
                cursor.execute('''
                    SELECT * FROM news_articles 
                    WHERE DATE(published) >= CURRENT_DATE - INTERVAL '3 days'
                    ORDER BY published DESC
                    LIMIT %s
                ''', (limit,))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
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
                
                if self.use_postgres:
                    cursor.execute('''
                        INSERT INTO user_interests (user_id, category)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id, category) DO NOTHING
                    ''', (user_id, category.lower()))
                else:
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
            self._execute(cursor, '''
                DELETE FROM user_interests WHERE user_id = ? AND category = ?
            ''', (user_id, category.lower()))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_user_interests(self, user_id: int) -> List[str]:
        """Get all interests for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, '''
                SELECT category FROM user_interests WHERE user_id = ?
            ''', (user_id,))
            if self.use_postgres:
                return [row[0] for row in cursor.fetchall()]
            else:
                return [row['category'] for row in cursor.fetchall()]
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        return ['tech', 'ai', 'science', 'space', 'finance', 'kyrgyzstan', 'world', 'sports', 'other']
    
    # ========== NEWS FEEDBACK ==========
    
    def add_news_feedback(self, user_id: int, news_id: int, feedback: int):
        """Add user feedback for news (1=like, -1=dislike)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO user_news_feedback (user_id, news_id, feedback)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, news_id) DO UPDATE SET
                        feedback = EXCLUDED.feedback
                ''', (user_id, news_id, feedback))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_news_feedback (user_id, news_id, feedback)
                    VALUES (?, ?, ?)
                ''', (user_id, news_id, feedback))
            
            conn.commit()
    
    def get_user_feedback_stats(self, user_id: int) -> Dict:
        """Get feedback statistics for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, '''
                SELECT feedback, COUNT(*) as count 
                FROM user_news_feedback 
                WHERE user_id = ?
                GROUP BY feedback
            ''', (user_id,))
            
            if self.use_postgres:
                stats = {row[0]: row[1] for row in cursor.fetchall()}
            else:
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
            
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO digest_schedules (user_id, enabled, schedule_time)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        enabled = EXCLUDED.enabled,
                        schedule_time = EXCLUDED.schedule_time
                ''', (user_id, 1 if enabled else 0, schedule_time))
            else:
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
            self._execute(cursor, '''
                SELECT * FROM digest_schedules WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            
            if row:
                if self.use_postgres:
                    return {
                        'enabled': bool(row[2]),
                        'schedule_time': row[3],
                        'last_sent': row[4]
                    }
                else:
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
            
            if self.use_postgres:
                cursor.execute('''
                    SELECT user_id FROM digest_schedules 
                    WHERE enabled = 1 
                    AND schedule_time = %s
                    AND (last_sent IS NULL OR DATE(last_sent) < CURRENT_DATE)
                ''', (current_time,))
                return [row[0] for row in cursor.fetchall()]
            else:
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
            self._execute(cursor, '''
                UPDATE digest_schedules SET last_sent = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()

    # ========== ADMIN MANAGEMENT ==========
    
    def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin (including main admin from env)"""
        import os
        main_admin = int(os.environ.get("ADMIN_ID", "0"))
        if telegram_id == main_admin:
            return True
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, '''
                SELECT COUNT(*) FROM admins WHERE telegram_id = ?
            ''', (telegram_id,))
            return cursor.fetchone()[0] > 0
    
    def add_admin(self, telegram_id: int, username: str, added_by: int, role: str = 'admin') -> bool:
        """Add new admin"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.use_postgres:
                    cursor.execute('''
                        INSERT INTO admins (telegram_id, username, role, added_by)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (telegram_id) DO UPDATE SET
                            username = EXCLUDED.username,
                            role = EXCLUDED.role
                    ''', (telegram_id, username, role, added_by))
                else:
                    cursor.execute('''
                        INSERT INTO admins (telegram_id, username, role, added_by)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(telegram_id) DO UPDATE SET
                            username = excluded.username,
                            role = excluded.role
                    ''', (telegram_id, username, role, added_by))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding admin: {e}")
            return False
    
    def remove_admin(self, telegram_id: int) -> bool:
        """Remove admin (can't remove main admin)"""
        import os
        main_admin = int(os.environ.get("ADMIN_ID", "0"))
        if telegram_id == main_admin:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, '''
                DELETE FROM admins WHERE telegram_id = ?
            ''', (telegram_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all_admins(self) -> List[Dict]:
        """Get all admins"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name, u.last_name 
                FROM admins a
                LEFT JOIN users u ON a.telegram_id = u.telegram_id
                ORDER BY a.created_at DESC
            ''')
            rows = cursor.fetchall()
            if self.use_postgres:
                return [{
                    "id": row[0], "telegram_id": row[1], "username": row[2],
                    "role": row[3], "added_by": row[4], "created_at": row[5],
                    "first_name": row[6], "last_name": row[7]
                } for row in rows]
            else:
                return [dict(row) for row in rows]
    
    def update_admin_role(self, telegram_id: int, new_role: str) -> bool:
        """Update admin role"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, '''
                UPDATE admins SET role = ? WHERE telegram_id = ?
            ''', (new_role, telegram_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # ========== BAN MANAGEMENT ==========
    
    def is_banned(self, telegram_id: int) -> Optional[Dict]:
        """Check if user is banned"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, '''
                SELECT * FROM banned_users WHERE telegram_id = ?
            ''', (telegram_id,))
            row = cursor.fetchone()
            if row:
                if self.use_postgres:
                    return {
                        "id": row[0], "telegram_id": row[1], "username": row[2],
                        "reason": row[3], "banned_by": row[4], "banned_at": row[5]
                    }
                else:
                    return dict(row)
            return None
    
    def ban_user(self, telegram_id: int, username: str, reason: str, banned_by: int) -> bool:
        """Ban user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.use_postgres:
                    cursor.execute('''
                        INSERT INTO banned_users (telegram_id, username, reason, banned_by)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (telegram_id) DO UPDATE SET
                            reason = EXCLUDED.reason,
                            banned_by = EXCLUDED.banned_by,
                            banned_at = CURRENT_TIMESTAMP
                    ''', (telegram_id, username, reason, banned_by))
                else:
                    cursor.execute('''
                        INSERT INTO banned_users (telegram_id, username, reason, banned_by)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(telegram_id) DO UPDATE SET
                            reason = excluded.reason,
                            banned_by = excluded.banned_by,
                            banned_at = CURRENT_TIMESTAMP
                    ''', (telegram_id, username, reason, banned_by))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error banning user: {e}")
            return False
    
    def unban_user(self, telegram_id: int) -> bool:
        """Unban user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._execute(cursor, '''
                DELETE FROM banned_users WHERE telegram_id = ?
            ''', (telegram_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all_banned(self) -> List[Dict]:
        """Get all banned users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.*, u.first_name, u.last_name,
                       admin.first_name as admin_first_name
                FROM banned_users b
                LEFT JOIN users u ON b.telegram_id = u.telegram_id
                LEFT JOIN users admin ON b.banned_by = admin.telegram_id
                ORDER BY b.banned_at DESC
            ''')
            rows = cursor.fetchall()
            if self.use_postgres:
                return [{
                    "id": row[0], "telegram_id": row[1], "username": row[2],
                    "reason": row[3], "banned_by": row[4], "banned_at": row[5],
                    "first_name": row[6], "last_name": row[7],
                    "admin_name": row[8]
                } for row in rows]
            else:
                return [dict(row) for row in rows]
    
    def get_admin_stats_extended(self) -> Dict:
        """Extended admin statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM contacts')
            total_contacts = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM chat_history')
            total_messages = cursor.fetchone()[0]
            
            # Admins count
            cursor.execute('SELECT COUNT(*) FROM admins')
            total_admins = cursor.fetchone()[0]
            
            # Banned count
            cursor.execute('SELECT COUNT(*) FROM banned_users')
            total_banned = cursor.fetchone()[0]
            
            # Active today
            if self.use_postgres:
                cursor.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE DATE(last_active) = CURRENT_DATE
                ''')
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE date(last_active) = date('now')
                ''')
            active_today = cursor.fetchone()[0]
            
            return {
                "total_users": total_users,
                "total_contacts": total_contacts,
                "total_messages": total_messages,
                "total_admins": total_admins,
                "total_banned": total_banned,
                "active_today": active_today
            }
