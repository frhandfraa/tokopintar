import pandas as pd
import re
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def clean_text(text):
    """Membersihkan teks dari URL, tag HTML, emoji, dan karakter non-alfanumerik."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()

def preprocess():
    print("📥 Membaca dataset...")
    df = pd.read_csv("data/tokopedia_products_with_review.csv")

    kolom_produk = ["product_id", "name", "category", "price", "rating_average", "count_sold"]
    df_produk = df[kolom_produk].copy()

    print("🧹 Membersihkan data...")
    df_produk.dropna(subset=["name", "category"], inplace=True)
    df_produk.fillna({"price": 0, "rating_average": 0, "count_sold": 0}, inplace=True)
    df_produk.drop_duplicates(subset=["product_id"], inplace=True)

    print("📝 Normalisasi teks...")
    df_produk["name_clean"] = df_produk["name"].apply(clean_text)
    df_produk["category_clean"] = df_produk["category"].apply(clean_text)
    df_produk["content"] = df_produk["name_clean"] + " " + df_produk["category_clean"]

    df_final = df_produk.rename(columns={
        "product_id": "id",
        "name": "name",
        "category": "category",
        "price": "price",
        "rating_average": "rating",
        "count_sold": "stock"
    })

    df_final["price"] = pd.to_numeric(df_final["price"], errors="coerce").fillna(0)
    df_final["rating"] = pd.to_numeric(df_final["rating"], errors="coerce").fillna(0)
    df_final["stock"] = pd.to_numeric(df_final["stock"], errors="coerce").fillna(0).astype(int)
    
    if "description" not in df_final.columns:
        df_final["description"] = df_final["content"]

    print("💾 Menyimpan ke database...")
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    # Cek apakah tabel sudah ada di database
    inspector = inspect(engine)
    if "products" in inspector.get_table_names():
        with engine.begin() as conn:
            print("🧹 Mengosongkan tabel produk lama (CASCADE)...")
            conn.execute(text("TRUNCATE TABLE products CASCADE;"))
    else:
        print("ℹ️ Tabel belum ada. Script akan membuat tabel baru...")

    # Masukkan data baru
    # if_exists='append' akan membuat tabel jika belum ada, atau menambah data jika sudah ada
    df_final[["id", "name", "category", "price", "stock", "rating", "description"]].to_sql(
        "products", engine, if_exists="append", index=False
    )
    
    print(f"✅ Berhasil menyimpan {len(df_final)} produk ke database.")

if __name__ == "__main__":
    preprocess()