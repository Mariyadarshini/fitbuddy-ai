from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_plan_fallback():
    payload = {
        "user_id": 1001,
        "username": "Test User",
        "age": 25,
        "weight": 70,
        "goal": "muscle gain",
        "intensity": "medium",
    }
    response = client.post("/api/generate-plan", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["workout_plan"]["days"]) == 7
    assert data["nutrition_tip"]


def test_update_plan():
    response = client.post("/api/update-plan/1001", json={"feedback": "Add more cardio and an extra rest day."})
    assert response.status_code == 200, response.text
    assert len(response.json()["updated_plan"]["days"]) == 7


def test_nutrition_tip():
    response = client.get("/api/nutrition-tip", params={"goal": "weight loss"})
    assert response.status_code == 200
    assert response.json()["nutrition_tip"]
