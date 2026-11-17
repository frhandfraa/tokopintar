import os
import secrets
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask import Blueprint, redirect, url_for, session, request, render_template, jsonify, current_app
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User

load_dotenv(override=True)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ==========================================
# HELPER KREDENSIAL OAUTH & SMTP EMAIL
# ==========================================
def get_fb_credentials():
    client_id = (
        os.getenv("FACEBOOK_CLIENT_ID")
        or os.getenv("FACEBOOK_APP_ID")
        or os.getenv("FB_CLIENT_ID")
        or current_app.config.get("FACEBOOK_CLIENT_ID")
    )
    client_secret = (
        os.getenv("FACEBOOK_CLIENT_SECRET")
        or os.getenv("FACEBOOK_APP_SECRET")
        or os.getenv("FB_CLIENT_SECRET")
        or current_app.config.get("FACEBOOK_CLIENT_SECRET")
    )
    return client_id, client_secret


def get_fb_redirect_uri():
    env_uri = os.getenv("FACEBOOK_REDIRECT_URI") or os.getenv("FB_REDIRECT_URI")
    return env_uri.strip() if env_uri else url_for("auth.facebook_callback", _external=True)


def get_google_credentials():
    client_id = (
        os.getenv("GOOGLE_CLIENT_ID")
        or os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        or current_app.config.get("GOOGLE_CLIENT_ID")
    )
    client_secret = (
        os.getenv("GOOGLE_CLIENT_SECRET")
        or os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        or current_app.config.get("GOOGLE_CLIENT_SECRET")
    )
    return client_id, client_secret


def get_google_redirect_uri():
    env_uri = os.getenv("GOOGLE_REDIRECT_URI")
    return env_uri.strip() if env_uri else url_for("auth.google_callback", _external=True)


