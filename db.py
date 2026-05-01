import sqlite3

DB_NAME = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
    
def init_db():
    with sqlite3.connect(DB_NAME, timeout=5, check_same_thread=False) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            completed INTEGER DEFAULT 0,
            user_email TEXT
        )
        """)
