from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Interaction, Product

interactions_bp = Blueprint("interactions", __name__)


@interactions_bp.route("", methods=["POST"])
@jwt_required()
def track():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if data["type"] not in ["view", "click", "purchase"]:
        return jsonify({"msg": "Tipe interaksi tidak valid"}), 400

    if not Product.query.get(data["product_id"]):
        return jsonify({"msg": "Produk tidak ditemukan"}), 404

    interaction = Interaction(
        user_id=user_id,
        product_id=data["product_id"],
        type=data["type"]
    )
    db.session.add(interaction)
    db.session.commit()
    return jsonify(interaction.to_dict()), 201