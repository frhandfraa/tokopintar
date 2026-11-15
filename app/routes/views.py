from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

# Rute untuk Halaman Utama (Katalog)
@views_bp.route('/')
def home():
    return render_template('index.html')

# Rute untuk Halaman Detail Produk
@views_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    # Mengirimkan variabel product_id ke dalam file HTML
    return render_template('product.html', product_id=product_id)