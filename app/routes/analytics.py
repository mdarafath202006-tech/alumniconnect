"""
app/routes/analytics.py – Analytics blueprint.
"""
from flask import Blueprint, render_template, jsonify

from app.utils.db import get_db
from app.utils.decorators import login_required
from app.ai.recommender import get_career_analytics

analytics_bp = Blueprint("analytics", __name__)


def _fetch_alumni_data():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT job_role, company, skills, graduation_year FROM alumni")
        return cur.fetchall()
    finally:
        cur.close(); db.close()


@analytics_bp.route("/analytics")
@login_required
def analytics():
    data = get_career_analytics(_fetch_alumni_data())
    return render_template("analytics.html", data=data)


@analytics_bp.route("/api/analytics")
@login_required
def api_analytics():
    return jsonify(get_career_analytics(_fetch_alumni_data()))
