
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from extensions import db
from models import User, Teacher, Class, Subject, Timetable, AttendanceSession
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta

with app.app_context():
    # Find or create teacher user
    email = "gohilparth333@gmail.com"
    teacher_user = User.query.filter_by(email=email, role="teacher").first()
    if not teacher_user:
        teacher_user = User(
            name="Parth Gohil",
            email=email,
            role="teacher",
            password_hash=generate_password_hash("teacher123"),
            created_at=datetime.utcnow(),
            is_active=True
        )
        db.session.add(teacher_user)
        db.session.commit()
        print(f"Created teacher user: {email} (password: teacher123)")
    teacher = Teacher.query.filter_by(user_id=teacher_user.id).first()
    if not teacher:
        teacher = Teacher(user_id=teacher_user.id, employee_id="T100", department="Science")
        db.session.add(teacher)
        db.session.commit()
        print("Created Teacher row.")

    # Create a class if none exists
    cls = Class.query.first()
    if not cls:
        cls = Class(standard="10", division="A", academic_year="2025-26")
        db.session.add(cls)
        db.session.commit()

    # Create a subject if none exists
    subj = Subject.query.first()
    if not subj:
        subj = Subject(name="Science", code="SCI", description="Science class")
        db.session.add(subj)
        db.session.commit()

    # Create a timetable entry for today if none exists
    today = date.today()
    start = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=1)
    tt = Timetable.query.filter_by(class_id=cls.id, subject_id=subj.id, teacher_id=teacher.id).first()
    if not tt:
        tt = Timetable(class_id=cls.id, subject_id=subj.id, teacher_id=teacher.id, day_of_week=today.weekday(), start_time=start.time(), end_time=end.time(), room_number="101")
        db.session.add(tt)
        db.session.commit()

    # Create an attendance session for today if none exists
    session = AttendanceSession.query.filter_by(timetable_id=tt.id, date=today).first()
    if not session:
        session = AttendanceSession(timetable_id=tt.id, date=today, start_time=start, end_time=end)
        db.session.add(session)
        db.session.commit()
        print("Created attendance session for today.")
    else:
        print("Attendance session for today already exists.")

    # Print all sessions for this teacher for today
    print("\nAttendance sessions for today (for teacher):")
    today = date.today()
    sessions = AttendanceSession.query.join(Timetable).filter(
        Timetable.teacher_id == teacher.id,
        AttendanceSession.date == today
    ).all()
    if not sessions:
        print("No sessions found for today.")
    else:
        for s in sessions:
            print(f"Session ID: {s.id}, Timetable ID: {s.timetable_id}, Date: {s.date}, Start: {s.start_time}, End: {s.end_time}")
    print("\nDone. Refresh your teacher dashboard and try generating a QR code.")
