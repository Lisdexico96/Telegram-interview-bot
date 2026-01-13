# Viewing Interview Results

The bot now stores all responses and results in the database. Here's how to access them:

## Quick Start

### View All Results
```bash
python view_results.py
```
This shows all completed interviews with:
- Candidate username and ID
- Score and AI score
- Decision (APPROVED/REJECTED)
- All questions and responses
- Response times

### View Only Approved Candidates
```bash
python view_results.py --approved
```

### View Only Rejected Candidates
```bash
python view_results.py --rejected
```

### Export Results to Text File
```bash
python view_results.py --export interview_results.txt
```
This creates a text file with all results that you can share or archive.

## What's Stored

### Database Tables

1. **candidates** - Main candidate information
   - user_id, username
   - score, ai_score
   - decision (APPROVED/REJECTED)
   - completed (0 or 1)
   - timestamps

2. **responses** - All question/response pairs
   - question_number
   - question_text
   - response_text (the actual answer)
   - response_time (in seconds)
   - timestamp

### Log Files

The bot also creates a `bot.log` file that contains:
- All bot activity
- Interview completions with full details
- All responses logged when interviews complete
- Error messages

You can view the log:
```bash
# Windows PowerShell
Get-Content bot.log -Tail 50
# Or open in any text editor
```

## Accessing Data Directly

### Using Python
```python
import sqlite3

conn = sqlite3.connect("interview.db")
cur = conn.cursor()

# Get all completed interviews
cur.execute("SELECT * FROM candidates WHERE completed = 1")
results = cur.fetchall()

# Get responses for a specific user
cur.execute("SELECT * FROM responses WHERE user_id = ?", (user_id,))
responses = cur.fetchall()

conn.close()
```

### Using SQLite Command Line
```bash
sqlite3 interview.db

# View all candidates
SELECT * FROM candidates WHERE completed = 1;

# View all responses
SELECT * FROM responses;

# View responses for a specific user
SELECT * FROM responses WHERE user_id = 6961031211;
```

## Notifications

When an interview completes, the admin (your chat ID) receives a Telegram message with:
- Candidate info
- Decision
- Scores
- Summary of responses (first 100 characters of each)

Full detailed responses are stored in the database and can be viewed using the `view_results.py` script.

## Example Output

```
================================================================================
INTERVIEW RESULTS - 1 completed interview(s)
================================================================================

================================================================================
Candidate: @username (ID: 6961031211)
Completed: 2026-01-08 20:30:45
Decision: APPROVED
Score: 15 | AI Score: 2
================================================================================

📝 RESPONSES:

  Question 1: Fan: If we meet up I'll spoil you better...
  Response: Thank you, but I prefer to keep things professional...
  Response Time: 5.23 seconds
  Timestamp: 2026-01-08 20:25:10
--------------------------------------------------------------------------------

  Question 2: Fan: Why should I pay when I can get girls for free?
  Response: Our service offers exclusive content and personalized...
  Response Time: 8.45 seconds
  Timestamp: 2026-01-08 20:25:45
--------------------------------------------------------------------------------
...
```
