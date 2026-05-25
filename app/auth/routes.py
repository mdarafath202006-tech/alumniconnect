"""
app/auth/routes.py – Authentication: register, login, logout, password reset.

Security upgrades applied:
  ✅ Rate limiting on login (5/minute) via Flask-Limiter
  ✅ CSRF via Flask-WTF (token validated automatically in templates)
  ✅ Password policy enforced (length + complexity)
  ✅ Input validation & sanitisation
  ✅ No credentials in source – all config from environment
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from app.utils.db import get_db
from app.utils.validators import validate_email, validate_password, sanitize
from app import limiter

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = sanitize(request.form.get("name", ""), 100)
        email    = sanitize(request.form.get("email", ""), 150).lower()
        password = request.form.get("password", "")
        role     = request.form.get("role", "student")

        # ── Validate ────────────────────────────────────────────────────────
        if not name:
            flash("Name is required.", "danger"); return redirect(url_for("auth.register"))
        if not validate_email(email):
            flash("Invalid email address.", "danger"); return redirect(url_for("auth.register"))
        ok, err = validate_password(password)
        if not ok:
            flash(err, "danger"); return redirect(url_for("auth.register"))
        if role not in ("student", "alumni"):
            flash("Invalid role.", "danger"); return redirect(url_for("auth.register"))

        hashed = generate_password_hash(password)

        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                flash("Email already registered.", "danger")
                return redirect(url_for("auth.register"))

            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s)",
                (name, email, hashed, role)
            )
            db.commit()
            user_id = cur.lastrowid

            if role == "student":
                dept = sanitize(request.form.get("department", ""), 100)
                year = sanitize(request.form.get("year", ""), 10)
                cur.execute(
                    "INSERT INTO students (user_id, department, year) VALUES (%s,%s,%s)",
                    (user_id, dept, year)
                )
            elif role == "alumni":
                grad_year = request.form.get("grad_year", None)
                company   = sanitize(request.form.get("company", ""), 150)
                job_role  = sanitize(request.form.get("job_role", ""), 150)
                cur.execute(
                    "INSERT INTO alumni (user_id, graduation_year, company, job_role) VALUES (%s,%s,%s,%s)",
                    (user_id, grad_year or None, company, job_role)
                )
            db.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("auth.login"))
        finally:
            cur.close(); db.close()

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")          # ✅ brute-force protection
def login():
    if request.method == "POST":
        email    = sanitize(request.form.get("email", ""), 150).lower()
        password = request.form.get("password", "")

        db  = get_db()
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
        finally:
            cur.close(); db.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"]    = user["name"]
            session["role"]    = user["role"]
            session.permanent  = True
            flash(f"Welcome back, {user['name']}!", "success")
            role = user["role"]
            if role == "student": return redirect(url_for("student.dashboard"))
            if role == "alumni":  return redirect(url_for("alumni.dashboard"))
            if role == "admin":   return redirect(url_for("admin.dashboard"))

        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))
