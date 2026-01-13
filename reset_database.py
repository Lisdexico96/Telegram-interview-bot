"""
Reset Database Script

Clears all interview data from the database while keeping the schema intact.
This is useful for resetting the bot during testing or when you want to
start fresh without losing the database structure.

This script requires the --yes flag to proceed, or can be run with
confirmation in the GUI launcher.
"""

import sqlite3
import sys
from typing import Tuple

from config import DB_FILE


def get_record_counts(cur: sqlite3.Cursor) -> Tuple[int, int]:
    """
    Get the current count of candidates and responses.
    
    Args:
        cur: Database cursor
        
    Returns:
        Tuple of (candidate_count, response_count)
    """
    cur.execute("SELECT COUNT(*) FROM candidates")
    candidate_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM responses")
    response_count = cur.fetchone()[0]
    
    return candidate_count, response_count


def reset_database() -> None:
    """
    Clear all data from the interview database.
    
    Deletes all records from both the candidates and responses tables,
    but preserves the database structure.
    
    Raises:
        FileNotFoundError: If database file doesn't exist
        sqlite3.Error: If database operation fails
    """
    if not DB_FILE.exists():
        print(f"ℹ Database file '{DB_FILE.name}' not found.")
        print("   Nothing to reset.")
        return
    
    conn = None
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()
        
        # Get counts before deletion
        candidate_count, response_count = get_record_counts(cur)
        
        print("Current database state:")
        print(f"  Candidates: {candidate_count}")
        print(f"  Responses: {response_count}")
        print()
        
        # Delete all data (order matters due to foreign key constraints)
        print("Deleting data...")
        cur.execute("DELETE FROM responses")
        print(f"  ✓ Deleted {response_count} response(s)")
        
        cur.execute("DELETE FROM candidates")
        print(f"  ✓ Deleted {candidate_count} candidate(s)")
        
        # Commit changes
        conn.commit()
        
        print()
        print("=" * 60)
        print("✓ Database reset completed successfully!")
        print("=" * 60)
        print()
        print("You can now start fresh interviews.")
    
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        print(f"✗ Database error: {e}")
        raise
    
    finally:
        if conn:
            conn.close()


def requires_confirmation() -> bool:
    """
    Check if the script was run with the --yes flag.
    
    Returns:
        True if confirmation is required, False if --yes flag is present
    """
    return "--yes" not in sys.argv and "-y" not in sys.argv


def main() -> None:
    """Main function to reset the database."""
    print("=" * 60)
    print("Interview Bot Database Reset")
    print("=" * 60)
    print()
    
    # Check if confirmation is required
    if requires_confirmation():
        print("This will delete ALL interview data from the database.")
        print()
        print("To proceed without confirmation, run:")
        print("  python reset_database.py --yes")
        print()
        print("Or use the GUI launcher which will prompt for confirmation.")
        return
    
    try:
        reset_database()
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Error: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
