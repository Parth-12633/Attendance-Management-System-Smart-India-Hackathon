This folder contains a minimal Alembic migration setup created by the assistant.

How to use:

1. Install Alembic in your virtual environment if not present:

```powershell
.\.venv\Scripts\Activate.ps1; pip install alembic
```

2. Ensure `SQLALCHEMY_DATABASE_URI` is set in your Flask config or `alembic.ini`.

3. Run the migration:

```powershell
# from project root
.\.venv\Scripts\Activate.ps1; flask db upgrade
```

If you don't use Flask-Migrate, you can run the generated SQL directly against your DB. The migration `migrations/versions/20250918_add_subject_to_attendance.py` will add a nullable `subject` column to the `attendance` table and downgrade will drop it.
