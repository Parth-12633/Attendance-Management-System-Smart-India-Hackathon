from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), nullable=False)  # student, teacher, admin
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    roll_no = db.Column(db.String(20), nullable=False)
    division = db.Column(db.String(10), nullable=False)
    standard = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    parent_phone = db.Column(db.String(15), nullable=True)
    interests = db.Column(db.Text, nullable=True)  # JSON string
    career_goals = db.Column(db.Text, nullable=True)
    face_encoding = db.Column(db.Text, nullable=True)  # For face recognition
    
    user = db.relationship('User', backref=db.backref('student', uselist=False))
    
    __table_args__ = (db.UniqueConstraint('roll_no', 'division', 'standard'),)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=True)
    subjects = db.Column(db.Text, nullable=True)  # JSON string
    
    user = db.relationship('User', backref=db.backref('teacher', uselist=False))

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    standard = db.Column(db.String(10), nullable=False)
    division = db.Column(db.String(10), nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('standard', 'division', 'academic_year'),)

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room_number = db.Column(db.String(20), nullable=True)
    
    class_ref = db.relationship('Class', backref='timetable_entries')
    subject = db.relationship('Subject', backref='timetable_entries')
    teacher = db.relationship('Teacher', backref='timetable_entries')

class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    qr_code = db.Column(db.Text, nullable=True)  # Base64 encoded QR code
    qr_token = db.Column(db.String(100), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    attendance_method = db.Column(db.String(20), default='manual')  # manual, qr, bluetooth, face
    
    timetable = db.relationship('Timetable', backref='attendance_sessions')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=False)
    status = db.Column(db.String(20), default='present')  # present, absent, late
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    marked_by = db.Column(db.String(20), default='system')  # system, teacher, qr, bluetooth, face
    confidence_score = db.Column(db.Float, nullable=True)  # For face recognition
    
    student = db.relationship('Student', backref='attendance_records')
    session = db.relationship('AttendanceSession', backref='attendance_records')
    
    __table_args__ = (db.UniqueConstraint('student_id', 'session_id'),)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_type = db.Column(db.String(50), nullable=False)  # study, assignment, project, career
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    estimated_duration = db.Column(db.Integer, nullable=True)  # in minutes
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    student = db.relationship('Student', backref='tasks')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # attendance, task, announcement
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_name = db.Column(db.String(100), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='permissions')
    granted_by_user = db.relationship('User', foreign_keys=[granted_by])
