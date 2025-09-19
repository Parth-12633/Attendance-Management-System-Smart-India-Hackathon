-- SQL script to add `subject` column to `attendance` table
-- Usage (SQLite):
--   sqlite3 instance/attendance.db < scripts/add_subject_column.sql

ALTER TABLE attendance ADD COLUMN subject VARCHAR(100);
