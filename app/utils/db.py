"""
app/utils/db.py – PostgreSQL database helper (Supabase)
"""
import os
import psycopg2
from flask import current_app


def get_db():
    """Return a new PostgreSQL connection using app config."""
    cfg = current_app.config

    return psycopg2.connect(
        host=cfg["DB_HOST"],
        database=cfg["DB_NAME"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        port=cfg.get("DB_PORT", 5432)
    )
