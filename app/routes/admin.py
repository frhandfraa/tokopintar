from flask import Blueprint, render_template, jsonify, request
from app.models import Product, Order, OrderItem, Interaction, User, db
from sqlalchemy import func
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

admin_bp = Blueprint('admin', __name__)

def get_current_user():
    claims = get_jwt()
    return int(get_jwt_identity()), claims.get("role")

# ==========================================
# RUTE HALAMAN & STATISTIK
# ==========================================
@admin_bp.route('/dashboard', methods=['GET'])
def view_dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    user_id, role = get_current_user()
    try:
        # 1. Ambil ID produk milik pedagang ini
        if role == 'admin':
            products = Product.query.all()
        else:
            products = Product.query.filter_by(seller_id=user_id).all()
            
        my_product_ids = [p.id for p in products]
        total_products = len(my_product_ids)

        # 2. Cari Pesanan yang mengandung produk tersebut
        if my_product_ids:
            order_items = OrderItem.query.filter(OrderItem.product_id.in_(my_product_ids)).all()
            order_ids = list(set([item.order_id for item in order_items]))
            orders = Order.query.filter(Order.id.in_(order_ids)).all()
        else:
            order_items = []
            orders = []

        total_orders = len(orders)
        
        # 3. Hitung Pendapatan (Hanya dari produk milik sendiri)
        total_revenue = sum([float(item.price) * item.quantity for item in order_items]) if order_items else 0

        # 4. Stok Menipis
        low_stock_products = [p for p in products if p.stock < 20]
        low_stock_products.sort(key=lambda x: x.stock)
        low_stock_data = [{"id": p.id, "name": p.name, "stock": p.stock} for p in low_stock_products[:10]]

        # 5. Produk Terlaris
        sales_count = {}
        if order_items:
            for item in order_items:
                sales_count[item.product_id] = sales_count.get(item.product_id, 0) + item.quantity
                
        top_sales = sorted(sales_count.items(), key=lambda x: x[1], reverse=True)[:5]
        top_products_data = []
        for pid, qty in top_sales:
            prod = Product.query.get(pid)
            if prod:
                top_products_data.append({"name": prod.name, "total_sold": qty})

        # 6. CTR (Global untuk sementara)
        total_views = Interaction.query.filter_by(type='view').count()
        total_clicks = Interaction.query.filter_by(type='click').count()
        ctr_percentage = round((total_clicks / total_views) * 100, 2) if total_views > 0 else 0

        return jsonify({
            "status": "success",
            "data": {
                "total_revenue": float(total_revenue), "total_orders": total_orders,
                "total_products": total_products, "ctr_percentage": ctr_percentage,
                "low_stock": low_stock_data, "top_products": top_products_data
            }
        })
    except Exception as e:
        print(f"ERROR STATS: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# API CRUD PRODUK
# ==========================================
@admin_bp.route('/products', methods=['GET'])
@jwt_required()
def admin_get_products():
    user_id, role = get_current_user()
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    
    if role == 'admin':
        query = Product.query
    else:
        query = Product.query.filter_by(seller_id=user_id)
        
    paginated = query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    data = [p.to_dict() for p in paginated.items]
    return jsonify({"data": data, "meta": {"current_page": paginated.page, "total_pages": paginated.pages}})

@admin_bp.route('/products', methods=['POST'])
@jwt_required()
def admin_add_product():
    user_id, role = get_current_user()
    try:
        data = request.get_json()
        new_product = Product(
            seller_id=user_id,
            name=data['name'], category=data.get('category', 'Umum'), 
            price=float(data['price']), stock=int(data['stock']), 
            description=data.get('description', ''), image_url=data.get('image_url', ''), rating=5.0
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message": "Produk berhasil ditambahkan"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def admin_edit_product(product_id):
    user_id, role = get_current_user()
    try:
        product = Product.query.get(product_id)
        if not product: return jsonify({"error": "Produk tidak ditemukan"}), 404
        if role != 'admin' and product.seller_id != user_id: return jsonify({"error": "Akses ditolak"}), 403

        data = request.get_json()
        product.name = data.get('name', product.name)
        product.category = data.get('category', product.category)
        product.price = float(data.get('price', product.price))
        product.stock = int(data.get('stock', product.stock))
        product.description = data.get('description', product.description)
        product.image_url = data.get('image_url', product.image_url)
        db.session.commit()
        return jsonify({"message": "Produk berhasil diupdate"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_product(product_id):
    user_id, role = get_current_user()
    try:
        product = Product.query.get(product_id)
        if not product: return jsonify({"error": "Produk tidak ditemukan"}), 404
        if role != 'admin' and product.seller_id != user_id: return jsonify({"error": "Akses ditolak"}), 403

        Interaction.query.filter_by(product_id=product_id).delete()
        OrderItem.query.filter_by(product_id=product_id).delete()
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Produk berhasil dihapus"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ==========================================
# API PESANAN (VERSI AMAN & ANTI-MACET)
# ==========================================
@admin_bp.route('/orders', methods=['GET'])
@jwt_required()
def admin_get_orders():
    user_id, role = get_current_user()
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        if role == 'admin':
            paginated = Order.query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        else:
            my_products = Product.query.filter_by(seller_id=user_id).all()
            my_product_ids = [p.id for p in my_products]
            
            if my_product_ids:
                order_items = OrderItem.query.filter(OrderItem.product_id.in_(my_product_ids)).all()
                order_ids = list(set([item.order_id for item in order_items]))
                
                paginated = Order.query.filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
            else:
                return jsonify({"data": [], "meta": {"current_page": 1, "total_pages": 1}})

        data = [{"id": o.id, "user_id": o.user_id, "total": float(o.total), "status": o.status, "date": o.created_at.strftime("%Y-%m-%d %H:%M")} for o in paginated.items]
        
        return jsonify({
            "data": data, 
            "meta": {"current_page": paginated.page, "total_pages": paginated.pages}
        })
    except Exception as e:
        print(f"ERROR ORDERS: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/orders/<int:order_id>', methods=['PUT'])
@jwt_required()
def admin_update_order_status(order_id):
    try:
        order = Order.query.get(order_id)
        if not order: return jsonify({"error": "Pesanan tidak ditemukan"}), 404
        data = request.get_json()
        new_status = data.get('status')
        if new_status in ['Pending', 'Dikirim', 'Selesai', 'Dibatalkan']:
            order.status = new_status
            db.session.commit()
            return jsonify({"message": "Status pesanan diperbarui"})
        return jsonify({"error": "Status tidak valid"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500