# Dokumen Pengujian & Evaluasi (Minggu 8)
## TokoPintar — Sistem Rekomendasi Produk Berbasis AI

| Item | Keterangan |
| :--- | :--- |
| Dokumen | Laporan Pengujian & Evaluasi |
| Versi | 1.0 |
| Status | Final |

---

## 1. Tujuan Pengujian
Memastikan sistem e-commerce berjalan dengan baik, fungsionalitas AI Service bekerja tanpa hambatan, dan mengevaluasi seberapa akurat rekomendasi produk yang dihasilkan.

## 2. Pengujian Fungsional (Black-Box Testing)

| Modul | Skenario Uji | Ekspektasi Hasil | Status |
| :--- | :--- | :--- | :--- |
| **Auth** | Registrasi pengguna baru (Pembeli) | Pengguna berhasil dibuat, password ter-hash | Lulus |
| **Auth** | Login dengan password salah | Mendapatkan respon `401 Unauthorized` | Lulus |
| **Produk** | Admin menambahkan produk baru | Produk tersimpan di DB dan muncul di katalog | Lulus |
| **Interaksi** | Pembeli mengklik detail produk | Tabel `interactions` mencatat tipe `click` | Lulus |
| **AI API** | Request `/recommend/popular?k=5` | Mengembalikan 5 produk dengan skor tertinggi | Lulus |
| **AI API** | Request `/recommend/content/1` | Mengembalikan produk mirip, bukan produk ID 1 | Lulus |
| **Caching** | Request API 2x berturut-turut | Respons kedua lebih cepat (Cache Hit di Redis) | Lulus |

## 3. Evaluasi Akurasi Rekomendasi

Evaluasi dilakukan untuk mengukur performa algoritma Content-Based Filtering dan Popularitas menggunakan metrik standar industri.

### A. Precision@K
Mengukur seberapa banyak item yang direkomendasikan (dari total K item) yang benar-benar relevan atau diklik oleh pengguna.

**Rumus:**
> **Precision@K = (Jumlah item relevan dalam Top-K) / K**

*Contoh:* Jika sistem merekomendasikan 5 produk (K=5), dan pengguna mengklik 2 dari produk tersebut, maka Precision@5 = 2/5 = 0.4 (40%).

### B. Click-Through Rate (CTR)
Mengukur efektivitas rekomendasi dengan membandingkan jumlah klik dengan jumlah tayangan (impresi).

**Rumus:**
> **CTR = (Total Klik pada Rekomendasi / Total Tayangan Rekomendasi) × 100%**

*Contoh:* Jika bagian "Rekomendasi" ditampilkan 1000 kali di halaman depan, dan diklik sebanyak 50 kali, maka CTR = 5%.

## 4. Cara Melakukan Evaluasi (SQL & Python)
1. Ambil data dari tabel `interactions` di PostgreSQL.
2. Filter interaksi yang terjadi pada area "Rekomendasi".
3. Hitung menggunakan script Python di folder `scripts/evaluate_model.py` (dibuat terpisah).

## 5. Kesimpulan Pengujian
- Sistem berhasil menangani beban dasar (CRUD, Auth, Tracking).
- AI Service berhasil mengembalikan rekomendasi dengan waktu respons rata-rata **< 200 ms** (berkat Redis).
- Akurasi rekomendasi Content-Based Filtering sangat bergantung pada kualitas deskripsi produk (TF-IDF).