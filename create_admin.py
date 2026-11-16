from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    print("⏳ Menyiapkan database...")
    db.create_all()
    
    email = "admin@tokopintar.com"
    password = "admin123"
    
    existing_admin = User.query.filter_by(email=email).first()
    if existing_admin:
        print("✅ Akun Admin sudah ada!")
    else:
        admin = User(name="Super Admin", email=email, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("🎉 Akun Admin berhasil dibuat!")
        print(f"Email: {email}")
        print(f"Password: {password}")