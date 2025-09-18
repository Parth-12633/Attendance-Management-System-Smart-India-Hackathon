-- Create sample data for testing
-- Run this script after setting up the database

-- Insert sample subjects
INSERT INTO subject (name, code, description) VALUES
('Mathematics', 'MATH101', 'Basic Mathematics'),
('Physics', 'PHY101', 'Introduction to Physics'),
('Chemistry', 'CHEM101', 'Basic Chemistry'),
('English', 'ENG101', 'English Language and Literature'),
('Computer Science', 'CS101', 'Introduction to Programming');

-- Insert sample admin user
INSERT INTO user (name, email, role, password_hash, is_active) VALUES
('Admin User', 'admin@school.edu', 'admin', 'pbkdf2:sha256:260000$salt$hash', true);

-- Insert sample teacher
INSERT INTO user (name, email, role, password_hash, is_active) VALUES
('John Smith', 'john.smith@school.edu', 'teacher', 'pbkdf2:sha256:260000$salt$hash', true),
('Sarah Johnson', 'sarah.johnson@school.edu', 'teacher', 'pbkdf2:sha256:260000$salt$hash', true);

INSERT INTO teacher (user_id, employee_id, department, subjects) VALUES
(2, 'T001', 'Mathematics', '["Mathematics", "Physics"]'),
(3, 'T002', 'Science', '["Chemistry", "Physics"]');

-- Insert sample students
INSERT INTO user (name, role, is_active) VALUES
('Alice Brown', 'student', true),
('Bob Wilson', 'student', true),
('Carol Davis', 'student', true),
('David Miller', 'student', true);

INSERT INTO student (user_id, roll_no, division, standard, phone, interests, career_goals) VALUES
(4, '001', 'A', '10', '1234567890', '["Mathematics", "Science"]', 'Engineering'),
(5, '002', 'A', '10', '1234567891', '["Literature", "History"]', 'Teaching'),
(6, '003', 'A', '10', '1234567892', '["Science", "Technology"]', 'Medicine'),
(7, '004', 'B', '10', '1234567893', '["Arts", "Music"]', 'Creative Arts');

-- Insert sample class
INSERT INTO class (standard, division, academic_year) VALUES
('10', 'A', '2024-25'),
('10', 'B', '2024-25');

-- Insert sample timetable entries
INSERT INTO timetable (class_id, subject_id, teacher_id, day_of_week, start_time, end_time, room_number) VALUES
(1, 1, 1, 1, '09:00:00', '10:00:00', 'R101'), -- Math on Tuesday
(1, 2, 1, 1, '10:00:00', '11:00:00', 'R102'), -- Physics on Tuesday
(1, 3, 2, 2, '09:00:00', '10:00:00', 'R103'), -- Chemistry on Wednesday
(2, 1, 1, 1, '11:00:00', '12:00:00', 'R101'), -- Math for Class B
(2, 2, 1, 2, '10:00:00', '11:00:00', 'R102'); -- Physics for Class B
