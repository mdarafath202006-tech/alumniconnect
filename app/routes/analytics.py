"""
app/routes/analytics.py – Analytics blueprint (PostgreSQL fixed)
"""
from flask import Blueprint, render_template, jsonify
import psycopg2.extras

from app.utils.db import get_db
from app.utils.decorators import login_required
from app.ai.recommender import get_career_analytics

analytics_bp = Blueprint("analytics", __name__)


# ───────────────────────── INTERNAL FETCH ─────────────────────────
def _fetch_alumni_data():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cur.execute("""
            SELECT job_role, company, skills, graduation_year
            FROM alumni
        """)
        return cur.fetchall()

    finally:
        cur.close()
        db.close()


# ───────────────────────── PAGE ─────────────────────────
@analytics_bp.route("/analytics")
@login_required
def analytics():
    data = get_career_analytics(_fetch_alumni_data())
    return render_template("analytics.html", data=data)


# ───────────────────────── API ─────────────────────────
@analytics_bp.route("/api/analytics")
@login_required
def api_analytics():
    return jsonify(get_career_analytics(_fetch_alumni_data()))
