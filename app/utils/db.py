"""
app/utils/db.py – PostgreSQL database helper (Supabase)
"""
import os
import psycopg2

def get_db():
    """Return a new PostgreSQL connection using Supabase DATABASE_URL."""

    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require"
    )

