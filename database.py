"""
database.py
-----------
Skillzhub Intern Tracker - Database Layer (Configured for Supabase PostgreSQL)

Design:
- interns        -> basic intern profile
- tasks          -> assignments/tasks given to an intern, with deadline
- submissions    -> when intern completes task: timestamp + score (0-10) + auto grade
- users          -> authentication (admin & intern accounts)

Grading rule:
    8 - 10  -> Excellent
    5 - 7   -> Good
    0 - 4   -> Fail
"""

import streamlit as st
import os
import hashlib
from datetime import datetime
from contextlib import contextmanager

# ---------------------------------------------------------------------------
# CONFIG - Supabase PostgreSQL (Robust connection handling)
# ---------------------------------------------------------------------------

def _get_db_url():
    """Get PostgreSQL connection URL from Streamlit secrets."""
    try:
        return st.secrets["postgres"]["db_url"]
    except Exception as e:
        raise RuntimeError(
            "PostgreSQL not configured. Please add [postgres] section "
            "with db_url in Streamlit secrets.toml"
        ) from e


@contextmanager
def get_connection():
    """Returns a PostgreSQL database connection.
    Parses the DB URL securely to avoid psycopg2 parsing issues with special characters."""
    import psycopg2
    import urllib.parse as urlparse
    
    db_url = _get_db_url()
    url = urlparse.urlparse(db_url)
    
    # Password me se URL encoding (%40 etc) ko clean karna
    password = urlparse.unquote(url.password) if url.password else ""
    
    # Explicit parameters ke sath connection open karna (No parsing error fallback)
    conn = psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=password,
        host=url.hostname,
        port=url.port
    )
    try:
        yield conn
    finally:
        conn.close()


def _ph():
    """Placeholder style for PostgreSQL (%s)."""
    return "%s"


def _hash_password(password):
    """Simple SHA-256 hash for password storage."""
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------------------------------------------------------
# SCHEMA
# ---------------------------------------------------------------------------
def init_db():
    with get_connection() as conn:
        cur = conn.cursor()

        id_type = "SERIAL PRIMARY KEY"

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS interns (
                id {id_type},
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                department TEXT,
                joining_date TEXT,
                created_at TEXT
            )
        """)

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS tasks (
                id {id_type},
                intern_id INTEGER NOT NULL REFERENCES interns(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                assigned_date TEXT,
                deadline TEXT,
                status TEXT DEFAULT 'Pending',
                file_name TEXT,
                file_path TEXT,
                submitted_at TEXT,
                completed_at TEXT,
                score REAL,
                grade TEXT
            )
        """)

        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                id {id_type},
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'intern')),
                intern_id INTEGER REFERENCES interns(id) ON DELETE SET NULL,
                created_at TEXT
            )
        """)

        conn.commit()

        # Lightweight migration for DBs created before file-upload columns existed
        _ensure_columns(conn)

        # Seed default admin if not exists
        _seed_default_admin(conn)


def _ensure_columns(conn):
    """Add new columns to an existing tasks table if they're missing (safe upgrade)."""
    cur = conn.cursor()
    cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS file_name TEXT")
    cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS file_path TEXT")
    cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS submitted_at TEXT")
    conn.commit()


