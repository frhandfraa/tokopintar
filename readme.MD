# TokoPintar 🛍️🤖
**Sistem E-Commerce dengan Rekomendasi Produk Berbasis AI (Content-Based Filtering) untuk UMKM**

TokoPintar adalah platform e-commerce modern yang dilengkapi dengan microservice AI untuk memberikan rekomendasi produk yang relevan kepada pembeli. Proyek ini dirancang untuk menyelesaikan masalah pembeli yang kewalahan memilih produk dan membantu UMKM meningkatkan konversi penjualan melalui personalisasi.

## ✨ Fitur Utama
- **Autentikasi JWT (JSON Web Token):** Sistem login aman dengan pembatasan akses berdasarkan role (Admin, Pedagang, Pembeli).
- **Katalog Produk:** Manajemen data produk (CRUD) dengan dukungan paginasi dan filter kategori.
- **Tracking Interaksi:** Mencatat perilaku pengguna secara real-time (view, click, purchase) sebagai bahan pembelajaran AI.
- **AI Recommendation Engine:** Memberikan rekomendasi produk yang mirip berdasarkan analisis teks (TF-IDF & Cosine Similarity).
- **Redis Caching:** Mempercepat waktu respons API rekomendasi dengan menyimpan hasil kalkulasi sementara.
- **Microservice Architecture:** Memisahkan App Server (E-Commerce) dan AI Service agar lebih skalabel dan mudah di-maintain.

## 🛠️ Tech Stack
- **Backend (App Server):** Python, Flask, SQLAlchemy
- **AI Service:** Python, Flask, Scikit-learn, Pandas
- **Database:** PostgreSQL
- **Cache:** Redis
- **Infrastruktur:** Docker & Docker Compose
- **Autentikasi:** Flask-JWT-Extended

---

## 🚀 Panduan Instalasi & Menjalankan Proyek

### 1. Prasyarat (Prerequisites)
Pastikan Anda sudah menginstal:
- Python 3.10+ (Disarankan versi 3.11 atau 3.12)
- Docker Desktop (Pastikan aplikasi Docker sedang berjalan)
- Git

### 2. Clone Repository
```bash
git clone https://github.com/USERNAME/tokopintar.git
cd tokopintar
```

### 3. Setup Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Konfigurasi Environment Variables
Buat file bernama `.env` di direktori utama, lalu isi dengan konfigurasi berikut:
```env
SECRET_KEY=tokopintar-secret-key-2026
JWT_SECRET_KEY=tokopintar-jwt-secret-2026
JWT_ACCESS_TOKEN_EXPIRES=86400
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/tokopintar
REDIS_URL=redis://localhost:6379/0
AI_SERVICE_URL=http://localhost:5001
```

### 6. Jalankan Database & Redis (Docker)
Buka terminal baru, lalu jalankan:
```bash
docker-compose up -d
```
Pastikan container `tokopintar_db` dan `tokopintar_redis` berstatus running.

### 7. Migrasi Database & Seeding Data Dummy
Kembali ke terminal utama (yang ada `(venv)`), jalankan:
```bash
python -m scripts.seed_db
```
Perintah ini akan membuat tabel dan mengisi 50 produk, 20 user, serta 300 interaksi dummy.

### 8. Latih Model AI
Sebelum menjalankan AI Service, kita harus melatih model dengan data produk yang ada:
```bash
python -m scripts.train_model
```

### 9. Jalankan Aplikasi
Proyek ini terdiri dari 2 server yang harus berjalan bersamaan. Buka **2 terminal terpisah** (pastikan venv aktif di keduanya):

**Terminal 1 (App Server / E-Commerce):**
```bash
python run.py
```
*(Berjalan di http://localhost:5000)*

**Terminal 2 (AI Microservice):**
```bash
python -m ai_service.app
```
*(Berjalan di http://localhost:5001)*

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Registrasi pengguna baru
- `POST /api/auth/login` - Login dan mendapatkan JWT Token
- `GET /api/auth/me` - Mendapatkan profil user (Butuh Bearer Token)

### Products & Recommendations
- `GET /api/products` - Mendapatkan daftar produk (paginasi)
- `GET /api/products/<id>` - Mendapatkan detail 1 produk
- `GET /api/products/<id>/similar` - **Mendapatkan rekomendasi produk mirip (AI)**

### Interactions
- `POST /api/interactions` - Mencatat interaksi user (view/click/purchase) (Butuh Bearer Token)

### Dashboard (Admin/Pedagang)
- `GET /api/dashboard/popular` - Produk terlaris
- `GET /api/dashboard/ctr` - Statistik Click-Through Rate
- `GET /api/dashboard/summary` - Ringkasan total produk, order, dan pendapatan

---

## 📁 Struktur Direktori
```text
tokopintar/
├── app/                  # Main App Server (E-Commerce)
│   ├── routes/           # Endpoint API (auth, products, dll)
│   ├── models.py         # Skema Database (SQLAlchemy)
│   ├── auth.py           # Logika JWT & Role
│   └── __init__.py       # Inisialisasi Flask & Blueprints
├── ai_service/           # Microservice AI (Rekomendasi)
│   ├── app.py            # Endpoint AI
│   ├── recommender.py    # Algoritma Content-Based Filtering
│   └── cache.py          # Logika Redis
├── scripts/              # Script Bantuan
│   ├── seed_db.py        # Script pengisi data dummy
│   └── train_model.py    # Script training model AI
├── docker-compose.yml    # Konfigurasi Docker (DB & Redis)
├── requirements.txt      # Daftar library Python
├── .env                  # Variabel environment (rahasia)
└── run.py                # Entry point App Server
```

---
## 👨‍💻 Author
**Farhan Defra Jaya Kusuma** - *Project Kewirausahaan & E-Commerce*
- GitHub: [@USERNAME](https://github.com/frhandfraa)