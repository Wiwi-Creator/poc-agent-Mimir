from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_is_available():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "Mimir Console" in response.text
    assert "Routing activity" in response.text


def test_agent_catalog_lists_full_team():
    client = TestClient(app)
    response = client.get("/api/agents")

    assert response.status_code == 200
    agents = response.json()
    assert [agent["id"] for agent in agents] == [
        "mimir",
        "hulk",
        "dragonite",
        "porygon",
        "sage",
        "mewtwo",
        "rotom",
    ]
    assert all(agent["status"] == "online" for agent in agents)
