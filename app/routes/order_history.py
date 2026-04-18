# app/routes/order_history.py
"""
CampusEats — Order History Blueprint
Endpoints:
  GET /api/order-history           — all orders for the logged-in user (newest first)
  GET /api/order-history?status=X  — filtered by status (Received / Served / Cancelled)
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from .. import mongo, limiter

order_history_bp = Blueprint("order_history", __name__)

VALID_STATUSES = {"Received", "Served", "Cancelled"}


def serialize_order(order: dict) -> dict:
    return {
        "_id":         str(order["_id"]),
        "orderId":     order.get("orderId", ""),
        "studentName": order.get("studentName", ""),
        "email":       order.get("email", ""),
        "items":       order.get("items", []),
        "status":      order.get("status", "Received"),
        "createdAt":   (
            order["createdAt"].isoformat()
            if isinstance(order.get("createdAt"), datetime)
            else str(order.get("createdAt", ""))
        ),
        "totalCost":   order.get("totalCost", 0)
    }


@order_history_bp.route("/order-history", methods=["GET"])
@jwt_required()
@limiter.limit("60 per hour")
def get_order_history():
    """
    Return all orders for the currently authenticated user.
    Optional query param: ?status=Received|Served|Cancelled
    """
    user_id  = get_jwt_identity()
    user_doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if not user_doc:
        return jsonify({"message": "User not found."}), 404

    email = user_doc.get("email", "")

    # Build query
    query: dict = {"email": email}

    status_filter = request.args.get("status", "").strip()
    if status_filter:
        if status_filter not in VALID_STATUSES:
            return jsonify({
                "message": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
            }), 400
        query["status"] = status_filter

    orders = list(
        mongo.db["Orders"]
        .find(query)
        .sort("createdAt", -1)   # newest first
    )

    return jsonify([serialize_order(o) for o in orders]), 200