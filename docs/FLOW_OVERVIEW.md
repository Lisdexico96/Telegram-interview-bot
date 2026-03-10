# Bot flow: order of processes and what happens at every step

This repository now ships with one active bot: the Python interview bot. An older Node.js prototype is still kept under `legacy/node-prototype/` for reference only.

---

## 1. Python bot (`python bot.py`) — Interview with 5 questions

**Data:** Stored in SQLite (`interview.db`). Admins get a Telegram notification when someone finishes.

### Step-by-step flow

| Step | User action | What the bot does |
|------|-------------|-------------------|
| **1** | User sends **`/start`** | Bot checks if they already completed (or have an interview in progress). If completed → shows result message and stops. If in progress → tells them to continue. If fresh → clears/resets their record, then asks: *"Please tell us your first name to get started."* |
| **2** | User sends **first name** (e.g. "Maria") | Bot validates (2–20 chars, no dots/newlines). Picks **5 random questions** from the pool and saves them for this user. Sends welcome message (*"Hello [name] 👋 …"*) and **first question**. Saves name and moves to question 1. |
| **3** | User sends **answer to question 1** | Bot scores the answer (rules + optional AI). Saves the response in DB. Sends **question 2**. |
| **4** | User sends **answer to question 2** | Same: score, save, send **question 3**. |
| **5** | User sends **answer to question 3** | Same: score, save, send **question 4**. |
| **6** | User sends **answer to question 4** | Same: score, save, send **question 5**. |
| **7** | User sends **answer to question 5** | Bot scores the last answer. Computes **final decision**: APPROVED, BORDERLINE, or NOT ELIGIBLE (from total score + AI score). Generates feedback text. Marks interview as **completed** (user cannot retake unless admin). Sends **feedback** to the user. If user is not an admin, bot **notifies admin(s)** via Telegram with candidate summary. |

**After completion**

- If user sends **`/start`** again → Bot says they already completed and shows the result (accepted vs. not accepted).
- **Admins** (IDs in `ADMIN_CHAT_ID`) can retake unlimited times; they see "Admin Test Mode" and no completion lock.

**Summary order:** `/start` → first name → welcome + Q1 → answer Q1 → Q2 → … → answer Q5 → decision + feedback + admin notification.

---

## 2. Archived Node.js prototype (`legacy/node-prototype/`) — reference only

**Data:** Passed applicants are appended to a **Google Sheet** (if configured). No SQLite.

### Step-by-step flow

| Step | User action | What the bot does |
|------|-------------|-------------------|
| **1** | User sends **`/start`** | Bot clears any previous “collecting” state and replies: *"Hello! 👋 Please tell us your first name to get started."* (This message is generic; the first real “application” is the next text.) |
| **2** | User sends **any text** (e.g. short intro / application) | Bot sends that text to **OpenAI** for evaluation. Bot replies with: **Score**, **Decision** (PASS or REJECT), and **Feedback**. |
| **3a** | If decision is **REJECT** | Flow ends. User can send another message to be evaluated again (each message is evaluated independently). |
| **3b** | If decision is **PASS** | Bot stores state (phase: collecting, step: name) and asks: *"What is your full name?"* |
| **4** | User sends **full name** | Bot saves it and asks: *"What is your email address?"* |
| **5** | User sends **email** | Bot saves it and asks: *"What is your phone number?"* |
| **6** | User sends **phone** | Bot saves it. If **Google Sheet is configured**: builds one row (Full Name, Email, Phone, Telegram Username, Telegram User ID, Application notes), appends to the sheet, then replies: *"✅ Your information has been saved. We will be in touch soon."* If **not configured**: replies that details were received but the sheet is not connected. Bot clears the user’s state. |

**After collection**

- User can send **`/start`** again and send new text to get a new evaluation (and possibly enter the PASS → collect details flow again).

**Summary order:** `/start` → application text → AI review (PASS/REJECT) → if PASS: full name → email → phone → save to Google Sheet (or “received but not saved”) → done.

---

## Quick comparison

| | Python bot | Node.js bot |
|--|------------|-------------|
| **Starts with** | `/start` then first name | `/start` then any application text |
| **Main flow** | 5 random interview questions, one by one | One AI evaluation per message |
| **Scoring** | Per-answer scoring + final decision (APPROVED / BORDERLINE / NOT ELIGIBLE) | Single PASS/REJECT per message |
| **Data stored** | SQLite (responses, scores, decision); admin notified on completion | Google Sheet row (only if PASS: name, email, phone, Telegram info, notes) |
| **Retake** | Blocked after completion (except admins) | Allowed; each message is a new evaluation |

Use the **Python bot** for the live interview flow. Use the archived Node.js section only if you need to understand or migrate older logic.
