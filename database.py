import sqlite3

def init_db():
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            file_name TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_file(file_id, file_name):
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("INSERT INTO files (file_id, file_name) VALUES (?, ?)", (file_id, file_name))
    conn.commit()
    file_row_id = c.lastrowid
    conn.close()
    return file_row_id

def get_file(file_row_id):
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("SELECT file_id, file_name FROM files WHERE id=?", (file_row_id,))
    result = c.fetchone()
    conn.close()
    return result
