from flask import Blueprint, request, jsonify, session, current_app
from models import db, User, Student, Teacher
from auth import generate_token
import jwt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Student login with Name + Roll No + Division + Standard + Password
    if data.get('login_type') == 'student':
        name = data.get('name')
        roll_no = data.get('roll_no')
        division = data.get('division')
        standard = data.get('standard')
        password = data.get('password')
        if not all([name, roll_no, division, standard, password]):
            return jsonify({'error': 'All student credentials required'}), 400
        student = Student.query.join(User).filter(
            User.name.ilike(f'%{name}%'),
            Student.roll_no == roll_no,
            Student.division == division,
            Student.standard == standard,
            User.is_active == True
        ).first()
        if not student or not student.user.check_password(password):
            return jsonify({'error': 'Invalid student credentials'}), 401
        token = generate_token(student.user.id)
        session.clear()  # Clear any existing session
        session['jwt_token'] = token
        session['user_id'] = student.user.id
        session['role'] = 'student'
        session['name'] = student.user.name
        return jsonify({
            'token': token,
            'user': {
                'id': student.user.id,
                'name': student.user.name,
                'role': 'student',
                'student_id': student.id,
                'roll_no': student.roll_no,
                'division': student.division,
                'standard': student.standard
            }
        })
    
    # Teacher/Admin login with email and password
    elif data.get('login_type') in ['teacher', 'admin']:
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=email, is_active=True).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if user.role != data.get('login_type'):
            return jsonify({'error': 'Invalid role'}), 401
        
        token = generate_token(user.id)
        session.clear()  # Clear any existing session
        session['jwt_token'] = token
        session['user_id'] = user.id
        session['role'] = user.role
        session['name'] = user.name
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
        
        if user.role == 'teacher' and user.teacher:
            user_data['teacher_id'] = user.teacher.id
            user_data['employee_id'] = user.teacher.employee_id
            user_data['department'] = user.teacher.department
        
        return jsonify({
            'token': token,
            'user': user_data
        })
    
    else:
        return jsonify({'error': 'Invalid login type'}), 400

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    token = request.headers.get('Authorization')
    if token:
        token = token.split(' ')[1]  # Remove 'Bearer '
    else:
        token = session.get('jwt_token')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(data['user_id'])
        if user and user.is_active:
            return jsonify({'valid': True, 'user_id': user.id, 'role': user.role})
        else:
            return jsonify({'valid': False}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401


### Registration endpoints

@auth_bp.route('/register/student', methods=['POST'])
def register_student():
    data = request.get_json()
    required = ['name', 'roll_no', 'division', 'standard', 'password']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'All fields are required'}), 400
    # Check for duplicate student (same roll_no, division, standard)
    if Student.query.filter_by(roll_no=data['roll_no'], division=data['division'], standard=data['standard']).first():
        return jsonify({'error': 'Student with this Roll No, Division, and Standard already exists'}), 409
    # Create user
    user = User(name=data['name'], role='student', is_active=True)
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()  # Get user.id
    # Create student
    student = Student(user_id=user.id, roll_no=data['roll_no'], division=data['division'], standard=data['standard'])
    db.session.add(student)
    db.session.commit()
    return jsonify({'message': 'Student registered successfully'}), 201
@auth_bp.route('/register/teacher', methods=['POST'])
def register_teacher():
    data = request.get_json()
    required = ['name', 'email', 'employee_id', 'department', 'password']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'All fields are required'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    if Teacher.query.filter_by(employee_id=data['employee_id']).first():
        return jsonify({'error': 'Employee ID already registered'}), 409
    user = User(name=data['name'], email=data['email'], role='teacher', is_active=True)
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()
    teacher = Teacher(user_id=user.id, employee_id=data['employee_id'], department=data['department'])
    db.session.add(teacher)
    db.session.commit()
    return jsonify({'message': 'Teacher registered successfully'}), 201

@auth_bp.route('/register/admin', methods=['POST'])
def register_admin():
    data = request.get_json()
    required = ['name', 'email', 'password']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'All fields are required'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    user = User(name=data['name'], email=data['email'], role='admin', is_active=True)
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Admin registered successfully'}), 201
