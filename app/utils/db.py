"""
app/utils/db.py – Thin database helper.
Uses environment-driven config; never hardcodes credentials.
"""
import mysql.connector
from flask import current_app


def get_db():
    """Return a new MySQL connection using app config."""
    cfg = current_app.config
    return mysql.connector.MySQLConnection(
        host=cfg["DB_HOST"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=cfg["DB_NAME"],
        charset="utf8mb4",
        autocommit=False,
    )
