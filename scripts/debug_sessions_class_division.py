
# Script to reassign related records from duplicate class (ID 4) to correct class (ID 1) and delete duplicate
from app import app
from models import db, Class, Timetable, AttendanceSession, Student

DUPLICATE_CLASS_ID = 4  # '10th'-'A'
CORRECT_CLASS_ID = 1    # '10'-'A'

with app.app_context():
    # Reassign timetables
    timetables = Timetable.query.filter_by(class_id=DUPLICATE_CLASS_ID).all()
    for tt in timetables:
        print(f"Updating Timetable ID {tt.id}: class_id {DUPLICATE_CLASS_ID} -> {CORRECT_CLASS_ID}")
        tt.class_id = CORRECT_CLASS_ID
    db.session.commit()

    # Reassign students (if any)
    students = Student.query.filter_by(standard='10th', division='A').all()
    for s in students:
        print(f"Updating Student ID {s.id}: standard '10th' -> '10'")
        s.standard = '10'
    db.session.commit()

    # Delete duplicate class
    duplicate = Class.query.get(DUPLICATE_CLASS_ID)
    if duplicate:
        print(f"Deleting duplicate Class ID {DUPLICATE_CLASS_ID}")
        db.session.delete(duplicate)
        db.session.commit()
    print("Duplicate class removed and related records reassigned.")