def send_otp_email(recipient_email, recipient_name, otp_code):
    """Mengirim kode verifikasi 6 digit ke email pendaftar via SMTP."""
    mail_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    mail_port = int(os.getenv("MAIL_PORT", 587))
    mail_user = os.getenv("MAIL_USERNAME") or os.getenv("SMTP_EMAIL")
    mail_pass = os.getenv("MAIL_PASSWORD") or os.getenv("SMTP_PASSWORD")

    print(f"📧 [OTP REGISTER] Email: {recipient_email} | Kode OTP: {otp_code}")

    if not mail_user or not mail_pass:
        print("⚠️ MAIL_USERNAME / MAIL_PASSWORD belum diisi di .env. Email asli tidak terkirim.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Kode Verifikasi TokoPintar: {otp_code}"
    msg["From"] = f"TokoPintar <{mail_user}>"
    msg["To"] = recipient_email

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
        <h2 style="color: #00B14F; margin-top: 0;">Verifikasi Akun TokoPintar</h2>
        <p>Halo <strong>{recipient_name}</strong>,</p>
        <p>Gunakan kode verifikasi berikut untuk menyelesaikan pendaftaran akun Anda (berlaku selama 5 menit):</p>
        <div style="background: #f0fdf4; border: 1px dashed #00B14F; padding: 14px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 6px; color: #007A35; margin: 20px 0;">
            {otp_code}
        </div>
        <p style="font-size: 12px; color: #6D7588;">Jangan bagikan kode ini kepada siapa pun.</p>
    </div>
    """
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(mail_server, mail_port, timeout=15) as server:
            server.starttls()
            server.login(mail_user, mail_pass)
            server.sendmail(mail_user, recipient_email, msg.as_string())
        print(f"✅ Email OTP berhasil dikirim ke {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Gagal mengirim email OTP: {e}")
        return False


def create_user_session_redirect(user, fallback_name):
    """Helper terpadu untuk membuat JWT dan mengarahkan ke halaman produk."""
    jwt_token = create_access_token(identity=str(user.id))
    display_name = getattr(user, "username", None) or getattr(user, "name", fallback_name)
    user_role = getattr(user, "role", "pembeli") or "pembeli"

    session.clear()
    session["user_id"] = user.id
    session["user_name"] = display_name
    session["role"] = user_role

    params = urlencode({
        "token": jwt_token,
        "user_id": user.id,
        "user_name": display_name,
        "user_role": user_role,
    })
    return redirect(f"/api/products/view?{params}")


# ==========================================
# VIEW ROUTES
# ==========================================
@auth_bp.route("/view/login")
def login_view():
    return render_template("login.html")


@auth_bp.route("/view/register")
def register_view():
    return render_template("register.html")


@auth_bp.route("/view/verify-otp")
def verify_otp_view():
    pending = session.get("pending_register")
    if not pending:
        return redirect(url_for("auth.register_view"))
    return f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verifikasi OTP - TokoPintar</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light d-flex align-items-center justify-content-center" style="min-height: 100vh;">
        <div class="card shadow-sm p-4" style="max-width: 420px; width: 100%;">
            <h4 class="fw-bold text-success mb-2">Verifikasi Email</h4>
            <p class="text-muted small">Kami telah mengirimkan kode 6 digit ke <strong>{pending['email']}</strong>.</p>
            <div id="otp-alert" class="alert alert-danger d-none py-2 small"></div>
            <div id="otp-success" class="alert alert-success d-none py-2 small"></div>
            <form id="otpForm" action="/api/auth/verify-otp" method="POST">
                <div class="mb-3">
                    <label class="form-label fw-semibold">Kode OTP (6 Digit)</label>
                    <input type="text" name="otp" id="otpInput" maxlength="6" pattern="[0-9]{{6}}" class="form-control form-control-lg text-center fw-bold" placeholder="000000" required autofocus>
                </div>
                <button type="submit" class="btn btn-success w-100 fw-bold">Verifikasi & Buat Akun</button>
            </form>
            <div class="text-center mt-3">
                <a href="/api/auth/resend-otp" class="small text-decoration-none text-success fw-semibold">Kirim ulang kode OTP</a>
            </div>
        </div>
        <script>
            const params = new URLSearchParams(window.location.search);
            const err = params.get('error');
            if (err) {{
                const box = document.getElementById('otp-alert');
                box.classList.remove('d-none');
                box.innerText = err === 'expired' ? 'Kode OTP sudah kedaluwarsa. Silakan kirim ulang.' : 'Kode OTP salah. Silakan cek kembali email Anda.';
            }}
            if (params.get('resent')) {{
                const okBox = document.getElementById('otp-success');
                okBox.classList.remove('d-none');
                okBox.innerText = 'Kode OTP baru telah dikirim ke email Anda.';
            }}
        </script>
    </body>
    </html>
    """


# ==========================================
# MANUAL LOGIN & REGISTER DENGAN OTP EMAIL
# ==========================================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    pw_field = getattr(user, "password_hash", None) or getattr(user, "password", None)

    if not user or not pw_field or not check_password_hash(pw_field, password):
        if request.is_json:
            return jsonify({"error": "Email atau password salah"}), 401
        return redirect(url_for("auth.login_view", error="invalid_credentials"))

    access_token = create_access_token(identity=str(user.id))
    display_name = getattr(user, "username", None) or getattr(user, "name", user.email)
    user_role = getattr(user, "role", "pembeli") or "pembeli"

    if request.is_json:
        return jsonify({
            "message": "Login berhasil",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": display_name,
                "email": user.email,
                "role": user_role,
            },
        }), 200

    return create_user_session_redirect(user, user.email)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "pembeli").strip().lower()
    if role not in ("pembeli", "pedagang"):
        role = "pembeli"

    if not username or not email or not password:
        if request.is_json:
            return jsonify({"error": "Semua kolom wajib diisi"}), 400
        return redirect(url_for("auth.register_view", error="missing_fields"))

    if User.query.filter_by(email=email).first():
        if request.is_json:
            return jsonify({"error": "Email sudah terdaftar"}), 400
        return redirect(url_for("auth.register_view", error="email_exists"))

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()

    session["pending_register"] = {
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password),
        "role": role,
        "otp": otp_code,
        "expires_at": expires_at,
    }

    sent = send_otp_email(email, username, otp_code)

    if request.is_json:
        return jsonify({
            "message": "Kode OTP telah dikirim ke email Anda. Mengalihkan ke halaman verifikasi...",
            "requires_otp": True,
            "email_sent": sent,
            "redirect_url": "/api/auth/view/verify-otp",
        }), 200

    return redirect(url_for("auth.verify_otp_view"))


