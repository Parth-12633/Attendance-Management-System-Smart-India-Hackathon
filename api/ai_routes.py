from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ai_recommendations import analyzer
from models import User, Student, Teacher
from auth import role_required

ai_bp = Blueprint('ai', __name__)

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
