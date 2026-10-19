import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

class ContentBasedRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        self.tfidf_matrix = None
        self.product_ids = None

    def fit(self, products: pd.DataFrame):
        # 1. Pastikan tidak ada nilai NaN, ubah semuanya jadi string kosong
        products = products.fillna("")
        
        # 2. Pastikan semua isinya string (bukan angka/float)
        products["name"] = products["name"].astype(str)
        products["category"] = products["category"].astype(str)
        products["description"] = products["description"].astype(str)
        
        # 3. Gabungkan teks
        products["content"] = (
            products["name"] + " " +
            products["category"] + " " +
            products["description"]
        )
        
        self.product_ids = products["id"].tolist()
        
        # 4. Latih model
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(products["content"])
            print(f"✅ Model dilatih dengan {len(self.product_ids)} produk")
        except ValueError as e:
            print("❌ Gagal melatih model. Pastikan teks produk tidak kosong.")
            raise e

    def recommend(self, product_id: int, top_n: int = 5):
        if product_id not in self.product_ids or self.tfidf_matrix is None:
            return []
        idx = self.product_ids.index(product_id)
        sim_scores = cosine_similarity(
            self.tfidf_matrix[idx], self.tfidf_matrix
        ).flatten()
        similar_indices = sim_scores.argsort()[::-1][1:top_n + 1]
        return [
            {"product_id": int(self.product_ids[i]), "score": float(sim_scores[i])}
            for i in similar_indices
        ]

    def save(self, path="ai_service/model.pkl"):
        with open(path, "wb") as f:
            pickle.dump({
                "vectorizer": self.vectorizer,
                "tfidf_matrix": self.tfidf_matrix,
                "product_ids": self.product_ids
            }, f)

    def load(self, path="ai_service/model.pkl"):
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.tfidf_matrix = data["tfidf_matrix"]
            self.product_ids = data["product_ids"]