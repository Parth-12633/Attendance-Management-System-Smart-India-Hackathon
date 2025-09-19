"""add manual_code column

Revision ID: a2472dd5d826
Revises: 20250918_add_subject_to_attendance
Create Date: 2025-09-18 10:34:56.789012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2472dd5d826'
down_revision = '20250918_add_subject_to_attendance'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attendance_session', sa.Column('manual_code', sa.String(6), unique=True, nullable=True))


def downgrade():
    op.drop_column('attendance_session', 'manual_code')