import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import app

def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"

def test_ready():
    client = app.test_client()
    response = client.get("/ready")
    assert response.status_code == 200
