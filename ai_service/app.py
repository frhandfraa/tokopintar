from flask import Flask, request, jsonify
from ai_service.recommender import ContentBasedRecommender
from ai_service import cache
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

app = Flask(__name__)
recommender = ContentBasedRecommender()

MODEL_PATH = "ai_service/model.pkl"
if os.path.exists(MODEL_PATH):
    recommender.load(MODEL_PATH)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "products": len(recommender.product_ids or [])
    })

@app.route("/recommend/similar/<int:product_id>", methods=["GET"])
def similar(product_id):
    top_n = int(request.args.get("top_n", 5))
    cached = cache.get_similar(product_id)
    if cached:
        return jsonify({"source": "cache", "data": cached}), 200

    recs = recommender.recommend(product_id, top_n=top_n)
    cache.set_similar(product_id, recs)
    return jsonify({"source": "model", "data": recs}), 200

@app.route("/recommend/retrain", methods=["POST"])
def retrain():
    engine = create_engine(os.getenv("DATABASE_URL"))
    df = pd.read_sql("SELECT id, name, category, description FROM products", engine)
    recommender.fit(df)
    recommender.save(MODEL_PATH)
    return jsonify({"msg": f"Model dilatih ulang dengan {len(df)} produk"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)