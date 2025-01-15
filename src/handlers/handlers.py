from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from datetime import datetime, timedelta
import logging
import sqlite3
import asyncio
from src.database.database import (
    ensure_user_in_db, 
    get_user_language, 
    update_user_score,
    log_quiz_attempt
)
from src.api.quiz_api import QuizAPI, format_question
from src.utils.utils import translate_text
from src.core.constants import LANGUAGES, YOUR_ADMIN_ID, DB_NAME

# Store scheduled jobs per user
user_jobs = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    welcome_text = translate_text("Welcome to the Quiz Bot\\! Type /help for commands\\.", lang)
    await update.message.reply_text(welcome_text, parse_mode='MarkdownV2')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    help_text = translate_text("""*Available Commands:*

/start \\- Initialize or reset your profile
/quiz \\- Choose quiz difficulty and start
/leaderboard \\- See top scorers
/user\\_info \\- Check your own information
/all\\_users \\- List all users who have interacted with the bot
/set\\_language \\- Change the bot's language
/my\\_quizzes \\- See your quiz history
/schedule\\_quiz \\- Schedule automatic quizzes
/stop\\_schedule \\- Stop automatic quizzes
/score\\_history \\- View your score history
/my\\_score \\- View your current score
/reset \\- Reset your score to 0
/help \\- Show this help message""", get_user_language(user.id))
    await update.message.reply_text(help_text, parse_mode='MarkdownV2')

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    # Show difficulty selection keyboard
    keyboard = [
        [InlineKeyboardButton("🟢 Easy", callback_data="difficulty_easy")],
        [InlineKeyboardButton("🟡 Medium", callback_data="difficulty_medium")],
        [InlineKeyboardButton("🔴 Hard", callback_data="difficulty_hard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        translate_text("Choose difficulty level:", lang),
        reply_markup=reply_markup
    )

async def send_quiz(context: ContextTypes.DEFAULT_TYPE, user_id: int, difficulty: str = None):
    """Send a quiz to the user."""
    try:
        lang = get_user_language(user_id)
        quiz_api = QuizAPI()
        params = {'amount': 1, 'type': 'multiple'}
        if difficulty:
            params['difficulty'] = difficulty
        
        question_data = await quiz_api.get_question(params)
        await quiz_api.close()
        
        if not question_data:
            error_msg = translate_text("Sorry, I couldn't fetch a question right now. Please try again later.", lang)
            await context.bot.send_message(chat_id=user_id, text=error_msg)
            return
        
        formatted_q = format_question(question_data)
        keyboard = []
        for option in formatted_q['options']:
            keyboard.append([InlineKeyboardButton(option, callback_data=f"quiz_{option}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(difficulty, "")
        question_text = f"{difficulty_emoji} {translate_text(formatted_q['question'], lang)}"
        
        # Store both question and answer in user data
        if not hasattr(context, 'user_data'):
            context.user_data = {}
        context.user_data[f'current_answer_{user_id}'] = formatted_q['answer']
        context.user_data[f'current_question_{user_id}'] = question_text
        
        await context.bot.send_message(
            chat_id=user_id,
            text=question_text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error sending quiz: {e}")

async def schedule_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    # Cancel existing job if any
    if user.id in user_jobs:
        user_jobs[user.id].schedule_removal()
    
    # Schedule new quiz every 30 minutes
    job = context.job_queue.run_repeating(
        lambda ctx: send_quiz(ctx, user.id),
        interval=1800,  # 30 minutes
        first=5  # First quiz after 5 seconds
    )
    user_jobs[user.id] = job
    
    await update.message.reply_text(
        translate_text("✅ Automatic quizzes scheduled! You'll receive a new question every 30 minutes.", lang)
    )

async def stop_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    if user.id in user_jobs:
        user_jobs[user.id].schedule_removal()
        del user_jobs[user.id]
        await update.message.reply_text(
            translate_text("✅ Automatic quizzes stopped.", lang)
        )
    else:
        await update.message.reply_text(
            translate_text("❌ No scheduled quizzes found.", lang)
        )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT username, score 
            FROM users 
            ORDER BY score DESC 
            LIMIT 10
        """)
        leaders = c.fetchall()
    
    if not leaders:
        await update.message.reply_text(translate_text("No scores yet!", lang))
        return
    
    leaderboard_text = "*🏆 Leaderboard 🏆*\n\n"
    for i, (username, score) in enumerate(leaders, 1):
        leaderboard_text += f"{i}. {username}: {score} points\n"
    
    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

async def user_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT username, score, language, created_at 
            FROM users 
            WHERE id = ?
        """, (user.id,))
        user_data = c.fetchone()
    
    if not user_data:
        await update.message.reply_text(translate_text("User information not found.", lang))
        return
    
    username, score, language, created_at = user_data
    info_text = translate_text(f"""*Your Information:*
Username: {username}
Score: {score}
Language: {LANGUAGES.get(language, language)}
Member since: {created_at}""", lang)
    
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def set_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for lang_code, lang_name in LANGUAGES.items():
        keyboard.append([InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose your language:", reply_markup=reply_markup)

async def my_score_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT score FROM users WHERE id = ?", (user.id,))
        score = c.fetchone()[0]
    
    score_text = translate_text(f"Your current score is: {score} points", lang)
    await update.message.reply_text(score_text)

async def reset_score_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET score = 0 WHERE id = ?", (user.id,))
        conn.commit()
    
    reset_text = translate_text("Your score has been reset to 0.", lang)
    await update.message.reply_text(reset_text)

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    if query.data.startswith('difficulty_'):
        difficulty = query.data.split('_')[1]
        context.user_data[f'difficulty_{user.id}'] = difficulty  # Store user's difficulty preference
        await query.edit_message_text(
            translate_text(f"Selected difficulty: {difficulty.capitalize()}\nFetching question...", lang)
        )
        await send_quiz(context, user.id, difficulty)
    
    elif query.data.startswith('quiz_'):
        user_answer = query.data[5:]
        correct_answer = context.user_data.get(f'current_answer_{user.id}')
        current_question = context.user_data.get(f'current_question_{user.id}')
        difficulty = context.user_data.get(f'difficulty_{user.id}')
        
        # Log the quiz attempt
        log_quiz_attempt(
            user.id,
            current_question,
            correct_answer,
            "General",  # You can update this if you track categories
            difficulty
        )
        
        # Prepare the response message
        response_parts = []
        response_parts.append(f"*Question:*\n{current_question}")
        response_parts.append(f"\n*Your answer:* {user_answer}")
        response_parts.append(f"*Correct answer:* {correct_answer}")
        
        if user_answer == correct_answer:
            # Get current score and update it
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT score FROM users WHERE id = ?", (user.id,))
                current_score = c.fetchone()[0]
                new_score = current_score + 1
            
            # Update score and log in history
            update_user_score(user.id, new_score)
            response_parts.append(f"\n✅ *Correct!* You earned a point!\nTotal score: {new_score}")
        else:
            response_parts.append("\n❌ *Wrong!*")
        
        # Show the complete response
        await query.edit_message_text(
            text="\n".join(response_parts),
            parse_mode='Markdown'
        )
        
        # Wait 3 seconds before sending the next question
        await asyncio.sleep(3)
        
        # Send next question with same difficulty
        difficulty = context.user_data.get(f'difficulty_{user.id}')
        await send_quiz(context, user.id, difficulty)
    
    elif query.data.startswith('lang_'):
        new_lang = query.data[5:]
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET language = ? WHERE id = ?", (new_lang, user.id))
            conn.commit()
        
        response = translate_text("Language updated successfully!", new_lang)
        await query.edit_message_text(text=response)

async def all_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users who have interacted with the bot."""
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    # Debug logging for admin ID
    logging.info(f"User ID: {user.id}, Type: {type(user.id)}")
    logging.info(f"Admin ID: {YOUR_ADMIN_ID}, Type: {type(YOUR_ADMIN_ID)}")
    
    # Only admin can see all users
    if user.id != YOUR_ADMIN_ID:
        await update.message.reply_text(
            translate_text("❌ This command is only available to administrators.", lang)
        )
        return
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT username, score, language, last_interaction
            FROM users
            ORDER BY last_interaction DESC
        """)
        users = c.fetchall()
    
    if not users:
        await update.message.reply_text(translate_text("No users found.", lang))
        return
    
    users_text = "*👥 All Users:*\n\n"
    for username, score, language, last_interaction in users:
        users_text += f"*{username}*\n"
        users_text += f"Score: {score}\n"
        users_text += f"Language: {LANGUAGES.get(language, language)}\n"
        users_text += f"Last seen: {last_interaction}\n\n"
    
    await update.message.reply_text(users_text, parse_mode='Markdown')

async def my_quizzes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's quiz history."""
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT question, answer, quiz_type, created_at
            FROM quizzes
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (user.id,))
        quizzes = c.fetchall()
    
    if not quizzes:
        await update.message.reply_text(
            translate_text("You haven't taken any quizzes yet!", lang)
        )
        return
    
    history_text = "*📚 Your Recent Quizzes:*\n\n"
    for question, answer, quiz_type, created_at in quizzes:
        history_text += f"*Question:* {question}\n"
        history_text += f"*Answer:* {answer}\n"
        history_text += f"*Category:* {quiz_type}\n"
        history_text += f"*Date:* {created_at}\n\n"
    
    await update.message.reply_text(history_text, parse_mode='Markdown')

async def score_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's score history."""
    user = update.effective_user
    ensure_user_in_db(user)
    lang = get_user_language(user.id)
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT score, timestamp
            FROM score_history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (user.id,))
        scores = c.fetchall()
    
    if not scores:
        await update.message.reply_text(
            translate_text("No score history available yet!", lang)
        )
        return
    
    history_text = "*📈 Your Score History:*\n\n"
    for score, timestamp in scores:
        history_text += f"Score: {score} points\n"
        history_text += f"Date: {timestamp}\n\n"
    
    await update.message.reply_text(history_text, parse_mode='Markdown')

def setup_handlers(application):
    """Register all handlers with the application."""
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("user_info", user_info_command))
    application.add_handler(CommandHandler("set_language", set_language_command))
    application.add_handler(CommandHandler("my_score", my_score_command))
    application.add_handler(CommandHandler("reset", reset_score_command))
    application.add_handler(CommandHandler("schedule_quiz", schedule_quiz_command))
    application.add_handler(CommandHandler("stop_schedule", stop_schedule_command))
    application.add_handler(CommandHandler("all_users", all_users_command))
    application.add_handler(CommandHandler("my_quizzes", my_quizzes_command))
    application.add_handler(CommandHandler("score_history", score_history_command))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    
    # Add error handler
    application.add_error_handler(lambda update, context: logging.error(f"Update {update} caused error {context.error}")) 