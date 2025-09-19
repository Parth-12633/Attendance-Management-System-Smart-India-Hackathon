import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from datetime import datetime, date

from app import app, db
from models import User, Teacher, Timetable, Class, Subject, AttendanceSession
from auth import generate_token
import jwt as pyjwt


@pytest.fixture
def client():
    # Use the existing application DB (do not re-init the SQLAlchemy instance)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'

    with app.app_context():
        db.create_all()

        # Create minimal data: class, subject, teacher, timetable and attendance session
        cls = Class(standard='10', division='A', academic_year='2025')
        db.session.add(cls)
        subj = Subject(name='Maths', code='MATH')
        db.session.add(subj)
        db.session.commit()

        user = User(name='Teacher One', role='teacher', email='t1@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.flush()
        teacher = Teacher(user_id=user.id, employee_id='T100')
        db.session.add(teacher)
        db.session.commit()

        tt = Timetable(class_id=cls.id, subject_id=subj.id, teacher_id=teacher.id, day_of_week=0, start_time=datetime.now().time(), end_time=datetime.now().time())
        db.session.add(tt)
        db.session.commit()

        # Create an attendance session so teacher endpoint can find it
        session = AttendanceSession(timetable_id=tt.id, date=date.today(), start_time=datetime.now(), attendance_method='qr')
        db.session.add(session)
        db.session.commit()

        client = app.test_client()
        yield client

        db.session.remove()
        db.drop_all()


def test_generate_qr_includes_subject(client):
    # Call the underlying view function directly inside a request context so we don't
    # rely on blueprint registration during tests.
    from api.teacher_routes import generate_session_qr

    with app.app_context():
        teacher = Teacher.query.first()
        session = AttendanceSession.query.first()
        assert session is not None

    fake_user = type('U', (), {'teacher': teacher, 'role': 'teacher'})()

    # Use a test_request_context so request.get_json() works inside the view
    with app.test_request_context(f'/api/teacher/session/{session.id}/generate_qr', method='POST', json={'subject': 'Science'}):
        # Call the un-decorated function (original implementation) to bypass auth decorators
        # generate_session_qr is wrapped by @token_required and @role_required; unwrap twice
        core_func = getattr(generate_session_qr, '__wrapped__', generate_session_qr)
        core_func = getattr(core_func, '__wrapped__', core_func)
        resp = core_func(fake_user, session.id)

        # resp may be a Flask Response
        if hasattr(resp, 'get_json'):
            data = resp.get_json()
        else:
            # If it returned a tuple (json, status), handle it
            if isinstance(resp, tuple):
                data = resp[0].get_json() if hasattr(resp[0], 'get_json') else resp[0]
            else:
                data = resp

        assert isinstance(data, dict)
        assert 'qr_code' in data
        assert 'jwt' in data

        decoded = pyjwt.decode(data['jwt'], app.config['SECRET_KEY'], algorithms=['HS256'])
        assert decoded.get('subject') == 'Science'
        assert decoded.get('session_id') == session.id
