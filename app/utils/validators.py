"""
app/utils/validators.py – Input validation helpers.
"""
import re


PASSWORD_MIN_LEN = 8
PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def validate_password(password: str) -> tuple[bool, str]:
    """Returns (ok, error_message)."""
    if len(password) < PASSWORD_MIN_LEN:
        return False, f"Password must be at least {PASSWORD_MIN_LEN} characters."
    if not PASSWORD_RE.match(password):
        return False, "Password must include uppercase, lowercase, and a digit."
    return True, ""


def sanitize(value: str, max_len: int = 500) -> str:
    """Strip and truncate a string."""
    return str(value or "").strip()[:max_len]
