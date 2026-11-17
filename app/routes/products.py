from flask import Blueprint, jsonify, render_template, request
from app.models import Product, Order, OrderItem, Interaction, User
from app import db
import requests
import random # Tambahan untuk acak
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

products_bp = Blueprint('products', __name__)

# ==========================================
# 1. RUTE HALAMAN WEB (HTML)
# ==========================================
@products_bp.route('/view', methods=['GET'])
def view_catalog(): return render_template('index.html')

@products_bp.route('/view/<int:product_id>', methods=['GET'])
def view_product_detail(product_id): return render_template('product.html', product_id=product_id)

@products_bp.route('/cart', methods=['GET'])
def view_cart(): return render_template('cart.html')

@products_bp.route('/success', methods=['GET'])
def view_success(): return render_template('success.html')

@products_bp.route('/wishlist', methods=['GET'])
def view_wishlist(): return render_template('wishlist.html')

# ==========================================
# 2. RUTE API PRODUK & KATEGORI
# ==========================================
@products_bp.route('', methods=['GET'])
def get_all_products():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=12, type=int)
    search_query = request.args.get('search', default='', type=str)
    category_query = request.args.get('category', default='', type=str)
    sort_query = request.args.get('sort', default='', type=str)
    seller_id = request.args.get('seller_id', default=None, type=int)
    
    query = Product.query
    if seller_id: query = query.filter(Product.seller_id == seller_id)
    if search_query: query = query.filter(Product.name.ilike(f'%{search_query}%'))
    if category_query: query = query.filter(Product.category.ilike(f'%{category_query}%'))
        
    if sort_query == 'price_asc': query = query.order_by(Product.price.asc())
    elif sort_query == 'price_desc': query = query.order_by(Product.price.desc())
    elif sort_query == 'rating_desc': query = query.order_by(Product.rating.desc())
    else: query = query.order_by(Product.id.desc())
        
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "data": [p.to_dict() for p in paginated.items],
        "meta": {
            "current_page": paginated.page, "total_pages": paginated.pages,
            "total_items": paginated.total, "has_next": paginated.has_next, "has_prev": paginated.has_prev
        }
    })

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = db.session.query(Product.category).distinct().all()
        cat_list = set()
        for cat in categories:
            if cat[0]:
                main_cat = cat[0].split('|')[0].replace('_', ' ').strip()
                if main_cat: cat_list.add(main_cat)
        return jsonify({"data": sorted(list(cat_list))})
    except Exception:
        return jsonify({"data": []})

@products_bp.route('/suggestions', methods=['GET'])
def get_search_suggestions():
    query = request.args.get('q', default='', type=str)
    if len(query) < 2: return jsonify({"data": []})
    suggestions = db.session.query(Product.name).filter(Product.name.ilike(f'%{query}%')).distinct().limit(7).all()
    return jsonify({"data": [s[0] for s in suggestions]})

@products_bp.route('/seller/<int:seller_id>', methods=['GET'])
def get_seller_info(seller_id):
    seller = User.query.get(seller_id)
    if not seller: return jsonify({"error": "Toko tidak ditemukan"}), 404
    return jsonify({"data": seller.to_dict()})

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    product = Product.query.get(product_id)
    if not product: return jsonify({"error": "Produk tidak ditemukan"}), 404
    return jsonify(product.to_dict())

# ==========================================
# 3. RUTE INTERAKSI & ULASAN
# ==========================================
@products_bp.route('/<int:product_id>/view', methods=['POST'])
def track_view(product_id):
    try:
        new_interaction = Interaction(user_id=1, product_id=product_id, type="view", timestamp=datetime.now())
        db.session.add(new_interaction); db.session.commit()
        return jsonify({"status": "success"})
    except Exception:
        db.session.rollback(); return jsonify({"status": "error"}), 500

@products_bp.route('/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    dummy_reviews = [
        {"user": "Budi S.", "rating": 5, "comment": "Barang sangat bagus dan sesuai deskripsi. Pengiriman cepat!"},
        {"user": "Siti A.", "rating": 4, "comment": "Kualitas oke, packing rapi. Recommended seller."},
        {"user": "Andi W.", "rating": 5, "comment": "Murah dan berkualitas, akan beli lagi nanti."},
        {"user": "Rina M.", "rating": 5, "comment": "Respon penjual cepat, barang sampai dengan selamat."}
    ]
    return jsonify({"data": dummy_reviews})

# ==========================================
# 4. RUTE AI SERVICE (REKOMENDASI ACak)
# ==========================================
@products_bp.route('/<int:product_id>/similar', methods=['GET'])
def get_similar_products(product_id):
    try:
        response = requests.get(f'http://localhost:5001/recommend/similar/{product_id}?top_n=4', timeout=3)
        if response.status_code != 200: return jsonify({"data": []})
        rec_list = response.json().get('data', [])
        recommendations = []
        for item in rec_list:
            product = Product.query.get(int(item.get('product_id', 0)))
            if product: recommendations.append({"id": product.id, "name": product.name, "price": float(product.price)})
        return jsonify({"data": recommendations})
    except Exception:
        return jsonify({"data": []})

@products_bp.route('/recommendations/popular', methods=['GET'])
def get_popular_recommendations():
    try:
        k = request.args.get('k', default=10, type=int) # Ambil lebih banyak untuk carousel
        
        # 1. Ambil lebih banyak data dari AI Service (misal k*3)
        response = requests.get(f'http://localhost:5001/recommend/popular?k={k*3}', timeout=2)
        if response.status_code == 200:
            rec_list = response.json().get('data', [])
            if rec_list:
                # ACAK hasil dari AI
                random.shuffle(rec_list)
                recommendations = []
                for item in rec_list[:k]:
                    product = Product.query.get(int(item.get('product_id', 0)))
                    if product: recommendations.append({"id": product.id, "name": product.name, "price": float(product.price)})
                
                if recommendations: return jsonify({"data": recommendations})

        # 2. FALLBACK: Jika AI mati, ambil acak dari database berdasarkan rating tertinggi
        # Menggunakan func.random() dari SQLAlchemy untuk PostgreSQL
        fallback_products = Product.query.order_by(func.random()).limit(k).all()
        return jsonify({"data": [{"id": p.id, "name": p.name, "price": float(p.price)} for p in fallback_products]})
    except Exception:
        return jsonify({"data": []})

# ==========================================
# 5. RUTE CHECKOUT
# ==========================================
@products_bp.route('/checkout', methods=['POST'])
@jwt_required()
def process_checkout():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        cart_items = data.get('cart', [])
        total_price = data.get('total_price', 0)

        if not cart_items: return jsonify({"error": "Keranjang kosong"}), 400

        new_order = Order(user_id=int(user_id), total=total_price, status="Pending", created_at=datetime.now())
        db.session.add(new_order); db.session.flush()

        for item in cart_items:
            product = Product.query.get(item['id'])
            if product:
                product.stock = max(0, product.stock - item['qty'])
                db.session.add(OrderItem(order_id=new_order.id, product_id=product.id, quantity=item['qty'], price=item['price']))
                db.session.add(Interaction(user_id=int(user_id), product_id=product.id, type="purchase", timestamp=datetime.now()))

        db.session.commit()
        return jsonify({"message": "Checkout berhasil!", "order_id": new_order.id}), 200
    except Exception:
        db.session.rollback(); return jsonify({"error": "Gagal memproses pesanan."}), 500

@products_bp.route("/about")
def about_view():
        return render_template("about.html")