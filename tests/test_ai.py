# File: tests/test_ai.py
import requests
import pytest

# Sesuaikan URL dengan port AI Service Anda (biasanya 5001)
BASE_URL = "http://localhost:5001"

def test_health_check():
    """Memastikan layanan AI menyala"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"

def test_recommend_popular():
    """Memastikan endpoint popular mengembalikan list produk"""
    response = requests.get(f"{BASE_URL}/recommend/popular?k=5")
    assert response.status_code == 200
    data = response.json()
    
    # Pastikan mengembalikan list
    assert "recommendations" in data
    # Pastikan jumlahnya sesuai dengan parameter K
    assert len(data["recommendations"]) <= 5

def test_recommend_content():
    """Memastikan endpoint content bekerja untuk ID produk tertentu"""
    product_id = 1 # Asumsi ID 1 ada di database
    response = requests.get(f"{BASE_URL}/recommend/content/{product_id}?k=3")
    
    # Jika produk tidak ada, API mungkin mengembalikan 404. 
    # Jika ada, harus 200 OK.
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert "recommendations" in data