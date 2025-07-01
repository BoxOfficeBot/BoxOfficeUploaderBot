import sqlite3

def init_db():
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT NOT NULL,
        file_name TEXT,
        file_type TEXT,
        schedule_time TEXT,
        channel_id INTEGER
    )''')
    conn.commit()
    conn.close()

def save_file(file_id, file_name, file_type):
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("INSERT INTO files (file_id, file_name, file_type) VALUES (?, ?, ?)", (file_id, file_name, file_type))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id

def get_file(file_row_id):
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("SELECT file_id, file_name, file_type, schedule_time, channel_id FROM files WHERE id=?", (file_row_id,))
    result = c.fetchone()
    conn.close()
    return result

def schedule_file(file_row_id, schedule_time, channel_id):
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("UPDATE files SET schedule_time=?, channel_id=? WHERE id=?", (schedule_time, channel_id, file_row_id))
    conn.commit()
    conn.close()
