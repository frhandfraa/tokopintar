# File: scripts/evaluate_model.py
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables dari file .env
load_dotenv()

# Ambil URL database dari .env, fallback ke localhost jika tidak ada
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password_rahasia_anda@localhost:5432/tokopintar_db")

def evaluate_recommendation_metrics():
    print("🔄 Menghubungkan ke database...")
    engine = create_engine(DATABASE_URL)
    
    try:
        # 1. Hitung CTR (Click-Through Rate)
        # Asumsi: 'view' adalah tayangan, 'click' adalah klik pada rekomendasi
        query_interactions = """
            SELECT type, COUNT(*) as total 
            FROM interactions 
            GROUP BY type;
        """
        df_interactions = pd.read_sql(query_interactions, engine)
        
        views = df_interactions[df_interactions['type'] == 'view']['total'].sum()
        clicks = df_interactions[df_interactions['type'] == 'click']['total'].sum()
        
        if views > 0:
            ctr = (clicks / views) * 100
            print(f"📊 Total Views   : {views}")
            print(f"📊 Total Clicks  : {clicks}")
            print(f"✅ CTR           : {ctr:.2f}%")
        else:
            print("⚠️ Belum ada data 'view' di database.")

        # 2. Simulasi Precision@K
        # Karena kita tidak menyimpan log rekomendasi spesifik, kita hitung rata-rata
        # produk yang diklik/dibeli per user.
        query_precision = """
            SELECT user_id, COUNT(DISTINCT product_id) as interacted_products
            FROM interactions
            WHERE type IN ('click', 'purchase')
            GROUP BY user_id;
        """
        df_precision = pd.read_sql(query_precision, engine)
        
        if not df_precision.empty:
            avg_interactions = df_precision['interacted_products'].mean()
            k = 10 # Asumsi kita menampilkan 10 rekomendasi (K=10)
            precision_at_k = min(avg_interactions / k, 1.0)
            print(f"🎯 Rata-rata interaksi per user: {avg_interactions:.2f}")
            print(f"✅ Precision@10 (Estimasi)     : {precision_at_k * 100:.2f}%")
        else:
            print("⚠️ Belum ada data interaksi pengguna.")

    except Exception as e:
        print(f"❌ Gagal mengevaluasi data: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    evaluate_recommendation_metrics()