@auth_bp.route("/resend-otp", methods=["GET", "POST"])
def resend_otp():
    pending = session.get("pending_register")
    if not pending:
        return redirect(url_for("auth.register_view"))

    new_otp = f"{secrets.randbelow(900000) + 100000}"
    pending["otp"] = new_otp
    pending["expires_at"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    session["pending_register"] = pending

    send_otp_email(pending["email"], pending["username"], new_otp)
    if request.is_json:
        return jsonify({"message": "Kode OTP baru telah dikirim"}), 200
    return redirect(url_for("auth.verify_otp_view", resent=1))


@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or request.form
    input_otp = (data.get("otp") or "").strip()
    pending = session.get("pending_register")

    if not pending:
        if request.is_json:
            return jsonify({"error": "Sesi pendaftaran tidak ditemukan"}), 400
        return redirect(url_for("auth.register_view"))

    if datetime.utcnow() > datetime.fromisoformat(pending["expires_at"]):
        if request.is_json:
            return jsonify({"error": "Kode OTP kedaluwarsa"}), 400
        return redirect(url_for("auth.verify_otp_view", error="expired"))

    if input_otp != pending["otp"]:
        if request.is_json:
            return jsonify({"error": "Kode OTP salah"}), 400
        return redirect(url_for("auth.verify_otp_view", error="invalid_otp"))

    new_user = User(email=pending["email"])
    if hasattr(new_user, "username"):
        new_user.username = pending["username"]
    elif hasattr(new_user, "name"):
        new_user.name = pending["username"]

    if hasattr(new_user, "password_hash"):
        new_user.password_hash = pending["password_hash"]
    elif hasattr(new_user, "password"):
        new_user.password = pending["password_hash"]

    if hasattr(new_user, "role"):
        new_user.role = pending.get("role", "pembeli")

    db.session.add(new_user)
    db.session.commit()
    session.pop("pending_register", None)

    return create_user_session_redirect(new_user, pending["username"])


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login_view"))


# ==========================================
# GOOGLE OAUTH ROUTES
# ==========================================
@auth_bp.route("/google/login")
def google_login():
    client_id, _ = get_google_credentials()
    redirect_uri = get_google_redirect_uri()

    if not client_id:
        print("❌ ERROR: GOOGLE_CLIENT_ID kosong/tidak terbaca dari .env")
        return redirect(url_for("auth.login_view", error="google_config_missing"))

    requested_role = request.args.get("role", "pembeli")
    session["oauth_role"] = requested_role if requested_role in ("pembeli", "pedagang") else "pembeli"

    params = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    })
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@auth_bp.route("/google/callback")
def google_callback():
    code = request.args.get("code")
    if not code:
        print("❌ Google Callback Error:", request.args.to_dict())
        return redirect(url_for("auth.login_view", error="google_auth_denied"))

    client_id, client_secret = get_google_credentials()
    redirect_uri = get_google_redirect_uri()

    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    token_data = token_res.json()

    if "access_token" not in token_data:
        print("❌ GOOGLE TOKEN FAILED:", token_data)
        print("   -> Redirect URI yang dikirim:", redirect_uri)
        return redirect(url_for("auth.login_view", error="google_token_failed"))

    profile_res = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        timeout=10,
    )
    google_user = profile_res.json()
    print("✅ DATA USER GOOGLE:", google_user)

    google_email = google_user.get("email")
    if not google_email:
        return redirect(url_for("auth.login_view", error="google_email_missing"))

    google_name = google_user.get("name") or google_email.split("@")[0]
    default_role = session.pop("oauth_role", "pembeli")

    user = User.query.filter_by(email=google_email).first()
    if not user:
        dummy_pw = generate_password_hash(secrets.token_hex(24))
        user = User(email=google_email)

        if hasattr(user, "username"):
            user.username = google_name
        elif hasattr(user, "name"):
            user.name = google_name

        if hasattr(user, "password_hash"):
            user.password_hash = dummy_pw
        elif hasattr(user, "password"):
            user.password = dummy_pw

        if hasattr(user, "role"):
            user.role = default_role

        try:
            db.session.add(user)
            db.session.commit()
            print(f"✅ User Google baru disimpan ke DB: ID={user.id}, Email={user.email}, Role={default_role}")
        except Exception as e:
            db.session.rollback()
            print("❌ DB COMMIT ERROR (Google):", e)
            return redirect(url_for("auth.login_view", error="db_save_failed"))

    return create_user_session_redirect(user, google_name)


