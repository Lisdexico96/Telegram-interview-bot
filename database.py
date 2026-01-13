"""
Database operations and setup
"""

import sqlite3
import os
import logging
from datetime import datetime
from config import DB_FILE

logger = logging.getLogger(__name__)

# Global database connection
conn = None
cur = None


def init_database():
    """Initialize database connection and create tables if needed."""
    global conn, cur
    
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    cur = conn.cursor()
    
    # Create candidates table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        question_index INTEGER DEFAULT -1,
        score INTEGER DEFAULT 0,
        ai_score INTEGER DEFAULT 0,
        last_time REAL,
        completed INTEGER DEFAULT 0,
        decision TEXT,
        feedback TEXT,
        has_completed_interview INTEGER DEFAULT 0,
        selected_questions TEXT
    )
    """)
    
    # Add new columns if they don't exist (for existing databases)
    try:
        cur.execute("ALTER TABLE candidates ADD COLUMN feedback TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        cur.execute("ALTER TABLE candidates ADD COLUMN has_completed_interview INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        cur.execute("ALTER TABLE candidates ADD COLUMN selected_questions TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Migrate existing completed=1 records to has_completed_interview=1
    cur.execute("UPDATE candidates SET has_completed_interview = 1 WHERE completed = 1")
    
    # Create responses table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_number INTEGER,
        question_text TEXT,
        response_text TEXT,
        response_time REAL,
        timestamp REAL,
        FOREIGN KEY (user_id) REFERENCES candidates(user_id)
    )
    """)
    
    conn.commit()
    logger.info("Database initialized successfully")


def clear_database():
    """Clear all data from the database only once today."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        flag_file = "last_clear_date.txt"
        
        # Check if we've already cleared today
        if os.path.exists(flag_file):
            with open(flag_file, 'r') as f:
                last_clear_date = f.read().strip()
            if last_clear_date == today:
                logger.info(f"Database already cleared today ({today}). Skipping clear.")
                return
        
        # Clear the database
        logger.info(f"Clearing database for today ({today})...")
        cur.execute("DELETE FROM responses")
        cur.execute("DELETE FROM candidates")
        cur.execute("DELETE FROM sqlite_sequence")
        conn.commit()
        
        # Save today's date to flag file
        with open(flag_file, 'w') as f:
            f.write(today)
        
        logger.info("Database cleared successfully (only for today)")
    except Exception as e:
        logger.error(f"Error clearing database: {e}", exc_info=True)


def close_database():
    """Close database connection."""
    global conn
    if conn:
        conn.close()
        logger.info("Database connection closed")


def get_cursor():
    """Get database cursor."""
    return cur


def get_connection():
    """Get database connection."""
    return conn
