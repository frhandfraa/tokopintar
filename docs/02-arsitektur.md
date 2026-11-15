# Dokumen Desain Arsitektur
## TokoPintar — Sistem Rekomendasi Produk Berbasis AI

| Item | Keterangan |
| :--- | :--- |
| Dokumen | Desain Arsitektur (Minggu 1) |
| Versi | 1.0 |
| Status | Final |

---

## 1. Gambaran Umum Arsitektur

TokoPintar menggunakan pendekatan **microservice** sederhana yang memisahkan aplikasi utama (App Server) dengan layanan AI (AI Service).

```text
+---------------------+
|   Client / Browser  |
+----------+----------+
           | HTTP
           v
+---------------------+
|      App Server     |
|  (Auth, CRUD, API)  |
+----+-----------+----+
     |           |
SQL  |           | HTTP
     v           v
+----------+  +--------------+
|PostgreSQL|  |  AI Service  |
| users    |  | TF-IDF+CosSim|
| products |  | Popularitas  |
| interacts|  +------+-------+
+----------+         |
                     v
               +----------+
               |  Redis   |
               +----------+
```

### Prinsip Desain
- **Separation of Concerns**: logika rekomendasi dipisahkan dari logika bisnis e-commerce.
- **Stateless API**: App Server dan AI Service dapat diskalakan secara independen.
- **Caching First**: hasil rekomendasi disimpan di Redis untuk mengurangi komputasi.

## 2. Tech Stack

| Komponen | Teknologi | Keterangan |
| :--- | :--- | :--- |
| App Server | FastAPI (Python) | REST API utama |
| AI Service | FastAPI / Flask (Python) | Layanan rekomendasi, port 5001 |
| Database | PostgreSQL | Penyimpanan data utama |
| Cache | Redis | Cache hasil rekomendasi |
| Autentikasi | JWT | Access token + role |
| Otorisasi | RBAC | Admin, Pedagang, Pembeli |
| Container | Docker & Docker Compose | Orkestrasi PostgreSQL & Redis |
| Dataset | Tokopedia (Kaggle) | Data produk untuk TF-IDF |
| Version Control | Git & GitHub | Manajemen kode |

## 3. Komponen Sistem

### 3.1 App Server
Bertanggung jawab atas:
- Registrasi & login pengguna (JWT).
- Otorisasi berbasis peran (Admin, Pedagang, Pembeli).
- CRUD produk, katalog, filter kategori, paginasi.
- Pencatatan interaksi (`view`, `click`, `purchase`).
- Dashboard analitik (produk terlaris, CTR, ringkasan total).
- Pemanggilan AI Service untuk rekomendasi.

### 3.2 AI Service
Bertanggung jawab atas:
- Endpoint rekomendasi produk berbasis Popularitas.
- Endpoint rekomendasi berbasis Content-Based Filtering (TF-IDF + Cosine Similarity).
- Cache hasil rekomendasi ke Redis.
- Mengembalikan daftar `product_id` beserta skor.

### 3.3 PostgreSQL
Menyimpan data utama: pengguna, produk, interaksi, dan pesanan.

### 3.4 Redis
Menyimpan hasil rekomendasi dengan TTL tertentu untuk mempercepat respons berikutnya.

## 4. Skema Basis Data (ERD Ringkas)

### `users`
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| id | UUID / SERIAL (PK) | Identitas pengguna |
| username | VARCHAR | Unik |
| email | VARCHAR | Unik |
| password_hash | VARCHAR | Hash password |
| role | ENUM | admin, pedagang, pembeli |
| created_at | TIMESTAMP | Waktu registrasi |

### `products`
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| id | UUID / SERIAL (PK) | Identitas produk |
| nama | VARCHAR | Nama produk |
| deskripsi | TEXT | Deskripsi (bahan TF-IDF) |
| kategori | VARCHAR | Kategori produk |
| harga | NUMERIC | Harga produk |
| stok | INTEGER | Jumlah stok |
| pedagang_id | FK → users.id | Pemilik produk |
| created_at | TIMESTAMP | Waktu dibuat |

