import os
import json
import uuid
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import app.models as models
from app.models import db

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def mask_email(email):
    if not email or "@" not in email:
        return email or "-"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"{local[0]}***@{domain}"
    return f"{local[:2]}***@{domain}"


def mask_phone(phone):
    if not phone:
        return ""
    digits = str(phone).strip()
    if len(digits) <= 2:
        return digits
    return "*" * (len(digits) - 2) + digits[-2:]


def get_extra_data_path():
    """File penyimpanan cadangan (alamat, gender, tgl lahir, foto) jika kolom belum ada di tabel User."""
    folder = os.path.join(current_app.root_path, "static", "data")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "user_profiles.json")


def load_extra_profiles():
    path = get_extra_data_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_extra_profiles(data):
    path = get_extra_data_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- VIEW HALAMAN PROFIL PELANGGAN ---
@profile_bp.route("/view")
def profile_view():
    return render_template("profile.html")


# --- API AMBIL DATA PROFIL LENGKAP ---
@profile_bp.route("", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = str(get_jwt_identity())
    User = getattr(models, "User", None)
    user = User.query.get(int(user_id)) if User else None

    if not user:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404

    extras = load_extra_profiles().get(user_id, {})

    display_name = getattr(user, "username", None) or getattr(user, "name", "")
    email = getattr(user, "email", "")
    role = getattr(user, "role", "pembeli")
    phone = getattr(user, "phone", None) or extras.get("phone", "")
    gender = getattr(user, "gender", None) or extras.get("gender", "Laki-laki")
    birth_date = getattr(user, "birth_date", None) or extras.get("birth_date", "")
    avatar_url = getattr(user, "avatar_url", None) or extras.get("avatar_url", "")
    addresses = extras.get("addresses", [])

    # Jika di models.py ada kolom address tunggal & daftar alamat masih kosong, jadikan alamat utama
    db_address = getattr(user, "address", None)
    if db_address and not addresses:
        addresses = [{
            "id": "addr-default",
            "label": "Rumah",
            "recipient": display_name,
            "phone": phone or "-",
            "full_address": db_address,
            "is_primary": True,
        }]

    return jsonify({
        "data": {
            "id": user.id,
            "name": display_name,
            "email": email,
            "masked_email": mask_email(email),
            "role": role,
            "phone": phone,
            "masked_phone": mask_phone(phone),
            "gender": gender,
            "birth_date": birth_date,
            "avatar_url": avatar_url,
            "addresses": addresses,
        }
    }), 200


# --- API UPDATE BIODATA PROFIL ---
@profile_bp.route("", methods=["PUT", "POST"])
@jwt_required()
def update_profile():
    user_id = str(get_jwt_identity())
    User = getattr(models, "User", None)
    user = User.query.get(int(user_id)) if User else None

    if not user:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404

    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    gender = (data.get("gender") or "Laki-laki").strip()
    birth_date = (data.get("birth_date") or "").strip()

    if new_name:
        if hasattr(user, "username"):
            user.username = new_name
        elif hasattr(user, "name"):
            user.name = new_name

    if hasattr(user, "phone"):
        user.phone = phone
    if hasattr(user, "gender"):
        user.gender = gender
    if hasattr(user, "birth_date"):
        user.birth_date = birth_date

    db.session.commit()

    all_extras = load_extra_profiles()
    user_extra = all_extras.get(user_id, {})
    user_extra.update({
        "phone": phone,
        "gender": gender,
        "birth_date": birth_date,
    })
    all_extras[user_id] = user_extra
    save_extra_profiles(all_extras)

    updated_name = getattr(user, "username", None) or getattr(user, "name", new_name)
    return jsonify({
        "message": "Profil berhasil diperbarui!",
        "user_name": updated_name,
    }), 200


# --- API UPLOAD FOTO PROFIL ---
@profile_bp.route("/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    user_id = str(get_jwt_identity())
    User = getattr(models, "User", None)
    user = User.query.get(int(user_id)) if User else None

    if not user:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404

    if "avatar" not in request.files:
        return jsonify({"error": "Tidak ada file gambar yang dipilih"}), 400

    file = request.files["avatar"]
    if not file or file.filename == "":
        return jsonify({"error": "Nama file tidak valid"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Format gambar harus JPG, JPEG, PNG, atau WEBP"}), 400

    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"

    upload_folder = os.path.join(current_app.root_path, "static", "uploads", "profiles")
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))

    avatar_url = f"/static/uploads/profiles/{filename}"

    if hasattr(user, "avatar_url"):
        user.avatar_url = avatar_url
        db.session.commit()

    all_extras = load_extra_profiles()
    user_extra = all_extras.get(user_id, {})
    user_extra["avatar_url"] = avatar_url
    all_extras[user_id] = user_extra
    save_extra_profiles(all_extras)

    return jsonify({
        "message": "Foto profil berhasil diperbarui!",
        "avatar_url": avatar_url,
    }), 200


# --- API MANAJEMEN BUKU ALAMAT ---
@profile_bp.route("/addresses", methods=["POST"])
@jwt_required()
def add_address():
    user_id = str(get_jwt_identity())
    User = getattr(models, "User", None)
    user = User.query.get(int(user_id)) if User else None

    data = request.get_json(silent=True) or {}
    label = (data.get("label") or "Rumah").strip()
    recipient = (data.get("recipient") or "").strip()
    phone = (data.get("phone") or "").strip()
    full_address = (data.get("full_address") or "").strip()
    is_primary = bool(data.get("is_primary", False))

    if not recipient or not phone or not full_address:
        return jsonify({"error": "Nama penerima, nomor HP, dan alamat lengkap wajib diisi"}), 400

    all_extras = load_extra_profiles()
    user_extra = all_extras.get(user_id, {})
    addresses = user_extra.get("addresses", [])

    if not addresses:
        is_primary = True

    if is_primary:
        for addr in addresses:
            addr["is_primary"] = False

    new_addr = {
        "id": f"addr-{uuid.uuid4().hex[:8]}",
        "label": label,
        "recipient": recipient,
        "phone": phone,
        "full_address": full_address,
        "is_primary": is_primary,
    }
    addresses.append(new_addr)

    if is_primary and user and hasattr(user, "address"):
        user.address = full_address
        db.session.commit()

    user_extra["addresses"] = addresses
    all_extras[user_id] = user_extra
    save_extra_profiles(all_extras)

    return jsonify({"message": "Alamat baru berhasil ditambahkan!", "addresses": addresses}), 201


@profile_bp.route("/addresses/<addr_id>/primary", methods=["POST"])
@jwt_required()
def set_primary_address(addr_id):
    user_id = str(get_jwt_identity())
    User = getattr(models, "User", None)
    user = User.query.get(int(user_id)) if User else None

    all_extras = load_extra_profiles()
    user_extra = all_extras.get(user_id, {})
    addresses = user_extra.get("addresses", [])

    primary_text = None
    for addr in addresses:
        addr["is_primary"] = (addr["id"] == addr_id)
        if addr["is_primary"]:
            primary_text = addr["full_address"]

    if primary_text and user and hasattr(user, "address"):
        user.address = primary_text
        db.session.commit()

    user_extra["addresses"] = addresses
    all_extras[user_id] = user_extra
    save_extra_profiles(all_extras)

    return jsonify({"message": "Alamat utama diperbarui!", "addresses": addresses}), 200


@profile_bp.route("/addresses/<addr_id>", methods=["DELETE"])
@jwt_required()
def delete_address(addr_id):
    user_id = str(get_jwt_identity())
    all_extras = load_extra_profiles()
    user_extra = all_extras.get(user_id, {})
    addresses = [a for a in user_extra.get("addresses", []) if a["id"] != addr_id]

    if addresses and not any(a.get("is_primary") for a in addresses):
        addresses[0]["is_primary"] = True

    user_extra["addresses"] = addresses
    all_extras[user_id] = user_extra
    save_extra_profiles(all_extras)

    return jsonify({"message": "Alamat dihapus.", "addresses": addresses}), 200


# --- API UBAH PASSWORD ---
@profile_bp.route("/password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    User = getattr(models, "User", None)
    user = User.query.get(user_id) if User else None

    if not user:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404

    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if len(new_password) < 6:
        return jsonify({"error": "Password baru minimal 6 karakter"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Konfirmasi password baru tidak cocok"}), 400

    pw_field = getattr(user, "password_hash", None) or getattr(user, "password", None)
    # Jika user mengisi password lama, validasi kecocokannya (akun OAuth boleh langsung atur password baru jika dikosongkan)
    if old_password and pw_field and not check_password_hash(pw_field, old_password):
        return jsonify({"error": "Password lama yang Anda masukkan salah"}), 400

    hashed = generate_password_hash(new_password)
    if hasattr(user, "password_hash"):
        user.password_hash = hashed
    elif hasattr(user, "password"):
        user.password = hashed

    db.session.commit()
    return jsonify({"message": "Password berhasil diubah!"}), 200