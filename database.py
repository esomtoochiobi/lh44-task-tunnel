import sqlite3

DB_NAME = "task_tunnel.db"

def get_connection():
  return sqlite3.connect(DB_NAME)

def _db_exists(cursor) -> bool:
  cursor.execute("PRAGMA user_version;")
  version = cursor.fetchone()[0]

  if version != 0:
    return True
  
  cursor.execute("PRAGMA user_version = 1;")
  return False

def init_db(include_dummy=False):
  conn = get_connection()
  cursor = conn.cursor()

  try:
    with conn:
      if _db_exists(cursor):
        return
      
      cursor.execute("PRAGMA foreign_keys = ON;")
      
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
            FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
        """)
    
    if include_dummy:
      from backend import save_profile # this sucks but whatever
      # feel free to add your own testing profile for your own system
      save_profile("Study Session", ["https://canvas.tamu.edu", "https://youtube.com"])
      save_profile("Triple Test", ["https://docs.python.org", "/home/cyren/dev/py/lh44-task-tunnel/shell.nix", "vesktop"])
  except:
    pass
  finally:
    conn.close()
  