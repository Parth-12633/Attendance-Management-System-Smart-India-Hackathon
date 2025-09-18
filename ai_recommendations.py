import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from models import db, Student, Attendance, Subject, Class
from sqlalchemy import func, and_

class AttendanceAnalyzer:
    def __init__(self):
        self.attendance_threshold = 75  # Minimum attendance percentage
        self.risk_threshold = 60       # Below this is high risk
        
    def get_student_attendance_stats(self, student_id, days=30):
        """Get attendance statistics for a student over specified days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        total_classes = db.session.query(Attendance).filter(
            and_(
                Attendance.student_id == student_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).count()
        
        attended_classes = db.session.query(Attendance).filter(
            and_(
                Attendance.student_id == student_id,
                Attendance.status == 'present',
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).count()
        
        percentage = (attended_classes / total_classes * 100) if total_classes > 0 else 0
        
        return {
            'total_classes': total_classes,
            'attended_classes': attended_classes,
            'percentage': round(percentage, 2),
            'missed_classes': total_classes - attended_classes
        }
    
    def identify_at_risk_students(self, class_id=None):
        """Identify students at risk of poor attendance"""
        at_risk_students = []
        
        query = db.session.query(Student)
        if class_id:
            query = query.filter(Student.class_id == class_id)
            
        students = query.all()
        
        for student in students:
            stats = self.get_student_attendance_stats(student.id)
            if stats['percentage'] < self.risk_threshold:
                at_risk_students.append({
                    'student': student,
                    'stats': stats,
                    'risk_level': 'high' if stats['percentage'] < 50 else 'medium'
                })
        
        return sorted(at_risk_students, key=lambda x: x['stats']['percentage'])
    
    def get_attendance_trends(self, student_id, days=30):
        """Analyze attendance trends for a student"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get daily attendance data
        daily_attendance = db.session.query(
            func.date(Attendance.date).label('date'),
            func.count(Attendance.id).label('total'),
            func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present')
        ).filter(
            and_(
                Attendance.student_id == student_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).group_by(func.date(Attendance.date)).all()
        
        trends = []
        for record in daily_attendance:
            percentage = (record.present / record.total * 100) if record.total > 0 else 0
            trends.append({
                'date': record.date.strftime('%Y-%m-%d'),
                'percentage': round(percentage, 2)
            })
        
        return trends
    
    def get_subject_wise_attendance(self, student_id):
        """Get attendance breakdown by subject"""
        subject_stats = db.session.query(
            Subject.name,
            func.count(Attendance.id).label('total'),
            func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present')
        ).join(Attendance).filter(
            Attendance.student_id == student_id
        ).group_by(Subject.id, Subject.name).all()
        
        results = []
        for stat in subject_stats:
            percentage = (stat.present / stat.total * 100) if stat.total > 0 else 0
            results.append({
                'subject': stat.name,
                'total': stat.total,
                'present': stat.present,
                'percentage': round(percentage, 2)
            })
        
        return sorted(results, key=lambda x: x['percentage'])
    
    def generate_recommendations(self, student_id):
        """Generate AI-powered recommendations for a student"""
        recommendations = []
        
        # Get overall stats
        stats = self.get_student_attendance_stats(student_id)
        subject_stats = self.get_subject_wise_attendance(student_id)
        trends = self.get_attendance_trends(student_id, 14)  # Last 2 weeks
        
        # Overall attendance recommendations
        if stats['percentage'] < self.attendance_threshold:
            recommendations.append({
                'type': 'warning',
                'category': 'Overall Attendance',
                'message': f"Your attendance is {stats['percentage']:.1f}%, which is below the required {self.attendance_threshold}%.",
                'action': 'Focus on attending all upcoming classes to improve your overall attendance.',
                'priority': 'high' if stats['percentage'] < 60 else 'medium'
            })
        
        # Subject-specific recommendations
        for subject in subject_stats:
            if subject['percentage'] < self.attendance_threshold:
                recommendations.append({
                    'type': 'subject_warning',
                    'category': f"{subject['subject']} Attendance",
                    'message': f"Your {subject['subject']} attendance is {subject['percentage']:.1f}%.",
                    'action': f"Prioritize attending {subject['subject']} classes to avoid academic issues.",
                    'priority': 'high' if subject['percentage'] < 50 else 'medium'
                })
        
        # Trend analysis
        if len(trends) >= 7:
            recent_avg = np.mean([t['percentage'] for t in trends[-7:]])
            older_avg = np.mean([t['percentage'] for t in trends[:-7]]) if len(trends) > 7 else recent_avg
            
            if recent_avg < older_avg - 10:
                recommendations.append({
                    'type': 'trend_warning',
                    'category': 'Attendance Trend',
                    'message': 'Your attendance has been declining recently.',
                    'action': 'Consider identifying and addressing any barriers to regular attendance.',
                    'priority': 'medium'
                })
            elif recent_avg > older_avg + 10:
                recommendations.append({
                    'type': 'positive',
                    'category': 'Attendance Improvement',
                    'message': 'Great job! Your attendance has been improving recently.',
                    'action': 'Keep up the good work and maintain this positive trend.',
                    'priority': 'low'
                })
        
        # Perfect attendance recognition
        if stats['percentage'] >= 95:
            recommendations.append({
                'type': 'achievement',
                'category': 'Excellent Attendance',
                'message': f'Outstanding! You have {stats["percentage"]:.1f}% attendance.',
                'action': 'Continue your excellent attendance record.',
                'priority': 'low'
            })
        
        return recommendations
    
    def get_class_insights(self, class_id):
        """Generate insights for a class"""
        students = Student.query.filter_by(class_id=class_id).all()
        
        class_stats = {
            'total_students': len(students),
            'high_performers': 0,
            'at_risk': 0,
            'average_attendance': 0
        }
        
        total_percentage = 0
        for student in students:
            stats = self.get_student_attendance_stats(student.id)
            total_percentage += stats['percentage']
            
            if stats['percentage'] >= 90:
                class_stats['high_performers'] += 1
            elif stats['percentage'] < 60:
                class_stats['at_risk'] += 1
        
        class_stats['average_attendance'] = round(total_percentage / len(students), 2) if students else 0
        
        return class_stats

# Initialize the analyzer
analyzer = AttendanceAnalyzer()
