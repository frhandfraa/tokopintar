from app import create_app, db

app = create_app()

if __name__ == "__main__":
    print("⏳ Sedang menyiapkan database...")
    with app.app_context():
        db.create_all()
        print("✅ Tabel database berhasil dibuat/dicek!")
    
    print("🚀 Menjalankan server di http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)