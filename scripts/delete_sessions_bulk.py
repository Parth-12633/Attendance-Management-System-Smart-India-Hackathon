# Script to delete all attendance records for sessions, then delete the sessions themselves
from app import app
from models import db, AttendanceSession, Timetable, Class, Attendance
from datetime import datetime

STANDARD = '10th'  # Delete all '10th'-'A' sessions
DIVISION = 'A'
DATE = datetime.now().date()

with app.app_context():
    cls = Class.query.filter_by(standard=STANDARD, division=DIVISION).first()
    if not cls:
        print(f"No class found for {STANDARD}-{DIVISION}")
        exit(1)
    timetables = Timetable.query.filter_by(class_id=cls.id).all()
    timetable_ids = [tt.id for tt in timetables]
    sessions = AttendanceSession.query.filter(AttendanceSession.timetable_id.in_(timetable_ids), AttendanceSession.date == DATE).all()
    print(f"Found {len(sessions)} sessions for {STANDARD}-{DIVISION} on {DATE}.")
    for s in sessions:
        # Delete attendance records for this session
        attendance_records = Attendance.query.filter_by(session_id=s.id).all()
        for a in attendance_records:
            print(f"Deleting attendance ID {a.id} for session {s.id}")
            db.session.delete(a)
        print(f"Deleting session ID {s.id}")
        db.session.delete(s)
    db.session.commit()
    print("All matching sessions and related attendance deleted.")
