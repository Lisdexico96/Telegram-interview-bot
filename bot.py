"""
Telegram Bot for OnlyFans Chatter Interview Process
Main entry point - clean and organized
"""

import os
import sys
import time
import logging
import subprocess
import signal
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import NetworkError, TimedOut, TelegramError, Conflict

from config import DB_FILE
from database import init_database, clear_database, close_database, get_cursor

# Configure logging (log file in bot directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(SCRIPT_DIR, 'bot.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from bot directory
ENV_PATH = os.path.join(SCRIPT_DIR, '.env')
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please create a .env file with BOT_TOKEN=your_token")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID not found in environment variables. Please create a .env file with ADMIN_CHAT_ID=your_chat_id")

ADMIN_IDS = [int(x) for x in ADMIN_CHAT_ID.split(",")]

# Import handlers AFTER ADMIN_IDS is defined to avoid import issues
from handlers import start_handler, handle_message, stop_command, error_handler

# Global application instance for graceful shutdown
app_instance = None

# Signal handler for Railway/cloud deployments
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    stop_bot()
    sys.exit(0)


def stop_bot():
    """Stop the bot gracefully and close all connections."""
    global app_instance
    
    try:
        logger.info("Stopping bot...")
        
        if app_instance:
            logger.info("Stopping Telegram bot application...")
            try:
                # Use async shutdown if event loop is running
                if app_instance.updater and app_instance.updater.running:
                    app_instance.stop()
                    # Let run_polling handle the shutdown, don't call shutdown() manually
                logger.info("Bot application stopped")
            except Exception as e:
                logger.warning(f"Error stopping application: {e}")
        
        close_database()
        
        logger.info("Bot stopped successfully")
        return True
    except Exception as e:
        logger.error(f"Error stopping bot: {e}", exc_info=True)
        return False


def kill_all_bot_processes():
    """Kill all running bot.py processes (excluding this one)."""
    try:
        if sys.platform == 'win32':
            try:
                result = subprocess.run(
                    ['wmic', 'process', 'where', 'commandline like "%bot.py%"', 'get', 'processid'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                pids = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.isdigit():
                        pid = int(line)
                        if pid != os.getpid():
                            pids.append(pid)
                
                for pid in pids:
                    try:
                        subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                     check=False, capture_output=True)
                        logger.info(f"Killed bot process {pid}")
                    except Exception as e:
                        logger.warning(f"Could not kill process {pid}: {e}")
            except Exception as e:
                logger.warning(f"Error finding processes on Windows: {e}")
        else:
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, check=False)
                
                for line in result.stdout.split('\n'):
                    if 'bot.py' in line and 'grep' not in line:
                        parts = line.split()
                        if parts:
                            try:
                                pid = int(parts[1])
                                if pid != os.getpid():
                                    os.kill(pid, signal.SIGTERM)
                                    logger.info(f"Killed bot process {pid}")
                            except (ValueError, IndexError, ProcessLookupError):
                                pass
            except Exception as e:
                logger.warning(f"Error finding processes on Unix: {e}")
    except Exception as e:
        logger.error(f"Error in kill_all_bot_processes: {e}")


def main() -> None:
    """Start the bot - main entry point."""
    global app_instance
    
    # Register signal handlers for graceful shutdown (Railway/cloud deployments)
    if sys.platform != 'win32':
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    try:
        logger.info("Initializing bot...")
        logger.info(f"Running on platform: {sys.platform}")
        logger.info(f"Python version: {sys.version}")
        
        # Initialize database
        init_database()
        clear_database()  # Clear once per day
        
        # Build application
        # Note: Timeouts are handled by the underlying httpx library
        # Default timeouts should be sufficient, but we'll verify connection first
        app_instance = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Register handlers (with admin functions for stop command)
        app_instance.add_handler(CommandHandler("start", start_handler))
        app_instance.add_handler(CommandHandler("stop", 
            lambda u, c: stop_command(u, c, ADMIN_IDS, stop_bot, kill_all_bot_processes)))
        app_instance.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app_instance.add_error_handler(error_handler)
        
        logger.info("Bot is starting...")
        logger.info(f"Bot token: {BOT_TOKEN[:10]}...")  # Log first 10 chars for verification
        
        logger.info("Press Ctrl+C to stop the bot")
        
        # Start polling with error handling
        # Note: run_polling() handles its own shutdown, so we don't manually stop/shutdown
        try:
            app_instance.run_polling(
                drop_pending_updates=True,
                allowed_updates=None  # Allow all updates
            )
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            # run_polling() already handles shutdown on KeyboardInterrupt
            close_database()
        except Conflict as e:
            logger.error(f"Conflict error: {e}")
            logger.error("Another bot instance is running with the same token.")
            logger.error("Please stop all other bot instances before starting this one.")
            logger.info("Attempting to kill other bot processes...")
            kill_all_bot_processes()
            logger.info("Waiting 3 seconds before retrying...")
            time.sleep(3)
            logger.info("Retrying bot start...")
            # Try one more time after killing processes
            try:
                app_instance.run_polling(drop_pending_updates=True)
            except Conflict:
                logger.error("Still conflicts after cleanup. Please manually stop all bot instances.")
                close_database()
                sys.exit(1)
        except (NetworkError, TimedOut) as e:
            logger.error(f"Network error during polling: {e}")
            logger.error("Bot will attempt to reconnect automatically on next message.")
            close_database()
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during polling: {e}", exc_info=True)
            close_database()
            raise
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        close_database()
        raise


if __name__ == '__main__':
    main()
