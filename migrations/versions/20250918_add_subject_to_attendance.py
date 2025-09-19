"""add subject column to attendance

Revision ID: 20250918_add_subject_to_attendance
Revises: 
Create Date: 2025-09-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250918_add_subject_to_attendance'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add a nullable subject column to attendance
    op.add_column('attendance', sa.Column('subject', sa.String(length=100), nullable=True))


def downgrade():
    # Remove the subject column
    op.drop_column('attendance', 'subject')
