import qrcode
import io
import base64
import secrets
import jwt
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date, timedelta
import pytz
from models import db, Teacher, AttendanceSession, Attendance, Student, Timetable, Class, Subject, User
from auth import token_required, role_required
from sqlalchemy import func, and_

teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

# Create session from dashboard UI
@teacher_bp.route('/create_session', methods=['POST'])
@token_required
@role_required(['teacher'])
def create_session(current_user):
    data = request.get_json() or {}
    class_standard = data.get('class_standard')
    class_division = data.get('class_division')
    subject_name = data.get('subject_name')
    subject_code = data.get('subject_code')
    room = data.get('room')
    start_hour = data.get('start_hour')
    end_hour = data.get('end_hour')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    if not all([class_standard, class_division, subject_name, subject_code, (start_time_str or start_hour), (end_time_str or end_hour)]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Find or create class
    cls = Class.query.filter_by(standard=class_standard, division=class_division, academic_year="2025-26").first()
    if not cls:
        cls = Class(standard=class_standard, division=class_division, academic_year="2025-26")
        db.session.add(cls)
        db.session.commit()

    # Find or create subject by code only (avoid UNIQUE constraint error)
    subj = Subject.query.filter_by(code=subject_code).first()
    if not subj:
        subj = Subject(name=subject_name, code=subject_code, description=subject_name)
        db.session.add(subj)
        db.session.commit()

    # Find or create timetable
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    today = now.date()
    if start_time_str and end_time_str:
        start = datetime.combine(today, datetime.strptime(start_time_str, "%H:%M").time())
        end = datetime.combine(today, datetime.strptime(end_time_str, "%H:%M").time())
        start = tz.localize(start)
        end = tz.localize(end)
    else:
        start = now
        end = now + timedelta(hours=(int(end_hour) - int(start_hour)))
    tt = Timetable.query.filter_by(class_id=cls.id, subject_id=subj.id, teacher_id=current_user.teacher.id).first()
    if not tt:
        tt = Timetable(class_id=cls.id, subject_id=subj.id, teacher_id=current_user.teacher.id, day_of_week=today.weekday(), start_time=start.time(), end_time=end.time(), room_number=room)
        db.session.add(tt)
        db.session.commit()

    # Delete all previous sessions for this class/division/subject for today
    prev_sessions = AttendanceSession.query.join(Timetable).filter(
        Timetable.class_id == cls.id,
        Timetable.subject_id == subj.id,
        Timetable.teacher_id == current_user.teacher.id,
        AttendanceSession.date == today
    ).all()
    for s in prev_sessions:
        db.session.delete(s)
    db.session.commit()

    # Create new session and set active
    session = AttendanceSession(timetable_id=tt.id, date=today, start_time=start, end_time=end, is_active=True)
    db.session.add(session)
    db.session.commit()
    created = True

    return jsonify({
        'success': True,
        'created': created,
        'session_id': session.id,
        'class': f"{class_standard}-{class_division}",
        'subject': subject_name,
        'start_time': start.isoformat(),
        'end_time': end.isoformat()
    })
def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    base64_img = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{base64_img}"
# QR code generation endpoint for attendance session
@teacher_bp.route('/session/<int:session_id>/generate_qr', methods=['POST'])
@token_required
@role_required(['teacher'])
def generate_session_qr(current_user, session_id):
    # Verify teacher owns this session
    session = AttendanceSession.query.join(Timetable).filter(
        AttendanceSession.id == session_id,
        Timetable.teacher_id == current_user.teacher.id
    ).first()
    if not session:
        return jsonify({'error': 'Session not found or access denied'}), 404




    data = request.get_json() or {}
    subject = data.get('subject')

    # Generate a short 6-character code
    short_code = secrets.token_urlsafe(4)[:6].upper()
    
    # Add random nonce for QR uniqueness
    nonce = secrets.token_hex(4)
    
    # create JWT payload with jti and optional subject
    jti = secrets.token_urlsafe(16)
    payload = {
        'session_id': session_id,
        'jti': jti,
        'code': short_code,
        'nonce': nonce,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=300),
    }
    if subject:
        payload['subject'] = subject

    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    # store jti, code, and qr_code (data URL) on session
    img_data = generate_qr_code(token)
    session.qr_token = jti
    session.manual_code = short_code
    session.qr_code = img_data
    session.is_active = True
    session.attendance_method = 'qr'
    db.session.commit()
    
    # Return both the short code and full JWT
    resp = {
        'qr_code': img_data,
        'jwt': short_code,  # Use short code for manual entry
        'expires_in': 300,
        '_debug_token': token if current_app.config.get('TESTING') else None
    }
    return jsonify(resp)

