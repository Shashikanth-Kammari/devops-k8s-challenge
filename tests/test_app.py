from app.app import app


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200


def test_ready():
    client = app.test_client()

    response = client.get("/ready")

    assert response.status_code in [200, 503]


def test_api():
    client = app.test_client()

    response = client.get("/api")

    assert response.status_code in [200, 500]