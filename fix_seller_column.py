from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("⏳ Menambahkan kolom seller_id ke tabel products...")
    try:
        # Menambahkan kolom beserta foreign key ke tabel users
        db.session.execute(text("ALTER TABLE products ADD COLUMN seller_id INTEGER REFERENCES users(id);"))
        db.session.commit()
        print("✅ Berhasil! Kolom seller_id sudah ditambahkan.")
    except Exception as e:
        db.session.rollback()
        if "already exists" in str(e):
            print("✅ Kolom seller_id sudah ada, tidak perlu ditambahkan lagi.")
        else:
            print(f"❌ Terjadi error: {e}")