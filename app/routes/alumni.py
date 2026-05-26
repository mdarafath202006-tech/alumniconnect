"""
app/routes/alumni.py – Alumni blueprint (PostgreSQL fixed)
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import psycopg2.extras

from app.utils.db import get_db
from app.utils.decorators import login_required, role_required
from app.utils.validators import sanitize

alumni_bp = Blueprint("alumni", __name__)


# ───────────────────────── DASHBOARD ─────────────────────────
@alumni_bp.route("/dashboard")
@login_required
@role_required("alumni")
def dashboard():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cur.execute("SELECT * FROM alumni WHERE user_id=%s", (session["user_id"],))
        profile = cur.fetchone()

        if profile:
            cur.execute("""
                SELECT mr.*, u.name AS student_name, s.department, s.year, s.skills
                FROM mentorship_requests mr
                JOIN students s ON mr.student_id = s.id
                JOIN users u ON s.user_id = u.id
                WHERE mr.alumni_id = %s
                ORDER BY mr.created_at DESC
            """, (profile["id"],))
            requests = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*) AS cnt
                FROM mentorship_requests
                WHERE alumni_id=%s AND status='accepted'
            """, (profile["id"],))
            accepted_count = cur.fetchone()["cnt"]

        else:
            requests = []
            accepted_count = 0

    finally:
        cur.close()
        db.close()

    return render_template(
        "alumni/dashboard.html",
        profile=profile,
        requests=requests,
        accepted_count=accepted_count
    )


# ───────────────────────── PROFILE ─────────────────────────
@alumni_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("alumni")
def profile():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        if request.method == "POST":
            cur.execute("""
                UPDATE alumni
                SET company=%s,
                    job_role=%s,
                    skills=%s,
                    location=%s,
                    linkedin=%s,
                    bio=%s
                WHERE user_id=%s
            """, (
                sanitize(request.form.get("company", ""), 150),
                sanitize(request.form.get("job_role", ""), 150),
                sanitize(request.form.get("skills", "")),
                sanitize(request.form.get("location", ""), 100),
                sanitize(request.form.get("linkedin", ""), 255),
                sanitize(request.form.get("bio", ""), 1000),
                session["user_id"]
            ))

            db.commit()
            flash("Profile updated!", "success")

        cur.execute("SELECT * FROM alumni WHERE user_id=%s", (session["user_id"],))
        profile = cur.fetchone()

    finally:
        cur.close()
        db.close()

    return render_template("alumni/profile.html", profile=profile)


# ───────────────────────── RESPOND REQUEST ─────────────────────────
@alumni_bp.route("/respond/<int:req_id>/<action>")
@login_required
@role_required("alumni")
def respond_request(req_id, action):
    if action not in ("accept", "reject"):
        flash("Invalid action.", "danger")
        return redirect(url_for("alumni.dashboard"))

    status = "accepted" if action == "accept" else "rejected"

    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("""
            UPDATE mentorship_requests
            SET status=%s
            WHERE id=%s
        """, (status, req_id))
        db.commit()

    finally:
        cur.close()
        db.close()

    flash(f"Request {status}.", "success")
    return redirect(url_for("alumni.dashboard"))


# ───────────────────────── VIEW PROFILE ─────────────────────────
@alumni_bp.route("/view/<int:alumni_id>")
@login_required
def view(alumni_id):
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cur.execute("""
            SELECT a.*, u.name, u.email
            FROM alumni a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        """, (alumni_id,))
        alum = cur.fetchone()

    finally:
        cur.close()
        db.close()

    if not alum:
        flash("Alumni not found.", "danger")
        return redirect(url_for("student.search"))

    return render_template("view_alumni.html", alumni=alum)
