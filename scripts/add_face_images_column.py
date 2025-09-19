import sqlite3

# Path to your SQLite database
DB_PATH = 'instance/attendance.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE student ADD COLUMN face_images TEXT;")
    print("Column 'face_images' added to 'student' table.")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("Column 'face_images' already exists.")
    else:
        print(f"Error: {e}")

conn.commit()
conn.close()