### `interactions`
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| id | UUID / SERIAL (PK) | Identitas interaksi |
| user_id | FK → users.id | Pengguna |
| product_id | FK → products.id | Produk |
| type | ENUM | view, click, purchase |
| timestamp | TIMESTAMP | Waktu interaksi |

### `orders` (opsional)
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| id | UUID / SERIAL (PK) | Identitas pesanan |
| user_id | FK → users.id | Pembeli |
| total | NUMERIC | Total belanja |
| status | VARCHAR | Status pesanan |
| created_at | TIMESTAMP | Waktu pesanan |

### Relasi
- `users (1) — (N) products` (pedagang memiliki banyak produk)
- `users (1) — (N) interactions`
- `products (1) — (N) interactions`
- `users (1) — (N) orders`

## 5. Kontrak API AI Service

| Metode | Endpoint | Parameter | Deskripsi |
| :--- | :--- | :--- | :--- |
| GET | `/recommend/popular` | `k` (opsional, default 10) | Rekomendasi produk terpopuler |
| GET | `/recommend/content/{product_id}` | `k` (opsional, default 10) | Rekomendasi produk mirip berdasarkan TF-IDF + Cosine Similarity |
| GET | `/health` | — | Status layanan |

**Contoh respons:**
```json
{
  "recommendations": [
    { "product_id": 12, "score": 0.87 },
    { "product_id": 34, "score": 0.81 }
  ]
}
```

## 6. Alur Data Rekomendasi

1. Pengguna membuka halaman depan atau detail produk.
2. App Server memanggil endpoint AI Service yang sesuai.
3. AI Service memeriksa **Redis**:
   - **Cache hit** → langsung mengembalikan hasil.
   - **Cache miss** → menghitung Popularitas / TF-IDF + Cosine Similarity, lalu menyimpan hasil ke Redis dengan TTL.
4. App Server menampilkan rekomendasi kepada pengguna.
5. Setiap interaksi (`view`, `click`, `purchase`) dicatat ke tabel `interactions`.
6. Data interaksi digunakan pada Minggu 8 untuk menghitung **CTR** dan **Precision@K**.

## 7. Strategi Caching

| Aspek | Ketentuan |
| :--- | :--- |
| Key | `rec:popular:{k}` dan `rec:content:{product_id}:{k}` |
| TTL | 5–15 menit (dapat disesuaikan) |
| Invalidasi | Otomatis via TTL; manual saat produk berubah (opsional) |

## 8. Struktur Direktori Proyek

```text
tokopintar/
├── app/                  # App Server (FastAPI)
│   ├── models/           # Model SQLAlchemy
│   ├── routers/          # Endpoint API
│   ├── auth/             # JWT & RBAC
│   └── services/         # Klien AI Service
├── ai_service/           # AI Service
│   ├── recommend/        # Popularitas & Content-Based
│   └── cache/            # Integrasi Redis
├── scripts/              # Pra-pemrosesan dataset
├── docs/                 # Dokumen perencanaan & arsitektur
├── docker-compose.yml    # PostgreSQL & Redis
├── requirements.txt
└── README.md
```

## 9. Keamanan

- Password disimpan sebagai **hash** (bcrypt/argon2).
- Autentikasi menggunakan **JWT** dengan masa berlaku terbatas.
- Otorisasi berbasis peran (**RBAC**) pada endpoint sensitif.
- Kredensial database dan Redis disimpan di **environment variable**.
- Validasi input pada seluruh endpoint API.

## 10. Kebutuhan Non-Fungsional

| Aspek | Target |
| :--- | :--- |
| Waktu respons rekomendasi (cache) | < 500 ms |
| Waktu respons API umum | < 300 ms |
| Ketersediaan | Stabil pada lingkungan lokal / demo |
| Skalabilitas | App Server & AI Service dapat dijalankan terpisah |
| Kemudahan deployment | Docker Compose satu perintah |

## 11. Rencana Integrasi

1. AI Service dijalankan pada port terpisah (contoh: `5001`).
2. URL AI Service dikonfigurasi melalui environment variable (`AI_SERVICE_URL`).
3. App Server memanggil AI Service melalui HTTP REST.
4. Jika AI Service tidak tersedia, App Server menampilkan rekomendasi fallback (populer/default).