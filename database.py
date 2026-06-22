import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'wedding.db')

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS host_script (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_no TEXT UNIQUE NOT NULL,
            bride_name TEXT NOT NULL,
            groom_name TEXT NOT NULL,
            wedding_date TEXT NOT NULL,
            host_name TEXT NOT NULL,
            current_version REAL DEFAULT 1.0,
            feedback_round INTEGER DEFAULT 0,
            finalized_status TEXT DEFAULT '未定稿',
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bride_name, groom_name, wedding_date)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS change_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            script_id INTEGER NOT NULL,
            modify_date TEXT NOT NULL,
            modify_paragraph TEXT NOT NULL,
            modify_reason TEXT NOT NULL,
            feedback_source TEXT,
            is_adopted INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (script_id) REFERENCES host_script(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS high_freq_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_text TEXT UNIQUE NOT NULL,
            occurrence_count INTEGER DEFAULT 1,
            first_occurrence TEXT DEFAULT CURRENT_TIMESTAMP,
            last_occurrence TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

def execute_query(sql, params=(), fetch_one=False):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    
    if fetch_one:
        result = cursor.fetchone()
    else:
        result = cursor.fetchall()
    
    conn.close()
    return result

def execute_non_query(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id