def _seed_default_admin(conn):
    """Create a default admin account if no admin exists."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cur.fetchone()[0] == 0:
        ph = _ph()
        hashed = _hash_password("admin123")
        cur.execute(
            f"INSERT INTO users (username, password, role, created_at) VALUES ({ph},{ph},{ph},{ph})",
            ("admin", hashed, "admin", datetime.now().isoformat()),
        )
        conn.commit()


def get_grade(score):
    """Score band -> grade text. 8-10 Excellent, 5-7 Good, <5 Fail."""
    if score is None:
        return None
    if score >= 8:
        return "Excellent"
    elif score >= 5:
        return "Good"
    else:
        return "Fail"


# ---------------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------------
def verify_user(username, password):
    """Check username/password. Returns user dict or None."""
    hashed = _hash_password(password)
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        cur.execute(
            f"SELECT id, username, role, intern_id FROM users WHERE username = {ph} AND password = {ph}",
            (username, hashed),
        )
        row = cur.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "role": row[2], "intern_id": row[3]}
        return None


def create_intern_user(intern_id, username, password):
    """Create a user account for an intern."""
    hashed = _hash_password(password)
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        try:
            cur.execute(
                f"INSERT INTO users (username, password, role, intern_id, created_at) VALUES ({ph},{ph},{ph},{ph},{ph})",
                (username, hashed, "intern", intern_id, datetime.now().isoformat()),
            )
            conn.commit()
            return True
        except Exception:
            return False


def signup_intern(name, email, phone, department, joining_date, username, password):
    """Register a new intern with profile + login account in one step.
    Returns (success, message)."""
    hashed = _hash_password(password)
    try:
        with get_connection() as conn:
            ph = _ph()
            cur = conn.cursor()
            # 1. Create intern profile
            cur.execute(
                f"""INSERT INTO interns (name, email, phone, department, joining_date, created_at)
                    VALUES ({ph},{ph},{ph},{ph},{ph},{ph}) RETURNING id""",
                (name, email, phone, department, joining_date, datetime.now().isoformat()),
            )
            intern_id = cur.fetchone()[0]

            # 2. Create user account linked to intern
            cur.execute(
                f"INSERT INTO users (username, password, role, intern_id, created_at) VALUES ({ph},{ph},{ph},{ph},{ph})",
                (username, hashed, "intern", intern_id, datetime.now().isoformat()),
            )
            conn.commit()
            return (True, "Account created successfully! You can now login.")
    except Exception as e:
        err = str(e)
        if "unique" in err.lower() or "duplicate" in err.lower():
            if "email" in err.lower():
                return (False, "This email is already registered.")
            return (False, "Username is already taken. Please choose another.")
        return (False, f"Could not create account: {err}")


def change_admin_password(username, old_password, new_password):
    """Change admin password after verifying old credentials. Returns (success, message)."""
    user = verify_user(username, old_password)
    if not user or user["role"] != "admin":
        return (False, "Invalid username or current password.")
    if len(new_password) < 6:
        return (False, "New password must be at least 6 characters.")
    hashed = _hash_password(new_password)
    try:
        with get_connection() as conn:
            ph = _ph()
            cur = conn.cursor()
            cur.execute(
                f"UPDATE users SET password = {ph} WHERE id = {ph}",
                (hashed, user["id"]),
            )
            conn.commit()
            return (True, "Password changed successfully!")
    except Exception as e:
        return (False, f"Could not change password: {e}")


def get_all_users():
    """Get all users for management."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.username, u.role, u.intern_id, i.name AS intern_name
            FROM users u
            LEFT JOIN interns i ON i.id = u.intern_id
            ORDER BY u.id
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# INTERNS
# ---------------------------------------------------------------------------
def add_intern(name, email, phone, department, joining_date):
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO interns (name, email, phone, department, joining_date, created_at) VALUES ({ph},{ph},{ph},{ph},{ph},{ph})",
            (name, email, phone, department, joining_date, datetime.now().isoformat()),
        )
        conn.commit()


def get_all_interns():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, phone, department, joining_date FROM interns ORDER BY name")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_intern_by_id(intern_id):
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, phone, department, joining_date FROM interns WHERE id = " + ph,
            (intern_id,),
        )
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None


