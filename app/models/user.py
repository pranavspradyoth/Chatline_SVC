from datetime import datetime, timezone
from bson import ObjectId
from .. import bcrypt


class User:
    """
    Helper that wraps MongoDB user documents.
    Not an ORM model — just structures the data.
    """
    COLLECTION = "users"

    def __init__(self, doc: dict):
        self._id       = doc.get("_id")
        self.email     = doc.get("email")
        self.full_name = doc.get("full_name")
        self.role      = doc.get("role", "student")
        self.is_active = doc.get("is_active", True)
        self.created_at = doc.get("created_at")
        self.last_login = doc.get("last_login")
        self._password_hash = doc.get("password_hash")

    # ── Password ──────────────────────────────────────────────────────────
    @staticmethod
    def hash_password(plaintext: str) -> str:
        return bcrypt.generate_password_hash(plaintext).decode("utf-8")

    def verify_password(self, plaintext: str) -> bool:
        return bcrypt.check_password_hash(self._password_hash, plaintext)

    # ── Serialise for JWT / API response ─────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "id":         str(self._id),
            "email":      self.email,
            "full_name":  self.full_name,
            "role":       self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    # ── Build a new document dict to insert ──────────────────────────────
    @staticmethod
    def build_document(email: str, password: str, full_name: str = None) -> dict:
        return {
            "email":         email,
            "full_name":     full_name,
            "password_hash": User.hash_password(password),
            "role":          "student",
            "is_active":     True,
            "created_at":    datetime.now(timezone.utc),
            "last_login":    None,
        }