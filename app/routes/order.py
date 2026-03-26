# app/routes/orders.py
"""
CampusEats — Orders Blueprint
Endpoints:
  POST /api/orders   — place a new order (decrements stock)
  GET  /api/orders   — get orders for the current user
"""
import random
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from .. import mongo, limiter

orders_bp = Blueprint("orders", __name__)


# ── Helpers ───────────────────────────────────────────────────

def serialize_order(order: dict) -> dict:
    return {
        "_id":         str(order["_id"]),
        "orderId":     order.get("orderId"),
        "studentName": order.get("studentName"),
        "email":       order.get("email"),
        "items":       order.get("items", []),
        "status":      order.get("status", "Received"),
        "createdAt":   order["createdAt"].isoformat() if isinstance(order.get("createdAt"), datetime) else str(order.get("createdAt")),
        "totalCost":   order.get("totalCost", 0),
    }


def generate_unique_order_id() -> str:
    """Generate Order_XXXXXXXXXX — retries until unique."""
    while True:
        digits   = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        order_id = f"Order_{digits}"
        if mongo.db["Orders"].count_documents({"orderId": order_id}) == 0:
            return order_id


def decrement_stock(items: list) -> None:
    """Reduce Menu stock for each ordered item."""
    for it in items:
        if not isinstance(it, dict):
            continue

        item_id = it.get("item_id")
        if not item_id:
            continue

        try:
            menu_obj_id = ObjectId(item_id)
        except Exception:
            continue

        menu_item = mongo.db["Menu"].find_one({"_id": menu_obj_id})
        if not menu_item:
            continue

        try:
            qty = int(it.get("qty") or it.get("quantity") or it.get("count") or 1)
        except (ValueError, TypeError):
            qty = 1

        try:
            stock_int = int(menu_item.get("stock", 0))
        except (ValueError, TypeError):
            stock_int = 0

        new_stock    = max(0, stock_int - qty)
        raw_stock    = menu_item.get("stock", 0)
        update_value = str(new_stock) if isinstance(raw_stock, str) else new_stock

        update_fields: dict = {"stock": update_value}
        if new_stock == 0:
            update_fields["available"] = False

        mongo.db["Menu"].update_one(
            {"_id": menu_obj_id},
            {"$set": update_fields}
        )


# ── Routes ────────────────────────────────────────────────────

@orders_bp.route("/orders", methods=["POST"])
@jwt_required()
@limiter.limit("30 per hour")
def add_order():
    """Place a new order and decrement menu stock."""
    data = request.get_json(silent=True) or {}

    items = data.get("items", [])
    if not items:
        return jsonify({"message": "Order must contain at least one item."}), 400

    total = data.get("total", 0)
    try:
        total = float(total)
    except (ValueError, TypeError):
        total = 0

    order_id = generate_unique_order_id()

    order = {
        "orderId":     order_id,
        "studentName": data.get("user_id"),
        "email":       data.get("email", ""),        # ← new field
        "items":       items,
        "status":      "Received",
        "createdAt":   datetime.now(timezone.utc),
        "totalCost":   total,
    }

    result = mongo.db["Orders"].insert_one(order)
    order["_id"] = result.inserted_id

    # Decrement stock for each item
    try:
        decrement_stock(items)
    except Exception as e:
        # Log but don't fail the order
        print(f"[WARN] Stock decrement error: {e}")

    return jsonify(serialize_order(order)), 200


@orders_bp.route("/orders", methods=["GET"])
@jwt_required()
@limiter.limit("60 per minute")
def get_my_orders():
    """Return all orders for the authenticated user (by email)."""
    user_id  = get_jwt_identity()
    user_doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        return jsonify({"message": "User not found."}), 404

    email  = user_doc.get("email", "")
    orders = list(
        mongo.db["Orders"]
        .find({"email": email})
        .sort("createdAt", -1)        # newest first
    )
    return jsonify([serialize_order(o) for o in orders]), 200