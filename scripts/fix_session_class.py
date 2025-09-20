# Script to fix the class for session 26 to use standard '10' instead of '10th'
from app import app
from models import db, AttendanceSession, Timetable, Class

SESSION_ID_TO_FIX = 26
CORRECT_STANDARD = '10'
DIVISION = 'A'

with app.app_context():
    session = AttendanceSession.query.get(SESSION_ID_TO_FIX)
    if not session:
        print(f"Session ID {SESSION_ID_TO_FIX} not found.")
        exit(1)
    tt = Timetable.query.get(session.timetable_id)
    if not tt:
        print(f"Timetable for session {SESSION_ID_TO_FIX} not found.")
        exit(1)
    # Find the correct class
    correct_class = Class.query.filter_by(standard=CORRECT_STANDARD, division=DIVISION).first()
    if not correct_class:
        print(f"No class found for standard '{CORRECT_STANDARD}', division '{DIVISION}'")
        exit(1)
    print(f"Updating Timetable ID {tt.id} class_id from {tt.class_id} to {correct_class.id}")
    tt.class_id = correct_class.id
    db.session.commit()
    print("Session class updated. Now students in 10-A will see this session.")
