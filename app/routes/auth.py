from flask import Blueprint, request, jsonify, render_template, redirect, make_response
from app.models import User, db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from datetime import timedelta
from functools import wraps
import os
import requests
import secrets

auth_bp = Blueprint('auth', __name__)

# Ambil konfigurasi dari .env
FB_APP_ID = os.getenv('FB_APP_ID')
FB_APP_SECRET = os.getenv('FB_APP_SECRET')
FB_REDIRECT_URI = os.getenv('FB_REDIRECT_URI')

# ==========================================
# FUNGSI DECORATOR UNTUK ROLE (RBAC)
# ==========================================
def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "Akses Ditolak! Anda tidak memiliki izin."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ==========================================
# 1. RUTE HALAMAN HTML
# ==========================================
@auth_bp.route('/view/login', methods=['GET'])
def view_login():
    return render_template('login.html')

@auth_bp.route('/view/register', methods=['GET'])
def view_register():
    return render_template('register.html')

# ==========================================
# 2. API AUTENTIKASI (EMAIL & PASSWORD)
# ==========================================
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'pembeli')

        if not name or not email or not password:
            return jsonify({"error": "Data tidak lengkap"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email sudah terdaftar"}), 400

        valid_role = role if role in ['pembeli', 'pedagang'] else 'pembeli'
        new_user = User(name=name, email=email, role=valid_role)
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

# ==========================================
# 3. LOGIN DENGAN FACEBOOK (OAUTH 2.0 ASLI)
# ==========================================
@auth_bp.route('/facebook/login')
def facebook_login():
    if not FB_APP_ID or not FB_APP_SECRET:
        return "Konfigurasi Facebook App ID/Secret belum diatur di file .env", 500
        
    # Buat URL otorisasi Facebook
    fb_auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={FB_APP_ID}&redirect_uri={FB_REDIRECT_URI}&scope=email,public_profile"
    return redirect(fb_auth_url)

@auth_bp.route('/facebook/callback')
def facebook_callback():
    code = request.args.get('code')
    error = request.args.get('error')
    
    # Jika user membatalkan login di halaman Facebook
    if error or not code:
        return redirect('/api/auth/view/login?error=facebook_cancelled')

    try:
        # 1. Tukar kode otorisasi dengan Access Token
        token_url = f"https://graph.facebook.com/v18.0/oauth/access_token?client_id={FB_APP_ID}&redirect_uri={FB_REDIRECT_URI}&client_secret={FB_APP_SECRET}&code={code}"
        token_res = requests.get(token_url).json()
        access_token = token_res.get('access_token')

        if not access_token:
            return redirect('/api/auth/view/login?error=facebook_token_failed')

        # 2. Ambil profil pengguna dari Facebook
        user_info_url = f"https://graph.facebook.com/me?fields=id,name,email,picture&access_token={access_token}"
        user_info = requests.get(user_info_url).json()
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        # Jika akun FB tidak punya email terdaftar
        if not email:
            return "Akun Facebook Anda tidak memiliki Email. Harap gunakan metode login lain.", 400

        # 3. Cek database, apakah user sudah ada?
        user = User.query.filter_by(email=email).first()
        
        # Jika belum, daftarkan otomatis sebagai pembeli
        if not user:
            random_password = secrets.token_hex(16) # Password acak karena login via FB
            user = User(name=name, email=email, role='pembeli')
            user.set_password(random_password)
            db.session.add(user)
            db.session.commit()

        # 4. Buat Token JWT aplikasi kita
        expires = timedelta(days=1)
        jwt_token = create_access_token(
            identity=str(user.id), 
            additional_claims={"role": user.role, "name": user.name},
            expires_delta=expires
        )

        # 5. Redirect ke frontend dengan menyisipkan JWT ke localStorage via script
        target_url = '/api/products/view' # Pembeli langsung ke beranda
        
        html_response = f"""
        <html>
        <head><title>Login Berhasil...</title></head>
        <body>
            <p>Login berhasil! Mengalihkan ke halaman utama...</p>
            <script>
                localStorage.setItem('token', '{jwt_token}');
                localStorage.setItem('user_role', '{user.role}');
                localStorage.setItem('user_name', '{user.name}');
                localStorage.setItem('user_id', '{user.id}');
                window.location.href = '{target_url}';
            </script>
        </body>
        </html>
        """
        return make_response(html_response)

    except Exception as e:
        print(f"Error FB Login: {str(e)}")
        return redirect('/api/auth/view/login?error=facebook_server_error')