import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

def set_similar(product_id, recommendations, ttl=7200):
    r.setex(f"rec:product:{product_id}", ttl, json.dumps(recommendations))

def get_similar(product_id):
    data = r.get(f"rec:product:{product_id}")
    return json.loads(data) if data else None