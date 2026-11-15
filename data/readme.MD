# Dataset TokoPintar

Folder ini digunakan untuk menyimpan dataset produk Tokopedia yang digunakan untuk melatih model **Content-Based Filtering (TF-IDF)**.

## ⚠️ Catatan Penting
File dataset berukuran sangat besar (CSV ~345 MB, JSON ~648 MB). Karena melebihi batas maksimal GitHub (100 MB per file), file dataset **tidak diunggah ke repositori ini**. 

## Cara Mengunduh Dataset
1. Unduh dataset melalui tautan berikut: **[https://drive.google.com/drive/folders/1muWWa_BrDTlzToGUhEBnyTWAo9-3rwKq?usp=sharing]**.
2. Ekstrak file jika berbentuk ZIP.
3. Letakkan file `tokopedia_products_with_review.csv` dan `tokopedia_products_with_review.json` ke dalam folder `data/` ini.
4. Pastikan nama file persis sama agar script AI Service dapat membacanya.