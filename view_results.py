#!/usr/bin/env python3
"""
Script to view interview results from the database.
Shows all candidates with their responses, scores, and decisions.
"""

import sqlite3
import sys
from datetime import datetime

from config import DB_FILE

def view_all_results():
    """View all interview results."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()
        
        # Get all completed interviews
        cur.execute("""
        SELECT user_id, username, name, score, ai_score, decision, completed, last_time
        FROM candidates
        WHERE completed = 1
        ORDER BY last_time DESC
        """)
        candidates = cur.fetchall()
        
        if not candidates:
            print("No completed interviews found.")
            return
        
        print("=" * 80)
        print(f"INTERVIEW RESULTS - {len(candidates)} completed interview(s)")
        print("=" * 80)
        
        for user_id, username, name, score, ai_score, decision, completed, last_time in candidates:
            timestamp = datetime.fromtimestamp(last_time).strftime("%Y-%m-%d %H:%M:%S")
            display_name = name if name else (f"@{username}" if username else f"User {user_id}")
            
            print(f"\n{'='*80}")
            print(f"Candidate: {display_name}")
            if name and username:
                print(f"Username: @{username}")
            print(f"User ID: {user_id}")
            print(f"Completed: {timestamp}")
            print(f"Decision: {decision}")
            print(f"Score: {score} | AI Score: {ai_score}")
            print(f"{'='*80}")
            
            # Get all responses for this candidate
            cur.execute("""
            SELECT question_number, question_text, response_text, response_time, timestamp
            FROM responses
            WHERE user_id = ?
            ORDER BY question_number
            """, (user_id,))
            responses = cur.fetchall()
            
            if responses:
                print("\n📝 RESPONSES:")
                for q_num, q_text, r_text, r_time, r_timestamp in responses:
                    response_time = datetime.fromtimestamp(r_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n  Question {q_num+1}: {q_text}")
                    print(f"  Response: {r_text}")
                    print(f"  Response Time: {r_time:.2f} seconds")
                    print(f"  Timestamp: {response_time}")
                    print("-" * 80)
            else:
                print("\n⚠️  No responses found for this candidate.")
            
            print()
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def view_approved_only():
    """View only approved candidates."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()
        
        cur.execute("""
        SELECT user_id, username, name, score, ai_score, decision, last_time
        FROM candidates
        WHERE completed = 1 AND decision = 'APPROVED'
        ORDER BY score DESC, last_time DESC
        """)
        candidates = cur.fetchall()
        
        if not candidates:
            print("No approved candidates found.")
            return
        
        print("=" * 80)
        print(f"APPROVED CANDIDATES - {len(candidates)} candidate(s)")
        print("=" * 80)
        
        for user_id, username, name, score, ai_score, decision, last_time in candidates:
            timestamp = datetime.fromtimestamp(last_time).strftime("%Y-%m-%d %H:%M:%S")
            display_name = name if name else (f"@{username}" if username else f"User {user_id}")
            print(f"\n{display_name} (ID: {user_id}) | Score: {score} | AI: {ai_score} | Completed: {timestamp}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

def view_rejected_only():
    """View only rejected candidates."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()
        
        cur.execute("""
        SELECT user_id, username, name, score, ai_score, decision, last_time
        FROM candidates
        WHERE completed = 1 AND decision = 'REJECTED'
        ORDER BY score DESC, last_time DESC
        """)
        candidates = cur.fetchall()
        
        if not candidates:
            print("No rejected candidates found.")
            return
        
        print("=" * 80)
        print(f"REJECTED CANDIDATES - {len(candidates)} candidate(s)")
        print("=" * 80)
        
        for user_id, username, name, score, ai_score, decision, last_time in candidates:
            timestamp = datetime.fromtimestamp(last_time).strftime("%Y-%m-%d %H:%M:%S")
            display_name = name if name else (f"@{username}" if username else f"User {user_id}")
            print(f"\n{display_name} (ID: {user_id}) | Score: {score} | AI: {ai_score} | Completed: {timestamp}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

def export_to_text(filename="interview_results.txt"):
    """Export all results to a text file."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cur = conn.cursor()
        
        cur.execute("""
        SELECT user_id, username, name, score, ai_score, decision, completed, last_time
        FROM candidates
        WHERE completed = 1
        ORDER BY last_time DESC
        """)
        candidates = cur.fetchall()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"INTERVIEW RESULTS - {len(candidates)} completed interview(s)\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for user_id, username, name, score, ai_score, decision, completed, last_time in candidates:
                timestamp = datetime.fromtimestamp(last_time).strftime("%Y-%m-%d %H:%M:%S")
                display_name = name if name else (f"@{username}" if username else f"User {user_id}")
                
                f.write(f"{'='*80}\n")
                f.write(f"Candidate: {display_name}\n")
                if name and username:
                    f.write(f"Username: @{username}\n")
                f.write(f"User ID: {user_id}\n")
                f.write(f"Completed: {timestamp}\n")
                f.write(f"Decision: {decision}\n")
                f.write(f"Score: {score} | AI Score: {ai_score}\n")
                f.write(f"{'='*80}\n\n")
                
                cur.execute("""
                SELECT question_number, question_text, response_text, response_time, timestamp
                FROM responses
                WHERE user_id = ?
                ORDER BY question_number
                """, (user_id,))
                responses = cur.fetchall()
                
                if responses:
                    f.write("RESPONSES:\n")
                    for q_num, q_text, r_text, r_time, r_timestamp in responses:
                        response_time = datetime.fromtimestamp(r_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"\n  Question {q_num+1}: {q_text}\n")
                        f.write(f"  Response: {r_text}\n")
                        f.write(f"  Response Time: {r_time:.2f} seconds\n")
                        f.write(f"  Timestamp: {response_time}\n")
                        f.write("-" * 80 + "\n")
                
                f.write("\n")
        
        conn.close()
        print(f"Results exported to {filename}")
        
    except Exception as e:
        print(f"Error exporting: {e}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--approved" or sys.argv[1] == "-a":
            view_approved_only()
        elif sys.argv[1] == "--rejected" or sys.argv[1] == "-r":
            view_rejected_only()
        elif sys.argv[1] == "--export" or sys.argv[1] == "-e":
            filename = sys.argv[2] if len(sys.argv) > 2 else "interview_results.txt"
            export_to_text(filename)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage:")
            print("  python view_results.py              # View all results")
            print("  python view_results.py --approved   # View only approved")
            print("  python view_results.py --rejected   # View only rejected")
            print("  python view_results.py --export [filename]  # Export to text file")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        view_all_results()

if __name__ == "__main__":
    main()