@teacher_bp.route('/sessions/today', methods=['GET'])
@token_required
@role_required(['teacher'])
def get_today_sessions(current_user):
    teacher = current_user.teacher
    today = date.today()

    print("[DEBUG] /api/teacher/sessions/today called by:", current_user.email, "(user_id:", current_user.id, ")")
    print("[DEBUG] Teacher.id:", teacher.id if teacher else None)

    # Get teacher's sessions for today
    sessions = db.session.query(AttendanceSession).join(Timetable).filter(
        Timetable.teacher_id == teacher.id,
        AttendanceSession.date == today
    ).all()

    print(f"[DEBUG] Found {len(sessions)} sessions for today.")
    for s in sessions:
        print(f"[DEBUG] Session: id={s.id}, timetable_id={s.timetable_id}, date={s.date}, start={s.start_time}, end={s.end_time}")

    session_data = []
    for session in sessions:
        # Count attendance for this session
        attendance_count = Attendance.query.filter_by(
            session_id=session.id,
            status='present'
        ).count()

        # Get total students in class
        total_students = Student.query.join(User).filter(
            Student.standard == session.timetable.class_ref.standard,
            Student.division == session.timetable.class_ref.division,
            User.is_active == True
        ).count()

        # Defensive: ensure start_time and end_time are present and formatted
        def format_dt(dt):
            if dt is None:
                return "--:--"
            try:
                return dt.isoformat()
            except Exception:
                return str(dt)

        session_info = {
            'id': session.id,
            'timetable_id': session.timetable_id,
            'subject': session.timetable.subject.name if session.timetable and session.timetable.subject else "",
            'class_name': f"{session.timetable.class_ref.standard}-{session.timetable.class_ref.division}" if session.timetable and session.timetable.class_ref else "",
            'room_number': session.timetable.room_number if session.timetable else "",
            'start_time': format_dt(session.start_time),
            'end_time': format_dt(session.end_time),
            'is_active': session.is_active,
            'attendance_count': attendance_count,
            'total_students': total_students
        }
        session_data.append(session_info)
    
    return jsonify({'sessions': session_data})

@teacher_bp.route('/attendance/live', methods=['GET'])
@token_required
@role_required(['teacher'])
def get_live_attendance(current_user):
    teacher = current_user.teacher
    today = date.today()
    
    # Get attendance records for teacher's classes today
    attendance_records = db.session.query(
        Attendance.status,
        Attendance.marked_at,
        User.name.label('student_name'),
        Student.roll_no,
        Student.standard,
        Student.division,
        Subject.name.label('subject_name')
    ).select_from(Attendance).join(Student).join(User).join(AttendanceSession).join(Timetable).join(Subject).filter(
        Timetable.teacher_id == teacher.id,
        AttendanceSession.date == today
    ).order_by(Attendance.marked_at.desc()).all()
    
    attendance_data = []
    for record in attendance_records:
        attendance_data.append({
            'student_name': record.student_name,
            'roll_no': record.roll_no,
            'class_name': f"{record.standard}-{record.division}",
            'subject': record.subject_name,
            'status': record.status,
            'marked_at': record.marked_at.isoformat() if record.marked_at else None
        })
    
    return jsonify({'attendance': attendance_data})

@teacher_bp.route('/session/<int:session_id>/students', methods=['GET'])
@token_required
@role_required(['teacher'])
def get_session_students(current_user, session_id):
    # Verify teacher owns this session
    session = AttendanceSession.query.join(Timetable).filter(
        AttendanceSession.id == session_id,
        Timetable.teacher_id == current_user.teacher.id
    ).first()
    
    if not session:
        return jsonify({'error': 'Session not found or access denied'}), 404
    
    # Get students in the class
    students = db.session.query(Student, User).join(User).filter(
        Student.standard == session.timetable.class_ref.standard,
        Student.division == session.timetable.class_ref.division,
        User.is_active == True
    ).order_by(Student.roll_no).all()
    
    # Get existing attendance records
    existing_attendance = {
        record.student_id: record.status for record in
        Attendance.query.filter_by(session_id=session_id).all()
    }
    
    student_data = []
    for student, user in students:
        student_data.append({
            'id': student.id,
            'name': user.name,
            'roll_no': student.roll_no,
            'current_status': existing_attendance.get(student.id, 'absent')
        })
    
    return jsonify({'students': student_data})

