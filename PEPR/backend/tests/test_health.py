from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the PEPR API"}

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "pepr-api"

def test_database_health_down():
    # Since DB is not running, it should return gracefully
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    assert response.json()["status"] == "down"

def test_redis_health_down():
    response = client.get("/api/v1/health/redis")
    assert response.status_code == 200
    assert response.json()["status"] == "down"

def test_qdrant_health_down():
    response = client.get("/api/v1/health/vector-db")
    assert response.status_code == 200
    assert response.json()["status"] == "down"