# ==========================================
# FACEBOOK OAUTH ROUTES
# ==========================================
@auth_bp.route("/facebook/login")
def facebook_login():
    client_id, _ = get_fb_credentials()
    redirect_uri = get_fb_redirect_uri()

    if not client_id:
        print("❌ ERROR: FACEBOOK_CLIENT_ID kosong/tidak terbaca dari .env")
        return redirect(url_for("auth.login_view", error="facebook_config_missing"))

    requested_role = request.args.get("role", "pembeli")
    session["oauth_role"] = requested_role if requested_role in ("pembeli", "pedagang") else "pembeli"

    fb_auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=email,public_profile"
    )
    return redirect(fb_auth_url)


@auth_bp.route("/facebook/callback")
def facebook_callback():
    code = request.args.get("code")
    if not code:
        print("❌ Facebook Callback Error:", request.args.to_dict())
        return redirect(url_for("auth.login_view", error="facebook_auth_denied"))

    client_id, client_secret = get_fb_credentials()
    redirect_uri = get_fb_redirect_uri()

    token_res = requests.get(
        "https://graph.facebook.com/v19.0/oauth/access_token",
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=10,
    )
    token_data = token_res.json()

    if "access_token" not in token_data:
        print("❌ FACEBOOK TOKEN FAILED:", token_data)
        print("   -> Redirect URI yang dikirim:", redirect_uri)
        return redirect(url_for("auth.login_view", error="facebook_token_failed"))

    profile_res = requests.get(
        "https://graph.facebook.com/v19.0/me",
        params={
            "fields": "id,name,email",
            "access_token": token_data["access_token"],
        },
        timeout=10,
    )
    fb_user = profile_res.json()
    print("✅ DATA USER FACEBOOK:", fb_user)

    fb_id = fb_user.get("id")
    if not fb_id:
        return redirect(url_for("auth.login_view", error="facebook_profile_failed"))

    fb_name = fb_user.get("name") or f"User_{fb_id[:6]}"
    fb_email = fb_user.get("email") or f"fb_{fb_id}@facebook.local"
    default_role = session.pop("oauth_role", "pembeli")

    user = User.query.filter_by(email=fb_email).first()
    if not user:
        dummy_pw = generate_password_hash(secrets.token_hex(24))
        user = User(email=fb_email)

        if hasattr(user, "username"):
            user.username = fb_name
        elif hasattr(user, "name"):
            user.name = fb_name

        if hasattr(user, "password_hash"):
            user.password_hash = dummy_pw
        elif hasattr(user, "password"):
            user.password = dummy_pw

        if hasattr(user, "role"):
            user.role = default_role

        try:
            db.session.add(user)
            db.session.commit()
            print(f"✅ User Facebook baru disimpan ke DB: ID={user.id}, Email={user.email}")
        except Exception as e:
            db.session.rollback()
            print("❌ DB COMMIT ERROR:", e)
            return redirect(url_for("auth.login_view", error="db_save_failed"))

    return create_user_session_redirect(user, fb_name)