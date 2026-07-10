from fastapi.testclient import TestClient

from src.api import fastapi_app
from src.api.fastapi_app import app


def test_api_health_and_doctor():
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    doctor = client.get("/llm/doctor")
    assert doctor.status_code == 200
    assert "llm_backend" in doctor.json()


def test_api_validates_search_payload():
    client = TestClient(app)
    res = client.post("/rag/search", json={"query": "", "top_k": 5})
    assert res.status_code == 422


def test_api_kb_docs_endpoint():
    client = TestClient(app)
    res = client.get("/kb/docs")
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_workbench_read_only_endpoints():
    client = TestClient(app)
    assert client.get("/dashboard/summary").status_code == 200
    assert client.get("/settings/public").status_code == 200
    assert client.get("/observability/logs?category=rag").status_code == 200
    assert client.get("/observability/logs?category=invalid").status_code == 422


def test_agent_workspace_bridge_rejects_path_escape():
    client = TestClient(app)
    response = client.post("/integrations/agent-workspace/organize", json={"path": "../outside"})
    assert response.status_code == 422


def test_api_ingest_payload_validation():
    client = TestClient(app)
    res = client.post("/kb/ingest", json={"path": "", "collection": "personal"})
    assert res.status_code == 422


def test_phase6_api_endpoints_exist():
    client = TestClient(app)
    assert client.post("/graph/build", json={}).status_code == 200
    assert client.post("/agents/crew/run", json={"topic": "RAG"}).status_code == 200
    assert client.post("/evaluation/compare", json={"dataset": "examples/sample_eval/rag_eval.jsonl", "config_a": {}, "config_b": {}}).status_code == 200
    assert client.post("/graph/ask", json={"query": "test"}).status_code == 409
    stream = client.post("/rag/ask/stream", json={"query": "RAG"})
    assert stream.status_code == 200
    assert "event: result" in stream.text


def test_api_token_auth_when_enabled(monkeypatch):
    client = TestClient(app)
    old = fastapi_app.config["server"].get("api_auth_enabled")
    fastapi_app.config["server"]["api_auth_enabled"] = True
    monkeypatch.setenv("PERSONAL_AI_API_TOKEN", "secret-token")
    try:
        assert client.get("/health").status_code == 200
        assert client.get("/llm/doctor").status_code == 401
        ok = client.get("/llm/doctor", headers={"Authorization": "Bearer secret-token"})
        assert ok.status_code == 200
    finally:
        fastapi_app.config["server"]["api_auth_enabled"] = old


def test_api_allows_nextjs_loopback_origin():
    client = TestClient(app)
    response = client.options(
        "/rag/ask/stream",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
