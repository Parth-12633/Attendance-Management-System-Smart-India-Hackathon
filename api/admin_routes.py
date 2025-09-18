from flask import Blueprint, request, jsonify, send_file
from models import db, User, Student, Teacher, Class, Subject, AttendanceSession, Attendance, Timetable
from auth import token_required, role_required
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_
import io
import csv
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/stats', methods=['GET'])
@token_required
@role_required(['admin'])
def get_system_stats(current_user):
    # Get system statistics
    total_users = User.query.filter_by(is_active=True).count()
    active_students = Student.query.join(User).filter(User.is_active == True).count()
    total_teachers = Teacher.query.join(User).filter(User.is_active == True).count()
    
    # Today's sessions
    today = date.today()
    today_sessions = AttendanceSession.query.filter_by(date=today).count()
    
    return jsonify({
        'total_users': total_users,
        'active_students': active_students,
        'total_teachers': total_teachers,
        'today_sessions': today_sessions
    })

@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required(['admin'])
def get_users(current_user):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    role_filter = request.args.get('role')
    status_filter = request.args.get('status')
    search_query = request.args.get('search')
    
    # Build query
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if status_filter:
        is_active = status_filter == 'active'
        query = query.filter_by(is_active=is_active)
    
    if search_query:
        query = query.filter(
            or_(
                User.name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )
    
    # Paginate results
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    users_data = []
    for user in pagination.items:
        user_info = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': None  # Placeholder - would need to track login times
        }
        
        # Add role-specific information
        if user.role == 'student' and user.student:
            user_info.update({
                'roll_no': user.student.roll_no,
                'division': user.student.division,
                'standard': user.student.standard
            })
        elif user.role == 'teacher' and user.teacher:
            user_info.update({
                'employee_id': user.teacher.employee_id,
                'department': user.teacher.department
            })
        
        users_data.append(user_info)
    
    return jsonify({
        'users': users_data,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@admin_bp.route('/users', methods=['POST'])
@token_required
@role_required(['admin'])
def create_user(current_user):
    data = request.get_json()
    
    required_fields = ['name', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Create user
        user = User(
            name=data['name'],
            role=data['role'],
            email=data.get('email'),
            is_active=True
        )
        
        # Set password for non-student users
        if data['role'] in ['teacher', 'admin']:
            if not data.get('email'):
                return jsonify({'error': 'Email required for teachers and admins'}), 400
            # Generate temporary password
            temp_password = f"temp{user.id}123"  # In production, use secure password generation
            user.set_password(temp_password)
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create role-specific records
        if data['role'] == 'student':
            if not all(field in data for field in ['roll_no', 'division', 'standard']):
                return jsonify({'error': 'Missing student fields'}), 400
            
            student = Student(
                user_id=user.id,
                roll_no=data['roll_no'],
                division=data['division'],
                standard=data['standard']
            )
            db.session.add(student)
            
        elif data['role'] == 'teacher':
            teacher = Teacher(
                user_id=user.id,
                employee_id=data.get('employee_id', f'T{user.id:03d}'),
                department=data.get('department', 'General')
            )
            db.session.add(teacher)
        
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'user_id': user.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
@token_required
@role_required(['admin'])
def update_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        # Update user fields
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'name' in data:
            user.name = data['name']
        
        if 'email' in data:
            user.email = data['email']
        
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting the current admin user
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    try:
        # Soft delete by deactivating
        user.is_active = False
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500

@admin_bp.route('/classes', methods=['GET'])
@token_required
@role_required(['admin'])
def get_classes(current_user):
    classes = Class.query.all()
    
    classes_data = []
    for cls in classes:
        classes_data.append({
            'id': cls.id,
            'standard': cls.standard,
            'division': cls.division,
            'academic_year': cls.academic_year
        })
    
    return jsonify({'classes': classes_data})

@admin_bp.route('/subjects', methods=['GET'])
@token_required
@role_required(['admin'])
def get_subjects(current_user):
    subjects = Subject.query.all()
    
    subjects_data = []
    for subject in subjects:
        subjects_data.append({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'description': subject.description
        })
    
    return jsonify({'subjects': subjects_data})

@admin_bp.route('/reports/generate', methods=['POST'])
@token_required
@role_required(['admin'])
def generate_report(current_user):
    data = request.get_json()
    
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    report_type = data['type']
    format_type = data['format']
    
    try:
        if report_type == 'attendance':
            # Generate attendance report
            attendance_data = db.session.query(
                User.name.label('student_name'),
                Student.roll_no,
                Student.standard,
                Student.division,
                Subject.name.label('subject_name'),
                AttendanceSession.date,
                Attendance.status,
                Attendance.marked_at
            ).select_from(Attendance).join(Student).join(User).join(AttendanceSession).join(Timetable).join(Subject).filter(
                AttendanceSession.date >= start_date,
                AttendanceSession.date <= end_date
            ).order_by(AttendanceSession.date.desc()).all()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Student Name', 'Roll No', 'Class', 'Subject', 'Date', 'Status', 'Marked At'])
            
            # Write data
            for record in attendance_data:
                writer.writerow([
                    record.student_name,
                    record.roll_no,
                    f"{record.standard}-{record.division}",
                    record.subject_name,
                    record.date.strftime('%Y-%m-%d'),
                    record.status,
                    record.marked_at.strftime('%Y-%m-%d %H:%M:%S') if record.marked_at else 'N/A'
                ])
            
            # Create file-like object
            output.seek(0)
            file_data = io.BytesIO(output.getvalue().encode('utf-8'))
            
            return send_file(
                file_data,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'attendance_report_{start_date}_{end_date}.csv'
            )
        
        else:
            return jsonify({'error': 'Report type not implemented'}), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to generate report'}), 500

@admin_bp.route('/backup', methods=['POST'])
@token_required
@role_required(['admin'])
def create_backup(current_user):
    try:
        # This is a simplified backup - in production, use proper database backup tools
        backup_data = {
            'users': [{'id': u.id, 'name': u.name, 'role': u.role} for u in User.query.all()],
            'students': [{'id': s.id, 'roll_no': s.roll_no} for s in Student.query.all()],
            'teachers': [{'id': t.id, 'employee_id': t.employee_id} for t in Teacher.query.all()],
            'backup_date': datetime.utcnow().isoformat()
        }
        
        import json
        backup_json = json.dumps(backup_data, indent=2)
        file_data = io.BytesIO(backup_json.encode('utf-8'))
        
        return send_file(
            file_data,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'backup_{date.today().isoformat()}.json'
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to create backup'}), 500

@admin_bp.route('/settings', methods=['POST'])
@token_required
@role_required(['admin'])
def save_settings(current_user):
    data = request.get_json()
    
    # In a real application, you would save these settings to a database table
    # For now, we'll just return success
    
    return jsonify({'message': 'Settings saved successfully'})
