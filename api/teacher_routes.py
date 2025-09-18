from flask import Blueprint, request, jsonify
from models import db, Teacher, AttendanceSession, Attendance, Student, Timetable, Class, Subject, User
from auth import token_required, role_required
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_

teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

@teacher_bp.route('/sessions/today', methods=['GET'])
@token_required
@role_required(['teacher'])
def get_today_sessions(current_user):
    teacher = current_user.teacher
    today = date.today()
    
    # Get teacher's sessions for today
    sessions = db.session.query(AttendanceSession).join(Timetable).filter(
        Timetable.teacher_id == teacher.id,
        AttendanceSession.date == today
    ).all()
    
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
        
        session_info = {
            'id': session.id,
            'timetable_id': session.timetable_id,
            'subject': session.timetable.subject.name,
            'class_name': f"{session.timetable.class_ref.standard}-{session.timetable.class_ref.division}",
            'room_number': session.timetable.room_number,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
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
