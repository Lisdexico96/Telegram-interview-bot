# Railway Deployment Guide

This guide will help you deploy your Telegram Interview Bot to Railway for 24/7 operation.

## Prerequisites

- A Railway account ([railway.app](https://railway.app))
- A GitHub account (or Railway CLI)
- Your Telegram Bot Token
- Your Telegram Chat ID

## Step 1: Prepare Your Repository

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Verify these files exist**:
   - `Procfile` - Defines the worker process
   - `railway.json` - Railway configuration
   - `requirements.txt` - Python dependencies
   - `.env.example` - Environment variables template

## Step 2: Create Railway Project

### Option A: Via Railway Dashboard (Recommended)

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will automatically detect it's a Python project

### Option B: Via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to existing project or create new
railway link
```

## Step 3: Configure Environment Variables

In Railway dashboard:

1. Go to your project
2. Click on your service
3. Go to **"Variables"** tab
4. Add these environment variables:

   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_CHAT_ID=your_chat_id_here
   ```

   **Important**: 
   - Replace with your actual values
   - Do NOT include quotes around values
   - For multiple admin IDs, separate with commas: `ADMIN_CHAT_ID=123456789,987654321`

## Step 4: Deploy

### Automatic Deployment (GitHub)

1. Railway will automatically deploy when you push to your main branch
2. Go to **"Deployments"** tab to see build progress
3. Wait for deployment to complete (usually 2-3 minutes)

### Manual Deployment (CLI)

```bash
railway up
```

## Step 5: Verify Deployment

1. Check **"Logs"** tab in Railway dashboard
2. You should see:
   ```
   Initializing bot...
   Bot is starting...
   Bot token: 8108233182...
   ```
3. Test your bot on Telegram:
   - Send `/start` to your bot
   - It should respond asking for your name

## Step 6: Monitor Your Bot

### View Logs

- **Railway Dashboard**: Go to your service → **"Logs"** tab
- **CLI**: `railway logs`

### Check Status

- **Railway Dashboard**: Service status shows "Active" when running
- Bot will automatically restart if it crashes (up to 10 times)

## Troubleshooting

### Bot Not Responding

1. **Check Logs**:
   - Go to Railway dashboard → Logs
   - Look for error messages
   - Common issues:
     - `BOT_TOKEN not found` → Environment variable not set
     - `Conflict error` → Another instance running (unlikely on Railway)
     - `Network error` → Temporary connection issue

2. **Verify Environment Variables**:
   - Go to Variables tab
   - Ensure `BOT_TOKEN` and `ADMIN_CHAT_ID` are set correctly
   - No extra spaces or quotes

3. **Check Deployment Status**:
   - Ensure deployment completed successfully
   - Service status should be "Active"

### Build Failures

1. **Check `requirements.txt`**:
   - Ensure all dependencies are listed
   - Verify Python version compatibility

2. **Check Logs**:
   - Railway shows build logs
   - Look for Python errors or missing dependencies

### Database Issues

- Railway provides ephemeral storage
- Database resets on each deployment
- For persistent storage, consider:
  - Railway PostgreSQL addon
  - External database service
  - Or accept that data resets on redeploy

## Railway-Specific Features

### Automatic Restarts

- Railway automatically restarts your bot if it crashes
- Configured in `railway.json` with `restartPolicyMaxRetries: 10`

### Logs

- All logs are captured automatically
- Accessible via Railway dashboard
- Logs are retained for a limited time

### Environment Variables

- Set in Railway dashboard
- Can be updated without redeploying
- Changes take effect on next restart

### Scaling

- Railway can scale your service
- For a Telegram bot, one instance is sufficient
- Multiple instances would cause conflicts

## Cost Considerations

- Railway offers a **free tier** with:
  - $5 free credit monthly
  - 500 hours of usage
  - Perfect for a single bot instance

- **Pricing**:
  - Pay-as-you-go after free tier
  - Typically $5-10/month for 24/7 bot operation
  - Check [railway.app/pricing](https://railway.app/pricing) for current rates

## Updating Your Bot

1. **Make changes locally**
2. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin main
   ```
3. **Railway auto-deploys** (if connected to GitHub)
4. **Or deploy manually**:
   ```bash
   railway up
   ```

## Stopping the Bot

### Via Railway Dashboard

1. Go to your service
2. Click **"Settings"**
3. Click **"Delete Service"** (or pause if available)

### Via CLI

```bash
railway down
```

## Best Practices

1. **Never commit `.env`** - Always use Railway Variables
2. **Monitor logs regularly** - Catch issues early
3. **Test locally first** - Before pushing to Railway
4. **Use version control** - Keep your code in GitHub
5. **Set up alerts** - Railway can notify you of issues

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## Support

If you encounter issues:

1. Check Railway logs first
2. Verify environment variables
3. Test bot locally to isolate issues
4. Check Railway status page
5. Review Railway documentation

---

**Your bot is now running 24/7 on Railway! 🚀**
