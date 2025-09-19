Tests & DB migration notes

- To run the integration tests (uses `pytest`):

```powershell
C:\Users\Admin\Desktop\sih\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests/test_qr_subject.py -q
```

- If you already have a SQLite DB at `instance/attendance.db` and you've changed the models (added `Attendance.subject`), apply the small migration SQL:

```powershell
sqlite3 instance/attendance.db < scripts/add_subject_column.sql
```

Alternatively, use Flask-Migrate to create and apply an Alembic migration (recommended for production DBs).
