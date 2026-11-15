# File: tests/test_ai.py
import requests
import pytest
import os

# Sesuaikan URL dengan port AI Service Anda (biasanya 5001)
BASE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:5001")

def test_health_check():
    """Memastikan layanan AI menyala"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        assert response.json().get("status") == "ok"
    except requests.exceptions.ConnectionError:
        # Jika layanan tidak bisa dihubungi, lewati tes ini alih-alih gagal
        pytest.skip(f"AI Service tidak berjalan di {BASE_URL} (Connection Refused)")

def test_recommend_popular():
    """Memastikan endpoint popular mengembalikan list produk"""
    try:
        response = requests.get(f"{BASE_URL}/recommend/popular?k=5", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Pastikan mengembalikan list
        assert "recommendations" in data
        # Pastikan jumlahnya sesuai dengan parameter K
        assert len(data["recommendations"]) <= 5
    except requests.exceptions.ConnectionError:
        pytest.skip(f"AI Service tidak berjalan di {BASE_URL} (Connection Refused)")

def test_recommend_content():
    """Memastikan endpoint content bekerja untuk ID produk tertentu"""
    product_id = 1 # Asumsi ID 1 ada di database
    try:
        response = requests.get(f"{BASE_URL}/recommend/content/{product_id}?k=3", timeout=5)
        
        # Jika produk tidak ada, API mungkin mengembalikan 404. 
        # Jika ada, harus 200 OK.
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "recommendations" in data
    except requests.exceptions.ConnectionError:
        pytest.skip(f"AI Service tidak berjalan di {BASE_URL} (Connection Refused)")