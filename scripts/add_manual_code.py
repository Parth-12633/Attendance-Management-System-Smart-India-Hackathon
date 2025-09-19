import sqlite3

def update_database():
    # Connect to the database
    conn = sqlite3.connect('instance/attendance.db')
    cursor = conn.cursor()
    
    try:
        # Add the manual_code column without UNIQUE constraint first
        cursor.execute('ALTER TABLE attendance_session ADD COLUMN manual_code VARCHAR(6)')
        print("Added manual_code column successfully!")
        
        # Create a unique index for the column
        cursor.execute('CREATE UNIQUE INDEX idx_manual_code ON attendance_session (manual_code) WHERE manual_code IS NOT NULL')
        print("Added unique constraint successfully!")
        
        # Commit changes
        conn.commit()
        print("Database updated successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_database()