from flask import Blueprint, render_template, jsonify, request
from app.models import Product, Order, OrderItem, Interaction, db
from sqlalchemy import func
from flask_jwt_extended import jwt_required, get_jwt

admin_bp = Blueprint('admin', __name__)

def is_admin():
    claims = get_jwt()
    return claims.get("role") == "admin"

@admin_bp.route('/dashboard', methods=['GET'])
def view_dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    if not is_admin(): return jsonify({"error": "Akses Ditolak!"}), 403
    try:
        total_revenue = db.session.query(func.sum(Order.total)).scalar() or 0
        total_orders = Order.query.count()
        total_products = Product.query.count()

        total_views = Interaction.query.filter_by(type='view').count()
        total_clicks = Interaction.query.filter_by(type='click').count()
        ctr_percentage = round((total_clicks / total_views) * 100, 2) if total_views > 0 else 0

        low_stock_products = Product.query.filter(Product.stock < 20).order_by(Product.stock.asc()).limit(10).all()
        low_stock_data = [{"id": p.id, "name": p.name, "stock": p.stock, "category": p.category} for p in low_stock_products]

        top_products_query = db.session.query(
            Product.name, func.sum(OrderItem.quantity).label('total_sold')
        ).join(OrderItem, Product.id == OrderItem.product_id)\
         .group_by(Product.id, Product.name)\
         .order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()
         
        top_products_data = [{"name": item[0], "total_sold": int(item[1])} for item in top_products_query]

        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        recent_orders_data = [{"id": o.id, "total": float(o.total), "status": o.status, "date": o.created_at.strftime("%Y-%m-%d %H:%M")} for o in recent_orders]

        return jsonify({
            "status": "success",
            "data": {
                "total_revenue": float(total_revenue), "total_orders": total_orders,
                "total_products": total_products, "ctr_percentage": ctr_percentage,
                "low_stock": low_stock_data, "top_products": top_products_data,
                "recent_orders": recent_orders_data
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route('/products', methods=['GET'])
@jwt_required()
def admin_get_products():
    if not is_admin(): return jsonify({"error": "Akses Ditolak"}), 403
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    paginated = Product.query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    data = [{"id": p.id, "name": p.name, "category": p.category, "price": float(p.price), "stock": p.stock} for p in paginated.items]
    return jsonify({"data": data, "meta": {"current_page": paginated.page, "total_pages": paginated.pages}})

@admin_bp.route('/products', methods=['POST'])
@jwt_required()
def admin_add_product():
    if not is_admin(): return jsonify({"error": "Akses Ditolak"}), 403
    try:
        data = request.get_json()
        new_product = Product(name=data['name'], category=data['category'], price=float(data['price']), stock=int(data['stock']), description=data.get('description', ''), rating=5.0)
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message": "Produk berhasil ditambahkan"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def admin_edit_product(product_id):
    if not is_admin(): return jsonify({"error": "Akses Ditolak"}), 403
    try:
        product = Product.query.get(product_id)
        data = request.get_json()
        product.name = data.get('name', product.name)
        product.category = data.get('category', product.category)
        product.price = float(data.get('price', product.price))
        product.stock = int(data.get('stock', product.stock))
        db.session.commit()
        return jsonify({"message": "Produk berhasil diupdate"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_product(product_id):
    if not is_admin(): return jsonify({"error": "Akses Ditolak"}), 403
    try:
        product = Product.query.get(product_id)
        Interaction.query.filter_by(product_id=product_id).delete()
        OrderItem.query.filter_by(product_id=product_id).delete()
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Produk berhasil dihapus"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500