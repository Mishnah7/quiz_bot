# Quick test commit to verify GitHub workflow

from telegram.ext import Application
from telegram import Update, BotCommand
from src.core.constants import TOKEN
from src.database.database import setup_db
from src.handlers.handlers import setup_handlers
import asyncio
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    """Start the bot."""
    # Setup
    logging.info("Starting bot...")
    setup_db()
    logging.info("Database setup complete")
    
    # Build application
    application = Application.builder().token(TOKEN).build()
    setup_handlers(application)
    logging.info("Handlers setup complete")
    
    # Set up commands menu
    commands = [
        BotCommand("start", "Initialize or reset your profile"),
        BotCommand("quiz", "Choose quiz difficulty and start"),
        BotCommand("leaderboard", "See top scorers"),
        BotCommand("user_info", "Check your own information"),
        BotCommand("all_users", "List all users who have interacted with the bot"),
        BotCommand("set_language", "Change the bot's language"),
        BotCommand("my_quizzes", "See your quiz history"),
        BotCommand("schedule_quiz", "Schedule automatic quizzes"),
        BotCommand("stop_schedule", "Stop automatic quizzes"),
        BotCommand("score_history", "View your score history"),
        BotCommand("my_score", "View your current score"),
        BotCommand("reset", "Reset your score to 0"),
        BotCommand("help", "Show this help message")
    ]
    application.bot.set_my_commands(commands)
    logging.info("Commands menu setup complete")
    
    # Start the bot
    logging.info("Starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main() 