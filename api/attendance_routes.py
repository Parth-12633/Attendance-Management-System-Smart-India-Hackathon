from flask import Blueprint, request, jsonify, current_app
from models import db, AttendanceSession, Attendance, Student, Timetable, Class, User, Subject, Teacher
from auth import token_required, role_required
from datetime import datetime, date, timedelta
import qrcode
import io
import base64
import secrets
import string
import jwt

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

@attendance_bp.route('/debug/sessions/today', methods=['GET'])
def debug_sessions_today():
    today = date.today()
    sessions = AttendanceSession.query.filter_by(date=today).all()
    result = []
    for s in sessions:
        tt = Timetable.query.get(s.timetable_id)
        subj = Subject.query.get(tt.subject_id) if tt else None
        cls = Class.query.get(tt.class_id) if tt else None
        teacher = Teacher.query.get(tt.teacher_id) if tt else None
        result.append({
            'id': s.id,
            'class': f"{cls.standard}-{cls.division}" if cls else None,
            'subject': subj.name if subj else None,
            'teacher': teacher.user.name if teacher else None,
            'start_time': s.start_time.isoformat() if s.start_time else None,
            'end_time': s.end_time.isoformat() if s.end_time else None,
            'is_active': s.is_active,
            'attendance_method': s.attendance_method
        })
    return jsonify({'sessions': result})
from flask import Blueprint, request, jsonify, current_app
from models import db, AttendanceSession, Attendance, Student, Timetable, Class, User, Subject, Teacher
from auth import token_required, role_required
from datetime import datetime, date, timedelta
import qrcode
import io
import base64
import secrets
import string
import jwt

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')


@attendance_bp.route('/generate-qr', methods=['POST'])
@token_required
@role_required(['teacher', 'admin'])
def generate_qr_code(current_user):
    data = request.get_json()
    timetable_id = data.get('timetable_id')

    if not timetable_id:
        return jsonify({'error': 'Timetable ID required'}), 400

    # Create attendance session first (inactive until QR used or teacher activates)
    session = AttendanceSession(
        timetable_id=timetable_id,
        date=date.today(),
        start_time=datetime.now(),
        attendance_method='qr'
    )
    db.session.add(session)
    db.session.flush()  # get session.id

    # Generate a jti for this QR and store it on the session
    jti = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
    session.qr_token = jti

    # Build JWT payload with short expiry
    payload = {
        'session_id': session.id,
        'jti': jti,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    # Generate QR image that encodes the JWT
    qr_data = token
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Store QR image (as data URL) and commit
    session.qr_code = f"data:image/png;base64,{qr_code_base64}"
    db.session.commit()

    return jsonify({
        'session_id': session.id,
        'qr_code': session.qr_code,
        'jwt': token,
        'expires_in': 30 * 60
    })

@attendance_bp.route('/mark-qr', methods=['POST'])
@token_required
@role_required(['student'])
def mark_attendance_qr(current_user):
    data = request.get_json()
    token = data.get('token') or data.get('jwt') or data.get('qr_token')
    manual_code = data.get('manual_code')

    if not token and not manual_code:
        return jsonify({'error': 'QR token or manual code required'}), 400

    session = None
    subject = None

    if manual_code:
        # Try to find session by manual code
        session = AttendanceSession.query.filter_by(
            manual_code=manual_code,
            is_active=True,
            date=date.today()
        ).first()
        if not session:
            return jsonify({'error': 'Invalid or expired manual code'}), 400
    else:
        # Handle QR token
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            session_id = payload.get('session_id')
            jti = payload.get('jti')
            subject = payload.get('subject')

            if not session_id or not jti:
                return jsonify({'error': 'Invalid QR payload'}), 400

            # Find session and verify stored jti matches
            session = AttendanceSession.query.filter_by(id=session_id, qr_token=jti, is_active=True).first()
            if not session:
                return jsonify({'error': 'Invalid or inactive QR session'}), 400
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'QR code expired'}), 400
        except Exception:
            return jsonify({'error': 'Invalid QR token'}), 400

    # Check if student already marked
    student = current_user.student
    existing = Attendance.query.filter_by(student_id=student.id, session_id=session.id).first()
    if existing:
        return jsonify({'error': 'Attendance already marked'}), 400

    # Mark attendance (record subject if present in token)
    attendance = Attendance(student_id=student.id, session_id=session.id, status='present', marked_by='qr', subject=subject)
    db.session.add(attendance)
    db.session.commit()

    resp = {'message': 'Attendance marked successfully', 'status': 'present', 'marked_at': attendance.marked_at.isoformat()}
    if subject:
        resp['subject'] = subject
    return jsonify(resp)

@attendance_bp.route('/sessions/today', methods=['GET'])
@token_required
def get_today_sessions(current_user):
    today = date.today()
    
    if current_user.role == 'student':
        student = current_user.student
        now = datetime.now()
        # Only show sessions that are active and current time is within start/end
        sessions = db.session.query(AttendanceSession).join(Timetable).join(Class).filter(
            AttendanceSession.date == today,
            Class.standard == student.standard,
            Class.division == student.division,
            AttendanceSession.is_active == True,
            AttendanceSession.start_time <= now,
            (AttendanceSession.end_time == None) | (AttendanceSession.end_time >= now)
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
