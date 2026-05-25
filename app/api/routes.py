"""
app/api/routes.py – REST API blueprint.

Endpoints:
  POST /api/auth/login          → returns JWT access + refresh tokens
  GET  /api/recommendations     → AI mentor list (JWT required)
  GET  /api/analytics           → career analytics JSON (JWT required)
  GET  /api/alumni/<id>         → single alumni profile (JWT required)
  POST /api/skill-gap           → skill gap analysis (JWT required)
"""
import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash

from app.utils.db import get_db
from app.ai.recommender import get_recommendations, get_career_analytics, get_skill_gap
from app import limiter

api_bp = Blueprint("api", __name__)


# ── JWT helpers ───────────────────────────────────────────────────────────────
def _make_token(user_id: int, role: str, expires_delta: datetime.timedelta) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + expires_delta,
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
            )
            request.jwt_payload = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


# ── Auth ──────────────────────────────────────────────────────────────────────
@api_bp.route("/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def api_login():
    data = request.get_json(silent=True) or {}
    email    = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
    finally:
        cur.close(); db.close()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    access  = _make_token(user["id"], user["role"],
                          current_app.config["JWT_ACCESS_TOKEN_EXPIRES"])
    refresh = _make_token(user["id"], user["role"],
                          current_app.config["JWT_REFRESH_TOKEN_EXPIRES"])

    return jsonify({
        "access_token":  access,
        "refresh_token": refresh,
        "user": {"id": user["id"], "name": user["name"], "role": user["role"]},
    })


# ── Recommendations ───────────────────────────────────────────────────────────
@api_bp.route("/recommendations")
@jwt_required
def api_recommendations():
    if request.jwt_payload.get("role") != "student":
        return jsonify({"error": "Students only"}), 403

    uid = request.jwt_payload["sub"]
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM students WHERE user_id=%s", (uid,))
        student = cur.fetchone()
        cur.execute("SELECT a.*, u.name, u.email FROM alumni a JOIN users u ON a.user_id=u.id")
        all_alumni = cur.fetchall()
    finally:
        cur.close(); db.close()

    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    ranked = get_recommendations(student, all_alumni)
    # Serialize – drop non-JSON-safe fields if any
    result = [
        {
            "alumni_id":      r["alumni"]["id"],
            "name":           r["alumni"]["name"],
            "job_role":       r["alumni"]["job_role"],
            "company":        r["alumni"]["company"],
            "skills":         r["alumni"]["skills"],
            "percent":        r["percent"],
            "matched_skills": r["matched_skills"],
        }
        for r in ranked
    ]
    return jsonify({"recommendations": result, "count": len(result)})


# ── Analytics ─────────────────────────────────────────────────────────────────
@api_bp.route("/analytics")
@jwt_required
def api_analytics():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT job_role, company, skills, graduation_year FROM alumni")
        alumni_data = cur.fetchall()
    finally:
        cur.close(); db.close()
    return jsonify(get_career_analytics(alumni_data))


# ── Single alumni ─────────────────────────────────────────────────────────────
@api_bp.route("/alumni/<int:alumni_id>")
@jwt_required
def api_alumni(alumni_id):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT a.id, a.graduation_year, a.company, a.job_role,
                   a.skills, a.location, a.linkedin, a.bio, u.name, u.email
            FROM alumni a JOIN users u ON a.user_id=u.id
            WHERE a.id=%s
        """, (alumni_id,))
        alum = cur.fetchone()
    finally:
        cur.close(); db.close()

    if not alum:
        return jsonify({"error": "Not found"}), 404
    return jsonify(alum)


# ── Skill gap ─────────────────────────────────────────────────────────────────
@api_bp.route("/skill-gap", methods=["POST"])
@jwt_required
def api_skill_gap():
    if request.jwt_payload.get("role") != "student":
        return jsonify({"error": "Students only"}), 403

    data        = request.get_json(silent=True) or {}
    target_role = str(data.get("target_role", "")).strip()
    if not target_role:
        return jsonify({"error": "target_role is required"}), 400

    uid = request.jwt_payload["sub"]
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM students WHERE user_id=%s", (uid,))
        student = cur.fetchone()
        cur.execute("SELECT skills, job_role FROM alumni")
        all_alumni = cur.fetchall()
    finally:
        cur.close(); db.close()

    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    return jsonify(get_skill_gap(student, target_role, all_alumni))
