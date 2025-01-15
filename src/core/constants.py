import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

ADMIN_ID = os.getenv("ADMIN_ID")
if not ADMIN_ID:
    raise ValueError("No ADMIN_ID found in environment variables")

# Alias for backward compatibility
YOUR_ADMIN_ID = ADMIN_ID

DB_NAME = 'quiz_bot.db'
LANGUAGES = {'en': 'English', 'es': 'Español', 'fr': 'Français'} 