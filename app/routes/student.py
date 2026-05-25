"""
app/routes/student.py – Student blueprint.

Upgrades:
  ✅ Blueprint-based routing
  ✅ Skill-gap analysis endpoint
  ✅ Sanitised inputs
  ✅ Matched-skills shown in recommendations
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.utils.db import get_db
from app.utils.decorators import login_required, role_required
from app.utils.validators import sanitize
from app.ai.recommender import get_recommendations, get_skill_gap

student_bp = Blueprint("student", __name__)


@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM students WHERE user_id=%s", (session["user_id"],))
        profile = cur.fetchone()
        sid = profile["id"] if profile else 0

        cur.execute("SELECT COUNT(*) AS cnt FROM mentorship_requests WHERE student_id=%s", (sid,))
        req_count = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM alumni")
        alumni_count = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM mentorship_requests WHERE student_id=%s AND status='accepted'", (sid,))
        accepted_count = cur.fetchone()["cnt"]
    finally:
        cur.close(); db.close()

    return render_template(
        "student/dashboard.html",
        profile=profile,
        req_count=req_count,
        alumni_count=alumni_count,
        accepted_count=accepted_count,
    )


@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("student")
def profile():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        if request.method == "POST":
            skills    = sanitize(request.form.get("skills", ""))
            interests = sanitize(request.form.get("interests", ""))
            bio       = sanitize(request.form.get("bio", ""), 1000)
            cur.execute(
                "UPDATE students SET skills=%s, interests=%s, bio=%s WHERE user_id=%s",
                (skills, interests, bio, session["user_id"])
            )
            db.commit()
            flash("Profile updated!", "success")

        cur.execute("SELECT * FROM students WHERE user_id=%s", (session["user_id"],))
        profile = cur.fetchone()
    finally:
        cur.close(); db.close()

    return render_template("student/profile.html", profile=profile)


@student_bp.route("/recommendations")
@login_required
@role_required("student")
def recommendations():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM students WHERE user_id=%s", (session["user_id"],))
        student = cur.fetchone()
        cur.execute("SELECT a.*, u.name, u.email FROM alumni a JOIN users u ON a.user_id=u.id")
        all_alumni = cur.fetchall()
    finally:
        cur.close(); db.close()

    ranked = []
    if student and (student.get("skills") or student.get("interests")):
        ranked = get_recommendations(student, all_alumni)
    else:
        ranked = [{"alumni": a, "score": 0, "percent": 0, "matched_skills": [], "skill_overlap": 0}
                  for a in all_alumni]

    return render_template("student/recommendations.html", ranked=ranked, student=student)


@student_bp.route("/skill-gap")
@login_required
@role_required("student")
def skill_gap():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM students WHERE user_id=%s", (session["user_id"],))
        student = cur.fetchone()
        cur.execute("SELECT skills, job_role FROM alumni")
        all_alumni = cur.fetchall()
        cur.execute("SELECT DISTINCT job_role FROM alumni WHERE job_role IS NOT NULL ORDER BY job_role")
        roles = [r["job_role"] for r in cur.fetchall()]
    finally:
        cur.close(); db.close()

    target_role = request.args.get("role", "")
    gap_data = {}
    if target_role and student:
        gap_data = get_skill_gap(student, target_role, all_alumni)

    return render_template("student/skill_gap.html",
                           student=student, roles=roles,
                           target_role=target_role, gap=gap_data)


@student_bp.route("/request_mentor/<int:alumni_id>", methods=["POST"])
@login_required
@role_required("student")
def request_mentor(alumni_id):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM students WHERE user_id=%s", (session["user_id"],))
        student = cur.fetchone()
        message = sanitize(request.form.get("message", ""), 500)
        # Prevent duplicate pending requests
        cur.execute(
            "SELECT id FROM mentorship_requests WHERE student_id=%s AND alumni_id=%s AND status='pending'",
            (student["id"], alumni_id)
        )
        if cur.fetchone():
            flash("You already have a pending request to this mentor.", "warning")
            return redirect(url_for("student.recommendations"))
        cur.execute(
            "INSERT INTO mentorship_requests (student_id, alumni_id, message) VALUES (%s,%s,%s)",
            (student["id"], alumni_id, message)
        )
        db.commit()
    finally:
        cur.close(); db.close()

    flash("Mentorship request sent!", "success")
    return redirect(url_for("student.recommendations"))


@student_bp.route("/search")
@login_required
@role_required("student")
def search():
    query   = sanitize(request.args.get("q", ""), 100)
    skill   = sanitize(request.args.get("skill", ""), 100)
    company = sanitize(request.args.get("company", ""), 100)

    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        sql    = "SELECT a.*, u.name, u.email FROM alumni a JOIN users u ON a.user_id=u.id WHERE 1=1"
        params = []
        if query:
            sql += " AND (u.name LIKE %s OR a.job_role LIKE %s OR a.skills LIKE %s)"
            params += [f"%{query}%"] * 3
        if skill:
            sql += " AND a.skills LIKE %s"
            params.append(f"%{skill}%")
        if company:
            sql += " AND a.company LIKE %s"
            params.append(f"%{company}%")
        cur.execute(sql, params)
        results = cur.fetchall()
    finally:
        cur.close(); db.close()

    return render_template("student/search.html",
                           results=results, query=query, skill=skill, company=company)
