from flask import Blueprint, request, jsonify
import requests
from app import db
from app.models import Product
from app.auth import role_required
from app.config import Config

products_bp = Blueprint("products", __name__)


@products_bp.route("", methods=["GET"])
def list_products():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    category = request.args.get("category")

    query = Product.query
    if category:
        query = query.filter_by(category=category)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "data": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages
    }), 200


@products_bp.route("/<int:pid>", methods=["GET"])
def get_product(pid):
    product = Product.query.get_or_404(pid)
    return jsonify(product.to_dict()), 200


@products_bp.route("/<int:pid>/similar", methods=["GET"])
def similar_products(pid):
    try:
        resp = requests.get(
            f"{Config.AI_SERVICE_URL}/recommend/similar/{pid}",
            params={"top_n": 5}, timeout=3
        )
        recs = resp.json().get("data", [])
    except requests.RequestException:
        return jsonify({"source": "fallback", "data": []}), 200

    product_ids = [r["product_id"] for r in recs]
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    product_map = {p.id: p.to_dict() for p in products}

    data = []
    for r in recs:
        if r["product_id"] in product_map:
            item = product_map[r["product_id"]]
            item["score"] = r["score"]
            data.append(item)

    return jsonify({"source": "ai", "data": data}), 200


@products_bp.route("", methods=["POST"])
@role_required("pedagang", "admin")
def create_product():
    data = request.get_json()
    product = Product(**data)
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201