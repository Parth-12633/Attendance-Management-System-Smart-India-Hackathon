# Script to update all Class.standard values from '10th' to '10'
from app import app
from models import db, Class

with app.app_context():
    classes = Class.query.filter_by(standard='10th').all()
    for cls in classes:
        print(f"Updating Class ID {cls.id}: '{cls.standard}' -> '10'")
        cls.standard = '10'
    db.session.commit()
    print("All relevant Class.standard values updated to '10'.")
