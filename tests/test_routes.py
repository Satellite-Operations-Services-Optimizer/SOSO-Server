from fastapi.testclient import TestClient
from event_relay_api.main import app

client = TestClient(app)

def test_create_ground_station():
    response = client.post("/create_ground_station", json={
        "name": "GroundStation1",
        "latitude": 40.7128,
        "longitude": -74.0060
    })
    assert response.status_code == 200
    assert response.json() is not None  # Assuming the endpoint returns the new ground station ID