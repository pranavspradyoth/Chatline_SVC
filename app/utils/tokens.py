"""
CampusEats — Password reset token helpers (itsdangerous)
"""
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


def generate_reset_token(email: str) -> str:
    """Generate a signed, time-limited token encoding *email*."""
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="password-reset-salt")


def verify_reset_token(token: str) -> str | None:
    """
    Verify *token* and return the encoded email, or None if
    the token is invalid or expired.
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    expiry = current_app.config.get("RESET_TOKEN_EXPIRY_SECONDS", 3600)
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=expiry)
        return email
    except (SignatureExpired, BadSignature):
        return None