@teacher_bp.route('/attendance/manual', methods=['POST'])
@token_required
@role_required(['teacher'])
def save_manual_attendance(current_user):
    data = request.get_json()
    session_id = data.get('session_id')
    attendance_data = data.get('attendance', [])
    
    if not session_id or not attendance_data:
        return jsonify({'error': 'Session ID and attendance data required'}), 400
    
    # Verify teacher owns this session
    session = AttendanceSession.query.join(Timetable).filter(
        AttendanceSession.id == session_id,
        Timetable.teacher_id == current_user.teacher.id
    ).first()
    
    if not session:
        return jsonify({'error': 'Session not found or access denied'}), 404
    
    try:
        # Update or create attendance records
        for record in attendance_data:
            student_id = record.get('student_id')
            status = record.get('status')
            
            if not student_id or not status:
                continue
            
            # Check if attendance already exists
            existing = Attendance.query.filter_by(
                student_id=student_id,
                session_id=session_id
            ).first()
            
            if existing:
                existing.status = status
                existing.marked_at = datetime.utcnow()
                existing.marked_by = 'teacher'
            else:
                new_attendance = Attendance(
                    student_id=student_id,
                    session_id=session_id,
                    status=status,
                    marked_by='teacher'
                )
                db.session.add(new_attendance)
        
        db.session.commit()
        return jsonify({'message': 'Attendance saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save attendance'}), 500

@teacher_bp.route('/analytics', methods=['GET'])
@token_required
@role_required(['teacher'])
def get_teacher_analytics(current_user):
    teacher = current_user.teacher
    
    # Get date range
    end_date = date.today()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    # Get attendance statistics
    attendance_stats = db.session.query(
        func.count(Attendance.id).label('total_marked'),
        func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present_count'),
        func.sum(func.case([(Attendance.status == 'late', 1)], else_=0)).label('late_count'),
        func.sum(func.case([(Attendance.status == 'absent', 1)], else_=0)).label('absent_count')
    ).select_from(Attendance).join(AttendanceSession).join(Timetable).filter(
        Timetable.teacher_id == teacher.id,
        AttendanceSession.date >= start_date,
        AttendanceSession.date <= end_date
    ).first()
    
    # Get class-wise attendance
    class_attendance = db.session.query(
        Class.standard,
        Class.division,
        func.count(Attendance.id).label('total_sessions'),
        func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present_count')
    ).select_from(Class).join(Timetable).join(AttendanceSession).outerjoin(Attendance).filter(
        Timetable.teacher_id == teacher.id,
        AttendanceSession.date >= start_date,
        AttendanceSession.date <= end_date
    ).group_by(Class.id).all()
    
    # Get low attendance students
    low_attendance_students = db.session.query(
        User.name,
        Student.roll_no,
        Student.standard,
        Student.division,
        func.count(AttendanceSession.id).label('total_sessions'),
        func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present_count')
    ).select_from(Student).join(User).join(Attendance, Attendance.student_id == Student.id).join(AttendanceSession).join(Timetable).filter(
        Timetable.teacher_id == teacher.id,
        AttendanceSession.date >= start_date,
        AttendanceSession.date <= end_date
    ).group_by(Student.id).having(
        func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)) / func.count(AttendanceSession.id) < 0.75
    ).all()
    
    return jsonify({
        'overall_stats': {
            'total_marked': attendance_stats.total_marked or 0,
            'present_count': attendance_stats.present_count or 0,
            'late_count': attendance_stats.late_count or 0,
            'absent_count': attendance_stats.absent_count or 0
        },
        'class_attendance': [{
            'class_name': f"{record.standard}-{record.division}",
            'total_sessions': record.total_sessions,
            'present_count': record.present_count,
            'attendance_percentage': round((record.present_count / record.total_sessions * 100), 2) if record.total_sessions > 0 else 0
        } for record in class_attendance],
        'low_attendance_students': [{
            'name': record.name,
            'roll_no': record.roll_no,
            'class_name': f"{record.standard}-{record.division}",
            'attendance_percentage': round((record.present_count / record.total_sessions * 100), 2) if record.total_sessions > 0 else 0
        } for record in low_attendance_students]
    })


@teacher_bp.route('/session/<int:session_id>/report', methods=['GET'])
@token_required
@role_required(['teacher'])
def session_report(current_user, session_id):
    # Verify teacher owns this session
    session = AttendanceSession.query.join(Timetable).filter(
        AttendanceSession.id == session_id,
        Timetable.teacher_id == current_user.teacher.id
    ).first()
    if not session:
        return jsonify({'error': 'Session not found or access denied'}), 404

    # Get attendance records
    records = db.session.query(Attendance, Student, User).select_from(Attendance).join(Student).join(User).filter(
        Attendance.session_id == session_id
    ).all()

    # Build CSV
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Roll No', 'Student Name', 'Status', 'Marked At', 'Marked By', 'Confidence'])
    for attendance, student, user in records:
        writer.writerow([
            student.roll_no,
            user.name,
            attendance.status,
            attendance.marked_at.isoformat() if attendance.marked_at else '',
            attendance.marked_by or '',
            attendance.confidence_score if attendance.confidence_score is not None else ''
        ])

    csv_data = output.getvalue()
    output.close()

    from flask import Response
    resp = Response(csv_data, mimetype='text/csv')
    filename = f"attendance_session_{session_id}.csv"
    resp.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return resp


