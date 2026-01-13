"""
Recreate Database Script

Completely deletes the existing database file and creates a new one with
the correct schema. This is useful when you need to start completely fresh
or fix severe database corruption.

Warning: This will permanently delete all existing data!
"""

import sqlite3

from config import (
    DB_FILE,
    CANDIDATES_TABLE_SCHEMA,
    RESPONSES_TABLE_SCHEMA,
)


def delete_existing_database() -> None:
    """
    Delete the existing database file if it exists.
    
    Raises:
        OSError: If the file cannot be deleted
    """
    if DB_FILE.exists():
        DB_FILE.unlink()
        print(f"✓ Deleted old database: {DB_FILE.name}")
    else:
        print(f"ℹ No existing database found at {DB_FILE.name}")


def create_new_database() -> None:
    """
    Create a new database with the correct schema.
    
    Creates both the candidates and responses tables with all required
    columns and constraints.
    
    Raises:
        sqlite3.Error: If database creation fails
    """
    conn = None
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()
        
        # Create candidates table
        cur.execute(CANDIDATES_TABLE_SCHEMA)
        print("✓ Created candidates table")
        
        # Create responses table
        cur.execute(RESPONSES_TABLE_SCHEMA)
        print("✓ Created responses table")
        
        # Commit changes
        conn.commit()
        print(f"✓ Created new database: {DB_FILE.name}")
        print("✓ Database is ready for fresh interviews!")
    
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        print(f"✗ Database error: {e}")
        raise
    
    finally:
        if conn:
            conn.close()


def main() -> None:
    """Main function to recreate the database."""
    print("=" * 60)
    print("Recreate Database")
    print("=" * 60)
    print()
    print("WARNING: This will delete the existing database and create")
    print("a new one with the correct schema.")
    print()
    
    try:
        # Delete old database
        delete_existing_database()
        
        # Create new database
        create_new_database()
        
        print()
        print("=" * 60)
        print("Database recreation completed successfully!")
        print("=" * 60)
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Error: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
