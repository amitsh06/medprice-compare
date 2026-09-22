from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_search_endpoint():
    r = client.get("/api/search", params={"q": "metformin"})
    assert r.status_code == 200
    assert all("Metformin" in m["salt"] for m in r.json())


def test_compare_endpoint_with_location():
    r = client.get("/api/medicines/m001/compare", params={"lat": 26.853, "lon": 75.805, "radius_km": 5})
    body = r.json()
    assert r.status_code == 200 and body["stats"]["count"] == len(body["offers"])


def test_compare_404():
    assert client.get("/api/medicines/zzz/compare").status_code == 404


def test_basket_endpoint():
    r = client.post("/api/basket", json={"medicine_ids": ["m001", "m004"]})
    assert r.status_code == 200 and isinstance(r.json(), list)
    assert client.post("/api/basket", json={"medicine_ids": ["bad"]}).status_code == 404


def test_ui_served():
    r = client.get("/")
    assert r.status_code == 200 and "MedPrice" in r.text
