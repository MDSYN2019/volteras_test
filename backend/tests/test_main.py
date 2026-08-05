from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

def test_application_metadata():
    assert app.title == "Volteras Vehicle Data API"
    assert app.version == "1.0.0"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_vehicle_data_router_is_registered():
    """
    Calling the endpoint without vehicle_id should produce a validation
    error rather than a 404, proving that the router was registered.
    """
    response = client.get("/api/v1/vehicle_data/")

    assert response.status_code == 422


def test_cors_allows_frontend_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_does_not_allow_unknown_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
