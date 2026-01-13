# Telegram Interview Bot

A sophisticated Telegram bot for conducting automated interviews with candidates. Features randomized question selection, AI-powered response scoring, and comprehensive result tracking.

## Features

- 🤖 **Automated Interview Process**: Conducts structured interviews with candidates
- 🎲 **Randomized Questions**: Each interview randomly selects 5 questions from a pool of 53+ questions
- 📊 **Intelligent Scoring**: Evaluates responses based on multiple criteria (fan control, emotional investment, monetization, rebuttal skills, pacing)
- 👤 **Name Collection**: Collects candidate names for easy identification
- 📝 **Response Tracking**: Stores all questions and responses in a database
- 🔍 **Result Viewing**: View and export interview results with detailed analytics
- 🛠️ **Admin Test Mode**: Admins can retake interviews unlimited times for testing
- 📈 **Decision Making**: Automatically determines APPROVED, BORDERLINE, or NOT ELIGIBLE based on scores

## Requirements

- Python 3.11 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Telegram Chat ID (from [@userinfobot](https://t.me/userinfobot))

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd telegram-interview-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_CHAT_ID=your_chat_id_here
   ```
   
   For multiple admin IDs, separate with commas:
   ```
   ADMIN_CHAT_ID=123456789,987654321
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## Deployment to Railway (24/7 Hosting)

Deploy your bot to Railway for 24/7 operation without running it locally.

**Quick Start:**
1. Push your code to GitHub
2. Create a Railway account at [railway.app](https://railway.app)
3. Create a new project and connect your GitHub repository
4. Add environment variables in Railway dashboard:
   - `BOT_TOKEN` - Your Telegram bot token
   - `ADMIN_CHAT_ID` - Your Telegram chat ID
5. Railway will automatically deploy your bot

**Detailed Guide:** See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) for complete deployment instructions.

## Getting Your Credentials

### Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the token you receive (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Chat ID
1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Start a conversation with the bot
3. It will reply with your chat ID (a number like `123456789`)

## Usage

### Starting the Bot

```bash
python bot.py
```

The bot will:
- Initialize the database
- Connect to Telegram
- Start polling for messages

### Interview Flow

1. Candidate sends `/start` to the bot
2. Bot asks for candidate's name
3. Bot sends personalized welcome message
4. Bot asks 5 randomly selected questions
5. Bot evaluates responses and provides decision
6. Admin receives notification with results

### Viewing Results

View all interview results:
```bash
python view_results.py
```

View only approved candidates:
```bash
python view_results.py --approved
```

View only rejected candidates:
```bash
python view_results.py --rejected
```

Export results to a file:
```bash
python view_results.py --export results.txt
```

### Admin Commands

- `/start` - Start/restart interview (admins can retake unlimited times)
- `/stop` - Stop the bot (admin only)

## Project Structure

```
telegram-interview-bot/
├── bot.py              # Main entry point
├── handlers.py          # Message and command handlers
├── database.py         # Database operations
├── questions.py         # Question pool and randomization
├── scoring.py          # Response scoring logic
├── utils.py            # Utility functions (feedback, notifications)
├── config.py           # Configuration constants
├── view_results.py     # Script to view interview results
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Scoring System

The bot evaluates responses on a 0-10 scale per question across 5 categories:

1. **Fan Control & Power** (0-2 points): Confidence, not neediness
2. **Emotional Investment Building** (0-2 points): Relationship building
3. **Monetization Trajectory** (0-2 points): Subtle sales setup
4. **Rebuttal Skill** (0-2 points): Handling objections
5. **Pacing & Realism** (0-2 points): Natural conversation flow

**Total possible score**: 50 points (5 questions × 10 points)

**Decision thresholds**:
- **APPROVED**: Score ≥ 24 (48%) with AI score ≤ 6
- **BORDERLINE**: Score ≥ 18 (36%) with AI score ≤ 8
- **NOT ELIGIBLE**: Below thresholds

## Database

The bot uses SQLite to store:
- Candidate information (name, username, scores, decision)
- All interview responses (questions, answers, response times)
- Interview completion status

Database file: `interview.db` (created automatically)

## Admin Features

Admins (defined in `ADMIN_CHAT_ID`) have special privileges:
- Can retake interviews unlimited times for testing
- Bypass completion locks
- Receive test mode indicators
- Don't receive self-notifications when completing tests

## Logging

All bot activity is logged to:
- Console output (real-time)
- `bot.log` file (persistent)

Logs include:
- User interactions
- Interview completions
- Errors and warnings
- All responses and scores

## Troubleshooting

### Bot not responding
- Check that `BOT_TOKEN` is correct in `.env`
- Verify internet connection
- Check `bot.log` for errors
- Ensure only one bot instance is running

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version is 3.11+

### Database errors
- Delete `interview.db` to reset (will be recreated)
- Check file permissions in the bot directory

### Conflict errors
- Stop all running bot instances
- Wait a few seconds
- Restart the bot

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
1. Check the `bot.log` file for error messages
2. Review the troubleshooting section
3. Check that all environment variables are set correctly

## Security Notes

- **Never commit `.env` file** - It contains sensitive credentials
- Keep your `BOT_TOKEN` secret
- Don't share your `ADMIN_CHAT_ID` publicly
- The `.gitignore` file excludes sensitive files by default
