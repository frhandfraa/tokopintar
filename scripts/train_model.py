import pandas as pd
from sqlalchemy import create_engine
from ai_service.recommender import ContentBasedRecommender
import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
df = pd.read_sql("SELECT id, name, category, description FROM products", engine)

print(f"📊 Total produk di database: {len(df)}")

if len(df) == 0:
    print("❌ Tabel products kosong. Pastikan Anda sudah menjalankan 'python -m scripts.preprocess_data'")
else:
    print(f"Contoh data: {df.iloc[0]['name']} | {df.iloc[0]['category']}")
    
    rec = ContentBasedRecommender()
    rec.fit(df)
    rec.save("ai_service/model.pkl")

    print("\n🔍 Contoh rekomendasi untuk produk ID pertama:")
    first_id = int(df.iloc[0]["id"])
    for r in rec.recommend(first_id, top_n=5):
        print(f"  → Produk {r['product_id']} (skor kemiripan: {r['score']:.3f})")