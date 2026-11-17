from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()
    
    email = "pedagang@tokopintar.com"
    password = "pedagang123"
    
    existing = User.query.filter_by(email=email).first()
    if existing:
        print("✅ Akun Pedagang sudah ada!")
    else:
        pedagang = User(name="Toko Berkah Jaya", email=email, role="pedagang")
        pedagang.set_password(password)
        db.session.add(pedagang)
        db.session.commit()
        print("🎉 Akun Pedagang berhasil dibuat!")
        print(f"Email: {email}")
        print(f"Password: {password}")