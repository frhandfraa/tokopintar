from app import create_app, db
from app.models import User, Product

app = create_app()

with app.app_context():
    print("⏳ Mencari akun pedagang...")
    pedagang = User.query.filter_by(email="pedagang@tokopintar.com").first()
    
    if not pedagang:
        print("❌ Akun pedagang belum dibuat! Jalankan 'python create_pedagang.py' dulu.")
    else:
        print(f"✅ Ditemukan Pedagang: {pedagang.name} (ID: {pedagang.id})")
        print("⏳ Memindahkan seluruh produk ke pedagang ini...")
        
        # Update semua produk yang seller_id-nya masih kosong
        updated_rows = db.session.query(Product).filter(Product.seller_id == None).update(
            {Product.seller_id: pedagang.id}, synchronize_session=False
        )
        
        db.session.commit()
        print(f"🎉 Berhasil! {updated_rows} produk sekarang menjadi milik {pedagang.name}.")