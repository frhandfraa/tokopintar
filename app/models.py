from app import db
from datetime import datetime
import bcrypt
from werkzeug.security import check_password_hash


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="pembeli")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        # Mendukung hash bawaan bcrypt ($2b$ / $2a$ / $2y$)
        if self.password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.checkpw(password.encode(), self.password_hash.encode())
        # Mendukung hash Werkzeug (scrypt: / pbkdf2:) dari registrasi OTP
        if "$" in self.password_hash:
            return check_password_hash(self.password_hash, password)
        # Fallback plain text lama
        return self.password_hash == password

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
        }


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.BigInteger, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # TAMBAHAN MULTI-VENDOR
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    price = db.Column(db.Numeric(12, 2), default=0)
    stock = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    rating = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),  # String agar 19-digit BigInteger tidak dibulatkan JavaScript
            "seller_id": self.seller_id,
            "name": self.name,
            "category": self.category,
            "price": float(self.price or 0),
            "stock": self.stock,
            "description": self.description,
            "image_url": self.image_url,
            "rating": self.rating,
        }


class Interaction(db.Model):
    __tablename__ = "interactions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.BigInteger, db.ForeignKey("products.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": str(self.product_id),
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
        }


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total": float(self.total or 0),
            "status": self.status,
            "items": [i.to_dict() for i in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.BigInteger, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Numeric(12, 2), default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": str(self.product_id),
            "quantity": self.quantity,
            "price": float(self.price or 0),
        }


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.BigInteger, db.ForeignKey("products.id"), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)