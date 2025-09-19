# ...existing code...

# ...existing code...

# ...existing code...

# Place this route after the dashboard routes

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps
import qrcode
import io
import base64
from extensions import db

app = Flask(__name__)

# Compatibility shims: patch Response.set_cookie and Response.delete_cookie to ignore unknown kwargs (like 'partitioned')
try:
    from werkzeug.wrappers import Response as _WResponse
    import inspect

    # Patch set_cookie
    sig = inspect.signature(_WResponse.set_cookie)
    if 'partitioned' not in sig.parameters:
        _orig_set_cookie = _WResponse.set_cookie
        def _set_cookie_compat(self, key, value='', max_age=None, expires=None,
                                path='/', domain=None, secure=False, httponly=False,
                                samesite=None, **kwargs):
            # Drop unsupported kwargs (e.g., partitioned) and call original
            return _orig_set_cookie(self, key, value=value, max_age=max_age,
                                     expires=expires, path=path, domain=domain,
                                     secure=secure, httponly=httponly, samesite=samesite)
        _WResponse.set_cookie = _set_cookie_compat

    # Patch delete_cookie
    sig_del = inspect.signature(_WResponse.delete_cookie)
    if 'partitioned' not in sig_del.parameters:
        _orig_delete_cookie = _WResponse.delete_cookie
        def _delete_cookie_compat(self, key, path='/', domain=None, secure=False, httponly=False,
                                  samesite=None, **kwargs):
            # Drop unsupported kwargs (e.g., partitioned) and call original
            return _orig_delete_cookie(self, key, path=path, domain=domain, secure=secure,
                                       httponly=httponly, samesite=samesite)
        _WResponse.delete_cookie = _delete_cookie_compat
except Exception:
    # If anything goes wrong, don't crash app startup; let runtime errors surface.
    pass

# Flask configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///attendance.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),
    SESSION_TYPE='filesystem'
)

# Enable CORS with support for credentials
CORS(app, supports_credentials=True)

# Make sessions permanent by default
@app.before_request
def make_session_permanent():
    session.permanent = True
    
# Handle OPTIONS requests for CORS preflight
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

db.init_app(app)
migrate = Migrate(app, db)

# Import models after db initialization
from models import *
from auth import *

# Register API blueprints (defensive imports so optional/heavy deps don't break app import)
def _try_register(bp_module, bp_name, url_prefix=None):
    try:
        mod = __import__(bp_module, fromlist=[bp_name])
        bp = getattr(mod, bp_name)
        if url_prefix:
            app.register_blueprint(bp, url_prefix=url_prefix)
        else:
            app.register_blueprint(bp)
        print(f"Registered blueprint: {bp_module}.{bp_name}")
    except Exception as e:
        # Log to stdout; don't crash app import
        print(f"Could not register blueprint {bp_module}.{bp_name}: {e}")


_try_register('api.auth_routes', 'auth_bp')
_try_register('api.attendance_routes', 'attendance_bp')
_try_register('api.student_routes', 'student_bp')
_try_register('api.teacher_routes', 'teacher_bp')
_try_register('api.admin_routes', 'admin_bp')
_try_register('api.ai_routes', 'ai_bp', url_prefix='/api/ai')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/student-dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/teacher-dashboard')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
