"""
run.py – Application entry point.

Usage:
  python run.py                    # development
  FLASK_ENV=production python run.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app, socketio

app = create_app(os.environ.get("FLASK_ENV", "development"))

@app.route("/run-seed")
def run_seed():
    import migrations.seed_users
    return "Seed completed!"


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config.get("DEBUG", True),
    )
