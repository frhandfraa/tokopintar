from app import create_app, db
from app.models import User, Product, Interaction
import random

app = create_app()


def seed():
    with app.app_context():
        db.create_all()

        # 1. Buat Admin
        if not User.query.filter_by(email="admin@tokopintar.id").first():
            admin = User(name="Admin", email="admin@tokopintar.id", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)

        # 2. Buat 20 User Pembeli
        for i in range(1, 21):
            email = f"user{i}@tokopintar.id"
            if not User.query.filter_by(email=email).first():
                u = User(name=f"User {i}", email=email, role="pembeli")
                u.set_password("password123")
                db.session.add(u)

        # 3. Buat 50 Produk
        categories = ["Sepatu", "Tas", "Pakaian", "Elektronik", "Kecantikan"]
        for i in range(1, 51):
            p = Product(
                name=f"Produk {i} {random.choice(categories)}",
                category=random.choice(categories),
                price=random.randint(50000, 1000000),
                stock=random.randint(5, 100),
                description=f"Deskripsi lengkap produk {i} berkualitas tinggi",
                rating=round(random.uniform(3.5, 5.0), 1)
            )
            db.session.add(p)

        db.session.commit()

        # 4. Buat 300 Interaksi (View/Click/Purchase)
        users = User.query.filter_by(role="pembeli").all()
        products = Product.query.all()

        for _ in range(300):
            i = Interaction(
                user_id=random.choice(users).id,
                product_id=random.choice(products).id,
                type=random.choices(["view", "click", "purchase"], weights=[6, 3, 1])[0]
            )
            db.session.add(i)

        db.session.commit()
        print("✅ Seeding selesai: 20 user, 50 produk, 300 interaksi berhasil dibuat!")


if __name__ == "__main__":
    seed()