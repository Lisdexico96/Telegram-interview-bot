"""
Check Database Script

Displays information about the current database state, including:
- Database file existence
- Table structure (columns)
- Number of candidates and responses
- List of all candidates with their data

This is a read-only operation that does not modify the database.
"""

import sqlite3
from typing import List, Tuple

from config import DB_FILE


def get_table_structure(cur: sqlite3.Cursor, table_name: str) -> List[Tuple]:
    """
    Get the structure of a database table.
    
    Args:
        cur: Database cursor
        table_name: Name of the table to inspect
        
    Returns:
        List of column information tuples
    """
    cur.execute(f"PRAGMA table_info({table_name})")
    return cur.fetchall()


def print_table_structure(cur: sqlite3.Cursor, table_name: str) -> None:
    """
    Print the structure of a database table.
    
    Args:
        cur: Database cursor
        table_name: Name of the table to display
    """
    columns = get_table_structure(cur, table_name)
    
    if not columns:
        print(f"  ℹ Table '{table_name}' has no columns")
        return
    
    print(f"{table_name.title()} table structure:")
    print(f"  {'Column Name':<25} {'Type':<15} {'Nullable':<10} {'Default'}")
    print(f"  {'-'*25} {'-'*15} {'-'*10} {'-'*20}")
    
    for col in columns:
        col_id, name, data_type, not_null, default_val, pk = col
        nullable = "No" if not_null else "Yes"
        default = default_val if default_val else "NULL"
        
        print(f"  {name:<25} {data_type:<15} {nullable:<10} {default}")
    
    print()


def get_candidates(cur: sqlite3.Cursor) -> List[Tuple]:
    """
    Get all candidates from the database.
    
    Args:
        cur: Database cursor
        
    Returns:
        List of candidate records
    """
    cur.execute("SELECT * FROM candidates")
    return cur.fetchall()


def get_record_counts(cur: sqlite3.Cursor) -> Tuple[int, int]:
    """
    Get the count of candidates and responses.
    
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


def print_candidate_info(candidates: List[Tuple], cur: sqlite3.Cursor) -> None:
    """
    Print detailed information about candidates.
    
    Args:
        candidates: List of candidate records
        cur: Database cursor (for getting column names)
    """
    if not candidates:
        print("No candidates found in database.")
        return
    
    # Get column names
    columns = get_table_structure(cur, "candidates")
    column_names = [col[1] for col in columns]
    
    print("Candidates in database:")
    print()
    
    for i, candidate in enumerate(candidates, 1):
        print(f"  Candidate #{i}:")
        for col_name, value in zip(column_names, candidate):
            print(f"    {col_name}: {value}")
        print()


def check_database() -> None:
    """
    Check and display database status and contents.
    
    Raises:
        sqlite3.Error: If database access fails
    """
    if not DB_FILE.exists():
        print(f"✗ Database file '{DB_FILE.name}' not found.")
        print(f"   Expected location: {DB_FILE}")
        print()
        print("   Run recreate_database.py to create the database.")
        return
    
    print("=" * 60)
    print("Database Status Check")
    print("=" * 60)
    print()
    print(f"Database file: {DB_FILE.name}")
    print(f"Full path: {DB_FILE}")
    print(f"File size: {DB_FILE.stat().st_size:,} bytes")
    print()
    
    conn = None
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()
        
        # Show table structure
        print_table_structure(cur, "candidates")
        print_table_structure(cur, "responses")
        
        # Get record counts
        candidate_count, response_count = get_record_counts(cur)
        
        print("Database Statistics:")
        print(f"  Candidates: {candidate_count}")
        print(f"  Responses: {response_count}")
        print()
        
        # Show candidate details
        candidates = get_candidates(cur)
        print_candidate_info(candidates, cur)
        
        print("=" * 60)
        print("✓ Database check completed")
        print("=" * 60)
    
    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        raise
    
    finally:
        if conn:
            conn.close()


def main() -> None:
    """Main function to check the database."""
    try:
        check_database()
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Error: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
