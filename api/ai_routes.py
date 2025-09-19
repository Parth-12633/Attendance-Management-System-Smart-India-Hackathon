from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ai_recommendations import analyzer
from models import User, Student, Teacher
from auth import role_required
import numpy as np
import os
from models import db, Student
from flask import current_app
import face_recognition

ai_bp = Blueprint('ai', __name__)

ENCODINGS_DIR = os.path.join(current_app.root_path, 'face_encodings')
os.makedirs(ENCODINGS_DIR, exist_ok=True)

@ai_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get AI recommendations for the current user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if not student:
                return jsonify({'error': 'Student profile not found'}), 404
            
            recommendations = analyzer.generate_recommendations(student.id)
            stats = analyzer.get_student_attendance_stats(student.id)
            subject_stats = analyzer.get_subject_wise_attendance(student.id)
            trends = analyzer.get_attendance_trends(student.id)
            
            return jsonify({
                'recommendations': recommendations,
                'stats': stats,
                'subject_stats': subject_stats,
                'trends': trends
            })
        
        elif user.role == 'teacher':
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if not teacher:
                return jsonify({'error': 'Teacher profile not found'}), 404
            
            # Get at-risk students for teacher's classes
            at_risk_students = analyzer.identify_at_risk_students()
            
            return jsonify({
                'at_risk_students': [{
                    'student_name': student['student'].name,
                    'roll_number': student['student'].roll_number,
                    'class_name': student['student'].class_obj.name if student['student'].class_obj else 'N/A',
                    'attendance_percentage': student['stats']['percentage'],
                    'risk_level': student['risk_level']
                } for student in at_risk_students]
            })
        
        else:
            return jsonify({'error': 'Invalid user role'}), 403
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/class-insights/<int:class_id>', methods=['GET'])
@jwt_required()
@role_required(['teacher', 'admin'])
def get_class_insights(class_id):
    """Get AI insights for a specific class"""
    try:
        insights = analyzer.get_class_insights(class_id)
        at_risk_students = analyzer.identify_at_risk_students(class_id)
        
        return jsonify({
            'insights': insights,
            'at_risk_students': [{
                'student_name': student['student'].name,
                'roll_number': student['student'].roll_number,
                'attendance_percentage': student['stats']['percentage'],
                'risk_level': student['risk_level']
            } for student in at_risk_students]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/student-analysis/<int:student_id>', methods=['GET'])
@jwt_required()
@role_required(['teacher', 'admin'])
def get_student_analysis(student_id):
    """Get detailed analysis for a specific student"""
    try:
        recommendations = analyzer.generate_recommendations(student_id)
        stats = analyzer.get_student_attendance_stats(student_id)
        subject_stats = analyzer.get_subject_wise_attendance(student_id)
        trends = analyzer.get_attendance_trends(student_id)
        
        return jsonify({
            'recommendations': recommendations,
            'stats': stats,
            'subject_stats': subject_stats,
            'trends': trends
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Facial Recognition Endpoints ---

@ai_bp.route('/register_face', methods=['POST'])
def register_face():
    import base64, json
    data = request.get_json()
    student_id = data.get('student_id')
    images = data.get('images', [])  # List of base64 images
    if not student_id or not images:
        return jsonify({'error': 'Missing student_id or images'}), 400
    # Limit to 5 images
    images = images[:5]
    encodings = []
    for img_b64 in images:
        img_bytes = base64.b64decode(img_b64.split(',')[1] if ',' in img_b64 else img_b64)
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        img_np = np.array(img)
        faces = face_recognition.face_encodings(img_np)
        if faces:
            encodings.append(faces[0])
    if not encodings:
        return jsonify({'error': 'No faces found'}), 400
    avg_encoding = np.mean(encodings, axis=0)
    npy_path = os.path.join(ENCODINGS_DIR, f'{student_id}.npy')
    np.save(npy_path, avg_encoding)
    student = Student.query.get(student_id)
    student.face_encoding = npy_path
    student.face_images = json.dumps(images)
    db.session.commit()
    return jsonify({'success': True})

@ai_bp.route('/recognize_face', methods=['POST'])
def recognize_face():
    data = request.get_json()
    image = data.get('image')  # base64 image or file path
    session_id = data.get('session_id')
    if not image or not session_id:
        return jsonify({'error': 'Missing image or session_id'}), 400
    img = face_recognition.load_image_file(image)
    faces = face_recognition.face_encodings(img)
    if not faces:
        return jsonify({'error': 'No face found'}), 400
    encoding = faces[0]
    # Compare with all student encodings
    students = Student.query.filter(Student.face_encoding.isnot(None)).all()
    for student in students:
        known_encoding = np.load(student.face_encoding)
        match = face_recognition.compare_faces([known_encoding], encoding, tolerance=0.5)[0]
        if match:
            # Mark attendance for this student and session
            from models import Attendance, AttendanceSession
            session = AttendanceSession.query.get(session_id)
            if not session:
                return jsonify({'error': 'Session not found'}), 404
            existing = Attendance.query.filter_by(student_id=student.id, session_id=session.id).first()
            if existing:
                return jsonify({'match': True, 'student_id': student.id, 'name': student.user.name, 'attendance': 'already_marked'})
            attendance = Attendance(student_id=student.id, session_id=session.id, status='present', marked_by='face')
            db.session.add(attendance)
            db.session.commit()
            return jsonify({'match': True, 'student_id': student.id, 'name': student.user.name, 'attendance': 'marked', 'marked_at': attendance.marked_at.isoformat()})
    return jsonify({'match': False})
