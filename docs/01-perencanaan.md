# Dokumen Perencanaan Proyek
## Sistem Rekomendasi Produk Berbasis AI untuk Meningkatkan Keputusan Pembelian dan Pengelolaan Stok pada Toko Luring

| Item | Keterangan |
| :--- | :--- |
| Nama Proyek | TokoPintar |
| Repositori | https://github.com/frhandfraa/tokopintar |
| Dokumen | Perencanaan Proyek (Minggu 1) |
| Versi | 1.0 |
| Status | Final |

---

## 1. Latar Belakang

Toko luring menghadapi dua masalah utama: (1) sulit memprediksi produk yang paling diminati sehingga pengelolaan stok tidak optimal, dan (2) pembeli kesulitan menemukan produk yang relevan tanpa bantuan rekomendasi. Di sisi lain, platform e-commerce besar telah memanfaatkan sistem rekomendasi berbasis AI untuk meningkatkan konversi dan efisiensi stok.

Proyek **TokoPintar** menjembatani kesenjangan tersebut dengan membangun aplikasi e-commerce yang dilengkapi **layanan AI untuk rekomendasi produk**, menggunakan pendekatan **Content-Based Filtering (TF-IDF + Cosine Similarity)** dan **Popularitas**, serta **pelacakan interaksi pengguna** sebagai bahan evaluasi.

## 2. Rumusan Masalah

1. Bagaimana membangun aplikasi e-commerce yang mencatat interaksi pengguna secara real-time?
2. Bagaimana menerapkan algoritma Content-Based Filtering dan Popularitas sebagai layanan rekomendasi terpisah?
3. Bagaimana mengintegrasikan layanan AI ke aplikasi utama agar rekomendasi tampil relevan dan cepat?
4. Bagaimana mengukur efektivitas rekomendasi (Precision@K dan CTR) serta memanfaatkannya untuk pengelolaan stok?

## 3. Tujuan Proyek

1. Membangun aplikasi e-commerce dengan autentikasi multi-role (**Admin, Pedagang, Pembeli**).
2. Mencatat setiap interaksi pengguna (`view`, `click`, `purchase`) ke dalam basis data.
3. Menyediakan **AI Service** terpisah yang menghasilkan rekomendasi produk.
4. Menampilkan rekomendasi pada halaman depan dan halaman detail produk.
5. Menyediakan dashboard analitik sederhana (produk terlaris, CTR, ringkasan total).
6. Mengevaluasi akurasi rekomendasi menggunakan metrik **Precision@K** dan **CTR**.

## 4. Ruang Lingkup

### 4.1 Termasuk dalam Lingkup
- Manajemen produk (CRUD) dengan paginasi dan filter kategori.
- Autentikasi JWT dan otorisasi berbasis peran (RBAC).
- Katalog produk dan halaman detail produk.
- Pelacakan interaksi pengguna (`view`, `click`, `purchase`).
- AI Service terpisah dengan Content-Based Filtering (TF-IDF + Cosine Similarity) dan Popularitas.
- Redis caching untuk mempercepat respons rekomendasi.
- Dashboard analitik untuk Admin/Pedagang.
- Integrasi AI Service dengan aplikasi utama.
- Kontainerisasi PostgreSQL dan Redis menggunakan Docker Compose.

### 4.2 Di Luar Lingkup
- Payment gateway produksi.
- Aplikasi mobile native.
- Collaborative filtering dan deep learning.
- Deployment produksi berskala besar / auto-scaling.
- Modul logistik dan pengiriman.

## 5. Metode AI yang Digunakan

| Metode | Fungsi | Alasan Pemilihan |
| :--- | :--- | :--- |
| **Popularitas** | Rekomendasi fallback untuk pengguna baru | Tidak memerlukan data historis pengguna |
| **Content-Based Filtering (TF-IDF + Cosine Similarity)** | Merekomendasikan produk mirip berdasarkan deskripsi/kategori | Efektif untuk data teks produk, tidak bergantung pada data pengguna lain |
| **Redis Caching** | Menyimpan hasil rekomendasi sementara | Mengurangi beban komputasi berulang dan mempercepat respons |

## 6. Rencana Kerja 9 Minggu

| Minggu | Fase & Fokus Utama | Aktivitas Kunci | Deliverable | Status |
| :---: | :--- | :--- | :--- | :---: |
| 1 | Perencanaan & Persiapan | Menentukan ruang lingkup, memilih metode AI, merancang arsitektur, menyusun rencana kerja | Dokumen Perencanaan & Desain Arsitektur | ✅ Selesai |
| 2 | Pengumpulan & Pra-pemrosesan Data | Mengumpulkan dataset Tokopedia (Kaggle), membersihkan duplikat & nilai kosong | Dataset bersih (CSV/JSON) | ✅ Selesai |
| 3 | Desain Basis Data & Struktur Proyek | Merancang skema (`users`, `products`, `interactions`), struktur folder, setup Git | ERD & Setup Proyek | ✅ Selesai |
| 4 | Pengembangan Modul Inti | Autentikasi JWT + RBAC, CRUD produk, katalog, filter & paginasi | Aplikasi dengan fungsi dasar e-commerce | ✅ Selesai |
| 5 | Implementasi Pelacakan Interaksi | Mencatat `view`, `click`, `purchase` ke database | Sistem pelacakan interaksi | ✅ Selesai |
| 6 | Pengembangan AI Service | Algoritma Popularitas & Content-Based Filtering, Redis caching | API rekomendasi berfungsi | ✅ Selesai |
| 7 | Integrasi & Dashboard | Integrasi AI ke aplikasi, tampilan rekomendasi, dashboard analitik | Sistem terintegrasi & dashboard | ✅ Selesai |
| 8 | Pengujian & Evaluasi | Unit test, integration test, evaluasi Precision@K & CTR, perbaikan bug | Laporan pengujian & perbaikan | ⏳ Berjalan |
| 9 | Dokumentasi & Presentasi | Dokumentasi teknis, panduan pengguna, video demo, materi sidang | Dokumentasi, demo, slide | ⏳ Berjalan |


## 7. Risiko dan Mitigasi

| Risiko | Dampak | Mitigasi |
| :--- | :--- | :--- |
| Dataset tidak representatif | Rekomendasi kurang relevan | Gunakan dataset Tokopedia + validasi manual sampel |
| AI Service lambat | Pengalaman pengguna menurun | Redis caching, batasi `K` rekomendasi, indexing TF-IDF |
| Bug integrasi antar layanan | Fitur tidak berjalan | Docker Compose, pengujian bertahap, logging |
| Waktu pengujian kurang | Kualitas tidak terukur | Alokasi khusus Minggu 8 |
| Data interaksi minim | Rekomendasi dingin (cold start) | Fallback ke metode Popularitas |

## 8. Indikator Keberhasilan

1. Aplikasi e-commerce berjalan dengan autentikasi multi-role dan CRUD produk.
2. Seluruh interaksi pengguna tercatat di basis data.
3. AI Service mengembalikan rekomendasi dalam waktu < 500 ms (dengan cache).
4. Rekomendasi tampil pada halaman depan dan detail produk.
5. Dashboard menampilkan produk terlaris, CTR, dan ringkasan total.
6. Evaluasi Precision@K dan CTR terdokumentasi pada Minggu 8.