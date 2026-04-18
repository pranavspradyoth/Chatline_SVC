from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from bson import ObjectId
import re

from .. import mongo, limiter
from ..models.user import User
from ..utils.tokens import generate_reset_token, verify_reset_token
from ..utils.email import send_password_reset_email

auth_bp = Blueprint("auth", __name__)

PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,128}$")

def validate_password(value):
    if not PASSWORD_PATTERN.match(value):
        raise ValidationError(
            "Password must be 8–128 characters with at least one uppercase, "
            "one lowercase, and one digit."
        )

class RegisterSchema(Schema):
    email     = fields.Email(required=True)
    password  = fields.Str(required=True, validate=validate_password)
    full_name = fields.Str(load_default=None, validate=validate.Length(max=120))

class LoginSchema(Schema):
    email    = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1, max=256))

class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)

class ResetPasswordSchema(Schema):
    token        = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate_password)


def _build_auth_response(user: User) -> dict:
    access_token = create_access_token(identity=str(user._id))
    return {
        "access_token": access_token,
        "token_type":   "Bearer",
        "expires_in":   7200,
        "user":         user.to_dict()
    }


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("100 per hour")
def register():
    try:
        data = RegisterSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"message": next(iter(err.messages.values()))[0]}), 422

    email = data["email"].lower().strip()

    if mongo.db.users.find_one({"email": email}):
        return jsonify({"message": "An account with this email already exists."}), 409

    doc = User.build_document(
        email=email,
        password=data["password"],
        full_name=data.get("full_name")
    )
    result = mongo.db.users.insert_one(doc)
    doc["_id"] = result.inserted_id

    return jsonify(_build_auth_response(User(doc))), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20 per hour;5 per minute")
def login():
    try:
        data = LoginSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"message": next(iter(err.messages.values()))[0]}), 422

    email = data["email"].lower().strip()
    doc   = mongo.db.users.find_one({"email": email})
    user  = User(doc) if doc else None

    if not user or not user.verify_password(data["password"]):
        return jsonify({"message": "Invalid email or password."}), 401

    if not user.is_active:
        return jsonify({"message": "Your account has been deactivated. Contact support."}), 403

    mongo.db.users.update_one(
        {"_id": doc["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )

    return jsonify(_build_auth_response(user)), 200


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")
def forgot_password():
    try:
        data = ForgotPasswordSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"message": next(iter(err.messages.values()))[0]}), 422

    email = data["email"].lower().strip()
    doc   = mongo.db.users.find_one({"email": email})

    SAFE_RESPONSE = jsonify({
        "message": "If an account exists for that email, a reset link has been sent."
    }), 200

    if not doc or not doc.get("is_active"):
        return SAFE_RESPONSE

    token     = generate_reset_token(email)
    frontend  = current_app.config["CORS_ORIGINS"][0].rstrip("/")
    reset_url = f"{frontend}/reset-password?token={token}"

    try:
        send_password_reset_email(email, reset_url)
    except Exception as exc:
        current_app.logger.error("Failed to send reset email to %s: %s", email, exc)

    return SAFE_RESPONSE


@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("10 per hour")
def reset_password():
    try:
        data = ResetPasswordSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"message": next(iter(err.messages.values()))[0]}), 422

    email = verify_reset_token(data["token"])
    if not email:
        return jsonify({"message": "This reset link is invalid or has expired."}), 400

    new_hash = User.hash_password(data["new_password"])
    result   = mongo.db.users.update_one(
        {"email": email, "is_active": True},
        {"$set": {"password_hash": new_hash}}
    )

    if result.matched_count == 0:
        return jsonify({"message": "Account not found."}), 404

    return jsonify({"message": "Your password has been updated successfully."}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    doc     = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not doc or not doc.get("is_active"):
        return jsonify({"message": "User not found."}), 404
    return jsonify(User(doc).to_dict()), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully."}), 200

@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
@limiter.limit("10 per hour")
def change_password():
    """Change password for the currently authenticated user."""
    data = request.get_json(silent=True) or {}
 
    current_password = data.get("current_password", "").strip()
    new_password_raw = data.get("new_password", "").strip()
 
    if not current_password or not new_password_raw:
        return jsonify({"message": "Both current and new password are required."}), 422
 
    if not PASSWORD_PATTERN.match(new_password_raw):
        return jsonify({
            "message": "New password must be 8-128 characters with at least one uppercase, lowercase, and digit."
        }), 422
 
    user_id  = get_jwt_identity()
    doc      = mongo.db.users.find_one({"_id": ObjectId(user_id)})
 
    if not doc:
        return jsonify({"message": "User not found."}), 404
 
    user = User(doc)
 
    if not user.verify_password(current_password):
        return jsonify({"message": "Current password is incorrect."}), 410
 
    new_hash = User.hash_password(new_password_raw)
    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password_hash": new_hash}}
    )
 
    return jsonify({"message": "Password changed successfully."}), 200