import sqlite3
from datetime import datetime
from src.core.constants import DB_NAME
import logging

# Function to adapt datetime objects for SQLite
def adapt_datetime(dt):
    return dt.isoformat()

# Register the adapter
sqlite3.register_adapter(datetime, adapt_datetime)

def setup_db():
    """Create tables if they don't exist."""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                score INTEGER DEFAULT 0,
                language TEXT DEFAULT 'en',
                last_interaction TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if difficulty column exists, if not, alter the table
        c.execute("PRAGMA table_info(quizzes)")
        columns = c.fetchall()
        column_names = [column[1] for column in columns]
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question TEXT,
                answer TEXT,
                quiz_type TEXT,
                difficulty TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # If difficulty column is missing, try to add it
        if 'difficulty' not in column_names:
            try:
                c.execute("""
                    ALTER TABLE quizzes 
                    ADD COLUMN difficulty TEXT
                """)
            except sqlite3.OperationalError:
                # Column might already exist
                pass
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                old_username TEXT,
                new_username TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS score_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                score INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()

def ensure_user_in_db(user):
    """Ensure the user exists in the database."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, username FROM users WHERE id=?", (user.id,))
            result = c.fetchone()
            
            current_time = datetime.now()
            
            if result is None:
                # New user
                c.execute("""
                    INSERT INTO users (id, username, score, last_interaction, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user.id, user.username or 'Anonymous', 0, current_time, current_time))
                
                # Initialize score history
                c.execute("""
                    INSERT INTO score_history (user_id, score)
                    VALUES (?, 0)
                """, (user.id,))
            else:
                # Existing user - check if username changed
                old_username = result[1]
                if user.username and old_username != user.username:
                    c.execute("""
                        INSERT INTO user_audit (user_id, old_username, new_username)
                        VALUES (?, ?, ?)
                    """, (user.id, old_username, user.username))
                    c.execute("UPDATE users SET username=? WHERE id=?", (user.username, user.id))
                
                # Update last interaction
                c.execute("UPDATE users SET last_interaction=? WHERE id=?", (current_time, user.id))
            
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error in ensure_user_in_db: {e}")

def get_user_language(user_id):
    """Get the user's preferred language."""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT language FROM users WHERE id=?", (user_id,))
        result = c.fetchone()
    return result[0] if result else 'en'

def update_user_score(user_id, new_score):
    """Update user's score and add to history."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET score = ? WHERE id = ?", (new_score, user_id))
            c.execute("""
                INSERT INTO score_history (user_id, score)
                VALUES (?, ?)
            """, (user_id, new_score))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error in update_user_score: {e}")

def log_quiz_attempt(user_id, question, answer, quiz_type, difficulty):
    """Log a quiz attempt in the database."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            
            # Ensure all parameters are strings
            question = str(question)
            answer = str(answer)
            quiz_type = str(quiz_type or 'General')
            difficulty = str(difficulty or 'unknown')
            
            c.execute("""
                INSERT INTO quizzes (user_id, question, answer, quiz_type, difficulty, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (user_id, question, answer, quiz_type, difficulty))
            conn.commit()
            logging.info(f"Quiz attempt logged for user {user_id}")
    except sqlite3.Error as e:
        logging.error(f"Database error in log_quiz_attempt: {e}")
        logging.error(f"Failed to log quiz attempt details:")
        logging.error(f"User ID: {user_id}")
        logging.error(f"Question: {question}")
        logging.error(f"Answer: {answer}")
        logging.error(f"Quiz Type: {quiz_type}")
        logging.error(f"Difficulty: {difficulty}") 