# app/routes/menu.py
"""
CampusEats — Menu Blueprint
Endpoints:
  GET /api/items                    — all menu items
  GET /api/categories               — all categories
  GET /api/itemsperCat?category=X   — items filtered by category
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from bson import ObjectId

from .. import mongo, limiter

menu_bp = Blueprint("menu", __name__)


def serialize_item(item: dict) -> dict:
    return {
        "_id":       str(item["_id"]),
        "name":      item.get("name"),
        "category":  item.get("category"),
        "price":     item.get("price"),
        "stock":     item.get("stock", 0),
        "available": item.get("available", True)
    }


def serialize_category(cat: dict) -> dict:
    return {
        "_id":  str(cat["_id"]),
        "name": cat.get("name")
    }


@menu_bp.route("/items", methods=["GET"])
@jwt_required()
@limiter.limit("120 per minute")
def get_items():
    """Return all menu items."""
    items = list(mongo.db["Menu"].find())
    return jsonify([serialize_item(i) for i in items]), 200


@menu_bp.route("/categories", methods=["GET"])
@jwt_required()
@limiter.limit("60 per minute")
def get_categories():
    """Return all categories."""
    categories = list(mongo.db["Category"].find())
    return jsonify([serialize_category(c) for c in categories]), 200


@menu_bp.route("/itemsperCat", methods=["GET"])
@jwt_required()
@limiter.limit("120 per minute")
def get_items_per_category():
    """Return items for a given category, excluding out-of-stock."""
    category = request.args.get("category", "").strip()
    if not category:
        return jsonify({"message": "Category parameter is required."}), 400

    items = list(mongo.db["Menu"].find({
        "category":  category,
        "stock":     {"$ne": "0"},
        "available": True
    }))
    return jsonify([serialize_item(i) for i in items]), 200