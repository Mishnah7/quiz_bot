# 🤖 Quiz Bot - Telegram Trivia Challenge

## Overview

Quiz Bot is an interactive Telegram bot that offers an engaging trivia experience with multiple difficulty levels, multilingual support, and score tracking.

## 🌟 Features

- Multiple difficulty levels (Easy, Medium, Hard)
- Multilingual support
- Real-time scoring system
- Leaderboard
- Automatic quiz scheduling
- User profile and history tracking

## 🚀 Prerequisites

- Python 3.8+
- Telegram Bot Token

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/quiz-bot.git
cd quiz-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Bot Token

Create a `.env` file in the project root:

```
BOT_TOKEN=your_telegram_bot_token_here
```

## 🎮 Usage

### Running the Bot

```bash
python -m src.core.bot
```

### Available Commands

- `/start` - Initialize or reset your profile
- `/quiz` - Choose quiz difficulty and start
- `/leaderboard` - See top scorers
- `/user_info` - Check your own information
- `/set_language` - Change the bot's language
- `/my_quizzes` - See your quiz history
- `/schedule_quiz` - Schedule automatic quizzes
- `/score_history` - View your score history
- `/help` - Show help message

## 🛠 Technologies

- Python
- Telegram Bot API
- SQLite
- python-telegram-bot
- Deep Translator

## 📦 Project Structure

```
quiz-bot/
│
├── src/
│   ├── core/
│   │   ├── bot.py        # Main bot entry point
│   │   └── constants.py  # Configuration constants
│   ├── api/
│   │   └── quiz_api.py   # Quiz API interactions
│   ├── database/
│   │   └── database.py   # Database operations
│   ├── handlers/
│   │   └── handlers.py   # Telegram bot command handlers
│   └── utils/
│       └── utils.py      # Utility functions
│
├── .env                  # Environment variables
├── setup.py              # Package setup
└── requirements.txt      # Project dependencies
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

Your Name - [realloC]

Project Link: [https://github.com/yourusername/quiz-bot](https://github.com/yourusername/quiz-bot)
