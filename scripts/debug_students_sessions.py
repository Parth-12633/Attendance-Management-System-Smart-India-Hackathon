# Script to print all students and today's sessions with class/division
def print_students():
    print("\n--- Students ---")
    from models import Student
    students = Student.query.all()
    for s in students:
        print(f"ID: {s.id}, Name: {s.user.name}, Standard: '{s.standard}', Division: '{s.division}' (raw)")

def print_sessions_today():
    print("\n--- Today's Sessions ---")
    from models import AttendanceSession, Timetable, Class
    from datetime import datetime
    import pytz
    today = datetime.now(pytz.timezone('Asia/Kolkata')).date()
    sessions = AttendanceSession.query.filter_by(date=today).all()
    for sess in sessions:
        tt = Timetable.query.get(sess.timetable_id)
        cls = Class.query.get(tt.class_id) if tt else None
        if cls:
            print(f"Session ID: {sess.id}, Class: '{cls.standard}'-'{cls.division}' (raw), Subject: {tt.subject.name if tt and tt.subject else 'N/A'}")
        else:
            print(f"Session ID: {sess.id}, Class: N/A, Subject: {tt.subject.name if tt and tt.subject else 'N/A'}")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        print_students()
        print_sessions_today()
