from flask import Blueprint, request, jsonify
from models import db, Student, Attendance, AttendanceSession, Task, Notification
from models import Timetable, Class, Subject, User, Teacher
from auth import token_required, role_required
from datetime import datetime, date, timedelta
from sqlalchemy import func

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

@student_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required(['student'])
def get_dashboard_data(current_user):
    student = current_user.student
    today = date.today()
    
    # Get today's attendance sessions
    sessions = db.session.query(AttendanceSession).join(Timetable).join(Class).filter(
        AttendanceSession.date == today,
        Class.standard == student.standard,
        Class.division == student.division
    ).all()
    
    # Get attendance records for today
    attendance_records = {
        record.session_id: record for record in 
        Attendance.query.filter_by(student_id=student.id).join(AttendanceSession).filter(
            AttendanceSession.date == today
        ).all()
    }
    
    # Format session data
    session_data = []
    for session in sessions:
        attendance = attendance_records.get(session.id)
        session_info = {
            'id': session.id,
            'subject': session.timetable.subject.name,
            'teacher': session.timetable.teacher.user.name,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'attendance_status': attendance.status if attendance else 'absent',
            'marked_at': attendance.marked_at.isoformat() if attendance else None
        }
        session_data.append(session_info)
    
    # Get weekly attendance stats
    week_start = today - timedelta(days=today.weekday())
    weekly_attendance = db.session.query(
        func.count(Attendance.id).label('present_count'),
        func.count(AttendanceSession.id).label('total_sessions')
    ).select_from(AttendanceSession).outerjoin(
        Attendance, 
        (Attendance.session_id == AttendanceSession.id) & 
        (Attendance.student_id == student.id) &
        (Attendance.status == 'present')
    ).join(Timetable).join(Class).filter(
        AttendanceSession.date >= week_start,
        AttendanceSession.date <= today,
        Class.standard == student.standard,
        Class.division == student.division
    ).first()
    
    # Get pending tasks
    pending_tasks = Task.query.filter_by(
        student_id=student.id,
        status='pending'
    ).count()
    
    # Get recent notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return jsonify({
        'sessions': session_data,
        'stats': {
            'present_today': len([s for s in session_data if s['attendance_status'] == 'present']),
            'total_today': len(session_data),
            'weekly_present': weekly_attendance.present_count or 0,
            'weekly_total': weekly_attendance.total_sessions or 0,
            'pending_tasks': pending_tasks
        },
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
    })

@student_bp.route('/tasks', methods=['GET'])
@token_required
@role_required(['student'])
def get_student_tasks(current_user):
    student = current_user.student
    
    # Get tasks with optional filtering
    status = request.args.get('status', 'all')
    limit = int(request.args.get('limit', 10))
    
    query = Task.query.filter_by(student_id=student.id)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
    
    task_data = []
    for task in tasks:
        task_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'type': task.task_type,
            'priority': task.priority,
            'status': task.status,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'estimated_duration': task.estimated_duration,
            'ai_generated': task.ai_generated,
            'created_at': task.created_at.isoformat()
        })
    
    return jsonify({'tasks': task_data})

@student_bp.route('/attendance-report', methods=['GET'])
@token_required
@role_required(['student'])
def get_attendance_report(current_user):
    student = current_user.student
    
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = date.today() - timedelta(days=30)  # Last 30 days
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = date.today()
    
    # Get attendance records
    attendance_query = db.session.query(
        AttendanceSession.date,
        AttendanceSession.start_time,
        Timetable.subject_id,
        Subject.name.label('subject_name'),
        User.name.label('teacher_name'),
        Attendance.status,
        Attendance.marked_at
    ).select_from(AttendanceSession).join(Timetable).join(Subject).join(Teacher).join(User).outerjoin(
        Attendance,
        (Attendance.session_id == AttendanceSession.id) & 
        (Attendance.student_id == student.id)
    ).join(Class).filter(
        AttendanceSession.date >= start_date,
        AttendanceSession.date <= end_date,
        Class.standard == student.standard,
        Class.division == student.division
    ).order_by(AttendanceSession.date.desc(), AttendanceSession.start_time)
    
    records = attendance_query.all()
    
    # Format the data
    report_data = []
    for record in records:
        report_data.append({
            'date': record.date.isoformat(),
            'subject': record.subject_name,
            'teacher': record.teacher_name,
            'status': record.status or 'absent',
            'marked_at': record.marked_at.isoformat() if record.marked_at else None
        })
    
    # Calculate summary statistics
    total_sessions = len(records)
    present_sessions = len([r for r in records if r.status == 'present'])
    late_sessions = len([r for r in records if r.status == 'late'])
    absent_sessions = total_sessions - present_sessions - late_sessions
    
    attendance_percentage = (present_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    return jsonify({
        'report': report_data,
        'summary': {
            'total_sessions': total_sessions,
            'present': present_sessions,
            'late': late_sessions,
            'absent': absent_sessions,
            'attendance_percentage': round(attendance_percentage, 2)
        },
        'date_range': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    })
