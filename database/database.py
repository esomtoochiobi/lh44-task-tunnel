import sqlite3

DB_NAME = "task_tunnel.db"

def get_connection():
  return sqlite3.connect(DB_NAME)

def init_db():
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        resource TEXT NOT NULL,
        FOREIGN KEY(profile_id) REFERENCES profiles(id)
    )
    """)

  conn.commit()
  conn.close()