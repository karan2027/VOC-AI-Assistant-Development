import sqlite3
import os
import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("assistant.memory")

class ConversationMemory:
    def __init__(self, db_path: str = "database/memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the database and creates tables if they don't exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Conversations history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        role TEXT NOT NULL,
                        message TEXT NOT NULL
                    )
                """)
                # User preference key-value pairs
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                """)
                # Context long-term facts
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS context_memory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        fact TEXT UNIQUE NOT NULL
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully at %s", self.db_path)
        except Exception as e:
            logger.error("Failed to initialize database: %s", e)

    def save_message(self, role: str, message: str):
        """Saves a conversation message (user or assistant)."""
        timestamp = datetime.datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO conversations (timestamp, role, message) VALUES (?, ?, ?)",
                    (timestamp, role, message)
                )
                conn.commit()
        except Exception as e:
            logger.error("Failed to save message to database: %s", e)

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieves recent conversation messages."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role, message FROM conversations ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                rows = cursor.fetchall()
                # Return in chronological order
                return [{"role": row["role"], "message": row["message"]} for row in reversed(rows)]
        except Exception as e:
            logger.error("Failed to retrieve conversation history: %s", e)
            return []

    def set_preference(self, key: str, value: str):
        """Sets a user preference or setting."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
                    (key, value)
                )
                conn.commit()
                logger.info("Preference set: %s = %s", key, value)
        except Exception as e:
            logger.error("Failed to set preference: %s", e)

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Gets a user preference by key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
                row = cursor.fetchone()
                return row[0] if row else default
        except Exception as e:
            logger.error("Failed to retrieve preference: %s", e)
            return default

    def add_fact(self, fact: str):
        """Saves a fact in the long-term context memory."""
        timestamp = datetime.datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO context_memory (timestamp, fact) VALUES (?, ?)",
                    (timestamp, fact)
                )
                conn.commit()
                logger.info("Fact saved: %s", fact)
        except Exception as e:
            logger.error("Failed to save fact: %s", e)

    def get_all_facts(self) -> List[str]:
        """Retrieves all long-term context facts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT fact FROM context_memory ORDER BY id DESC")
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error("Failed to retrieve facts: %s", e)
            return []

    def clear_history(self):
        """Clears conversation logs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations")
                conn.commit()
                logger.info("Conversation history cleared.")
        except Exception as e:
            logger.error("Failed to clear history: %s", e)
            
    def clear_all(self):
        """Clears all data in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations")
                cursor.execute("DELETE FROM preferences")
                cursor.execute("DELETE FROM context_memory")
                conn.commit()
                logger.info("All database tables cleared.")
        except Exception as e:
            logger.error("Failed to clear database: %s", e)
