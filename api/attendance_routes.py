from flask import Blueprint, request, jsonify
from models import db, AttendanceSession, Attendance, Student, Timetable, Class, User, Subject
from auth import token_required, role_required
from datetime import datetime, date
import qrcode
import io
import base64
import secrets
import string

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

@attendance_bp.route('/generate-qr', methods=['POST'])
@token_required
@role_required(['teacher', 'admin'])
def generate_qr_code(current_user):
    data = request.get_json()
    timetable_id = data.get('timetable_id')
    
    if not timetable_id:
        return jsonify({'error': 'Timetable ID required'}), 400
    
    # Generate unique token for QR code
    qr_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    # Create attendance session
    session = AttendanceSession(
        timetable_id=timetable_id,
        date=date.today(),
        start_time=datetime.now(),
        qr_token=qr_token,
        attendance_method='qr'
    )
    
    # Generate QR code
    qr_data = f"attendance:{qr_token}:{timetable_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    session.qr_code = qr_code_base64
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'session_id': session.id,
        'qr_code': qr_code_base64,
        'qr_token': qr_token,
        'expires_in': 3600  # 1 hour
    })

@attendance_bp.route('/mark-qr', methods=['POST'])
@token_required
@role_required(['student'])
def mark_attendance_qr(current_user):
    data = request.get_json()
    qr_token = data.get('qr_token')
    
    if not qr_token:
        return jsonify({'error': 'QR token required'}), 400
    
    # Find active session
    session = AttendanceSession.query.filter_by(
        qr_token=qr_token,
        is_active=True
    ).first()
    
    if not session:
        return jsonify({'error': 'Invalid or expired QR code'}), 400
    
    # Check if already marked
    student = current_user.student
    existing = Attendance.query.filter_by(
        student_id=student.id,
        session_id=session.id
    ).first()
    
    if existing:
        return jsonify({'error': 'Attendance already marked'}), 400
    
    # Mark attendance
    attendance = Attendance(
        student_id=student.id,
        session_id=session.id,
        status='present',
        marked_by='qr'
    )
    
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({
        'message': 'Attendance marked successfully',
        'status': 'present',
        'marked_at': attendance.marked_at.isoformat()
    })

@attendance_bp.route('/sessions/today', methods=['GET'])
@token_required
def get_today_sessions(current_user):
    today = date.today()
    
    if current_user.role == 'student':
        student = current_user.student
        # Get sessions for student's class
        sessions = db.session.query(AttendanceSession).join(Timetable).join(Class).filter(
            AttendanceSession.date == today,
            Class.standard == student.standard,
            Class.division == student.division
        ).all()
    else:
        # Teachers see all sessions they're teaching
        sessions = db.session.query(AttendanceSession).join(Timetable).filter(
            AttendanceSession.date == today,
            Timetable.teacher_id == current_user.teacher.id if current_user.role == 'teacher' else True
        ).all()
    
    session_data = []
    for session in sessions:
        session_info = {
            'id': session.id,
            'subject': session.timetable.subject.name,
            'teacher': session.timetable.teacher.user.name,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'is_active': session.is_active,
            'attendance_method': session.attendance_method
        }
        
        if current_user.role == 'student':
            # Check if student has marked attendance
            attendance = Attendance.query.filter_by(
                student_id=current_user.student.id,
                session_id=session.id
            ).first()
            session_info['attendance_status'] = attendance.status if attendance else 'absent'
            session_info['marked_at'] = attendance.marked_at.isoformat() if attendance else None
        
        session_data.append(session_info)
    
    return jsonify({'sessions': session_data})

@attendance_bp.route('/report', methods=['GET'])
@token_required
@role_required(['teacher', 'admin'])
def attendance_report(current_user):
    class_id = request.args.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = db.session.query(Attendance).join(AttendanceSession).join(Student).join(User)
    
    if class_id:
        query = query.join(Timetable).join(Class).filter(Class.id == class_id)
    
    if start_date:
        query = query.filter(AttendanceSession.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    
    if end_date:
        query = query.filter(AttendanceSession.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    attendance_records = query.all()
    
    report_data = []
    for record in attendance_records:
        report_data.append({
            'student_name': record.student.user.name,
            'roll_no': record.student.roll_no,
            'division': record.student.division,
            'standard': record.student.standard,
            'subject': record.session.timetable.subject.name,
            'date': record.session.date.isoformat(),
            'status': record.status,
            'marked_at': record.marked_at.isoformat(),
            'marked_by': record.marked_by
        })
    
    return jsonify({'attendance_report': report_data})
