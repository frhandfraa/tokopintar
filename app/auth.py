from flask import Blueprint, request, jsonify, render_template
from app.models import User, db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from datetime import timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# ==========================================
# FUNGSI DECORATOR UNTUK ROLE (RBAC)
# ==========================================
def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            # allowed_roles sekarang berbentuk tuple, misal: ("admin", "pedagang")
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "Akses Ditolak! Anda tidak memiliki izin."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ==========================================
# RUTE UNTUK MENAMPILKAN HALAMAN HTML
# ==========================================
@auth_bp.route('/view/login', methods=['GET'])
def view_login():
    return render_template('login.html')

@auth_bp.route('/view/register', methods=['GET'])
def view_register():
    return render_template('register.html')

# ==========================================
# RUTE API AUTENTIKASI
# ==========================================
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return jsonify({"error": "Data tidak lengkap"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email sudah terdaftar"}), 400

        new_user = User(name=name, email=email, role="pembeli")
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Registrasi berhasil, silakan login"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return jsonify({"error": "Email atau password salah"}), 401

        expires = timedelta(days=1)
        access_token = create_access_token(
            identity=str(user.id), 
            additional_claims={"role": user.role, "name": user.name},
            expires_delta=expires
        )

        return jsonify({
            "message": "Login berhasil",
            "access_token": access_token,
            "user": user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500