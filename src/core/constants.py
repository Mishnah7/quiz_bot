import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

DB_NAME = 'quiz_bot.db'
LANGUAGES = {'en': 'English', 'es': 'Español', 'fr': 'Français'}
YOUR_ADMIN_ID = 332948906  # Replace with your actual admin user ID 