from flask import Blueprint, jsonify, render_template, request
from app.models import Product, Order, OrderItem, Interaction
from app import db
import requests
from datetime import datetime

products_bp = Blueprint('products', __name__)

# ==========================================
# 1. RUTE HALAMAN WEB (HTML)
# ==========================================
@products_bp.route('/view', methods=['GET'])
def view_catalog():
    return render_template('index.html')

@products_bp.route('/view/<int:product_id>', methods=['GET'])
def view_product_detail(product_id):
    return render_template('product.html', product_id=product_id)

@products_bp.route('/cart', methods=['GET'])
def view_cart():
    return render_template('cart.html')

@products_bp.route('/success', methods=['GET'])
def view_success():
    return render_template('success.html')

@products_bp.route('/wishlist', methods=['GET'])
def view_wishlist():
    return render_template('wishlist.html')

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
    
    query = Product.query
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
    if category_query:
        query = query.filter(Product.category.ilike(f'%{category_query}%'))
        
    if sort_query == 'price_asc': query = query.order_by(Product.price.asc())
    elif sort_query == 'price_desc': query = query.order_by(Product.price.desc())
    elif sort_query == 'rating_desc': query = query.order_by(Product.rating.desc())
    else: query = query.order_by(Product.id.desc())
        
    paginated_products = query.paginate(page=page, per_page=per_page, error_out=False)
    data = [p.to_dict() for p in paginated_products.items]
        
    return jsonify({
        "data": data,
        "meta": {
            "current_page": paginated_products.page,
            "total_pages": paginated_products.pages,
            "total_items": paginated_products.total,
            "has_next": paginated_products.has_next,
            "has_prev": paginated_products.has_prev
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

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    product = Product.query.get(product_id)
    if not product: return jsonify({"error": "Produk tidak ditemukan"}), 404
    return jsonify(product.to_dict())

# ==========================================
# 3. RUTE INTERAKSI & ULASAN (REVIEWS)
# ==========================================
@products_bp.route('/<int:product_id>/view', methods=['POST'])
def track_view(product_id):
    try:
        # Simulasi user ID 1 (Guest) karena belum login
        new_interaction = Interaction(user_id=1, product_id=product_id, type="view", timestamp=datetime.now())
        db.session.add(new_interaction)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error"}), 500

@products_bp.route('/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    # Mock Data (Simulasi Ulasan Tokopedia) karena tabel belum diisi
    dummy_reviews = [
        {"user": "Budi S.", "rating": 5, "comment": "Barang sangat bagus dan sesuai deskripsi. Pengiriman cepat!"},
        {"user": "Siti A.", "rating": 4, "comment": "Kualitas oke, packing rapi. Recommended seller."},
        {"user": "Andi W.", "rating": 5, "comment": "Murah dan berkualitas, akan beli lagi nanti."},
        {"user": "Rina M.", "rating": 5, "comment": "Respon penjual cepat, barang sampai dengan selamat."}
    ]
    return jsonify({"data": dummy_reviews})

# ==========================================
# 4. RUTE AI SERVICE (REKOMENDASI)
# ==========================================
@products_bp.route('/<int:product_id>/similar', methods=['GET'])
def get_similar_products(product_id):
    try:
        response = requests.get(f'http://localhost:5001/recommend/similar/{product_id}?top_n=4', timeout=3)
        if response.status_code != 200: return jsonify({"data": []})
        ai_data = response.json()
        rec_list = ai_data.get('data', [])
        recommendations = []
        for item in rec_list:
            pid = item.get('product_id')
            try: product = Product.query.get(int(pid)) 
            except ValueError: continue
            if product: recommendations.append({"id": product.id, "name": product.name, "price": float(product.price)})
        return jsonify({"data": recommendations})
    except Exception:
        return jsonify({"data": []})

@products_bp.route('/recommendations/popular', methods=['GET'])
def get_popular_recommendations():
    try:
        k = request.args.get('k', default=4, type=int)
        response = requests.get(f'http://localhost:5001/recommend/popular?k={k}', timeout=3)
        if response.status_code == 200:
            ai_data = response.json()
            rec_list = ai_data.get('data', [])
            recommendations = []
            for item in rec_list:
                pid = item.get('product_id')
                try: product = Product.query.get(int(pid))
                except ValueError: continue
                if product: recommendations.append({"id": product.id, "name": product.name, "price": float(product.price)})
            if recommendations: return jsonify({"data": recommendations})
        fallback_products = Product.query.order_by(Product.rating.desc()).limit(k).all()
        return jsonify({"data": [{"id": p.id, "name": p.name, "price": float(p.price)} for p in fallback_products]})
    except Exception:
        return jsonify({"data": []})

# ==========================================
# 5. RUTE CHECKOUT
# ==========================================
@products_bp.route('/checkout', methods=['POST'])
def process_checkout():
    try:
        data = request.get_json()
        cart_items = data.get('cart', [])
        total_price = data.get('total_price', 0)

        if not cart_items: return jsonify({"error": "Keranjang kosong"}), 400

        # Asumsi user_id 1 sudah ada di database sebagai Guest
        new_order = Order(user_id=1, total=total_price, status="Pending", created_at=datetime.now())
        db.session.add(new_order)
        db.session.flush()

        for item in cart_items:
            product = Product.query.get(item['id'])
            if product:
                product.stock = max(0, product.stock - item['qty'])
                new_item = OrderItem(order_id=new_order.id, product_id=product.id, quantity=item['qty'], price=item['price'])
                db.session.add(new_item)
                new_interaction = Interaction(user_id=1, product_id=product.id, type="purchase", timestamp=datetime.now())
                db.session.add(new_interaction)

        db.session.commit()
        return jsonify({"message": "Checkout berhasil!", "order_id": new_order.id}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error Checkout: {e}")
        return jsonify({"error": "Gagal memproses pesanan."}), 500