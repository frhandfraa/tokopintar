from flask import Blueprint, jsonify, render_template, request
from app.models import Product 
from app import db
import requests

products_bp = Blueprint('products', __name__)

# ==========================================
# 1. RUTE HALAMAN WEB
# ==========================================

@products_bp.route('/view', methods=['GET'])
def view_catalog():
    return render_template('index.html')

@products_bp.route('/view/<int:product_id>', methods=['GET'])
def view_product_detail(product_id):
    return render_template('product.html', product_id=product_id)

# ==========================================
# 2. RUTE API (JSON)
# ==========================================

@products_bp.route('', methods=['GET'])
def get_all_products():
    per_page = request.args.get('per_page', default=24, type=int)
    products = Product.query.limit(per_page).all()
    
    data = []
    for p in products:
        data.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
            "rating": float(p.rating),
            "stock": p.stock
        })
    return jsonify({"data": data})

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Produk tidak ditemukan"}), 404
        
    return jsonify({
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "price": float(product.price),
        "rating": float(product.rating),
        "stock": product.stock,
        "description": product.description or "Tidak ada deskripsi."
    })

# ==========================================
# 3. RUTE AI (VERSI DEBUG)
# ==========================================

@products_bp.route('/<int:product_id>/similar', methods=['GET'])
def get_similar_products(product_id):
    print(f"\n--- MENCARI REKOMENDASI UNTUK ID: {product_id} ---")
    
    try:
        # 1. Tembak AI Service
        ai_url = f'http://localhost:5001/recommend/similar/{product_id}?top_n=4'
        print(f"Mencoba memanggil AI: {ai_url}")
        
        response = requests.get(ai_url, timeout=5)
        
        if response.status_code != 200:
            print(f"❌ AI Service Error! Status: {response.status_code}")
            return jsonify({"data": []})

        ai_data = response.json()
        print(f"✅ Respons dari AI: {ai_data}")
        
        rec_list = ai_data.get('data', [])
        print(f"Jumlah rekomendasi dari AI: {len(rec_list)}")

        recommendations = []
        
        # 2. Cocokkan dengan database
        for item in rec_list:
            pid = item.get('product_id')
            print(f"Mencari produk ID: {pid} di database...")
            
            # Paksa jadi integer jika ID di DB Anda adalah angka
            try:
                product = Product.query.get(int(pid)) 
            except ValueError:
                print(f"ID {pid} bukan angka yang valid.")
                continue
            
            if product:
                print(f"   -> Ditemukan: {product.name}")
                recommendations.append({
                    "id": product.id,
                    "name": product.name,
                    "price": float(product.price)
                })
            else:
                print(f"   -> ⚠️ TIDAK DITEMUKAN di database.")
                
        print(f"Total produk yang siap dikirim ke web: {len(recommendations)}")
        print("--------------------------------------------------\n")
        
        return jsonify({"data": recommendations})

    except requests.exceptions.ConnectionError:
        print("❌ GAGAL KONEKSI: Pastikan AI Service menyala di port 5001!")
        return jsonify({"data": []})
    except Exception as e:
        print(f"❌ ERROR SYSTEM: {e}")
        return jsonify({"data": []})