def get_intern_score_summary():
    """Get each intern with their task count, avg score, and grade distribution."""
    with get_connection() as conn:
        cur = conn.cursor()
        avg_sql = "ROUND(CAST(AVG(t.score) AS NUMERIC), 2)"
        cur.execute(f"""
            SELECT
                i.id,
                i.name,
                i.email,
                i.department,
                COUNT(t.id) AS total_tasks,
                COUNT(CASE WHEN t.status = 'Completed' THEN 1 END) AS completed_tasks,
                {avg_sql} AS avg_score,
                COUNT(CASE WHEN t.grade = 'Excellent' THEN 1 END) AS excellent_count,
                COUNT(CASE WHEN t.grade = 'Good' THEN 1 END) AS good_count,
                COUNT(CASE WHEN t.grade = 'Fail' THEN 1 END) AS fail_count
            FROM interns i
            LEFT JOIN tasks t ON t.intern_id = i.id
            GROUP BY i.id, i.name, i.email, i.department
            ORDER BY i.name
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def delete_intern(intern_id):
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        # Also delete the associated user account if exists
        cur.execute(f"DELETE FROM users WHERE intern_id = {ph}", (intern_id,))
        cur.execute(f"DELETE FROM interns WHERE id = {ph}", (intern_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------
def assign_task(intern_id, title, description, deadline):
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        cur.execute(
            f"""INSERT INTO tasks (intern_id, title, description, assigned_date, deadline, status)
                VALUES ({ph},{ph},{ph},{ph},{ph},'Pending')""",
            (intern_id, title, description, datetime.now().isoformat(), deadline),
        )
        conn.commit()


def get_all_tasks():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, i.name AS intern_name, t.intern_id, t.title, t.description,
                   t.assigned_date, t.deadline, t.status, t.file_name, t.file_path,
                   t.submitted_at, t.completed_at, t.score, t.grade
            FROM tasks t
            JOIN interns i ON i.id = t.intern_id
            ORDER BY t.id DESC
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_tasks_by_intern(intern_id):
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        cur.execute(
            f"""SELECT id, title, description, assigned_date, deadline, status,
                       file_name, file_path, submitted_at, completed_at, score, grade
                FROM tasks WHERE intern_id = {ph} ORDER BY id DESC""",
            (intern_id,),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def submit_task(task_id, file_name, file_path):
    """Intern uploads their completed work. Records the real completion timestamp."""
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        cur.execute(
            f"""UPDATE tasks
                SET status = 'Submitted', file_name = {ph}, file_path = {ph}, submitted_at = {ph}
                WHERE id = {ph}""",
            (file_name, file_path, datetime.now().isoformat(), task_id),
        )
        conn.commit()


def get_tasks_by_status(status):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, i.name AS intern_name, t.intern_id, t.title, t.description,
                   t.assigned_date, t.deadline, t.status, t.file_name, t.file_path,
                   t.submitted_at, t.completed_at, t.score, t.grade
            FROM tasks t
            JOIN interns i ON i.id = t.intern_id
            WHERE t.status = %s
            ORDER BY t.id DESC
        """, (status,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def complete_task(task_id, score):
    """Mark a task complete with a timestamp + score (0-10), auto-computes grade."""
    grade = get_grade(score)
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        cur.execute(
            f"""UPDATE tasks
                SET status = 'Completed', completed_at = {ph}, score = {ph}, grade = {ph}
                WHERE id = {ph}""",
            (datetime.now().isoformat(), score, grade, task_id),
        )
        conn.commit()


def delete_task(task_id):
    with get_connection() as conn:
        ph = _ph()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM tasks WHERE id = {ph}", (task_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# STATS
# ---------------------------------------------------------------------------
def get_stats():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM interns")
        total_interns = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed'")
        completed_tasks = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Pending'")
        pending_tasks = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Submitted'")
        submitted_tasks = cur.fetchone()[0]

        cur.execute("SELECT AVG(score) FROM tasks WHERE score IS NOT NULL")
        avg_score = cur.fetchone()[0]

        cur.execute("SELECT grade, COUNT(*) FROM tasks WHERE grade IS NOT NULL GROUP BY grade")
        grade_counts = {row[0]: row[1] for row in cur.fetchall()}

        return {
            "total_interns": total_interns,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "submitted_tasks": submitted_tasks,
            "avg_score": round(avg_score, 2) if avg_score else 0,
            "grade_counts": grade_counts,
        }