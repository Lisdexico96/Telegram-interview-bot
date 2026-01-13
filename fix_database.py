"""
Fix Database Script

Fixes database schema issues by adding missing columns and clearing all data.
This is useful when the database schema is outdated or corrupted.

The script:
1. Adds any missing columns to the candidates table
2. Clears all existing data
3. Verifies the database state

Warning: This will clear all existing data!
"""

import sqlite3
from typing import List, Tuple

from config import (
    DB_FILE,
    CANDIDATES_MIGRATION_COLUMNS,
)


def column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    """
    Check if a column exists in a table.
    
    Args:
        cur: Database cursor
        table: Table name
        column: Column name
        
    Returns:
        True if column exists, False otherwise
    """
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]
    return column in columns


def add_missing_columns(cur: sqlite3.Cursor) -> List[str]:
    """
    Add any missing columns to the candidates table.
    
    Args:
        cur: Database cursor
        
    Returns:
        List of column names that were added
    """
    added_columns = []
    
    for col_name, col_type in CANDIDATES_MIGRATION_COLUMNS:
        if not column_exists(cur, "candidates", col_name):
            try:
                cur.execute(
                    f"ALTER TABLE candidates ADD COLUMN {col_name} {col_type}"
                )
                print(f"  ✓ Added column: {col_name}")
                added_columns.append(col_name)
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    print(f"  ℹ Column '{col_name}' already exists")
                else:
                    print(f"  ✗ Error adding column '{col_name}': {e}")
        else:
            print(f"  ℹ Column '{col_name}' already exists")
    
    return added_columns


def clear_all_data(cur: sqlite3.Cursor) -> Tuple[int, int]:
    """
    Clear all data from the database.
    
    Args:
        cur: Database cursor
        
    Returns:
        Tuple of (candidate_count, response_count) before deletion
    """
    # Get counts before deletion
    cur.execute("SELECT COUNT(*) FROM candidates")
    candidate_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM responses")
    response_count = cur.fetchone()[0]
    
    # Delete all data (order matters due to foreign key constraints)
    cur.execute("DELETE FROM responses")
    cur.execute("DELETE FROM candidates")
    
    # Reset flags for any remaining records (safety measure)
    cur.execute(
        "UPDATE candidates SET "
        "has_completed_interview = 0, "
        "completed = 0, "
        "score = 0, "
        "ai_score = 0"
    )
    
    return candidate_count, response_count


def fix_database() -> None:
    """
    Fix database schema and clear all data.
    
    Raises:
        FileNotFoundError: If database file doesn't exist
        sqlite3.Error: If database operation fails
    """
    if not DB_FILE.exists():
        print(f"✗ Database file '{DB_FILE.name}' not found.")
        print("   Please create the database first using recreate_database.py")
        return
    
    conn = None
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()
        
        print("Fixing database schema...")
        print()
        
        # Add missing columns
        added_columns = add_missing_columns(cur)
        
        if added_columns:
            print(f"\n✓ Added {len(added_columns)} missing column(s)")
        else:
            print("\n✓ All required columns already exist")
        
        print()
        print("Clearing all data...")
        
        # Clear all data
        candidate_count, response_count = clear_all_data(cur)
        
        print(f"  ✓ Deleted {candidate_count} candidate(s)")
        print(f"  ✓ Deleted {response_count} response(s)")
        
        # Commit changes
        conn.commit()
        
        # Verify final state
        cur.execute("SELECT COUNT(*) FROM candidates")
        final_candidate_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM responses")
        final_response_count = cur.fetchone()[0]
        
        print()
        print("=" * 60)
        print("✓ Database fixed and cleared successfully!")
        print("=" * 60)
        print()
        print("Final database state:")
        print(f"  Candidates: {final_candidate_count}")
        print(f"  Responses: {final_response_count}")
        print()
        print("Database is ready for fresh interviews!")
    
    except sqlite3.OperationalError as e:
        if conn:
            conn.rollback()
        print(f"\n✗ Database error: {e}")
        print("Make sure the bot is not running, then try again.")
        raise
    
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\n✗ Error: {e}")
        raise
    
    finally:
        if conn:
            conn.close()


def main() -> None:
    """Main function to fix the database."""
    print("=" * 60)
    print("Fix Database Schema")
    print("=" * 60)
    print()
    print("This will:")
    print("  1. Add any missing columns to the candidates table")
    print("  2. Clear all existing data from the database")
    print()
    
    try:
        fix_database()
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Error: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
