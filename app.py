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

# Register API blueprints
from api.auth_routes import auth_bp
from api.attendance_routes import attendance_bp
from api.student_routes import student_bp
from api.teacher_routes import teacher_bp
from api.admin_routes import admin_bp
from api.ai_routes import ai_bp

app.register_blueprint(auth_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(student_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(ai_bp, url_prefix='/api/ai')

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
