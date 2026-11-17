import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
import app.models as models

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

ALLOWED_MEDIA_EXT = {"png", "jpg", "jpeg", "webp", "gif", "mp4", "webm", "mov", "ogg"}
VIDEO_EXT = {"mp4", "webm", "mov", "ogg"}


def is_allowed_media(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_MEDIA_EXT


def get_data_dir():
    folder = os.path.join(current_app.root_path, "static", "data")
    os.makedirs(folder, exist_ok=True)
    return folder


def get_review_media_store_path():
    return os.path.join(get_data_dir(), "review_media.json")


def load_review_media():
    path = get_review_media_store_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_review_media(data):
    path = get_review_media_store_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_order_meta_path():
    return os.path.join(get_data_dir(), "order_meta.json")


def load_order_meta():
    path = get_order_meta_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_order_meta(order_id, meta_dict):
    all_meta = load_order_meta()
    all_meta[str(order_id)] = meta_dict
    with open(get_order_meta_path(), "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)


def get_order_model():
    return getattr(models, "Order", None) or getattr(models, "Transaction", None)


def get_order_item_model():
    return getattr(models, "OrderItem", None)


def get_review_model():
    return getattr(models, "Review", None) or getattr(models, "ProductReview", None)


def serialize_order(order, all_meta=None):
    Product = getattr(models, "Product", None)
    OrderItemModel = get_order_item_model()
    if all_meta is None:
        all_meta = load_order_meta()

    order_id = getattr(order, "id", None)
    meta = all_meta.get(str(order_id), {}) if order_id else {}

    status = (getattr(order, "status", None) or "diproses").lower()
    total_price = (
        getattr(order, "total_price", None)
        or getattr(order, "total_amount", None)
        or getattr(order, "total", 0)
    )
    created_at = getattr(order, "created_at", None)
    created_str = created_at.strftime("%d %b %Y, %H:%M") if isinstance(created_at, datetime) else str(created_at or "-")
    tracking_number = getattr(order, "tracking_number", None) or f"TP-{100000 + (order_id or 0)}"
    shipping_address = getattr(order, "shipping_address", None) or meta.get("shipping_address") or "Alamat utama pembeli"
    payment_method = getattr(order, "payment_method", None) or meta.get("payment_method") or "Transfer / E-Wallet"

    items_data = []
    raw_items = (
        OrderItemModel.query.filter_by(order_id=order_id).all()
        if OrderItemModel and order_id
        else (getattr(order, "items", None) or [])
    )

    for item in raw_items:
        prod = getattr(item, "product", None)
        prod_id = getattr(item, "product_id", None) or (getattr(prod, "id", None) if prod else None)
        if not prod and prod_id and Product:
            prod = Product.query.filter_by(id=prod_id).first()

        prod_name = getattr(prod, "name", None) if prod else getattr(item, "product_name", f"Produk #{prod_id}")
        prod_img = (
            getattr(prod, "image_url", None)
            if prod and getattr(prod, "image_url", None)
            else f"https://loremflickr.com/200/200/product?lock={prod_id or 1}"
        )
        qty = getattr(item, "quantity", None) or getattr(item, "qty", 1)
        price = getattr(item, "price", None) or (getattr(prod, "price", 0) if prod else 0)

        items_data.append({
            "product_id": str(prod_id) if prod_id else None,
            "name": prod_name,
            "image_url": prod_img,
            "qty": qty,
            "price": float(price),
        })

    return {
        "id": order_id,
        "invoice": f"INV/TP/{datetime.now().year}/{order_id:04d}" if order_id else "INV/TP/0000",
        "status": status,
        "total_price": float(total_price or 0),
        "created_at": created_str,
        "tracking_number": tracking_number,
        "shipping_address": shipping_address,
        "payment_method": payment_method,
        "items": items_data,
    }


@orders_bp.route("/view")
def orders_view():
    return render_template("orders.html")


@orders_bp.route("", methods=["GET"])
@jwt_required()
def get_my_orders():
    user_id = int(get_jwt_identity())
    OrderModel = get_order_model()

    if not OrderModel:
        return jsonify({"data": []}), 200

    all_meta = load_order_meta()
    query = OrderModel.query.filter_by(user_id=user_id).order_by(OrderModel.id.desc())
    orders = query.all()
    return jsonify({"data": [serialize_order(o, all_meta) for o in orders]}), 200


# --- API CHECKOUT PESANAN BARU ---
@orders_bp.route("/checkout", methods=["POST"])
@jwt_required()
def checkout_order():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])

    if not items:
        return jsonify({"error": "Keranjang belanja kosong"}), 400

    Product = getattr(models, "Product", None)
    OrderModel = get_order_model()
    OrderItemModel = get_order_item_model()

    try:
        total_amount = 0
        validated_items = []

        for item in items:
            raw_pid = item.get("product_id") or item.get("id")
            qty = int(item.get("quantity") or item.get("qty") or 1)
            if not raw_pid or qty <= 0:
                continue

            pid = int(str(raw_pid).strip())
            product = Product.query.filter(Product.id == pid).first()
            if not product:
                return jsonify({"error": f"Produk #{pid} tidak ditemukan"}), 404

            if (product.stock or 0) < qty:
                return jsonify({"error": f"Stok '{product.name}' tidak mencukupi (sisa {product.stock})"}), 400

            unit_price = float(product.price or item.get("price") or 0)
            total_amount += unit_price * qty
            validated_items.append((product, qty, unit_price))

        if not validated_items:
            return jsonify({"error": "Tidak ada item valid untuk diproses"}), 400

        shipping_cost = float(data.get("shipping_cost") or 0)
        discount = float(data.get("discount") or 0)
        grand_total = max(0, total_amount + shipping_cost - discount)

        order = OrderModel(
            user_id=user_id,
            total=grand_total,
            status="Pending",
        )
        if hasattr(order, "shipping_address") and data.get("shipping_address"):
            order.shipping_address = data.get("shipping_address")
        if hasattr(order, "payment_method") and data.get("payment_method"):
            order.payment_method = data.get("payment_method")

        db.session.add(order)
        db.session.flush()

        for product, qty, unit_price in validated_items:
            product.stock = max(0, (product.stock or 0) - qty)
            order_item = OrderItemModel(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                price=unit_price,
            )
            db.session.add(order_item)

        db.session.commit()

        save_order_meta(order.id, {
            "shipping_address": data.get("shipping_address") or "Alamat utama pembeli",
            "payment_method": data.get("payment_method") or "Transfer Bank / E-Wallet",
            "shipping_cost": shipping_cost,
            "discount": discount,
        })

        return jsonify({
            "message": "Checkout berhasil! Pesanan Anda sedang diproses.",
            "order_id": order.id,
            "total": grand_total,
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@orders_bp.route("/<int:order_id>/complete", methods=["POST"])
@jwt_required()
def complete_order(order_id):
    user_id = int(get_jwt_identity())
    OrderModel = get_order_model()

    order = OrderModel.query.get(order_id) if OrderModel else None
    if not order:
        return jsonify({"error": "Pesanan tidak ditemukan"}), 404

    if order.user_id != user_id:
        return jsonify({"error": "Anda tidak memiliki akses ke pesanan ini"}), 403

    order.status = "selesai"
    db.session.commit()
    return jsonify({"message": "Pesanan dikonfirmasi selesai! Silakan beri ulasan & bukti foto/video."}), 200


# --- API KIRIM ULASAN DENGAN BUKTI FOTO & VIDEO ---
@orders_bp.route("/review", methods=["POST"])
@jwt_required()
def submit_review():
    user_id = int(get_jwt_identity())

    if request.form or request.files:
        raw_product_id = request.form.get("product_id")
        raw_rating = request.form.get("rating", 5)
        comment = (request.form.get("comment") or "").strip()
        uploaded_files = request.files.getlist("media")
    else:
        data = request.get_json(silent=True) or {}
        raw_product_id = data.get("product_id")
        raw_rating = data.get("rating", 5)
        comment = (data.get("comment") or "").strip()
        uploaded_files = []

    if not raw_product_id:
        return jsonify({"error": "ID produk tidak terbaca"}), 400

    try:
        product_id = int(str(raw_product_id).strip())
        rating = int(raw_rating)
    except (ValueError, TypeError):
        return jsonify({"error": "Format ID produk atau rating tidak valid"}), 400

    if not (1 <= rating <= 5):
        return jsonify({"error": "Rating harus antara 1 sampai 5"}), 400

    Product = getattr(models, "Product", None)
    ReviewModel = get_review_model()
    user = models.User.query.get(user_id)
    reviewer_name = user.name if user else "Pembeli TokoPintar"

    product = Product.query.filter(Product.id == product_id).first() if Product else None
    if not product:
        return jsonify({"error": "Produk tidak ditemukan"}), 404

    saved_media = []
    if uploaded_files:
        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "reviews")
        os.makedirs(upload_dir, exist_ok=True)

        for file in uploaded_files[:5]:
            if file and file.filename and is_allowed_media(file.filename):
                ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
                fname = f"rev_{product_id}_{uuid.uuid4().hex[:10]}.{ext}"
                file.save(os.path.join(upload_dir, fname))
                media_type = "video" if ext in VIDEO_EXT else "image"
                saved_media.append({
                    "type": media_type,
                    "url": f"/static/uploads/reviews/{fname}"
                })

    final_comment = comment or "Produk sesuai deskripsi, pengiriman cepat!"
    review_id = None

    if ReviewModel:
        review = ReviewModel(
            product_id=product_id,
            user_name=reviewer_name,
            rating=rating,
            comment=final_comment,
        )
        db.session.add(review)
        db.session.flush()
        review_id = review.id

    if saved_media:
        all_media = load_review_media()
        prod_key = str(product_id)
        prod_reviews = all_media.get(prod_key, [])
        prod_reviews.append({
            "review_id": review_id,
            "user_name": reviewer_name,
            "comment": final_comment,
            "media": saved_media
        })
        all_media[prod_key] = prod_reviews
        save_review_media(all_media)

    if hasattr(product, "rating"):
        current_rating = float(product.rating or 0)
        product.rating = float(rating) if current_rating == 0 else round((current_rating + rating) / 2, 1)

    db.session.commit()
    return jsonify({
        "message": "Terima kasih! Ulasan beserta bukti foto/video Anda berhasil dipublikasikan.",
        "media_count": len(saved_media)
    }), 201


# --- API AMBIL ULASAN + BUKTI FOTO/VIDEO UNTUK DETAIL PRODUK ---
@orders_bp.route("/reviews/<product_id>", methods=["GET"])
def get_product_reviews_with_media(product_id):
    ReviewModel = get_review_model()
    try:
        int_pid = int(str(product_id).strip())
    except (ValueError, TypeError):
        return jsonify({"data": []}), 200

    reviews = ReviewModel.query.filter_by(product_id=int_pid).order_by(ReviewModel.created_at.desc()).all() if ReviewModel else []
    media_map = load_review_media().get(str(int_pid), [])

    result = []
    for r in reviews:
        matched_media = []
        for m in media_map:
            if m.get("review_id") == r.id or (m.get("user_name") == r.user_name and m.get("comment") == r.comment):
                matched_media = m.get("media", [])
                break

        result.append({
            "id": r.id,
            "user": r.user_name,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.strftime("%d %b %Y") if r.created_at else "",
            "media": matched_media
        })

    return jsonify({"data": result}), 200