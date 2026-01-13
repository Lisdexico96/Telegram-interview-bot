# Quick Setup Guide

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Step-by-Step Setup

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd telegram-interview-bot
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Get Your Telegram Credentials

#### Bot Token
1. Open Telegram
2. Search for [@BotFather](https://t.me/BotFather)
3. Send `/newbot`
4. Follow the instructions to create your bot
5. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### Chat ID
1. Open Telegram
2. Search for [@userinfobot](https://t.me/userinfobot)
3. Start a conversation
4. The bot will reply with your chat ID (a number)

### 4. Configure Environment Variables

**On Windows:**
```powershell
Copy-Item .env.example .env
notepad .env
```

**On Linux/Mac:**
```bash
cp .env.example .env
nano .env
```

Edit `.env` and replace the placeholder values:
```
BOT_TOKEN=your_actual_token_here
ADMIN_CHAT_ID=your_actual_chat_id_here
```

### 5. Run the Bot

```bash
python bot.py
```

You should see:
```
Initializing bot...
Bot is starting...
Press Ctrl+C to stop the bot
```

### 6. Test the Bot

1. Open Telegram
2. Search for your bot (the username you gave it)
3. Send `/start`
4. Follow the interview process

## Troubleshooting

**"BOT_TOKEN not found"**
- Make sure `.env` file exists in the same directory as `bot.py`
- Check that `BOT_TOKEN=` line is in the file
- Verify there are no extra spaces around the `=`

**"Module not found" errors**
- Run: `pip install -r requirements.txt`
- Make sure you're using Python 3.11+

**Bot not responding**
- Check `bot.log` for error messages
- Verify your internet connection
- Make sure only one instance of the bot is running

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [README_VIEW_RESULTS.md](README_VIEW_RESULTS.md) for viewing interview results
- Review the code structure in [CODE_ORGANIZATION.md](CODE_ORGANIZATION.md)
