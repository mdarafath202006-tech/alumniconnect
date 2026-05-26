"""
app/routes/admin.py – Admin blueprint (PostgreSQL fixed)
"""
from flask import Blueprint, render_template
import psycopg2.extras

from app.utils.db import get_db
from app.utils.decorators import login_required, role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # ── counts ─────────────────────────
        cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE role='student'")
        students = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE role='alumni'")
        alumni_count = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM mentorship_requests")
        req_count = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM mentorship_requests WHERE status='accepted'")
        accepted = cur.fetchone()["cnt"]

        # ── recent users ─────────────────────────
        cur.execute("""
            SELECT name, email, role, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent_users = cur.fetchall()

        # ── recent requests ─────────────────────────
        cur.execute("""
            SELECT
                mr.id,
                u_s.name AS student,
                u_a.name AS alumni,
                mr.status,
                mr.created_at
            FROM mentorship_requests mr
            JOIN students s ON mr.student_id = s.id
            JOIN alumni a ON mr.alumni_id = a.id
            JOIN users u_s ON s.user_id = u_s.id
            JOIN users u_a ON a.user_id = u_a.id
            ORDER BY mr.created_at DESC
            LIMIT 10
        """)
        recent_requests = cur.fetchall()

    finally:
        cur.close()
        db.close()

    return render_template(
        "admin/dashboard.html",
        students=students,
        alumni_count=alumni_count,
        req_count=req_count,
        accepted=accepted,
        recent_users=recent_users,
        recent_requests=recent_requests,
    )
