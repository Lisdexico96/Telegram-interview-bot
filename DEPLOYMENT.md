# Deployment Guide

This bot can be deployed to various platforms for 24/7 operation.

## 🚂 Railway (Recommended)

Railway is the easiest way to deploy this bot. See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) for detailed instructions.

**Quick Steps:**
1. Push code to GitHub
2. Create Railway project
3. Connect GitHub repository
4. Add environment variables
5. Deploy!

## 🐳 Docker (Alternative)

You can also deploy using Docker:

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### Build and Run

```bash
docker build -t telegram-interview-bot .
docker run -d --env-file .env telegram-interview-bot
```

## ☁️ Other Platforms

### Heroku

1. Create `Procfile`: `worker: python bot.py`
2. Deploy via Heroku CLI or GitHub integration
3. Set environment variables in Heroku dashboard

### Render

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python bot.py`
5. Add environment variables

### DigitalOcean App Platform

1. Create new app from GitHub
2. Select Python buildpack
3. Set run command: `python bot.py`
4. Add environment variables

## Environment Variables

All platforms require these environment variables:

- `BOT_TOKEN` - Your Telegram bot token
- `ADMIN_CHAT_ID` - Your Telegram chat ID (comma-separated for multiple)

## Important Notes

- **Never commit `.env` file** - Always use platform's environment variable settings
- **Database persistence** - Most platforms use ephemeral storage. Consider external database for persistent data
- **Logs** - Check platform's logging system for bot output
- **Restarts** - Configure automatic restarts on failure

## Support

For platform-specific issues, refer to:
- Railway: [docs.railway.app](https://docs.railway.app)
- Docker: [docs.docker.com](https://docs.docker.com)
- Heroku: [devcenter.heroku.com](https://devcenter.heroku.com)
