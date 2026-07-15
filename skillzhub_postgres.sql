-- =============================================================
-- Skillzhub Intern Tracker - PostgreSQL Schema
-- =============================================================
-- Run this once to create the database and tables before
-- switching SKILLZHUB_DB=postgres in your environment.
--
-- Usage:
--   createdb skillzhub
--   psql -d skillzhub -f skillzhub_postgres.sql
-- =============================================================

-- 1. INTERNS TABLE
CREATE TABLE IF NOT EXISTS interns (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    department TEXT,
    joining_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. TASKS TABLE
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    intern_id INTEGER NOT NULL REFERENCES interns(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    assigned_date TIMESTAMP DEFAULT NOW(),
    deadline DATE,
    status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Submitted', 'Completed')),
    file_name TEXT,
    file_path TEXT,
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    score NUMERIC(4,1) CHECK (score >= 0 AND score <= 10),
    grade TEXT CHECK (grade IN ('Excellent', 'Good', 'Fail'))
);

-- 3. USERS TABLE (authentication: admin & intern accounts)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'intern')),
    intern_id INTEGER REFERENCES interns(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed default admin account (password: admin123)
-- SHA-256 hash of 'admin123' = 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
INSERT INTO users (username, password, role)
SELECT 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin');

-- 4. INDEXES (faster lookups for dashboard / filters)
CREATE INDEX IF NOT EXISTS idx_tasks_intern_id ON tasks(intern_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_grade ON tasks(grade);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- =============================================================
-- 4. AUTO-GRADE FUNCTION + TRIGGER (optional but recommended)
-- Automatically sets grade whenever a score is inserted/updated,
-- so grading logic lives in the database itself, not just the app.
--   8 - 10  -> Excellent
--   5 - 7   -> Good
--   0 - 4   -> Fail
-- =============================================================
CREATE OR REPLACE FUNCTION set_task_grade()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.score IS NULL THEN
        NEW.grade := NULL;
    ELSIF NEW.score >= 8 THEN
        NEW.grade := 'Excellent';
    ELSIF NEW.score >= 5 THEN
        NEW.grade := 'Good';
    ELSE
        NEW.grade := 'Fail';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_task_grade ON tasks;
CREATE TRIGGER trg_set_task_grade
    BEFORE INSERT OR UPDATE OF score ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION set_task_grade();

-- =============================================================
-- 4b. MIGRATION (run this ONLY if you already created the tables
-- before file-upload support was added, so the tables exist but
-- are missing these columns)
-- =============================================================
-- ALTER TABLE tasks ADD COLUMN IF NOT EXISTS file_name TEXT;
-- ALTER TABLE tasks ADD COLUMN IF NOT EXISTS file_path TEXT;
-- ALTER TABLE tasks ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP;
-- ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_status_check;
-- ALTER TABLE tasks ADD CONSTRAINT tasks_status_check CHECK (status IN ('Pending', 'Submitted', 'Completed'));

-- =============================================================
-- 5. SAMPLE DATA (optional - remove if not needed)
-- =============================================================
-- INSERT INTO interns (name, email, phone, department, joining_date)
-- VALUES ('Ali Raza', 'ali@example.com', '03001234567', 'Web Development', '2026-07-01');

-- INSERT INTO tasks (intern_id, title, description, deadline)
-- VALUES (1, 'Build a login form', 'Use HTML/CSS/JS', '2026-07-20');

-- =============================================================
-- 6. USEFUL QUERIES
-- =============================================================

-- Mark a task completed with a score (grade auto-fills via trigger):
-- UPDATE tasks SET status = 'Completed', completed_at = NOW(), score = 9 WHERE id = 1;

-- Dashboard stats:
-- SELECT COUNT(*) FROM interns;
-- SELECT COUNT(*) FROM tasks WHERE status = 'Completed';
-- SELECT AVG(score) FROM tasks WHERE score IS NOT NULL;
-- SELECT grade, COUNT(*) FROM tasks WHERE grade IS NOT NULL GROUP BY grade;

-- All tasks with intern name, newest first:
-- SELECT t.*, i.name AS intern_name
-- FROM tasks t JOIN interns i ON i.id = t.intern_id
-- ORDER BY t.id DESC;
