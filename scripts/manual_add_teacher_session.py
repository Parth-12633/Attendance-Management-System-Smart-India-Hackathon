import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from extensions import db
from models import User, Teacher, Class, Subject, Timetable, AttendanceSession
from datetime import datetime, date, timedelta

email = input("Enter teacher email: ").strip()
class_std = input("Enter class standard (e.g. 10): ").strip()
class_div = input("Enter class division (e.g. A): ").strip()
subject_name = input("Enter subject name (e.g. Science): ").strip()
subject_code = input("Enter subject code (e.g. SCI): ").strip()
room = input("Enter room number (e.g. 101): ").strip()
start_hour = int(input("Enter start hour (24h, e.g. 10): "))
end_hour = int(input("Enter end hour (24h, e.g. 11): "))

with app.app_context():
    teacher_user = User.query.filter_by(email=email, role="teacher").first()
    if not teacher_user:
        print(f"No teacher user found with email {email}. Register this teacher first.")
        sys.exit(1)
    teacher = Teacher.query.filter_by(user_id=teacher_user.id).first()
    if not teacher:
        print("No Teacher row found for user. Register as teacher first.")
        sys.exit(1)

    # Class
    cls = Class.query.filter_by(standard=class_std, division=class_div, academic_year="2025-26").first()
    if not cls:
        cls = Class(standard=class_std, division=class_div, academic_year="2025-26")
        db.session.add(cls)
        db.session.commit()

    # Subject
    subj = Subject.query.filter_by(name=subject_name, code=subject_code).first()
    if not subj:
        subj = Subject(name=subject_name, code=subject_code, description=subject_name)
        db.session.add(subj)
        db.session.commit()

    # Timetable
    today = date.today()
    start = datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end = datetime.now().replace(hour=end_hour, minute=0, second=0, microsecond=0)
    tt = Timetable.query.filter_by(class_id=cls.id, subject_id=subj.id, teacher_id=teacher.id).first()
    if not tt:
        tt = Timetable(class_id=cls.id, subject_id=subj.id, teacher_id=teacher.id, day_of_week=today.weekday(), start_time=start.time(), end_time=end.time(), room_number=room)
        db.session.add(tt)
        db.session.commit()

    # Attendance Session
    session = AttendanceSession.query.filter_by(timetable_id=tt.id, date=today).first()
    if not session:
        session = AttendanceSession(timetable_id=tt.id, date=today, start_time=start, end_time=end)
        db.session.add(session)
        db.session.commit()
        print("Created attendance session for today.")
    else:
        print("Attendance session for today already exists.")

    print(f"Session ID: {session.id if session else 'N/A'} | Teacher: {email} | Class: {class_std}-{class_div} | Subject: {subject_name}")
    print("Done. Refresh your teacher dashboard and try generating a QR code.")
