# Bot verification: OpenAI + Airtable

This checklist confirms the **single bot** you run is the one that uses OpenAI for decisions and saves passed applicants to Airtable.

---

## Which bot runs

- **Entry point:** `npm start` → runs `node index.js` (Telegraf).
- **Procfile:** `worker: npm start`
- **Railway:** `startCommand`: `npm start`

So the **only running instance** is the **Node.js bot** (`index.js`).

---

## 1. OpenAI for decision making

- **File:** `index.js` uses `evaluateApplicant(text)` from `evaluateApplicant.js`.
- **Flow:** On every text message (after `/start`), the bot calls OpenAI (GPT-4o-mini), gets a **score**, **PASS/REJECT** decision, and **feedback**, then replies with that to the user.
- **Env:** `OPENAI_API_KEY` must be set (in `.env` or Railway Variables). If missing, the bot says: "Evaluation is not configured. Add OPENAI_API_KEY in .env".

**Verify in code:**
- `index.js` line ~4: `const evaluateApplicant = require('./evaluateApplicant');`
- `index.js` line ~92–98: checks `OPENAI_API_KEY`, then `await evaluateApplicant(text)`.
- `evaluateApplicant.js`: uses `OPENAI_API_KEY`, calls OpenAI API.

---

## 2. Airtable for saving passed applicants

- **File:** `index.js` uses `appendApplicant(...)` from `airtable.js` (not `sheets.js`).
- **Flow:** When the decision is **PASS**, the bot asks for full name → email → phone, then calls `appendApplicant(...)` to create one Airtable record.
- **Env:** `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID` must be set. Optional: `AIRTABLE_TABLE_NAME` (default `Chatters`).

**Verify in code:**
- `index.js` line ~4: `const { appendApplicant } = require('./airtable');`
- `index.js` line ~65–69: checks `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID`, then `await appendApplicant({ fullName, email, phone, ... })`.
- `airtable.js`: builds Airtable API request with fields **Name**, **Email**, **Phone**, **Telegram Username**, **Telegram User ID**, **Application notes**, **Status** (= `Passed`).

**Airtable table:** Your base must have a table (e.g. "Hiring database") with these **exact** field names (or the API will fail):

- Name  
- Email  
- Phone  
- Telegram Username  
- Telegram User ID  
- Application notes  
- Status  

---

## 3. Env vars to set (Railway or .env)

| Variable | Required | Purpose |
|----------|----------|---------|
| `BOT_TOKEN` | ✅ | Telegram bot token |
| `OPENAI_API_KEY` | ✅ | OpenAI decisions (PASS/REJECT) |
| `AIRTABLE_API_KEY` | ✅ | Airtable API (save passed applicants) |
| `AIRTABLE_BASE_ID` | ✅ | Airtable base ID (e.g. `appXXXXXXXX`) |
| `AIRTABLE_TABLE_NAME` | Optional | Table name (default: `Chatters`) |
| `ADMIN_CHAT_ID` | Optional | For future admin features |

---

## 4. Quick test

1. Start the bot: `npm start` (or deploy on Railway).
2. In Telegram: send `/start`, then any short application message.
3. You should get a reply with **Score**, **Decision** (PASS or REJECT), and **Feedback** → confirms **OpenAI** is used.
4. If the decision is **PASS**, the bot asks for name → email → phone, then says "Your information has been saved" → confirms **Airtable** is used. Check your Airtable table for the new record.

---

## Summary

- **One bot:** Node.js (`index.js`), started with `npm start`.
- **OpenAI:** Used for every application message; decision = PASS or REJECT.
- **Airtable:** One new record per **passed** applicant (name, email, phone, Telegram info, application notes, Status = Passed).
