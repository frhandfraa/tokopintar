from flask import Blueprint, jsonify, request
from app import db
from app.models import Interaction, Product, Order
from app.auth import role_required
from sqlalchemy import func, desc

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/popular", methods=["GET"])
def popular():
    limit = int(request.args.get("limit", 10))
    results = db.session.query(
        Product.id, Product.name, func.count(Interaction.id).label("total")
    ).join(Interaction).filter(
        Interaction.type == "purchase"
    ).group_by(Product.id).order_by(desc("total")).limit(limit).all()

    return jsonify([
        {"product_id": r.id, "name": r.name, "total": r.total}
        for r in results
    ]), 200


@dashboard_bp.route("/ctr", methods=["GET"])
@role_required("admin", "pedagang")
def ctr():
    views = Interaction.query.filter_by(type="view").count()
    clicks = Interaction.query.filter_by(type="click").count()
    purchases = Interaction.query.filter_by(type="purchase").count()

    return jsonify({
        "views": views, "clicks": clicks, "purchases": purchases,
        "ctr": round(clicks / views, 4) if views > 0 else 0,
        "conversion_rate": round(purchases / clicks, 4) if clicks > 0 else 0
    }), 200


@dashboard_bp.route("/summary", methods=["GET"])
@role_required("admin", "pedagang")
def summary():
    return jsonify({
        "total_products": Product.query.count(),
        "total_orders": Order.query.count(),
        "total_revenue": float(
            db.session.query(func.sum(Order.total)).scalar() or 0
        )
    }), 200