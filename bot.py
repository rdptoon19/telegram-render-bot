# This script is configured to run as a Webhook on Render or similar hosting.
# The necessary environment variables (PORT, WEBHOOK_URL, BOT_TOKEN) 
# will be provided automatically by the Render service.

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# --- RENDER CONFIGURATION ---
# Render automatically sets the PORT variable for web services
PORT = int(os.environ.get('PORT', '8443')) 

# The full URL provided by Render (e.g., https://your-app-name.onrender.com)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# --- BOT CONFIGURATION ---
# The Bot Token is fetched from the secure environment variables on Render
BOT_TOKEN = os.environ.get('BOT_TOKEN') 
# Your confirmed Chat ID is hardcoded here (5599633069)
TARGET_CHAT_ID = '5599633069' 

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcoming message."""
    await update.message.reply_text(
        f"👋 Hello! This bot is now live and monitoring the score for you (Chat ID: {TARGET_CHAT_ID})."
    )

async def score_update_loop(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    This function simulates a background task that periodically checks a score
    and sends a message to the TARGET_CHAT_ID.
    It runs every 60 seconds.
    """
    
    # ----------------------------------------------------
    # TODO: Replace this simulated logic with your actual API calls 
    # to check the real-time score data.
    # ----------------------------------------------------
    
    score_data = context.job.data
    
    # Simulate a goal every time the job runs
    score_data['Home'] += 1
    
    current_score = f"{score_data['Home']} - {score_data['Away']}"
    update_message = f"🚨 **SCORE ALERT** 🚨\n\nMan Utd vs. Liverpool\nNew Score: {current_score}"
    
    try:
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID, 
            text=update_message, 
            parse_mode='Markdown'
        )
        logger.info(f"Score sent: {current_score}")
    except TelegramError as e:
        logger.error(f"Error sending message to chat ID {TARGET_CHAT_ID}: {e}")
        # Stop the job if the chat ID is invalid or the bot is blocked
        if 'chat not found' in str(e):
             context.job.schedule_removal()
             logger.warning("Job removed: Chat ID not valid.")


def main() -> None:
    """Start the bot and the background score monitor."""

    # 1. Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # 2. Add handlers
    application.add_handler(CommandHandler("start", start))

    # 3. Add the periodic job (The background score checker)
    job_queue = application.job_queue
    
    # Initial score state to pass to the job
    initial_score = {'Home': 0, 'Away': 0}
    
    # Set the job to run every 60 seconds (1 minute)
    job_queue.run_repeating(score_update_loop, interval=60, first=10, data=initial_score)

    # 4. Set up the Webhook
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL environment variable is not set. Cannot run in production.")
        return

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,  # Use the token as a secret path
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )
    logger.info(f"Bot started on port {PORT}. Webhook URL: {WEBHOOK_URL}/{BOT_TOKEN}")


if __name__ == '__main__':
    # Initial checks for required environment variables
    if not BOT_TOKEN:
        logger.error("FATAL: BOT_TOKEN environment variable is not set. Deployment failed.")
    else:
        main()

