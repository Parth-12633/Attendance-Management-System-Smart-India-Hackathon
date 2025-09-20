# Script to print all classes with standard, division, academic_year
from app import app
from models import Class

with app.app_context():
    print("--- Classes ---")
    for cls in Class.query.all():
        print(f"ID: {cls.id}, Standard: '{cls.standard}', Division: '{cls.division}', Academic Year: '{getattr(cls, 'academic_year', 'N/A')}'")
