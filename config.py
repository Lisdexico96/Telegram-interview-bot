"""
Configuration constants for the Telegram Interview Bot scripts.
Centralizes shared settings and database schema definitions.
"""

from pathlib import Path
from typing import List, Tuple

# ============================================================================
# PATHS
# ============================================================================

# Base directory for the project
BASE_DIR = Path(__file__).parent

# Database file path
DB_FILE = BASE_DIR / "interview.db"

# ============================================================================
# DATABASE SCHEMA
# ============================================================================

# Candidates table schema
CANDIDATES_TABLE_SCHEMA = """
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
    has_completed_interview INTEGER DEFAULT 0
)
"""

# Responses table schema
RESPONSES_TABLE_SCHEMA = """
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
"""

# Columns that may need to be added to existing databases
CANDIDATES_MIGRATION_COLUMNS: List[Tuple[str, str]] = [
    ("name", "TEXT"),
    ("completed", "INTEGER DEFAULT 0"),
    ("decision", "TEXT"),
    ("feedback", "TEXT"),
    ("has_completed_interview", "INTEGER DEFAULT 0"),
]

# ============================================================================
# SCRIPT LAUNCHER CONFIGURATION
# ============================================================================

# GUI window settings
WINDOW_TITLE = "Telegram Interview Bot - Script Launcher"
WINDOW_SIZE = "800x600"
FONT_TITLE = ('Arial', 16, 'bold')
FONT_DESCRIPTION = ('Arial', 8)
FONT_OUTPUT = ('Consolas', 9)

# Output text area height
OUTPUT_HEIGHT = 15
